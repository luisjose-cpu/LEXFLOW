export type TenantId = string;
export type UserId = string;
export type ClientId = string;
export type CaseId = string;

export type ProductModule =
  | "legal-core"
  | "expediente360"
  | "portal"
  | "communication"
  | "ai"
  | "intelligence"
  | "automation"
  | "billing"
  | "analytics";

export type CaseStatus = "active" | "paused" | "closed" | "risk";

export interface LegalMetric {
  label: string;
  value: string;
  trend: string;
}

export interface NavigationItem {
  label: string;
  href: string;
  module: ProductModule;
}
