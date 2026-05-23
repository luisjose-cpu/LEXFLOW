import { AppShell } from "@/components/app-shell";
import { PlaceholderPage } from "@/components/placeholder-page";

export default function SettingsPage() {
  return (
    <AppShell>
      <PlaceholderPage
        description="Configuracion de tenant, usuarios, roles, permisos, integraciones, billing y controles de auditoria."
        emptyDescription="P10 debe separar configuracion SaaS, tenant lifecycle, seguridad y facturacion."
        emptyTitle="Settings preparado para SaaS"
        eyebrow="LEXFLOW OS"
        module="legal-core"
        title="Settings"
      />
    </AppShell>
  );
}
