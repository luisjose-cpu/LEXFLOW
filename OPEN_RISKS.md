# OPEN_RISKS

## P15 - LEXFLOW OS Final

- Produccion publica no debe activarse hasta completar proveedor WhatsApp Business real, vector store productivo, pasarela de pago real, pentest externo y monitoreo cloud.
- RAG P15 es deterministico para piloto; produccion requiere embeddings reales, store cifrado, retencion por tenant y evaluaciones de calidad.
- Marketplace queda future-ready, no instalado como canal de extensiones productivo.
- Integraciones judiciales reales requieren permisos, politicas de uso y manejo humano de CAPTCHA.

Estado: `RELEASE READY FOR PILOT / NOT READY FOR PUBLIC PRODUCTION`.

- Production secrets are not yet managed by a secret manager.
- Upload malware scanning is not implemented.
- Live judicial integrations are mock-only and require legal/source review.
- Real billing webhooks are not implemented or signature-verified.
- Backup restore drill evidence is pending.
- CI/CD gates are not yet enforced remotely.
- Automation sensitive actions need production approval gates before broad rollout.
- Observability is basic and needs metrics backend, tracing, and alert routing.
