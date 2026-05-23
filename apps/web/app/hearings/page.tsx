import { AppShell } from "@/components/app-shell";
import { PlaceholderPage } from "@/components/placeholder-page";

export default function HearingsPage() {
  return (
    <AppShell>
      <PlaceholderPage
        description="Calendario de audiencias, vencimientos, alertas, responsables, preparacion documental y seguimiento."
        emptyDescription="P2 debe integrar eventos, responsables, recordatorios y auditoria de cambios criticos."
        emptyTitle="Audiencias listo para agenda legal"
        eyebrow="Agenda judicial"
        module="legal-core"
        title="Audiencias"
      />
    </AppShell>
  );
}
