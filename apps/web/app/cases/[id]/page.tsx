import { AppShell } from "@/components/app-shell";
import { Case360Workspace } from "@/components/case-360-workspace";
import { getDemoCase360 } from "@/lib/case-360-demo";

export default async function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = getDemoCase360(id);

  return (
    <AppShell>
      <Case360Workspace initialData={data} />
    </AppShell>
  );
}
