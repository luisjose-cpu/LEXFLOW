# P7 Communication Architecture

## Model

Communication is organized by case thread:

- `communication_threads`: one tenant/case/client scoped conversation.
- `communication_messages`: message history with direction, channel, status, provider id, and template metadata.
- `message_templates`: reusable tenant-scoped templates.
- `notification_rules`: event-to-channel/template mapping.

## Channel Strategy

P7 supports:

- `portal`: active local channel.
- `whatsapp`: active through WhatsAppMockProvider.
- `email`: payload-ready placeholder.
- `push`: future placeholder.

## Provider Boundary

WhatsApp sends go through `WhatsAppProvider`. Production WhatsApp Business integration must replace the provider without changing CommunicationService or route contracts.

## Audit

Every created communication message writes `communication_message_created`. Notifications write `notification_sent` and mark-read writes `notification_marked_read`.
