import { AppShell } from "@/components/app-shell";
import { CaseResourcePage } from "@/components/operational-core";
import { findCase } from "@/lib/operational-demo";

export default async function CaseAutomationPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <CaseResourcePage legalCase={findCase(id)} type="automation" />
    </AppShell>
  );
}
