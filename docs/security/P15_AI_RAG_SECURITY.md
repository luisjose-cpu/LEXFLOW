# P15 - AI and RAG Security

## Principios

- No hay decisiones juridicas autonomas.
- Toda salida IA requiere revision profesional.
- Toda respuesta RAG cita fuente o declara ausencia de evidencia.
- El acceso se controla por RBAC y tenant isolation.
- Las consultas IA/RAG quedan auditadas.

## Riesgos controlados

- Alucinacion: mitigada por fuente obligatoria o respuesta sin evidencia.
- Fuga cross-tenant: mitigada por `tenant_id` en todas las consultas.
- Exposicion de documentos cliente: depende de permisos y visibilidad ya definidos en Portal Cliente.
- Uso no trazable: mitigado con `audit_logs` para RAG, busqueda global y copiloto.

## Produccion pendiente

- Vector store cifrado con backups.
- Politicas de retencion y eliminacion por tenant.
- Evaluaciones de prompts con fixtures legales.
- Revision de privacidad para proveedores IA.
- Red team/pentest sobre endpoints IA.
