import { AppShell } from "@/components/app-shell";
import { ClientDetail } from "@/components/operational-core";
import { findClient } from "@/lib/operational-demo";

export default async function ClientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <AppShell>
      <ClientDetail client={findClient(id)} />
    </AppShell>
  );
}
