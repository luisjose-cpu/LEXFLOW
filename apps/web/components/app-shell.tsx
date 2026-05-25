import { webNavigation } from "@lexflow/shared";
import { Sparkles } from "lucide-react";
import Link from "next/link";
import type { ReactNode } from "react";
import { SearchGlobalBar } from "@/components/operational-core";

export function AppShell({ children }: { children: ReactNode }) {
  return (
    <main className="min-h-screen bg-mist">
      <div className="mx-auto grid w-full max-w-7xl gap-5 px-4 py-5 sm:px-6 lg:grid-cols-[260px_1fr] lg:px-8">
        <aside className="overflow-y-auto rounded-lg border border-white/80 bg-white p-4 shadow-soft lg:sticky lg:top-5 lg:h-[calc(100vh-2.5rem)]">
          <Link className="flex items-center gap-3" href="/dashboard">
            <span className="grid h-10 w-10 place-items-center rounded-md bg-legal-900 text-white">
              <Sparkles size={19} aria-hidden="true" />
            </span>
            <span>
              <span className="block text-sm font-semibold text-legal-900">LEXFLOW</span>
              <span className="block text-xs text-slate-500">Legal OS</span>
            </span>
          </Link>
          <nav className="mt-6 grid min-w-0 gap-1">
            {webNavigation.map((item) => (
              <Link
                className="flex min-w-0 items-center rounded-md px-3 py-2 text-sm font-semibold text-slate-600 transition hover:bg-legal-50 hover:text-legal-900"
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            ))}
          </nav>
        </aside>
        <section className="min-w-0">
          <div className="mb-5">
            <SearchGlobalBar compact />
          </div>
          {children}
        </section>
      </div>
    </main>
  );
}
