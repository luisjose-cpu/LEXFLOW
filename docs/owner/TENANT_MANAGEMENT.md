# Tenant Management

## Operaciones soportadas

- Crear tenant.
- Editar metadata comercial.
- Suspender tenant.
- Reactivar tenant.
- Cancelar tenant futuro.
- Cambiar plan.
- Configurar limites.
- Activar modulos por feature flag.
- Revisar uso, health score, tickets y billing.

## Auditoria obligatoria

Generar `owner_audit_logs` para:

- creacion de tenant
- suspension
- reactivacion
- cambio de plan
- cambio de feature flags
- creacion/resolucion de ticket
- intervencion temporal

## Separacion de datos

Tenant Management muestra metadata operativa y comercial. Contenido legal sensible queda redacted salvo intervencion temporal autorizada.
