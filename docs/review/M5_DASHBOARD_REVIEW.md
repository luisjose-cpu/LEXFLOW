# M5 Dashboard Gerencial Review

Estado: **80% - listo para piloto**

## Existente

- Frontend: dashboard, command center y componentes KPI/riesgo/productividad.
- Endpoints: `/dashboard/overview`, `/dashboard/search`, KPIs, risks, productivity, judicial-monitoring, communications, ai, legal-intelligence, trends, snapshot.
- Servicios: `CommandCenterService`, KPI, risk, productivity y analytics.
- Tests: `test_command_center_p10.py`, `legal-command-center.test.tsx`.

## Validacion funcional

- Cubre casos activos/criticos, audiencias, documentos pendientes, mensajes, IA, noticias y CAPTCHA.
- Tiene busqueda global preparada.
- Dashboard puede sostener demo ejecutiva de 10 minutos.

## Gaps

- Algunos widgets frontend usan datos demo o agregaciones mock.
- Falta medicion de performance cloud con tenant real.
- Requiere cache/observabilidad para carga de produccion.
- Falta drill-down completo en todos los KPIs.

## Accion

Conectar todos los paneles a APIs vivas y medir SLA: dashboard menor a 2s.

Ready: **Si, piloto**

