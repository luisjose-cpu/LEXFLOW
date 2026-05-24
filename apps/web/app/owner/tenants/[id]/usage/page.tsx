import { TenantUsage } from "@/components/owner-console";

export default async function OwnerTenantUsagePage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TenantUsage tenantId={id} />;
}
