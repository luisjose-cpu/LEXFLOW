import { AppShell } from "@/components/app-shell";
import { PlaceholderPage } from "@/components/placeholder-page";

export default function CasesPage() {
  return (
    <AppShell>
      <PlaceholderPage
        description="Centro Expediente 360 para estado, etapas, vencimientos, documentos, comunicaciones, automatizaciones e IA."
        emptyDescription="P2 debe entregar listado real de expedientes, filtros, estados, vencimientos y trazabilidad por tenant."
        emptyTitle="Expedientes listo para P2"
        eyebrow="Expediente 360"
        module="expediente360"
        title="Expedientes"
      />
    </AppShell>
  );
}
