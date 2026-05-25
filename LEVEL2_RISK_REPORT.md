# LEVEL2 Risk Report

## Seguridad

- Endpoints aplican RBAC mediante permisos `warroom:read`, `crm:*`, `financial:*`, `risk:read`, `demo:write`.
- Todo modelo nuevo contiene `tenant_id`.
- Acciones criticas CRM, financial y demo crean `audit_logs`.
- `client_user` queda bloqueado para vistas financieras y comerciales.

## Riesgos abiertos

- War Room en produccion requiere cache y observabilidad para no sobrecargar DB.
- Financial necesita controles de acceso mas finos por rol si el estudio separa finanzas de abogados.
- Demo reset no debe ejecutarse sobre tenant productivo real sin flag/confirmacion adicional.

