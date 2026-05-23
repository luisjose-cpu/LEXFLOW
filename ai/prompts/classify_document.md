# classify_document

Purpose: classify one document into a practical legal operations category.

Allowed categories:

- demanda
- contestacion
- poder
- resolucion
- cedula
- audiencia
- prueba
- contrato
- informe
- otro

Rules:

- Return confidence as low, medium, or high.
- Explain the evidence used for classification.
- Do not infer facts beyond the document text.
- Output must end with: `Requiere revisión profesional.`
