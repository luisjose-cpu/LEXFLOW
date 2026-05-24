# Tenant User Invitations

## Estado implementado

- `tenant_admin` puede crear invitaciones de usuario desde Settings.
- Cada invitacion define correo, nombre y rol permitido del tenant.
- El invitado acepta en `/login/invite` y define su propia password.
- El token se guarda solo como hash SHA-256 en `user_invitations`.
- La migracion `20260524_0016` crea persistencia cloud para invitaciones.
- En `local/test` el token puede devolverse para QA; en produccion no se retorna.

## Endpoints

- `POST /api/v1/users/invitations`
- `GET /api/v1/users/invitations`
- `POST /api/v1/auth/invitations/accept`

## Seguridad

- No se crean passwords compartidas para nuevos usuarios.
- No se guarda token plano.
- No se exponen tokens al listar invitaciones.
- Solo roles tenant invitables: `tenant_admin`, `partner`, `lawyer`, `assistant`, `client_user`.
- `client_user` y `lawyer` no pueden crear invitaciones por RBAC.
- Cada creacion y aceptacion registra `audit_log` sin password, hash ni token.

## Pendiente productivo

- Conectar proveedor real de email transaccional.
- Agregar expiracion/reenviar/cancelar invitacion desde UI.
- Politica por tenant para MFA obligatorio al aceptar invitacion.
