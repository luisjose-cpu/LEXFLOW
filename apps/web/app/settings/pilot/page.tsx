import { AppShell } from "@/components/app-shell";
import { OpsCenter } from "@/components/ops-center";

export default function PilotSettingsPage() {
  return (
    <AppShell>
      <OpsCenter view="pilot" />
    </AppShell>
  );
}
