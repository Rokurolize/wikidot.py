# Feature Draft: Large Corpus Page And Source Collection Ergonomics

## Background / Problem

Large Wikidot corpus collection currently requires callers to tune ListPages pagination, source-fetch batch size, parent/child lookups, and client-side filtering themselves. Rollout evidence shows practical users needed:

- bounded ListPages scans with explicit `limit`, `perPage`, and `offset`
- source retrieval for many pages
- fallback from batched source fetch to smaller batches or individual pages
- parent-child discovery with `site.pages.search(parent=...)`
- client-side filtering because compound ListPages tag queries were unsafe for the observed workflow

The existing primitives are useful, but the library does not expose an ergonomic iterator or collection helper for this operational shape.

## Proposed Solution

Add large-corpus helper APIs around existing `SearchPagesQuery` and `PageCollection` behavior.

Possible shape:

```python
for page in site.pages.iter_search(tags="scp", per_page=250, batch_pages=True):
    ...

for result in site.pages.iter_sources(
    tags="scp",
    per_page=250,
    source_batch_size=25,
    fallback_batch_size=1,
):
    if result.ok:
        write_source(result.page.fullname, result.source)
    else:
        record_failure(result.page.fullname, result.error)
```

## Alternatives Considered

- Keep requiring callers to manage offsets and source batches manually. This gives maximum control but repeats subtle logic across scripts.
- Only document recommended pagination settings. Documentation helps, but does not address timeout fallback or structured per-page failure reporting.

## Use Case

A corpus acquisition script needs to discover thousands of pages, fetch source text, record failures without aborting the whole run, and resume safely after timeouts.

## Acceptance Criteria

- Provide a page iterator that yields pages across ListPages pagination without loading an unbounded site into memory by default.
- Provide a source iterator or helper that returns structured success/failure records.
- Support configurable source batch size and fallback batch size.
- Preserve existing `SearchPagesQuery` behavior and avoid changing `site.pages.search(...)`.
- Document that multiple tags passed to ListPages may not be a safe AND filter for all workflows; callers that require strict AND semantics should filter client-side.
- Unit tests cover pagination offsets, source batch fallback, per-page error reporting, and parent search.

## Upstream-Safe Motivation

wikidot.py already exposes the core mechanisms needed for corpus collection. Iterators and structured source results would make large collection scripts safer, faster, and easier to resume without changing existing APIs.

## Local Evidence, Not For Upstream Paste

- Local rollout `019df644-518c-74b1-a95b-3b89865f49ce` recorded that bounded EN listing worked with `limit=250`, `perPage=250`, and offsets, while unbounded listing was too coarse and was interrupted after more than two minutes.
- The same rollout recorded that compound ListPages tag queries such as `tags="fr scp"` were not safe as an AND filter for that use, so the script moved to single selectors plus client-side inclusion/exclusion.
- The same rollout recorded source fetch timeout problems for CN pages, including a single page that timed out three times.
- Local rollout `019e6454-88fa-7332-a0dd-a0ad98b1289c` included an adapter that tried batch source fetch first, then fell back to per-page source fetch and emitted per-page failures.

## Additional Information

The small local PR drafts in [002-pr-batch-source-page-id-lookups.md](002-pr-batch-source-page-id-lookups.md) and [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md) are immediate performance improvements for this feature area, but this issue remains broader and should be designed separately.
