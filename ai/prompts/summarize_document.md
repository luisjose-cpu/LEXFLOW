# summarize_document

Purpose: summarize one legal document for a professional user.

Rules:

- Do not give legal advice or decide strategy.
- Preserve parties, dates, amounts, obligations, deadlines, and procedural status when present.
- Mark uncertainty explicitly.
- Output must end with: `Requiere revisión profesional.`

Output shape:

- `summary`
- `key_points`
- `risks_or_missing_information`
- `next_review_items`
- `disclaimer`
