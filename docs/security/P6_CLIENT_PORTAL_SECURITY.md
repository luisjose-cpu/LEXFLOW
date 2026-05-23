# P6 Client Portal Security

## Access Boundary

The portal is only available to users with the `client_user` role. Lawyers, assistants, and tenant admins use the internal application, not client portal endpoints.

## Isolation Rules

- Always filter by authenticated tenant.
- Always resolve a linked client before returning portal data.
- Always filter cases by `client_id`.
- Never return internal notes, legal strategy, private documents, or pending judicial updates.
- Never trust a client-provided `client_id`.

## Audited Actions

- Client message creation writes `portal_message_created`.
- Client document upload writes `portal_document_uploaded`.

## Current P6 Linking Strategy

Demo client access is linked by `Client.contact_email == authenticated_user.email`. Production should replace this with an explicit client-user membership table that supports multiple contacts per client.
