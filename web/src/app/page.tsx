import { SearchForm } from "@/components/search-form";

export default function Home() {
  return (
    <section className="flex max-w-[72ch] flex-col gap-6 py-8">
      <div className="flex flex-col gap-4">
        <h1 className="font-heading text-[32px] font-semibold leading-tight">
          Know when a supplier&rsquo;s FDA record changes.
        </h1>
        <p className="text-ink-muted">
          Free lookup of FDA import alerts, refusals and warning letters for food and supplement suppliers.
        </p>
      </div>
      <SearchForm />
    </section>
  );
}
