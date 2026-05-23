from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.db import models as dbm
from app.services.ai_practical import AI_REVIEW_DISCLAIMER
from app.services.case_overview import audit_case_action, get_case_or_404


class LegalSourceAdapterMock:
    def __init__(self, source_key: str, category: str) -> None:
        self.source_key = source_key
        self.category = category

    def fetch(self, source: dbm.LegalNewsSource) -> list[dict[str, object]]:
        now = datetime.now(UTC)
        title_by_source = {
            "lp_derecho": "LP Derecho: nuevo criterio sobre notificacion procesal",
            "juris_pe": "Juris.pe: precedente relevante en materia laboral",
            "el_peruano": "El Peruano: norma publicada para cumplimiento regulatorio",
            "spij": "SPIJ: actualizacion normativa sistematizada",
            "poder_judicial": "Poder Judicial: jurisprudencia destacada de sala suprema",
            "mpfn": "MPFN: directiva institucional para investigacion fiscal",
            "sinoe": "SINOE: aviso oficial de casilla electronica",
        }
        tags_by_source = {
            "lp_derecho": ["procesal", "notificacion"],
            "juris_pe": ["jurisprudencia", "laboral"],
            "el_peruano": ["normativa", "cumplimiento"],
            "spij": ["normativa", "busqueda"],
            "poder_judicial": ["jurisprudencia", "civil"],
            "mpfn": ["penal", "fiscalia"],
            "sinoe": ["judicial", "alerta"],
        }
        return [
            {
                "external_id": f"{self.source_key}-mock-001",
                "title": title_by_source.get(self.source_key, f"{source.name}: actualizacion legal"),
                "url": f"{source.source_url.rstrip('/')}/mock-001",
                "category": self.category,
                "summary": "Actualizacion simulada desde adapter mock permitido; no se realiza scraping agresivo.",
                "tags": tags_by_source.get(self.source_key, [self.category]),
                "trend_score": "rising",
                "published_at": now,
                "metadata_json": {"adapter": self.source_key, "mode": "mock"},
            }
        ]


class LegalNewsAIService:
    def summarize(self, news: dbm.LegalNews) -> str:
        base = news.summary or "Contenido legal pendiente de revision."
        return f"Resumen IA: {base} Impacto operativo sugerido: revisar expedientes relacionados por etiquetas {', '.join(news.tags)}. {AI_REVIEW_DISCLAIMER}"


class LegalNewsSourceService:
    def __init__(self) -> None:
        self.adapters = {
            "lp_derecho": LegalSourceAdapterMock("lp_derecho", "news"),
            "juris_pe": LegalSourceAdapterMock("juris_pe", "jurisprudence"),
            "el_peruano": LegalSourceAdapterMock("el_peruano", "normative"),
            "spij": LegalSourceAdapterMock("spij", "normative"),
            "poder_judicial": LegalSourceAdapterMock("poder_judicial", "jurisprudence"),
            "mpfn": LegalSourceAdapterMock("mpfn", "institutional"),
            "sinoe": LegalSourceAdapterMock("sinoe", "judicial"),
        }

    def list(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.LegalNewsSource]:
        return db.scalars(
            select(dbm.LegalNewsSource).where(dbm.LegalNewsSource.tenant_id == str(tenant_id), dbm.LegalNewsSource.deleted_at.is_(None)).order_by(dbm.LegalNewsSource.name.asc())
        ).all()

    def get(self, db: Session, *, tenant_id: UUID | str, source_id: UUID | str) -> dbm.LegalNewsSource:
        source = db.scalar(
            select(dbm.LegalNewsSource).where(
                dbm.LegalNewsSource.id == str(source_id),
                dbm.LegalNewsSource.tenant_id == str(tenant_id),
                dbm.LegalNewsSource.deleted_at.is_(None),
            )
        )
        if not source:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal news source not found")
        return source

    def create(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        name: str,
        source_url: str,
        category: str,
        adapter_key: str,
        actor_user_id: UUID | str | None,
        request_id: str | None,
    ) -> dbm.LegalNewsSource:
        source = dbm.LegalNewsSource(
            tenant_id=str(tenant_id),
            name=name,
            source_url=source_url,
            category=category,
            adapter_key=adapter_key,
            config_json={"policy": "api_rss_or_mock_only", "no_aggressive_scraping": True},
        )
        db.add(source)
        db.flush()
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="legal_news_source_created",
            entity_type="legal_news_source",
            entity_id=source.id,
            request_id=request_id,
            metadata={"adapter_key": adapter_key},
        )
        db.commit()
        return source

    def sync(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        source_id: UUID | str,
        actor_user_id: UUID | str | None,
        request_id: str | None,
    ) -> dict[str, object]:
        source = self.get(db, tenant_id=tenant_id, source_id=source_id)
        adapter = self.adapters.get(source.adapter_key, LegalSourceAdapterMock(source.adapter_key, source.category))
        created = []
        for item in adapter.fetch(source):
            existing = db.scalar(
                select(dbm.LegalNews).where(
                    dbm.LegalNews.tenant_id == str(tenant_id),
                    dbm.LegalNews.source_id == source.id,
                    dbm.LegalNews.external_id == item["external_id"],
                )
            )
            if existing:
                continue
            news = dbm.LegalNews(
                tenant_id=str(tenant_id),
                source_id=source.id,
                external_id=str(item["external_id"]),
                title=str(item["title"]),
                url=str(item["url"]),
                category=str(item["category"]),
                summary=str(item["summary"]),
                tags=list(item["tags"]),
                trend_score=str(item["trend_score"]),
                published_at=item["published_at"],
                metadata_json=dict(item["metadata_json"]),
            )
            db.add(news)
            db.flush()
            created.append(news)
        source.last_checked_at = datetime.now(UTC)
        self._ensure_alerts_and_tags(db, tenant_id=tenant_id, news_items=created)
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="legal_news_source_synced",
            entity_type="legal_news_source",
            entity_id=source.id,
            request_id=request_id,
            metadata={"created": len(created), "adapter_key": source.adapter_key},
        )
        db.commit()
        return {"source_id": source.id, "created": len(created), "last_checked_at": source.last_checked_at.isoformat()}

    def _ensure_alerts_and_tags(self, db: Session, *, tenant_id: UUID | str, news_items: list[dbm.LegalNews]) -> None:
        tag_service.ensure_many(db, tenant_id=tenant_id, names=sorted({tag for item in news_items for tag in item.tags}))
        for item in news_items:
            if item.trend_score == "rising":
                db.add(
                    dbm.LegalAlert(
                        tenant_id=str(tenant_id),
                        news_id=item.id,
                        title=f"Tendencia detectada: {item.title[:120]}",
                        body="Nueva fuente legal sincronizada con impacto potencial en expedientes relacionados.",
                        severity="medium",
                        tags=item.tags,
                    )
                )


