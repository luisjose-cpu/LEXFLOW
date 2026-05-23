import { AppShell } from "@/components/app-shell";
import { PlaceholderPage } from "@/components/placeholder-page";

export default function DocumentsPage() {
  return (
    <AppShell>
      <PlaceholderPage
        description="Repositorio legal con storage S3-compatible, OCR, clasificacion, permisos, versionado y trazabilidad."
        emptyDescription="P2/P3 deben definir carga, metadatos, clasificacion, busqueda y retencion documental."
        emptyTitle="Documentos preparado para storage y OCR"
        eyebrow="Documento"
        module="legal-core"
        title="Documentos"
      />
    </AppShell>
  );
}
