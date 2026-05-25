# LEVEL3_RAG_ENGINE

RAG + Context Engine builds context from tenant memory and returns answers only with cited sources or an explicit no-evidence response.

API: `POST /api/v1/intelligence/rag/query`

Frontend: `/intelligence/rag`

Pipeline: memory -> index -> embeddings -> RAG -> context -> AI response.
