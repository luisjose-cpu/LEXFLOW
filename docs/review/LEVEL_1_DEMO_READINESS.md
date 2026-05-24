# Nivel 1 Demo Readiness

Estado: **demo creada / reutilizada**

LEXFLOW ya cuenta con infraestructura de demo suficiente para Nivel 1:

- Seed demo backend con tenant, usuarios, clientes, expedientes, documentos, audiencias, tareas, fuentes judiciales, updates, noticias, planes y auditoria.
- Endpoint `/api/v1/lexflow-os/demo` para recorrido comercial.
- Endpoint `/api/v1/seed/demo` para datos demo en ambientes no productivos.
- Owner Console con creacion y reset de tenants demo.
- Script comercial existente en `docs/product/PILOT_DEMO_SCRIPT.md`.
- Paquete piloto comercial existente con onboarding, alcance y metricas.

## Demo de 10 minutos recomendada

1. Dashboard: mostrar KPIs, riesgos, SINOE, IA, mensajes y pendientes.
2. Buscar cliente/expediente desde global search.
3. Abrir Expediente360 y explicar timeline operativo.
4. Revisar documentos y audiencia proxima.
5. Ejecutar SINOE mock y mostrar update/timeline/audit.
6. Ejecutar resumen IA y recalcar "requiere revision profesional".
7. Enviar comunicacion WhatsApp mock.
8. Entrar al Portal Cliente y mostrar visibilidad segura.
9. Ejecutar automation controlada/dry-run.
10. Cerrar en audit log y Command Center.

## Criterio de demo aprobada

- No requiere credenciales reales de SINOE, WhatsApp u OpenAI.
- No expone secretos ni datos sensibles.
- Muestra la cadena: cliente -> expediente -> documento -> comunicacion -> automation -> IA -> inteligencia -> decision.
- Puede correrse en local, staging o tenant demo cloud.

## Pendiente antes de piloto con cliente real

- Configurar tenant productivo/piloto.
- Crear admin real del estudio.
- Definir datos demo, anonimizados o reales autorizados.
- Ejecutar smoke cloud con `/health`, login, dashboard, expediente, portal y audit.

