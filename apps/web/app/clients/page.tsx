import { AppShell } from "@/components/app-shell";
import { ClientList, ClientSearch } from "@/components/operational-core";
import { PageHeader } from "@lexflow/ui";
import Link from "next/link";

export default function ClientsPage() {
  return (
    <AppShell>
      <div className="grid gap-5">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <PageHeader
            description="Clientes con identificacion, contactos, riesgo, documentos, comunicaciones, expedientes, SINOE, IA y timeline."
            eyebrow="Cliente"
            title="Clientes"
          />
          <Link className="inline-flex h-10 items-center justify-center rounded-md bg-legal-900 px-4 text-sm font-semibold text-white" href="/clients/create">
            Nuevo cliente
          </Link>
        </div>
        <ClientSearch />
        <ClientList />
      </div>
    </AppShell>
  );
}
