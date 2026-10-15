import Link from "next/link";

import { firmPlace, supplierPath } from "@/lib/format";
import { SEARCH_LIMIT, type FirmHit } from "@/lib/search";

type Props = { query: string; state: "results" | "unknown-fei" | "short"; hits: FirmHit[] };

const NOTE = "text-ink-muted";

export function SearchResults({ query, state, hits }: Props) {
  if (state === "short") {
    return <p className={NOTE}>Enter at least 3 characters of the supplier&rsquo;s name, or its FEI number.</p>;
  }
  if (state === "unknown-fei") {
    return (
      <p className={NOTE}>
        No firm with FEI {query} in the FDA sources we searched. This does not mean the firm has no FDA record.
      </p>
    );
  }
  if (hits.length === 0) {
    return (
      <p className={NOTE}>
        No firm found for &ldquo;{query}&rdquo; in the FDA sources we searched. This does not mean the firm has no FDA
        record: try a shorter part of the name, or the FEI number.
      </p>
    );
  }
  return (
    <section aria-label="Search results" className="flex flex-col gap-3">
      <p className={`${NOTE} text-sm`}>
        {hits.length === SEARCH_LIMIT
          ? `Showing the first ${SEARCH_LIMIT} matches. Type more of the name, or search by FEI number, to narrow the list.`
          : `${hits.length} firm${hits.length === 1 ? "" : "s"}`}
      </p>
      <ol className="rounded-md border border-border bg-surface">
        {hits.map((hit) => (
          <li key={hit.fei} className="flex flex-col gap-0.5 border-b border-border px-4 py-3 last:border-b-0 sm:px-6">
            <Link href={supplierPath(hit.fei, hit.slug)} className="font-semibold [overflow-wrap:anywhere]">
              {hit.name}
            </Link>
            <span className="text-[15px] text-ink-muted">
              <span className="font-mono font-medium text-ink">FEI {hit.fei}</span>
              {firmPlace(hit) ? ` · ${firmPlace(hit)}` : ""}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
