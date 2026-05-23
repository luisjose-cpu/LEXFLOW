# P8 IA Practica Legal

## Goal

Create practical legal AI for OCR, document summary, classification, structured extraction, pending items, case summary, and basic search.

## Product Rule

AI never makes legal decisions. Every AI result must include:

`Requiere revisión profesional.`

## Capabilities

- OCR over tenant-scoped documents.
- Document summary.
- Document classification.
- Extraction of dates, parties, deadlines, obligations, and pending items.
- Case summary.
- Basic case search.
- Human approval or rejection for AI jobs.

## Human Review

AI jobs are created as `pending_review`. A professional user with `ai:review` permission must approve or reject the job before the result can be treated as accepted work product.

## Frontend

The `/ai` route shows the practical AI workspace: document pipeline, case intelligence, review queue, structured extraction, and prompt inventory.
