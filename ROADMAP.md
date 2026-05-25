# ROADMAP.md

## P0 - Project Governance

Goal: establish documents, rules, risks, and readiness for disciplined execution.

Deliverables:

- Required governance documents
- Required folder structure
- Risk register
- Decision log
- P1 readiness checklist

## P1 - Arquitectura Base

Goal: create the monorepo foundation for web, mobile/PWA, API, cloud, testing, premium design, AI, and SaaS growth.

Expected themes:

- Monorepo conventions
- API foundation
- Web shell
- App and package workspaces
- Design system and shared UI
- API skeleton
- Infra skeleton
- Test harness
- Documentation and readiness for backend core

## P2 - Backend Core

Goal: create the multitenant backend core with auth, RBAC, clients, cases, users, roles, and audit.

Expected themes:

- JWT auth and refresh tokens
- RBAC roles and permissions
- Tenant isolation
- Users, clients, cases, roles, and audit endpoints
- Request middleware and service layer
- Backend tests and seed data
- Tenant MFA security policy for role-based enforcement in Settings

## P3 - Base De Datos Completa + Fuentes Judiciales

Goal: implement the MVP database for Expediente 360, authorized judicial updates, Portal Cliente, WhatsApp, AI, and dashboard workflows.

## P4 - Expediente 360 + QA

Goal: deliver the star matter workspace with backend overview/mutation endpoints, premium responsive UI, and QA coverage.

## P5 - Actualizacion Judicial Automatizada

Goal: register, monitor, pause, audit, and approve updates from official or authorized judicial sources with human-in-the-loop CAPTCHA handling.

SINOE extension:

- Settings integration with encrypted credentials.
- SINOE case source linking in Expediente 360.
- Mock adapter first; real adapter only through permitted official/authorized integration.
- CAPTCHA checkpoints remain human-in-the-loop and explicitly forbid bypass.

## Operational Core - Clients, Cases And Expediente 360 Advanced

Goal: connect the daily legal workflow from client intake to case operation, documents, hearings, SINOE updates, communications, AI, automation and intelligence.

Delivered scope:

- Global search over clients, cases, documents, hearings, judicial updates, communications and linked intelligence.
- Client 360 views with onboarding wizard, profile, documents, case grid, timeline, tags, risk, notes, communications and metrics.
- Case center with create/edit and dedicated resource views for documents, hearings, communications, judicial/SINOE, automation and intelligence.
- Backend operational endpoints with tenant isolation and SINOE module consumption.

## Owner Console - SaaS Proprietary Control Plane

Goal: give LEXFLOW's owner a separate control plane to manage tenants, plans, billing, support, feature flags, demos, interventions, audit and system health.

Delivered scope:

- Owner backend tables and endpoints under `/owner/*`.
- Owner JWT auth with MFA TOTP enrollment and login enforcement.
- Owner RBAC boundary separate from tenant users.
- Owner SaaS dashboard, tenant list/detail, usage, billing, feature flags, plans, support, system health, demos, interventions and audit views.
- Security docs for temporary authorized support access and sensitive data redaction.

## P6 - Portal Cliente

Goal: provide secure, mobile-first client access to authorized cases, documents, notifications, and messages.

## P7 - Communication And WhatsApp

Goal: add governed multichannel communication, WhatsApp Business readiness, notifications, and message auditability.

## P8 - Practical Legal AI

Goal: add OCR, classification, extraction, summaries, RAG, and practical legal assistant workflows.

## P9 - Intelligence And Command Center

Goal: turn operational data into legal management decisions.

## P10 - Billing, Automation Studio, Hardening, Cloud, And Release

Goal: subscriptions, automation authoring, production readiness, backups, monitoring, security review, performance, and QA.

## Production Functionalization Plan

Grouped into 8 execution parts:

1. Security/Auth: password change, session revocation, password recovery, MFA, audit hardening.
2. Tenant Onboarding: productive tenant creation, initial admin, invites, branding, import.
3. Storage/Documents: S3 signed URLs, scan, versioning, lifecycle, retention.
4. Integrations: SINOE authorized adapter, WhatsApp Business, email and webhooks.
5. Billing: real payment provider, invoices, limits and subscription enforcement.
6. AI/RAG: OCR, embeddings, vector store, citations and usage controls.
7. QA/Observability: E2E, load tests, logs, metrics, backups and restore drills.
8. Commercial/Compliance: landing, contracts, privacy, DPA, pilot runbooks and support.

Started:

- Part 1 now includes tenant password change, password recovery, MFA TOTP and session revocation.
- Part 2 now includes owner tenant onboarding, tenant user invitations with one-time hashed tokens, resend/cancellation and transactional email provider readiness.
- Part 1 now includes password reset request/confirm with one-time hashed tokens and login recovery screens.
- Part 1 now includes tenant MFA TOTP with encrypted secrets, login enforcement and Settings controls.
- Part 2 now includes Owner tenant onboarding with initial admin, seats, plan subscription, feature flags, limits and handoff readiness.
# Nivel 2 - Modulos altamente vendibles

- War Room Legal: centro operativo en tiempo real.
- Legal CRM: pipeline lead -> cliente -> expediente.
- Engine Rentabilidad: margen, ROI, gastos y horas por expediente.
- Risk Engine: score juridico operativo por expediente, cliente y estudio.
- Demo Mode: datasets, reset y snapshot demo comercial.

# Nivel 3 - Legal OS Intelligence

- Legal Digital Twin: modelo operativo de clientes, abogados, expedientes, carga, riesgo y simulacion.
- Knowledge Vault: biblioteca viva de plantillas, precedentes y prompts.
- Legal Memory Engine: memoria tenant-scoped indexada desde documentos, timeline y comunicaciones.
- Legal Graph: nodos y relaciones persistentes para cliente, expediente, documento y riesgo.
- Copiloto Gerencial: insights ejecutivos con fuentes, recomendaciones y revision profesional.
- Marketplace Legal: catalogo instalable sin pagos reales.
- LATAM Ready Engine: configuracion por pais, moneda, timezone, fuentes y proveedores.
- RAG + Context Engine: respuestas con citas o ausencia explicita de evidencia.
- AI Agents Framework: agentes con permisos, audit log, salida JSON y review required.

# Nivel 4 - Enterprise Legal Intelligence Platform

- Enterprise Multi-Org Engine: organization -> tenant -> department -> team -> user.
- Legal Data Platform: eventos, indexacion, analytics y future ML.
- Orchestration Layer: event bus, rule engine y state manager.
- Enterprise AI Swarm: agentes coordinados con permisos, handoff, audit y revision.
- Observability and Telemetry: metricas por API, IA, SINOE, automation, storage y workers.
- Revenue and Growth Engine: conversion, upsell, health score y churn.
- API and Integration Platform: API keys hash-only, webhooks y OAuth future-ready.
- Compliance and Governance OS: policies, evidence vault, retention y approvals.
- LEXFLOW Cloud: multi-env, backups, DR y HA future-ready.
