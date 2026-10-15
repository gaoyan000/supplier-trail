import type { Metadata } from "next";
import { redirect } from "next/navigation";

import { SearchForm } from "@/components/search-form";
import { SearchResults } from "@/components/search-results";
import { db } from "@/lib/db";
import { supplierPath } from "@/lib/format";
import { parseQuery, searchFirms, type FirmHit } from "@/lib/search";
import { getFirmByFei } from "@/lib/suppliers";

export const metadata: Metadata = {
  title: "Search suppliers — SupplierTrail",
  robots: { index: false, follow: true },
};

export default async function SearchPage({ searchParams }: PageProps<"/search">) {
  const raw = (await searchParams).q;
  const query = (Array.isArray(raw) ? raw[0] : raw)?.trim() ?? "";
  const parsed = parseQuery(query);
  if (parsed.kind === "empty") redirect("/");

  let hits: FirmHit[] = [];
  if (parsed.kind === "fei") {
    const firm = await getFirmByFei(db(), parsed.fei);
    if (firm) redirect(supplierPath(firm.fei, firm.slug));
  } else if (parsed.kind === "name") {
    hits = await searchFirms(db(), parsed.norm);
  }

  return (
    <section className="flex max-w-[72ch] flex-col gap-6 py-4">
      <h1 className="font-heading text-2xl font-semibold leading-tight">Search suppliers</h1>
      <SearchForm query={query} />
      <SearchResults
        query={parsed.kind === "fei" ? parsed.fei : query}
        state={parsed.kind === "fei" ? "unknown-fei" : parsed.kind === "short" ? "short" : "results"}
        hits={hits}
      />
    </section>
  );
}
