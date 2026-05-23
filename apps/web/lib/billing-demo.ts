export const billingPlans = [
  {
    code: "START",
    name: "Start",
    price: "$49",
    cadence: "mes",
    description: "Para estudios pequenos que dejan Excel y necesitan operar expedientes con portal.",
    limits: ["3 usuarios", "50 expedientes", "10 GB storage"],
    features: ["expediente360", "client_portal", "dashboard", "mobile_pwa"]
  },
  {
    code: "PRO",
    name: "Pro",
    price: "$149",
    cadence: "mes",
    description: "Operacion legal completa con comunicaciones, monitoreo judicial y control gerencial.",
    limits: ["12 usuarios", "300 expedientes", "1.000 mensajes WhatsApp mock"],
    features: ["expediente360", "client_portal", "whatsapp", "judicial_automation", "dashboard", "mobile_pwa", "automation_studio"]
  },
  {
    code: "AI",
    name: "AI",
    price: "$299",
    cadence: "mes",
    description: "IA practica legal, inteligencia juridica y automatizacion ampliada.",
    limits: ["30 usuarios", "1.000 expedientes", "500 trabajos IA"],
    features: ["expediente360", "client_portal", "whatsapp", "ai", "legal_intelligence", "judicial_automation", "dashboard", "mobile_pwa", "automation_studio", "custom_branding"]
  },
  {
    code: "ENTERPRISE",
    name: "Enterprise",
    price: "Custom",
    cadence: "contrato",
    description: "Gobierno avanzado, dominio propio, API access y limites acordados.",
    limits: ["Usuarios ilimitados", "API access", "Dominio propio"],
    features: ["expediente360", "client_portal", "whatsapp", "ai", "legal_intelligence", "judicial_automation", "dashboard", "mobile_pwa", "custom_branding", "custom_domain", "api_access"]
  }
];

export const featureLabels: Record<string, string> = {
  expediente360: "Expediente 360",
  client_portal: "Portal Cliente",
  whatsapp: "WhatsApp Business",
  ai: "IA practica legal",
  legal_intelligence: "Inteligencia juridica",
  judicial_automation: "Automatizacion judicial",
  dashboard: "Command Center",
  mobile_pwa: "PWA movil",
  automation_studio: "Automation Studio",
  custom_branding: "Marca personalizada",
  custom_domain: "Dominio propio",
  api_access: "API access"
};

export const currentSubscription = {
  plan: "AI",
  status: "trialing",
  seats: 8,
  trialEndsAt: "2026-06-05",
  periodEndsAt: "2026-06-21",
  invoice: "MOCK-20260522-AI",
  amount: "$2.392"
};

export const usageMeters = [
  { feature: "expediente360", label: "Expedientes", used: 3, limit: 1000 },
  { feature: "ai", label: "Trabajos IA", used: 6, limit: 500 },
  { feature: "whatsapp", label: "WhatsApp mock", used: 8, limit: 5000 },
  { feature: "mobile_pwa", label: "Sesiones PWA", used: 12, limit: 1000 },
  { feature: "storage", label: "Storage GB", used: 18, limit: 500 }
];

export const onboardingSteps = [
  { title: "Crear tenant", body: "Datos comerciales, region, moneda, politicas y usuarios iniciales." },
  { title: "Elegir plan", body: "Trial START, PRO, AI o contrato ENTERPRISE con limites y modulos claros." },
  { title: "Activar modulos", body: "Expediente 360, Portal, PWA, IA, inteligencia, judicial y dashboard por feature gate." },
  { title: "Validar cobro mock", body: "Suscripcion, invoice y webhook mock antes de integrar proveedor real." }
];
