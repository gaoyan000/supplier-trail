import { Search } from "lucide-react";

export function SearchForm({ query = "" }: { query?: string }) {
  return (
    <form action="/search" method="get" role="search" className="flex flex-col gap-2">
      <label htmlFor="q" className="font-medium">
        Supplier name or FEI number
      </label>
      <div className="flex flex-wrap gap-2">
        <div className="relative min-w-0 flex-[1_1_320px]">
          <Search aria-hidden="true" size={20} className="absolute left-3 top-1/2 -translate-y-1/2 text-ink-muted" />
          <input
            id="q"
            name="q"
            type="search"
            defaultValue={query}
            required
            maxLength={120}
            autoComplete="off"
            className="min-h-12 w-full rounded-md border border-border-strong bg-surface pl-10 pr-3 text-ink"
          />
        </div>
        <button
          type="submit"
          className="min-h-12 cursor-pointer rounded-md bg-accent px-6 font-semibold text-accent-fg"
        >
          Search
        </button>
      </div>
    </form>
  );
}
