import { Button, Card, Input } from "@lexflow/ui";
import { ShieldCheck, Sparkles } from "lucide-react";
import Link from "next/link";

export default function LoginPage() {
  return (
    <main className="grid min-h-screen place-items-center bg-mist px-4 py-8">
      <Card className="w-full max-w-md">
        <div className="flex items-center gap-3">
          <span className="grid h-11 w-11 place-items-center rounded-md bg-legal-900 text-white">
            <Sparkles size={20} aria-hidden="true" />
          </span>
          <div>
            <p className="text-sm font-semibold text-legal-900">LEXFLOW</p>
            <p className="text-xs text-slate-500">Ingreso seguro multiestudio</p>
          </div>
        </div>
        <div className="mt-8 grid gap-4">
          <Input label="Correo" placeholder="socia@estudio.com" type="email" />
          <Input label="Password" placeholder="••••••••" type="password" />
          <Link href="/dashboard">
            <Button>Entrar al Legal OS</Button>
          </Link>
        </div>
        <div className="mt-6 flex items-start gap-2 rounded-lg bg-legal-50 p-3 text-sm text-legal-900">
          <ShieldCheck size={18} aria-hidden="true" />
          <p>Placeholder P1 preparado para auth, tenant context, MFA y auditoria de acceso.</p>
        </div>
      </Card>
    </main>
  );
}
