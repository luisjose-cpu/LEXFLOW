# Pilot Demo Script

## Duracion objetivo

7 a 10 minutos.

## Audiencia

Socio, abogado senior, asistente operativo y responsable administrativo del estudio.

## Mensaje central

LEXFLOW convierte informacion dispersa en una cadena operativa gobernada: expediente, documento, comunicacion, automatizacion, IA, inteligencia y decision.

## Preparacion

- Abrir `http://localhost:3041`.
- Tener disponibles rutas `/dashboard`, `/cases/case-demo`, `/lexflow-os`, `/demo`, `/portal`, `/automation`.
- Usar tenant demo o tenant piloto.
- Recordar: IA requiere revision profesional y RAG cita fuente o declara ausencia de evidencia.

## Guion minuto a minuto

### 0:00 - 1:00 | Problema

Mostrar la landing y decir:

> Hoy el estudio trabaja con Excel, Drive, carpetas, correos y WhatsApp. El problema no es falta de herramientas; es falta de sistema operativo.

Punto a reforzar:

- LEXFLOW no es una pantalla aislada.
- LEXFLOW conecta cliente, expediente, documento, comunicacion, automatizacion, IA, inteligencia y decision.

### 1:00 - 2:00 | Socio ve dashboard

Ruta: `/dashboard`.

Mostrar:

- Casos activos.
- Riesgos.
- Audiencias.
- Documentos pendientes.
- Comunicaciones.
- IA.
- CAPTCHA pendientes.

Frase sugerida:

> El socio no entra a buscar archivos; entra a decidir donde poner atencion.

### 2:00 - 3:20 | Expediente 360

Ruta: `/cases/case-demo` o expediente demo disponible.

Mostrar:

- Cliente.
- Estado.
- Riesgo.
- Timeline.
- Documentos.
- Audiencias.
- Tareas.
- Comunicaciones.
- Auditoria.

Frase sugerida:

> El expediente es el centro de gravedad. Todo lo demas vive conectado a el.

### 3:20 - 4:20 | Actualizacion judicial mock

Mostrar panel de fuentes judiciales o flujo mock.

Puntos:

- Fuentes autorizadas.
- No evasion CAPTCHA.
- Si aparece CAPTCHA: pausa, notificacion, intervencion humana y auditoria.

Frase sugerida:

> Automatizamos lo permitido y pausamos lo que exige intervencion humana.

### 4:20 - 5:20 | IA practica + RAG Legal

Ruta: `/ai` o `/lexflow-os`.

Mostrar:

- OCR/resumen/clasificacion.
- RAG pipeline.
- Respuesta con fuentes.
- Respuesta sin evidencia cuando corresponda.

Frase sugerida:

> La IA no decide. Organiza, resume y busca evidencia para que el abogado revise.

### 5:20 - 6:20 | WhatsApp mock + Portal Cliente

Rutas: `/communication` y `/portal`.

Mostrar:

- Mensaje mock.
- Portal del cliente.
- Documento visible.
- Timeline publico.
- Restriccion de notas internas.

Frase sugerida:

> El cliente ve lo que debe ver, no la estrategia interna del estudio.

### 6:20 - 7:40 | Cliente responde y abogado ve comunicacion

Mostrar:

- Mensaje entrante.
- Historial.
- Relacion con expediente.
- Auditoria.

Frase sugerida:

> WhatsApp deja de ser memoria informal y pasa a ser comunicacion trazable.

### 7:40 - 8:50 | Automation Studio

Ruta: `/automation`.

Mostrar:

- Trigger.
- Condition.
- Action.
- Audit.
- Result.

Frase sugerida:

> El estudio puede convertir reglas operativas repetibles en flujos controlados.

### 8:50 - 10:00 | Cierre y decision

Ruta: `/demo` o `/lexflow-os`.

Cerrar con:

- Demo E2E.
- Release ready for pilot.
- Production not ready.
- Propuesta de piloto de 2 a 4 semanas.

Pregunta final:

> Si este flujo funcionara con 5 expedientes reales de su estudio, que resultado haria que valga la pena avanzar?

## Objeciones esperadas

- Seguridad: explicar tenant isolation, RBAC, auditoria, no credenciales hardcodeadas y produccion pendiente.
- IA: explicar fuentes, revision profesional y no decision juridica.
- Migracion: iniciar con 3 a 5 expedientes, no todo el historico.
- WhatsApp: mock en piloto salvo proveedor real aprobado.
- Judicial: adapters mock/autorizados, sin evasion CAPTCHA.
