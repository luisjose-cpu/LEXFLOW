# Tenant Management

## Operaciones soportadas

- Crear tenant desde Owner Console usando `/api/v1/owner/tenants`.
- Crear admin inicial del estudio durante el alta owner.
- Crear suscripcion mock, seats, limites SaaS y feature flags por plan durante el alta.
- Consultar handoff de onboarding usando `/api/v1/owner/tenants/{id}/onboarding`.
- Editar metadata comercial.
- Suspender tenant.
- Reactivar tenant.
- Cancelar tenant futuro.
- Cambiar plan.
- Configurar limites.
- Configurar limites duros por tenant desde Owner Console usando `/api/v1/owner/tenants/{id}/limits`.
- Activar modulos por feature flag.
- Revisar uso, health score, tickets y billing.
- Crear demos comerciales aisladas usando `/api/v1/owner/demos`.
- Resetear demos comerciales usando `/api/v1/owner/demos/{id}/reset` antes de una reunion o piloto.

## Auditoria obligatoria

Generar `owner_audit_logs` para:

- creacion de tenant
- alta de tenant con plan, suscripcion y admin inicial
- suspension
- reactivacion
- cambio de plan
- cambio de feature flags
- cambio de limites comerciales
- creacion/resolucion de ticket
- intervencion temporal

## Separacion de datos

Tenant Management muestra metadata operativa y comercial. Contenido legal sensible queda redacted salvo intervencion temporal autorizada.

## Handoff productivo

El Owner Console puede preparar el tenant, pero la password temporal nunca debe enviarse por la app ni quedar en logs. El handoff recomendado es:

- URL de login
- slug del tenant
- correo admin
- password temporal por canal seguro externo
- solicitud de cambio de password y activacion MFA en primer acceso
