import { AppShell } from "@/components/app-shell";
import { BillingSaaS } from "@/components/billing-saas";

export default function PricingPage() {
  return (
    <AppShell>
      <BillingSaaS view="pricing" />
    </AppShell>
  );
}
