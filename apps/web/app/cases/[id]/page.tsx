import { AppShell } from "@/components/app-shell";
import {
  AlertsPanel,
  AuditSummaryPanel,
  CaseHeader,
  CaseTimeline,
  ClientSummaryCard,
  CommunicationsPanel,
  DocumentsPanel,
  HearingsPanel,
  IntelligenceRelatedPanel,
  JudicialUpdatesPanel,
  NextActionsPanel,
  TasksPanel
} from "@/components/case-360";
import { getDemoCase360 } from "@/lib/case-360-demo";
import {
  CaptchaCheckpointModal,
  JudicialSourcesPanel,
  JudicialUpdatesList,
  SourceConfigurationForm,
  demoJudicialSources,
  demoJudicialUpdates
} from "@/components/judicial-sources";
import {
  CaptchaCheckpointModal as SinoeCaptchaCheckpointModal,
  SinoeCaseSourceForm,
  SinoeUpdateHistory,
  SinoeUpdatePanel
} from "@/components/sinoe-integration";

export default async function CaseDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const data = getDemoCase360(id);

  return (
    <AppShell>
      <div className="grid gap-5">
        <CaseHeader data={data} />
        <section className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          <ClientSummaryCard data={data} />
          <NextActionsPanel items={data.next_actions} />
          <AlertsPanel items={data.alerts} />
          <CaseTimeline items={data.timeline} />
          <DocumentsPanel items={data.documents} />
          <HearingsPanel items={data.hearings} />
          <TasksPanel items={data.tasks} />
          <JudicialUpdatesPanel items={data.judicial_updates} />
          <JudicialSourcesPanel sources={demoJudicialSources} />
          <SinoeUpdatePanel sources={data.case_sources} />
          <SinoeUpdateHistory updates={data.judicial_updates} />
          <JudicialUpdatesList updates={demoJudicialUpdates} />
          <SourceConfigurationForm />
          <SinoeCaseSourceForm caseId={data.case.id} />
          <CommunicationsPanel items={data.communications} />
          <IntelligenceRelatedPanel items={data.related_intelligence} />
          <AuditSummaryPanel data={data.audit_summary} />
        </section>
        <CaptchaCheckpointModal checkpoint={{ id: "chk-1", status: "pending", reason: "captcha_required" }} />
        <SinoeCaptchaCheckpointModal checkpoint={{ id: "sinoe-chk-1", status: "pending", reason: "captcha_required" }} />
      </div>
    </AppShell>
  );
}
