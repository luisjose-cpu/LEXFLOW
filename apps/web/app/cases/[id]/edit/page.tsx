import { AppShell } from "@/components/app-shell";
import { CaseEditForm } from "@/components/operational-core";
import { findCase } from "@/lib/operational-demo";

export default async function CaseEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <CaseEditForm legalCase={findCase(id)} />
    </AppShell>
  );
}
