# M3 Portal Cliente Review

Estado: **82% - listo para piloto**

## Existente

- Rutas: `/portal/login`, `/portal`, `/portal/cases`, `/portal/cases/[id]`, documentos, notificaciones, mensajes y perfil.
- Endpoints: `client-portal/me`, casos, detalle, timeline, documentos, audiencias, notificaciones, mensajes, uploads, downloads y reportes.
- Servicio: `client_portal_service`.
- Seguridad: visibilidad cliente, bloqueo de privados, tenant isolation, control de descarga.
- Tests: `test_client_portal_p6.py`, `client-portal.test.tsx`.

## Validacion funcional

- El cliente solo ve informacion propia y marcada como visible.
- Documentos privados/no aprobados no se exponen.
- Mensajes y subida documental crean auditoria.
- Portal esta preparado para mobile/PWA.

## Gaps

- El frontend mantiene areas demo y necesita mas conexion live-data con backend cloud.
- Reportes del portal son basicos para piloto; falta PDF/descarga formal.
- Subidas requieren UX de progreso, errores y confirmacion documental.
- Falta E2E cross-client en cloud con tenant real.

## Accion

Conectar las acciones principales del portal a API productiva y validar con usuario `client_user`.

Ready: **Si, piloto**

