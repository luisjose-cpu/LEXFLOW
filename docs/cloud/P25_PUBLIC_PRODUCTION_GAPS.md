# P25 - Public Production Gaps

## Estado actual

LEXFLOW esta listo para piloto cloud controlado cuando `/readiness` devuelve:

- `production_ready=true`
- `status=ready`
- `blockers=0`

Produccion publica comercial requiere ademas:

- `public_production_ready=true`
- `warnings=0`

## Gaps actuales esperados

Mientras no se configuren proveedores reales, readiness mantiene warnings:

- `openai_configured`: configurar `OPENAI_API_KEY` antes de usar IA real.
- `whatsapp_configured`: configurar `WHATSAPP_BUSINESS_TOKEN` antes de despacho WhatsApp real.
- `billing_configured`: configurar `BILLING_PROVIDER_SECRET` antes de suscripciones/pagos reales.

## Variables a cerrar

```env
OPENAI_API_KEY=replace-with-real-openai-key
WHATSAPP_BUSINESS_TOKEN=replace-with-real-whatsapp-business-token
BILLING_PROVIDER_SECRET=replace-with-real-billing-provider-secret
```

Para produccion publica tambien validar:

```env
STORAGE_BACKEND=s3
S3_ENDPOINT=https://provider.example
S3_ACCESS_KEY=replace-with-real-access-key
S3_SECRET_KEY=replace-with-real-secret-key
S3_BUCKET=lexflow-production
REQUIRE_VERIFIED_DOCUMENT_DOWNLOADS=true
```

## Validacion

1. Guardar secrets reales en Render/Vercel, nunca en el repositorio.
2. Redeploy API y web.
3. Ejecutar:

```powershell
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
$env:LEXFLOW_WEB_URL="https://lexflow-web-nine.vercel.app"
npm run cloud:evidence
```

4. Confirmar en el JSON:

- `readiness.production_ready=true`
- `readiness.public_production_ready=true`
- `readiness.blockers=0`
- `readiness.warnings=0`
- `external_providers.ai=live`
- `external_providers.whatsapp=live`
- `external_providers.billing=live`

## Riesgos pendientes

- Validar contratos comerciales y terminos de uso de cada proveedor.
- Configurar monitoreo externo y alertas fuera de Render/Vercel.
- Ejecutar pentest y registrar remediaciones.
- Ejecutar restore drill real con evidencia RPO/RTO en `reports/restore/`.
