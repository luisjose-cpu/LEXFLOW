export const csvTemplates = [
  {
    kind: "clients",
    label: "Clientes",
    required: "name",
    csv: "name,contact_email,risk_profile,tags\nAcme Legal,legal@acme.test,high,corporate;pilot"
  },
  {
    kind: "cases",
    label: "Expedientes",
    required: "client_email, title",
    csv: "client_email,title,external_case_number,status,description\nlegal@acme.test,Cobro Acme,ACME-001,active,Expediente piloto"
  },
  {
    kind: "documents",
    label: "Documentos",
    required: "case_external_case_number, filename",
    csv: "case_external_case_number,filename,content_type,classification,is_client_visible\nACME-001,demanda-acme.pdf,application/pdf,pleading,true"
  }
];

export const importFlow = [
  "Bootstrap tenant",
  "Clientes dry-run",
  "Clientes commit",
  "Expedientes commit",
  "Manifiesto documental",
  "Upload bytes",
  "Verify + scan"
];

export const pilotMetrics = [
  { label: "Clientes", value: "2", trend: "importados" },
  { label: "Expedientes", value: "1", trend: "piloto" },
  { label: "Documentos", value: "1", trend: "pending upload" },
  { label: "Audit", value: "4", trend: "eventos ops" }
];

export const pilotChecklist = [
  { label: "Tenant configurado", ok: true },
  { label: "Usuarios internos creados", ok: true },
  { label: "Clientes cargados", ok: true },
  { label: "Expedientes cargados", ok: true },
  { label: "Manifiesto documental", ok: true },
  { label: "Storage listo", ok: true },
  { label: "Documentos verificados", ok: false },
  { label: "Demo E2E ejecutada", ok: false }
];

export const productionGate = [
  { key: "PostgreSQL", status: "required", detail: "DATABASE_URL productivo" },
  { key: "Secrets", status: "required", detail: "JWT/S3 fuertes" },
  { key: "CORS", status: "required", detail: "sin localhost y solo HTTPS" },
  { key: "Seeds", status: "required", detail: "demo seed off" },
  { key: "Tests", status: "pass", detail: "lint/test/build/API" },
  { key: "Pentest", status: "pending", detail: "externo" }
];

export const gateCommands = [
  "npm run lint",
  "npm run test",
  "npm run build",
  "npm run test:api",
  "powershell -NoProfile -ExecutionPolicy Bypass -File scripts/production-gate.ps1",
  "npm run cloud:wait-revision",
  "npm run cloud:smoke",
  "npm run cloud:evidence",
  "npm run cloud:public-ready"
];
