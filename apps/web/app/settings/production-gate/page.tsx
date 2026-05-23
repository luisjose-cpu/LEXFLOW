import { AppShell } from "@/components/app-shell";
import { OpsCenter } from "@/components/ops-center";

export default function ProductionGateSettingsPage() {
  return (
    <AppShell>
      <OpsCenter view="gate" />
    </AppShell>
  );
}
