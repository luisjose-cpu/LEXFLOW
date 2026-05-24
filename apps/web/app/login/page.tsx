"use client";

import { Button, Card } from "@lexflow/ui";
import { Building2, ShieldCheck, Sparkles } from "lucide-react";
import { useRouter } from "next/navigation";
import React from "react";
import { FormEvent, useMemo, useState } from "react";

type LoginResponse = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  user: {
    id: string;
    tenant_id: string;
    email: string;
    full_name: string;
    role: string;
  };
};

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "https://lexflow-api.onrender.com";

function Field({
  label,
  name,
  value,
  onChange,
  placeholder,
  type = "text",
  autoComplete
}: {
  label: string;
  name: string;
  value: string;
  onChange: (value: string) => void;
  placeholder: string;
  type?: string;
  autoComplete?: string;
}) {
  return (
    <label className="grid gap-2 text-sm font-semibold text-ink">
      {label}
      <input
        autoComplete={autoComplete}
        className="h-11 rounded-md border border-slate-200 bg-white px-3 text-sm font-normal text-ink outline-none transition placeholder:text-slate-400 focus:border-legal-500 focus:shadow-[0_0_0_3px_rgba(36,153,232,0.18)]"
        name={name}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder}
        type={type}
        value={value}
      />
    </label>
  );
}

export default function LoginPage() {
  const router = useRouter();
  const [tenantSlug, setTenantSlug] = useState("piloto");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "error">("idle");
  const [error, setError] = useState("");
  const canSubmit = useMemo(() => tenantSlug.trim() && email.trim() && password, [email, password, tenantSlug]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!canSubmit || status === "loading") return;

    setStatus("loading");
    setError("");

    try {
      const response = await fetch(`${API_URL}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email: email.trim(),
          password,
          tenant_slug: tenantSlug.trim()
        })
      });

      if (!response.ok) {
        throw new Error(response.status === 401 ? "Credenciales o estudio incorrectos." : "No pudimos iniciar sesion.");
      }

      const body = (await response.json()) as LoginResponse;
      localStorage.setItem("lexflow.access_token", body.access_token);
      localStorage.setItem("lexflow.refresh_token", body.refresh_token);
      localStorage.setItem("lexflow.user", JSON.stringify(body.user));
      localStorage.setItem("lexflow.tenant_id", body.user.tenant_id);
      localStorage.setItem("lexflow.tenant_slug", tenantSlug.trim());
      router.push("/dashboard");
    } catch (caught) {
      setStatus("error");
      setError(caught instanceof Error ? caught.message : "No pudimos iniciar sesion.");
    }
  }

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
        <form className="mt-8 grid gap-4" onSubmit={handleSubmit}>
          <Field
            autoComplete="organization"
            label="Estudio"
            name="tenant_slug"
            onChange={setTenantSlug}
            placeholder="piloto"
            value={tenantSlug}
          />
          <Field
            autoComplete="email"
            label="Correo"
            name="email"
            onChange={setEmail}
            placeholder="socia@estudio.com"
            type="email"
            value={email}
          />
          <Field
            autoComplete="current-password"
            label="Password"
            name="password"
            onChange={setPassword}
            placeholder="Password del estudio"
            type="password"
            value={password}
          />
          {error ? (
            <div className="rounded-md border border-red-200 bg-red-50 px-3 py-2 text-sm font-medium text-red-700" role="alert">
              {error}
            </div>
          ) : null}
          <Button type="submit">{status === "loading" ? "Validando acceso..." : "Entrar al Legal OS"}</Button>
        </form>
        <div className="mt-6 flex items-start gap-2 rounded-lg bg-legal-50 p-3 text-sm text-legal-900">
          <ShieldCheck size={18} aria-hidden="true" />
          <p>Ingreso conectado al API cloud con JWT, contexto tenant y auditoria de acceso.</p>
        </div>
        <div className="mt-3 flex items-start gap-2 rounded-lg border border-slate-200 bg-white p-3 text-xs leading-5 text-slate-600">
          <Building2 size={16} className="mt-0.5 text-legal-700" aria-hidden="true" />
          <p>
            Usa el slug del estudio productivo. Para este piloto: <span className="font-semibold text-ink">piloto</span>.
          </p>
        </div>
      </Card>
    </main>
  );
}
