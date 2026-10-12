import Link from "next/link";

export default function NotFound() {
  return (
    <section className="flex max-w-[72ch] flex-col gap-4 py-8">
      <h1 className="font-heading text-[32px] font-semibold leading-tight">Page not found</h1>
      <p className="text-ink-muted">
        We have no page at this address. A supplier page exists only for an FDA Establishment Identifier (FEI) that
        appears in the FDA sources we search.
      </p>
      <p>
        <Link href="/">Back to the home page</Link>
      </p>
    </section>
  );
}
