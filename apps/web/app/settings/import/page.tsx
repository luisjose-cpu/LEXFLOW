import { AppShell } from "@/components/app-shell";
import { OpsCenter } from "@/components/ops-center";

export default function ImportSettingsPage() {
  return (
    <AppShell>
      <OpsCenter view="import" />
    </AppShell>
  );
}
