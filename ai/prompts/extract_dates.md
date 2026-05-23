# extract_dates

Purpose: extract relevant dates from one document or case context.

Rules:

- Return dates in ISO format when possible.
- Preserve the original text snippet for each date.
- Mark approximate or ambiguous dates.
- Do not calculate deadlines unless the source clearly defines the rule.
- Output must end with: `Requiere revisión profesional.`

Output fields: `date`, `label`, `source_text`, `confidence`, `needs_review`.