class LegalNewsService:
    def list(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        search: str | None = None,
        tag: str | None = None,
        category: str | None = None,
    ) -> list[dbm.LegalNews]:
        query = select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == str(tenant_id), dbm.LegalNews.status == "published")
        if search:
            like = f"%{search}%"
            query = query.where(or_(dbm.LegalNews.title.ilike(like), dbm.LegalNews.summary.ilike(like), dbm.LegalNews.ai_summary.ilike(like)))
        if category:
            query = query.where(dbm.LegalNews.category == category)
        items = db.scalars(query.order_by(dbm.LegalNews.published_at.desc().nullslast(), dbm.LegalNews.created_at.desc())).all()
        if tag:
            items = [item for item in items if tag in item.tags]
        return items

    def get(self, db: Session, *, tenant_id: UUID | str, news_id: UUID | str) -> dbm.LegalNews:
        news = db.scalar(select(dbm.LegalNews).where(dbm.LegalNews.id == str(news_id), dbm.LegalNews.tenant_id == str(tenant_id)))
        if not news:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal news not found")
        return news

    def summarize(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        news_id: UUID | str,
        actor_user_id: UUID | str | None,
        request_id: str | None,
    ) -> dbm.LegalNews:
        news = self.get(db, tenant_id=tenant_id, news_id=news_id)
        news.ai_summary = legal_news_ai_service.summarize(news)
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="legal_news_ai_summarized",
            entity_type="legal_news",
            entity_id=news.id,
            request_id=request_id,
            metadata={"source_id": news.source_id},
        )
        db.commit()
        return news

    def favorite(self, db: Session, *, tenant_id: UUID | str, news_id: UUID | str, actor_user_id: UUID | str, request_id: str | None) -> dict[str, object]:
        news = self.get(db, tenant_id=tenant_id, news_id=news_id)
        favorite = db.scalar(
            select(dbm.LegalNewsFavorite).where(
                dbm.LegalNewsFavorite.tenant_id == str(tenant_id),
                dbm.LegalNewsFavorite.news_id == news.id,
                dbm.LegalNewsFavorite.user_id == str(actor_user_id),
            )
        )
        if not favorite:
            favorite = dbm.LegalNewsFavorite(tenant_id=str(tenant_id), news_id=news.id, user_id=str(actor_user_id))
            db.add(favorite)
            db.flush()
            audit_case_action(
                db,
                tenant_id=tenant_id,
                actor_user_id=actor_user_id,
                action="legal_news_favorited",
                entity_type="legal_news",
                entity_id=news.id,
                request_id=request_id,
            )
        db.commit()
        return {"news_id": news.id, "favorite": True}

    def link_case(
        self,
        db: Session,
        *,
        tenant_id: UUID | str,
        news_id: UUID | str,
        case_id: UUID | str,
        actor_user_id: UUID | str | None,
        note: str | None,
        request_id: str | None,
    ) -> dict[str, object]:
        news = self.get(db, tenant_id=tenant_id, news_id=news_id)
        get_case_or_404(db, tenant_id=tenant_id, case_id=case_id)
        link = db.scalar(
            select(dbm.LegalNewsCaseLink).where(
                dbm.LegalNewsCaseLink.tenant_id == str(tenant_id),
                dbm.LegalNewsCaseLink.news_id == news.id,
                dbm.LegalNewsCaseLink.case_id == str(case_id),
            )
        )
        if not link:
            link = dbm.LegalNewsCaseLink(tenant_id=str(tenant_id), news_id=news.id, case_id=str(case_id), linked_by_user_id=str(actor_user_id) if actor_user_id else None, note=note)
            db.add(link)
            db.flush()
        audit_case_action(
            db,
            tenant_id=tenant_id,
            actor_user_id=actor_user_id,
            action="legal_news_linked_to_case",
            entity_type="legal_news",
            entity_id=news.id,
            request_id=request_id,
            metadata={"case_id": str(case_id), "link_id": link.id},
        )
        db.commit()
        return {"id": link.id, "news_id": news.id, "case_id": str(case_id)}

    def related_to_case(self, db: Session, *, tenant_id: UUID | str, case_id: UUID | str) -> list[dbm.LegalNews]:
        links = db.scalars(select(dbm.LegalNewsCaseLink).where(dbm.LegalNewsCaseLink.tenant_id == str(tenant_id), dbm.LegalNewsCaseLink.case_id == str(case_id))).all()
        if not links:
            return []
        ids = [link.news_id for link in links]
        return db.scalars(select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == str(tenant_id), dbm.LegalNews.id.in_(ids)).order_by(dbm.LegalNews.created_at.desc())).all()


