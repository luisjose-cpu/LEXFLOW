# M6 IA Practica Legal Review

Estado: **78% - parcial, piloto con mocks**

## Existente

- Endpoints: OCR, resumen, clasificacion, extraccion, resumen expediente, busqueda, jobs, approve/reject.
- Servicios: `AIService`, `OCRService`, `DocumentAnalysisService`, `CaseSummaryService`, `AIJobService`, `AIUsageAuditService`.
- Providers: `MockOCRProvider`, `MockLLMProvider`, `OpenAILLMProvider` preparado.
- Prompts: resumen, clasificacion, fechas, partes, plazos, obligaciones, case summary, smart search, draft assistant.
- Tests: `test_ai_practical_p8.py`, `ai-practical.test.tsx`.
- Regla: salida requiere revision profesional.

## Validacion funcional

- Jobs de IA son auditables y revisables.
- No se toman decisiones juridicas automaticas.
- La IA se integra en documentos, expediente y dashboard.

## Gaps

- OpenAI/OCR real requiere variables, limites, costos y politica de datos.
- Frontend IA aun necesita mas flujos live-data.
- Falta RAG productivo con citas por fuente para respuestas avanzadas.
- Falta matriz de evaluacion de calidad por tipo documental.

## Accion

Activar proveedor real solo por tenant autorizado, con usage caps y logs de revision humana.

Ready: **Parcial**

