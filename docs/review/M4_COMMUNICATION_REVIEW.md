# M4 Comunicacion + WhatsApp Review

Estado: **78% - parcial, piloto con mock**

## Existente

- Endpoints: comunicaciones por expediente, plantillas CRUD, notificaciones send/test/list/mark-read.
- Servicio: `CommunicationService`, `NotificationService`, `WhatsAppService`, `MessageTemplateService`.
- Provider interface: `WhatsAppProvider`, `WhatsAppMockProvider`, `WhatsAppBusinessProvider` placeholder.
- Plantillas: audiencia proxima, documento requerido, informe disponible, actualizacion expediente, proximo paso.
- Tests: `test_communication_p7.py`, `communication-center.test.tsx`.
- Integracion: timeline, portal, expediente y audit logs.

## Validacion funcional

- WhatsApp mock permite demo comercial sin credenciales reales.
- Plantillas y mensajes se auditan.
- Las comunicaciones pueden asociarse a expediente y cliente.

## Gaps

- Falta proveedor WhatsApp Business real con webhooks, plantillas aprobadas y manejo de errores.
- Recordatorios programados requieren scheduler productivo.
- UI aun debe conectarse completamente al backend en todos los estados.
- Costos/mensajeria por tenant no estan cerrados para produccion.

## Accion

Mantener mock para demo, cerrar contrato/provider real y activar feature flag por tenant.

Ready: **Parcial**

