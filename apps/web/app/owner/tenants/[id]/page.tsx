import { TenantDetail } from "@/components/owner-console";

export default async function OwnerTenantDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TenantDetail tenantId={id} />;
}
