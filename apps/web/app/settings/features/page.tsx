import { AppShell } from "@/components/app-shell";
import { BillingSaaS } from "@/components/billing-saas";

export default function FeatureSettingsPage() {
  return (
    <AppShell>
      <BillingSaaS view="features" />
    </AppShell>
  );
}
