from __future__ import annotations

from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.domain.models import User
from app.services.billing import billing_service


TRIGGERS = [
    "CASE_CREATED",
    "CASE_STATUS_CHANGED",
    "HEARING_CREATED",
    "HEARING_UPCOMING",
    "DOCUMENT_REQUESTED",
    "DOCUMENT_UPLOADED",
    "JUDICIAL_UPDATE_APPROVED",
    "CAPTCHA_REQUIRED",
    "CLIENT_MESSAGE_RECEIVED",
    "TASK_OVERDUE",
    "AI_SUMMARY_COMPLETED",
    "LEGAL_NEWS_ALERT_CREATED",
]

ACTIONS = [
    "CREATE_TASK",
    "SEND_PORTAL_NOTIFICATION",
    "SEND_WHATSAPP_MESSAGE_MOCK",
    "SEND_EMAIL_PREPARED",
    "CREATE_CASE_EVENT",
    "REQUEST_DOCUMENT",
    "CHANGE_CASE_STATUS",
    "ASSIGN_USER",
    "CREATE_CLIENT_ALERT",
    "CREATE_INTERNAL_ALERT",
    "RUN_AI_SUMMARY_MOCK",
    "LINK_LEGAL_NEWS_TO_CASE",
]


class AutomationService:
    def catalog(self) -> dict[str, object]:
        return {
            "triggers": TRIGGERS,
            "actions": ACTIONS,
            "conditions": ["ALWAYS", "CASE_STATUS_EQUALS", "PAYLOAD_EQUALS", "FEATURE_ENABLED"],
        }

    def list_workflows(self, db: Session, *, tenant_id: UUID | str) -> list[dict[str, object]]:
        rows = db.scalars(
            select(dbm.AutomationWorkflow)
            .where(dbm.AutomationWorkflow.tenant_id == str(tenant_id), dbm.AutomationWorkflow.deleted_at.is_(None))
            .order_by(dbm.AutomationWorkflow.created_at.desc())
        ).all()
        return [self.serialize_workflow(row) for row in rows]

    def create_workflow(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        actor: User,
        name: str,
        trigger_key: str,
        description: str,
        conditions: list[dict[str, object]],
        actions: list[dict[str, object]],
        request_id: str | None,
    ) -> dict[str, object]:
        self.ensure_feature_enabled(db, tenant_id=tenant_id)
        self.validate_trigger(trigger_key)
        self.validate_actions(actions)
        workflow = dbm.AutomationWorkflow(tenant_id=str(tenant_id), name=name, description=description, trigger_key=trigger_key, status="draft")
        db.add(workflow)
        db.flush()
        self.replace_steps(db, workflow=workflow, conditions=conditions, actions=actions)
        self.record_audit(db, tenant_id=tenant_id, actor=actor, action="automation.create_workflow", entity_type="automation_workflow", entity_id=workflow.id, request_id=request_id, metadata={"trigger_key": trigger_key})
        db.commit()
        db.refresh(workflow)
        return self.serialize_workflow(workflow)

    def update_workflow(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        workflow_id: UUID | str,
        actor: User,
        name: str | None,
        description: str | None,
        trigger_key: str | None,
        conditions: list[dict[str, object]] | None,
        actions: list[dict[str, object]] | None,
        request_id: str | None,
    ) -> dict[str, object]:
        self.ensure_feature_enabled(db, tenant_id=tenant_id)
        workflow = self.workflow_or_404(db, tenant_id=tenant_id, workflow_id=workflow_id)
        if trigger_key:
            self.validate_trigger(trigger_key)
            workflow.trigger_key = trigger_key
        if name is not None:
            workflow.name = name
        if description is not None:
            workflow.description = description
        if actions is not None:
            self.validate_actions(actions)
        if conditions is not None or actions is not None:
            self.replace_steps(db, workflow=workflow, conditions=conditions or [self.serialize_condition(item) for item in workflow.conditions], actions=actions or [self.serialize_action(item) for item in workflow.actions])
        self.record_audit(db, tenant_id=tenant_id, actor=actor, action="automation.update_workflow", entity_type="automation_workflow", entity_id=workflow.id, request_id=request_id, metadata={})
        db.commit()
        db.refresh(workflow)
        return self.serialize_workflow(workflow)

    def activate(self, db: Session, *, tenant_id: UUID | str, workflow_id: UUID | str, actor: User, request_id: str | None) -> dict[str, object]:
        self.ensure_feature_enabled(db, tenant_id=tenant_id)
        workflow = self.workflow_or_404(db, tenant_id=tenant_id, workflow_id=workflow_id)
        if not workflow.actions:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workflow requires at least one action")
        workflow.status = "active"
        self.record_audit(db, tenant_id=tenant_id, actor=actor, action="automation.activate_workflow", entity_type="automation_workflow", entity_id=workflow.id, request_id=request_id, metadata={"status": "active"})
        db.commit()
        return self.serialize_workflow(workflow)

    def delete(self, db: Session, *, tenant_id: UUID | str, workflow_id: UUID | str, actor: User, request_id: str | None) -> None:
        workflow = self.workflow_or_404(db, tenant_id=tenant_id, workflow_id=workflow_id)
        workflow.soft_delete()
        self.record_audit(db, tenant_id=tenant_id, actor=actor, action="automation.delete_workflow", entity_type="automation_workflow", entity_id=workflow.id, request_id=request_id, metadata={})
        db.commit()

    def run_workflow(self, db: Session, *, tenant_id: UUID | str, workflow_id: UUID | str, actor: User, event_payload: dict[str, object], dry_run: bool, request_id: str | None) -> dict[str, object]:
        self.ensure_feature_enabled(db, tenant_id=tenant_id)
        workflow = self.workflow_or_404(db, tenant_id=tenant_id, workflow_id=workflow_id)
        if workflow.status != "active" and not dry_run:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Workflow must be active before running")
        run = dbm.AutomationRun(tenant_id=str(tenant_id), workflow_id=workflow.id, trigger_key=workflow.trigger_key, status="running", event_payload_json=event_payload)
        db.add(run)
        db.flush()

        condition_results = [self.evaluate_condition(condition, event_payload) for condition in sorted(workflow.conditions, key=lambda item: item.order_index)]
        for index, result in enumerate(condition_results):
            db.add(dbm.AutomationRunStep(tenant_id=str(tenant_id), run_id=run.id, order_index=index, step_type="condition", key=result["key"], status="succeeded" if result["passed"] else "skipped", result_json=result))
        passed = all(result["passed"] for result in condition_results) if condition_results else True
        action_results: list[dict[str, object]] = []
        if passed:
            for offset, action in enumerate(sorted(workflow.actions, key=lambda item: item.order_index), start=len(condition_results)):
                result = self.execute_action(db, tenant_id=tenant_id, actor=actor, action=action, event_payload=event_payload, dry_run=dry_run)
                action_results.append(result)
                db.add(dbm.AutomationRunStep(tenant_id=str(tenant_id), run_id=run.id, order_index=offset, step_type="action", key=action.action_type, status="succeeded", result_json=result))
        run.status = "succeeded" if passed else "skipped"
        run.completed_at = dbm.now_utc()
        run.result_json = {"conditions_passed": passed, "actions": action_results, "dry_run": dry_run}
        self.record_audit(db, tenant_id=tenant_id, actor=actor, action="automation.run_workflow", entity_type="automation_run", entity_id=run.id, request_id=request_id, metadata={"workflow_id": workflow.id, "dry_run": str(dry_run)})
        db.commit()
        db.refresh(run)
        return self.serialize_run(run)

    def trigger(self, db: Session, *, tenant_id: UUID | str, trigger_key: str, actor: User, event_payload: dict[str, object], request_id: str | None) -> list[dict[str, object]]:
        self.ensure_feature_enabled(db, tenant_id=tenant_id)
        self.validate_trigger(trigger_key)
        workflows = db.scalars(
            select(dbm.AutomationWorkflow).where(
                dbm.AutomationWorkflow.tenant_id == str(tenant_id),
                dbm.AutomationWorkflow.trigger_key == trigger_key,
                dbm.AutomationWorkflow.status == "active",
                dbm.AutomationWorkflow.deleted_at.is_(None),
            )
        ).all()
        return [self.run_workflow(db, tenant_id=tenant_id, workflow_id=workflow.id, actor=actor, event_payload=event_payload, dry_run=False, request_id=request_id) for workflow in workflows]

    def list_runs(self, db: Session, *, tenant_id: UUID | str, workflow_id: UUID | str | None = None) -> list[dict[str, object]]:
        query = select(dbm.AutomationRun).where(dbm.AutomationRun.tenant_id == str(tenant_id)).order_by(dbm.AutomationRun.created_at.desc())
        if workflow_id:
            query = query.where(dbm.AutomationRun.workflow_id == str(workflow_id))
        return [self.serialize_run(run) for run in db.scalars(query).all()]

    def replace_steps(self, db: Session, *, workflow: dbm.AutomationWorkflow, conditions: list[dict[str, object]], actions: list[dict[str, object]]) -> None:
        workflow.conditions.clear()
        workflow.actions.clear()
        db.flush()
        for index, item in enumerate(conditions):
            workflow.conditions.append(dbm.AutomationCondition(tenant_id=workflow.tenant_id, order_index=index, condition_type=str(item.get("condition_type", "ALWAYS")), config_json=dict(item.get("config", {}))))
        for index, item in enumerate(actions):
            workflow.actions.append(dbm.AutomationAction(tenant_id=workflow.tenant_id, order_index=index, action_type=str(item["action_type"]), config_json=dict(item.get("config", {}))))

    def evaluate_condition(self, condition: dbm.AutomationCondition, payload: dict[str, object]) -> dict[str, object]:
        if condition.condition_type == "ALWAYS":
            return {"key": condition.condition_type, "passed": True}
        if condition.condition_type == "CASE_STATUS_EQUALS":
            expected = condition.config_json.get("status")
            return {"key": condition.condition_type, "passed": payload.get("case_status") == expected, "expected": expected, "actual": payload.get("case_status")}
        if condition.condition_type == "PAYLOAD_EQUALS":
            key = str(condition.config_json.get("key"))
            expected = condition.config_json.get("value")
            return {"key": condition.condition_type, "passed": payload.get(key) == expected, "field": key}
        if condition.condition_type == "FEATURE_ENABLED":
            return {"key": condition.condition_type, "passed": True, "feature": condition.config_json.get("feature_key")}
        return {"key": condition.condition_type, "passed": False, "error": "unknown_condition"}

    def execute_action(self, db: Session, *, tenant_id: UUID | str, actor: User, action: dbm.AutomationAction, event_payload: dict[str, object], dry_run: bool) -> dict[str, object]:
        case_id = event_payload.get("case_id")
        title = str(action.config_json.get("title", action.action_type.replace("_", " ").title()))
        if dry_run:
            return {"action_type": action.action_type, "status": "prepared", "dry_run": True}
        if action.action_type == "CREATE_TASK" and case_id:
            task = dbm.Task(tenant_id=str(tenant_id), case_id=str(case_id), assigned_user_id=str(actor.id), title=title, status="open")
            db.add(task)
            db.flush()
            return {"action_type": action.action_type, "status": "created", "task_id": task.id}
        if action.action_type == "SEND_PORTAL_NOTIFICATION":
            notification = dbm.Notification(tenant_id=str(tenant_id), user_id=str(actor.id), case_id=str(case_id) if case_id else None, title=title, body=str(action.config_json.get("body", "Automatizacion ejecutada")), channel="portal", status="sent")
            db.add(notification)
            db.flush()
            return {"action_type": action.action_type, "status": "sent", "notification_id": notification.id}
        if action.action_type == "CREATE_CASE_EVENT" and case_id:
            event = dbm.CaseEvent(tenant_id=str(tenant_id), case_id=str(case_id), event_type="automation", title=title, description=str(action.config_json.get("body", "")))
            db.add(event)
            db.flush()
            return {"action_type": action.action_type, "status": "created", "case_event_id": event.id}
        if action.action_type == "RUN_AI_SUMMARY_MOCK":
            job = dbm.AiJob(tenant_id=str(tenant_id), case_id=str(case_id) if case_id else None, job_type="case_summary", status="completed", result_json={"summary": "Resumen IA mock generado por Automation Studio.", "requires_review": True}, completed_at=dbm.now_utc())
            db.add(job)
            db.flush()
            return {"action_type": action.action_type, "status": "completed", "ai_job_id": job.id}
        return {"action_type": action.action_type, "status": "prepared", "provider": "mock"}

    def ensure_feature_enabled(self, db: Session, *, tenant_id: UUID | str) -> None:
        features = billing_service.features(db, tenant_id=tenant_id)["features"]
        enabled = any(item["feature_key"] == "automation_studio" and item["enabled"] for item in features)
        if not enabled:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Automation Studio requires plan upgrade")

    def workflow_or_404(self, db: Session, *, tenant_id: UUID | str, workflow_id: UUID | str) -> dbm.AutomationWorkflow:
        workflow = db.scalars(select(dbm.AutomationWorkflow).where(dbm.AutomationWorkflow.tenant_id == str(tenant_id), dbm.AutomationWorkflow.id == str(workflow_id), dbm.AutomationWorkflow.deleted_at.is_(None))).first()
        if not workflow:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        return workflow

    def validate_trigger(self, trigger_key: str) -> None:
        if trigger_key not in TRIGGERS:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported trigger")

    def validate_actions(self, actions: list[dict[str, object]]) -> None:
        if not actions:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Workflow requires at least one action")
        for action in actions:
            if action.get("action_type") not in ACTIONS:
                raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported action")

    def serialize_workflow(self, workflow: dbm.AutomationWorkflow) -> dict[str, object]:
        return {
            "id": workflow.id,
            "name": workflow.name,
            "description": workflow.description,
            "trigger_key": workflow.trigger_key,
            "status": workflow.status,
            "conditions": [self.serialize_condition(item) for item in sorted(workflow.conditions, key=lambda row: row.order_index)],
            "actions": [self.serialize_action(item) for item in sorted(workflow.actions, key=lambda row: row.order_index)],
        }

    def serialize_condition(self, condition: dbm.AutomationCondition) -> dict[str, object]:
        return {"id": condition.id, "condition_type": condition.condition_type, "config": condition.config_json, "order_index": condition.order_index}

    def serialize_action(self, action: dbm.AutomationAction) -> dict[str, object]:
        return {"id": action.id, "action_type": action.action_type, "config": action.config_json, "order_index": action.order_index}

    def serialize_run(self, run: dbm.AutomationRun) -> dict[str, object]:
        return {
            "id": run.id,
            "workflow_id": run.workflow_id,
            "trigger_key": run.trigger_key,
            "status": run.status,
            "result": run.result_json,
            "error_message": run.error_message,
            "steps": [
                {"id": step.id, "step_type": step.step_type, "key": step.key, "status": step.status, "result": step.result_json}
                for step in sorted(run.steps, key=lambda item: item.order_index)
            ],
        }

    def record_audit(self, db: Session, *, tenant_id: UUID | str, actor: User, action: str, entity_type: str, entity_id: str, request_id: str | None, metadata: dict[str, object]) -> None:
        db.add(dbm.AuditLog(tenant_id=str(tenant_id), actor_user_id=str(actor.id), action=action, entity_type=entity_type, entity_id=entity_id, request_id=request_id, metadata_json=metadata))


automation_service = AutomationService()
