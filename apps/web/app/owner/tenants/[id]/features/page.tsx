import { TenantFeatures } from "@/components/owner-console";

export default async function OwnerTenantFeaturesPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  return <TenantFeatures tenantId={id} />;
}
