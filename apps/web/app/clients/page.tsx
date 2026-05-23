import { AppShell } from "@/components/app-shell";
import { PlaceholderPage } from "@/components/placeholder-page";

export default function ClientsPage() {
  return (
    <AppShell>
      <PlaceholderPage
        description="Registro multi-tenant de clientes, contactos, permisos de portal, riesgo, actividad y relacion con expedientes."
        emptyDescription="P2 debe definir modelo de cliente, contactos, autorizaciones, busqueda y auditoria de cambios."
        emptyTitle="Clientes preparado para legal-core"
        eyebrow="Cliente"
        module="legal-core"
        title="Clientes"
      />
    </AppShell>
  );
}
