import { AppShell } from "@/components/app-shell";
import { ClientEditForm } from "@/components/operational-core";
import { findClient } from "@/lib/operational-demo";

export default async function ClientEditPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <ClientEditForm client={findClient(id)} />
    </AppShell>
  );
}
