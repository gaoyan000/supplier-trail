import { Route } from "lucide-react";
import Link from "next/link";

export function SiteHeader() {
  return (
    <header className="border-b border-border bg-surface">
      <div className="mx-auto flex max-w-[1200px] flex-wrap items-center gap-6 px-4 py-3.5 sm:px-6">
        <Link href="/" className="flex min-h-11 items-center gap-2 font-heading text-xl font-semibold text-ink no-underline">
          <Route aria-hidden="true" size={22} className="text-accent" />
          SupplierTrail
        </Link>
        <nav aria-label="Main" className="flex flex-wrap gap-5 text-base">
          <Link href="/" className="flex min-h-11 items-center text-ink-muted no-underline hover:text-ink">
            Search
          </Link>
        </nav>
      </div>
    </header>
  );
}
