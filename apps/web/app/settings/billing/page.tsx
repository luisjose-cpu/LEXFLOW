import { AppShell } from "@/components/app-shell";
import { BillingSaaS } from "@/components/billing-saas";

export default function BillingSettingsPage() {
  return (
    <AppShell>
      <BillingSaaS view="billing" />
    </AppShell>
  );
}
