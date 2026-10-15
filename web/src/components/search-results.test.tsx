import { renderToStaticMarkup } from "react-dom/server";
import { describe, expect, it } from "vitest";

import { SEARCH_LIMIT, type FirmHit } from "@/lib/search";

import { SearchResults } from "./search-results";

const hit: FirmHit = {
  fei: "3000000000",
  slug: "example-foods-co-ltd",
  name: "Example Foods Co., Ltd",
  address: "No. 1 Sample Road, Example City",
  city: "Example City",
  country: "China",
};

const render = (props: Parameters<typeof SearchResults>[0]) => renderToStaticMarkup(<SearchResults {...props} />);

describe("SearchResults", () => {
  it("links each firm to its supplier page with FEI and place to tell firms apart", () => {
    const html = render({ query: "example foods", state: "results", hits: [hit] });
    expect(html).toContain('href="/supplier/3000000000-example-foods-co-ltd"');
    expect(html).toContain("Example Foods Co., Ltd</a>");
    expect(html).toContain("FEI 3000000000");
    expect(html).toContain("No. 1 Sample Road, Example City, China");
    expect(html).toContain("1 firm");
  });

  it("says when the list is cut off", () => {
    const hits = Array.from({ length: SEARCH_LIMIT }, (_, i) => ({ ...hit, fei: String(3000000000 + i) }));
    expect(render({ query: "example", state: "results", hits })).toContain(`first ${SEARCH_LIMIT} matches`);
    expect(render({ query: "example", state: "results", hits: [hit] })).not.toContain("first");
  });

  it("uses a neutral empty state that does not imply a clear record", () => {
    const html = render({ query: "Unknown <b>Firm</b>", state: "results", hits: [] });
    expect(html).toContain("No firm found for “Unknown &lt;b&gt;Firm&lt;/b&gt;”");
    expect(html).toContain("does not mean the firm has no FDA record");
    expect(html).not.toMatch(/✓|No issues/);
  });

  it("explains an unknown FEI and a too-short search", () => {
    expect(render({ query: "3999999999", state: "unknown-fei", hits: [] })).toContain(
      "No firm with FEI 3999999999 in the FDA sources we searched",
    );
    expect(render({ query: "ab", state: "short", hits: [] })).toContain("at least 3 characters");
  });
});
