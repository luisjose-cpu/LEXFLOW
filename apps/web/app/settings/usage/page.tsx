import { AppShell } from "@/components/app-shell";
import { BillingSaaS } from "@/components/billing-saas";

export default function UsageSettingsPage() {
  return (
    <AppShell>
      <BillingSaaS view="usage" />
    </AppShell>
  );
}
