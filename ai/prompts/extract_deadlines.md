# extract_deadlines

Purpose: identify procedural or operational deadlines.

Rules:

- Prefer explicit deadlines found in the source.
- If a deadline is implied, mark it as `needs_professional_calculation`.
- Do not decide whether a deadline is valid, expired, or legally binding.
- Include the source text and basis.
- Output must end with: `Requiere revisión profesional.`
