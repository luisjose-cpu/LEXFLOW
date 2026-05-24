import { TenantBilling } from "@/components/owner-console";

export default async function OwnerTenantBillingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TenantBilling tenantId={id} />;
}
