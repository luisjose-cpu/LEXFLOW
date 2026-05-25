# LEVEL2 Risk Engine

Risk Engine calcula score 0-100:

- 0-30: verde
- 31-70: ambar
- 71-100: rojo

Factores: plazos, documentos, audiencias, CAPTCHA, IA pendiente, inactividad, errores sync y automatizaciones fallidas.

Endpoints:

- `GET /api/v1/risk`
- `GET /api/v1/risk/cases/{case_id}`
- `GET /api/v1/risk/clients/{client_id}`

Ruta web: `/risk`.

La salida no decide; explica riesgos y requiere criterio profesional.

