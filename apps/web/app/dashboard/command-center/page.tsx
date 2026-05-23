import { AppShell } from "@/components/app-shell";
import { LegalCommandCenter } from "@/components/legal-command-center";

export default function CommandCenterPage() {
  return (
    <AppShell>
      <LegalCommandCenter mode="command" />
    </AppShell>
  );
}
