# P15 - LEXFLOW OS Architecture

## Capa OS

P15 agrega una capa de orquestacion sobre los modulos existentes. No reemplaza Expediente 360, Portal, IA, Inteligencia, Billing ni Automation; los conecta como sistema operativo legal.

## Backend

Servicio: `app.services.lexflow_os.LexflowOSService`

Endpoints:

- `GET /api/v1/lexflow-os/memory`
- `POST /api/v1/lexflow-os/rag/query`
- `POST /api/v1/lexflow-os/search`
- `POST /api/v1/lexflow-os/copilot`
- `GET /api/v1/lexflow-os/agents`
- `GET /api/v1/lexflow-os/graph`
- `GET /api/v1/lexflow-os/marketplace`
- `GET /api/v1/lexflow-os/demo`
- `GET /api/v1/lexflow-os/release-status`

## Frontend

Rutas:

- `/lexflow-os`
- `/demo`
- `/`

Componente principal: `LexflowOSFinal`.

## RAG Legal

El flujo conceptual es:

`documento -> OCR -> chunks -> embeddings -> vector_store -> consulta_contextual -> respuesta_con_fuentes`

La implementacion P15 usa datos deterministas de demo para QA estable. Produccion requiere vector store administrado, cifrado, retencion y monitoreo.

## Grafo

El Legal Graph vincula:

`Cliente -> Expediente -> Documento -> Comunicacion -> Automatizacion -> IA -> Inteligencia -> Decision`

Cada nodo y arista debe mantenerse tenant-scoped.
