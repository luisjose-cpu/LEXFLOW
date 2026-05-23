# DECISIONS.md

## Decision Log

### D-0001 - Govern Before Expanding Functionality

Date: 2026-05-22

Decision: P0 establishes governance documents, project rules, architecture direction, security requirements, QA rules, roadmap, risks, and P1 readiness before further functional expansion.

Reason: LEXFLOW has a broad product surface and legal confidentiality requirements. Governance prevents fragmented screens, weak tenant boundaries, and uncontrolled implementation.

Status: Accepted

### D-0002 - Product Spine Is Mandatory

Date: 2026-05-22

Decision: All modules must connect to `CLIENTE -> EXPEDIENTE -> DOCUMENTO -> COMUNICACION -> AUTOMATIZACION -> IA -> INTELIGENCIA -> DECISION`.

Reason: The commercial promise is a legal operating system, not a generic CRM or document manager.

Status: Accepted

### D-0003 - Existing Scaffold Is Preserved

Date: 2026-05-22

Decision: Existing scaffold files are preserved during P0. P0 will not add new functional backend, frontend, database, or Docker behavior.

Reason: Project rules prohibit deleting existing code without explicit authorization. The current request only asks for governance deliverables.

Status: Accepted
