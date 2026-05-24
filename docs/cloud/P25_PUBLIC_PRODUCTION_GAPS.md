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
- `billing_webhook_signature_required`: activar `REQUIRE_BILLING_WEBHOOK_SIGNATURE=true` antes de webhooks reales.
- `credential_encryption_key_configured`: configurar `CREDENTIAL_ENCRYPTION_KEY` dedicado y fuerte para credenciales cifradas y MFA.
- `failed_login_backend_redis`: configurar `FAILED_LOGIN_BACKEND=redis` para bloqueo de intentos fallidos entre replicas.
- `malware_scanner_configured`: configurar `MALWARE_SCANNER_PROVIDER` real antes de cargas publicas.

Si el cloud todavia no muestra `malware_scanner_configured`, significa que Render no esta corriendo el ultimo commit. Ejecutar `npm run cloud:revision` y redeploy latest `master`.

## Variables a cerrar

```env
OPENAI_API_KEY=replace-with-real-openai-key
WHATSAPP_BUSINESS_TOKEN=replace-with-real-whatsapp-business-token
BILLING_PROVIDER_SECRET=replace-with-real-billing-provider-secret
REQUIRE_BILLING_WEBHOOK_SIGNATURE=true
CREDENTIAL_ENCRYPTION_KEY=replace-with-real-dedicated-credential-encryption-key
FAILED_LOGIN_BACKEND=redis
```

Para produccion publica tambien validar:

```env
STORAGE_BACKEND=s3
S3_ENDPOINT=https://provider.example
S3_ACCESS_KEY=replace-with-real-access-key
S3_SECRET_KEY=replace-with-real-secret-key
S3_BUCKET=lexflow-production
REQUIRE_VERIFIED_DOCUMENT_DOWNLOADS=true
MALWARE_SCANNER_PROVIDER=clamav
```

Los valores `replace-with...`, `placeholder`, `dummy-secret` o equivalentes no cuentan como secretos validos aunque tengan longitud suficiente.

Aplicar y revisar tambien:

- `infra/cloud/s3-lifecycle-policy.json`
- `infra/cloud/s3-cors-policy.json`
- `docs/cloud/S3_STORAGE_POLICY.md`

## Validacion

1. Guardar secrets reales en Render/Vercel, nunca en el repositorio.
2. Redeploy API y web.
3. Ejecutar:

```powershell
$env:LEXFLOW_API_URL="https://lexflow-api.onrender.com"
$env:LEXFLOW_WEB_URL="https://lexflow-web-nine.vercel.app"
npm run cloud:revision -- -Strict
npm run cloud:evidence
npm run cloud:public-ready
npm run db:restore-evidence
```

4. Confirmar en el JSON:

- `readiness.production_ready=true`
- `readiness.public_production_ready=true`
- `readiness.blockers=0`
- `readiness.warnings=0`
- `external_providers.ai=live`
- `external_providers.whatsapp=live`
- `external_providers.billing=live`
- `credential_encryption_key_configured` sin warning.
- `ALLOWED_ORIGINS` usa solo origenes HTTPS.
- `LEXFLOW_WEB_URL` apunta al dominio publico HTTPS.
- `REQUIRE_OWNER_MFA=true`.
- `db:restore-evidence` valida un restore drill real reciente con `restore_completed` y sin secretos en la evidencia.

## Riesgos pendientes

- Validar contratos comerciales y terminos de uso de cada proveedor.
- Configurar monitoreo externo y alertas fuera de Render/Vercel.
- Ejecutar pentest y registrar remediaciones.
- Ejecutar restore drill real con evidencia RPO/RTO en `reports/restore/` y aprobar `npm run db:restore-evidence`.
- Revisar CSP estricta por dominio cuando se cierren proveedores externos finales; Next ya aplica headers base de hardening.
