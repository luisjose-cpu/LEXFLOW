# M1 Expediente360 Review

Estado: **86% - listo para piloto**

## Existente

- Pantallas: `/cases`, `/cases/create`, `/cases/[id]`, vistas operativas de documentos, audiencias, comunicaciones, judicial, automation e intelligence.
- Frontend: `Case360Workspace`, `Case360`, `OperationalCore`.
- Endpoints: `/api/v1/cases/{case_id}/overview`, eventos, tareas, audiencias, documentos, status, comunicaciones, judicial, automation e intelligence.
- Servicios: `operational_core_service`, flujo de auditoria de casos y servicios relacionados.
- Modelos: `Client`, `Case`, `CaseEvent`, `Document`, `Hearing`, `Task`, `JudicialUpdate`, `CommunicationMessage`, `AuditLog`.
- Tests: `test_case_overview_p4.py`, `test_operational_core.py`, `case-360*.test.tsx`, `operational-core.test.tsx`.
- Docs: `docs/product/P4_EXPEDIENTE_360.md`, `docs/product/OPERATIONAL_CORE_CLIENTS_CASES_360.md`.

## Validacion funcional

- Cliente, estado, riesgo, responsable, juzgado, materia y submateria estan representados.
- Timeline global existe y consume eventos, documentos, audiencias, judicial updates y comunicaciones.
- Integraciones IA, SINOE y Automation aparecen en el expediente como superficies conectadas.
- Acciones criticas generan auditoria en backend.
- La API aplica tenant isolation y RBAC mediante dependencias de permisos.

## Gaps

- Upload documental avanzado aun requiere endurecer UX y evidencias de storage en cloud.
- Audiencias necesitan captura completa de resultado, acta y recordatorios productivos.
- Checklists, versionado documental y graph legal estan parcialmente preparados, no cerrados.
- Falta E2E cloud estable desde login hasta expediente, SINOE mock, IA y timeline.

## Accion

Prioridad inmediata: cerrar el flujo real de expediente desde cliente -> expediente -> documento -> audiencia -> SINOE mock -> IA -> comunicacion -> audit log, medido en cloud.

Ready: **Si, piloto**