class LegalAlertService:
    def list(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.LegalAlert]:
        return db.scalars(select(dbm.LegalAlert).where(dbm.LegalAlert.tenant_id == str(tenant_id)).order_by(dbm.LegalAlert.created_at.desc())).all()


class LegalTagService:
    def ensure_many(self, db: Session, *, tenant_id: UUID | str, names: list[str]) -> list[dbm.LegalTag]:
        rows = []
        for name in names:
            existing = db.scalar(select(dbm.LegalTag).where(dbm.LegalTag.tenant_id == str(tenant_id), func.lower(dbm.LegalTag.name) == name.lower()))
            if existing:
                rows.append(existing)
                continue
            tag = dbm.LegalTag(tenant_id=str(tenant_id), name=name)
            db.add(tag)
            rows.append(tag)
        return rows

    def list(self, db: Session, *, tenant_id: UUID | str) -> list[dbm.LegalTag]:
        return db.scalars(select(dbm.LegalTag).where(dbm.LegalTag.tenant_id == str(tenant_id)).order_by(dbm.LegalTag.name.asc())).all()


class LegalTrendService:
    def trends(self, db: Session, *, tenant_id: UUID | str) -> list[dict[str, object]]:
        news = db.scalars(select(dbm.LegalNews).where(dbm.LegalNews.tenant_id == str(tenant_id), dbm.LegalNews.status == "published")).all()
        counter = Counter(tag for item in news for tag in item.tags)
        return [
            {"tag": tag, "count": count, "momentum": "rising" if count >= 2 else "watch"}
            for tag, count in counter.most_common(8)
        ]


def serialize_source(source: dbm.LegalNewsSource) -> dict[str, object]:
    return {
        "id": source.id,
        "name": source.name,
        "source_url": source.source_url,
        "category": source.category,
        "adapter_key": source.adapter_key,
        "status": source.status,
        "last_checked_at": source.last_checked_at.isoformat() if source.last_checked_at else None,
    }


def serialize_news(news: dbm.LegalNews, *, favorite: bool = False) -> dict[str, object]:
    return {
        "id": news.id,
        "source_id": news.source_id,
        "title": news.title,
        "url": news.url,
        "category": news.category,
        "summary": news.summary,
        "ai_summary": news.ai_summary,
        "status": news.status,
        "tags": news.tags,
        "trend_score": news.trend_score,
        "favorite": favorite,
        "published_at": news.published_at.isoformat() if news.published_at else None,
    }


def serialize_alert(alert: dbm.LegalAlert) -> dict[str, object]:
    return {
        "id": alert.id,
        "news_id": alert.news_id,
        "title": alert.title,
        "body": alert.body,
        "severity": alert.severity,
        "status": alert.status,
        "tags": alert.tags,
        "created_at": alert.created_at.isoformat(),
    }


legal_news_ai_service = LegalNewsAIService()
tag_service = LegalTagService()
legal_news_source_service = LegalNewsSourceService()
legal_news_service = LegalNewsService()
legal_alert_service = LegalAlertService()
legal_trend_service = LegalTrendService()
