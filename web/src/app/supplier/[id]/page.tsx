import type { Metadata } from "next";
import { notFound, permanentRedirect } from "next/navigation";
import { cache } from "react";

import { SupplierRecord } from "@/components/supplier/supplier-record";
import { db } from "@/lib/db";
import { parseFilter } from "@/lib/events";
import { parsePage, parseSupplierId, supplierPath, supplierTitle, todayIso } from "@/lib/format";
import { getDataAsOf, getEvents, getFirmByFei, getSummary } from "@/lib/suppliers";

const loadFirm = cache(async (id: string) => {
  const parsed = parseSupplierId(id);
  const firm = parsed && (await getFirmByFei(db(), parsed.fei));
  return firm ? { firm, canonical: parsed.slug === firm.slug } : null;
});

function one(value: string | string[] | undefined): string | undefined {
  return Array.isArray(value) ? value[0] : value;
}

export async function generateMetadata({ params }: PageProps<"/supplier/[id]">): Promise<Metadata> {
  const found = await loadFirm((await params).id);
  if (!found) return {};
  const { firm } = found;
  const place = [firm.city, firm.country].filter(Boolean).join(", ");
  return {
    title: supplierTitle(firm.name),
    description: `FDA records for ${firm.name} (FEI ${firm.fei})${place ? `, ${place}` : ""}: import refusals, inspections, recalls and warning letters, each with its FDA source.`,
    alternates: { canonical: supplierPath(firm.fei, firm.slug) },
    robots: firm.indexable ? undefined : { index: false, follow: true },
  };
}

export default async function SupplierPage({ params, searchParams }: PageProps<"/supplier/[id]">) {
  const found = await loadFirm((await params).id);
  if (!found) notFound();
  const { firm } = found;
  if (!found.canonical) permanentRedirect(supplierPath(firm.fei, firm.slug));

  const query = await searchParams;
  const filter = parseFilter(one(query.type));
  const page = parsePage(one(query.page));
  const today = todayIso();
  const sql = db();
  const [summary, events, asOf] = await Promise.all([
    getSummary(sql, firm.id, today),
    getEvents(sql, firm.id, filter.types, page),
    getDataAsOf(sql),
  ]);

  return (
    <SupplierRecord
      firm={firm}
      summary={summary}
      events={events}
      filter={filter.key}
      page={page}
      asOf={asOf}
      today={today}
    />
  );
}
