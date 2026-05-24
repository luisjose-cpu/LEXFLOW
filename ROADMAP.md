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
