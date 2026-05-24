import { AppShell } from "@/components/app-shell";
import { AccountSecurity } from "@/components/account-security";
import { PlaceholderPage } from "@/components/placeholder-page";
import { SecurityAlerts } from "@/components/security-alerts";
import { TenantSecurityPolicy } from "@/components/tenant-security-policy";
import { UserInvitations } from "@/components/user-invitations";
import { Badge, Card, PageHeader } from "@lexflow/ui";
import { Link2, ShieldCheck } from "lucide-react";
import Link from "next/link";

export default function SettingsPage() {
  return (
    <AppShell>
      <div className="grid gap-5">
        <PageHeader
          description="Configuracion de tenant, usuarios, roles, permisos, integraciones, billing y controles de auditoria."
          eyebrow="LEXFLOW OS"
          title="Settings"
        />
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <Card>
            <div className="flex items-center gap-2 text-sm font-semibold text-legal-700">
              <Link2 size={18} aria-hidden="true" />
              <span>Integraciones</span>
            </div>
            <h2 className="mt-4 text-xl font-semibold text-ink">SINOE</h2>
            <p className="mt-2 text-sm leading-6 text-slate-600">
              Credenciales cifradas, prueba de conexion mock y flujo CAPTCHA con intervencion humana.
            </p>
            <div className="mt-4 flex flex-wrap items-center gap-2">
              <Badge>autorizado</Badge>
              <Badge>audit_log</Badge>
              <Badge>no bypass CAPTCHA</Badge>
            </div>
            <Link
              className="mt-5 inline-flex h-10 items-center justify-center gap-2 rounded-md bg-legal-900 px-4 text-sm font-semibold text-white transition hover:bg-legal-700"
              href="/settings/integrations/sinoe"
            >
              <ShieldCheck size={16} aria-hidden="true" />
              Configurar SINOE
            </Link>
          </Card>
          <AccountSecurity />
          <TenantSecurityPolicy />
          <SecurityAlerts />
          <UserInvitations />
          <PlaceholderPage
            description="Preparado para ajustes de tenant lifecycle, seguridad, facturacion y permisos."
            emptyDescription="El siguiente bloque separa usuarios, roles, billing y politicas por tenant."
            emptyTitle="Settings SaaS preparado"
            eyebrow="Legal OS"
            module="legal-core"
            title="Gobierno"
          />
        </section>
      </div>
    </AppShell>
  );
}
