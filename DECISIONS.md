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

### D-0004 - SINOE Starts With Mock Adapter And Human CAPTCHA

Date: 2026-05-24

Decision: SINOE integration begins with `SinoeAdapterMock`, encrypted tenant credentials, explicit RBAC, audit logs and a human-in-the-loop CAPTCHA checkpoint flow.

Reason: SINOE access must be authorized and compliant. LEXFLOW must not evade CAPTCHA, break anti-bot measures, automate CAPTCHA resolution or ship a real connector without confirming an allowed integration path.

Status: Accepted

### D-0005 - Operational Core Consumes Existing Judicial Automation

Date: 2026-05-24

Decision: Client, case and Expediente 360 advanced views expose judicial status through the existing SINOE case source and judicial update contracts.

Reason: Judicial automation already has a governed module with CAPTCHA human-in-the-loop, audit and evidence rules. Recreating that logic inside client or case screens would fragment compliance and increase operational risk.

Status: Accepted

### D-0006 - Owner Console Is A Separate Control Plane

Date: 2026-05-24

Decision: Owner Console is implemented as a SaaS owner control plane under `/owner` and `/api/v1/owner/*`, separated from normal tenant workflows.

Reason: LEXFLOW's product owner must manage tenants, billing, plans, support, feature flags, demos and health without becoming a privileged tenant user or exposing sensitive legal content by default.

Status: Accepted

### D-0007 - Owner Auth Uses Dedicated JWT Scope

Date: 2026-05-24

Decision: Owner Console authentication uses dedicated owner JWTs with `scope=owner`, refresh-token versioning and a separate owner bootstrap script.

Reason: Tenant JWTs must not grant control-plane access, and production/staging owner access cannot depend on ad hoc headers.

Status: Accepted
# 2026-05-24 - Nivel 2 commercial modules

Decision: implementar War Room, CRM, Financial, Risk y Demo Mode como capa agregadora del core existente.

Reason: Nivel 2 debe ser vendible y conectado, no un grupo de pantallas aisladas. El modulo consume Expediente360, SINOE, IA, Automation, Dashboard, Portal y Owner sin duplicar logica judicial.

Consequences: los proveedores reales siguen tras feature flags; los calculos son deterministas y auditables para piloto.
