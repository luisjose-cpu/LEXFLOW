# P7 Comunicacion + WhatsApp Business

## Goal

Create an intelligent communication system for portal, email-ready messages, WhatsApp Business readiness, future push notifications, automatic messages, reminders, document requests, hearing notices, and history.

## Backend Services

- CommunicationService
- NotificationService
- WhatsAppService
- MessageTemplateService
- CommunicationAuditService

## Providers

- WhatsAppProvider interface
- WhatsAppMockProvider
- WhatsAppBusinessProvider placeholder

## Tables

- `communication_threads`
- `communication_messages`
- `message_templates`
- `notification_rules`

## Endpoints

- `GET /api/v1/cases/{case_id}/communications`
- `POST /api/v1/cases/{case_id}/communications`
- `GET /api/v1/message-templates`
- `POST /api/v1/message-templates`
- `PATCH /api/v1/message-templates/{template_id}`
- `DELETE /api/v1/message-templates/{template_id}`
- `GET /api/v1/notifications`
- `POST /api/v1/notifications/send`
- `POST /api/v1/notifications/test`
- `POST /api/v1/notifications/{notification_id}/mark-read`

## Templates

- `audiencia_proxima`
- `documento_requerido`
- `informe_disponible`
- `actualizacion_expediente`
- `proximo_paso`

## Product Flow

Client portal messages create a client-safe inbound message and also bridge into the internal communication thread so lawyers can answer from the case workspace.
