import { AppShell } from "@/components/app-shell";
import { ClientOnboardingWizard } from "@/components/operational-core";

export default function ClientCreatePage() {
  return (
    <AppShell>
      <ClientOnboardingWizard />
    </AppShell>
  );
}
