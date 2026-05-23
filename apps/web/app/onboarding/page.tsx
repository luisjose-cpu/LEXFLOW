import { AppShell } from "@/components/app-shell";
import { BillingSaaS } from "@/components/billing-saas";

export default function OnboardingPage() {
  return (
    <AppShell>
      <BillingSaaS view="onboarding" />
    </AppShell>
  );
}
