# M7 Automation Studio Review

Estado: **76% - parcial, piloto controlado**

## Existente

- Endpoints: catalogo, workflows CRUD, activar, run manual, trigger run, run history.
- Servicio: `automation_service`.
- Builder UI: `automation-studio`.
- Triggers/actions: SINOE, audiencias, documentos, cliente, portal, IA, comunicaciones.
- Tests: `test_automation_studio_p13.py`, `automation-studio.test.tsx`.
- Auditoria de workflows y runs.

## Validacion funcional

- Estructura TRIGGER -> CONDITION -> ACTION -> AUDIT -> RESULT existe.
- Puede ejecutar workflows mock/controlados.
- Integraciones base con SINOE, documentos, portal, IA y comunicaciones estan modeladas.

## Gaps

- Retry/backoff y cola de jobs no estan cerrados para produccion.
- Builder necesita conexion live-data completa y validacion visual de reglas.
- Feature gates finales por plan/tenant requieren endurecimiento.
- Falta E2E de workflow real con timeline y audit log en cloud.

## Accion

Limitar piloto a workflows seguros, con dry-run, audit log y aprobacion de tenant_admin.

Ready: **Parcial**

