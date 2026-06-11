# PR: Validate ListPages response count

## Problem Statement

`PageCollection.search_pages(...)` uses a custom first-page ListPages retry loop that calls direct `site.amc_request(..., return_exceptions=True)` and selects the first returned result. Before this change, a connector, mock, or adapter that returned zero responses caused an internal `IndexError("list index out of range")` during response selection. That indexing error was then treated as a retryable exception and eventually surfaced as the generic exhausted-fetch message instead of explaining that the one-request ListPages response-count contract was broken.

This was a low-context failure at the browser-free page search boundary. It also made malformed response arity look like a transient fetch problem, which could hide broken recorded-response fixtures or connector changes.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify ListPages search as infrastructure for page lookup, source collection, publishing helpers, migration ledgers, archival jobs, generated tests, and local fixtures. Existing local slices hardened ListPages around retry controls, exhausted-retry site/offset context, response payload shape, missing/malformed response bodies, pager parsing, field parsing, retained site/client state, and shared retry response counts. They did not validate the direct first-page `site.amc_request(..., return_exceptions=True)` result count before selecting the single response-or-exception slot.

The local fix is committed as `f0782aa`.

## Affected Workflows

- Browser-free page search through `PageCollection.search_pages(...)`.
- `Site.pages.search(...)`, page lookup, source iterators, and publish helpers that depend on first-page ListPages results.
- Generated page inventory, migration, archival, publishing, or verification scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct ListPages responses.
- Debugging malformed connector behavior where response count, not response body shape, is the first broken contract.

## Proposed Fix

Add a small ListPages response-count guard. Validate that the direct first-page ListPages response sequence has exactly one entry before indexing it. Raise `UnexpectedException` with site, offset, expected count, and actual count on mismatch.

## Implementation Notes

The change adds `_require_listpages_response_count(...)` next to the existing ListPages retry-control validator. `_request_listpages_page(...)` now calls `site.amc_request(...)` inside the existing exception-catching retry boundary, then validates the returned sequence outside that catch before selecting response zero.

Actual exceptions raised by `site.amc_request(...)` remain retryable exactly as before. Only malformed response sequence arity now fails immediately, because it is a local contract violation rather than a transient response object.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_rejects_first_page_response_count_mismatch_before_retry_exhaustion -q --tb=short
uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages -q --tb=short
uv run pytest tests/unit/test_page.py -q --tb=short
uv run pytest tests/unit/test_site.py tests/unit/test_search_pages_query.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

The focused RED run failed before the fix because an empty direct ListPages result produced an internal raw `IndexError`, then surfaced as the generic `Failed to get ListPages page ...` exhausted-fetch message after retries. The focused GREEN run passed after adding the count guard. `TestPageCollectionSearchPages` passed 38 tests, `tests/unit/test_page.py` passed 502 tests, adjacent page/search/site coverage passed 811 tests, full unit verification passed 3976 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid ListPages first-page requests still send the same request body and parse the same returned payloads.
- Existing retry behavior for exceptions returned in the single response-or-exception slot remains unchanged.
- Existing private-site `not_ok` mapping, `try_again` retry handling, exhausted-retry diagnostics, payload/body diagnostics, pager parsing, and field parsing remain unchanged.
- Mismatched response-count failures occur before retry exhaustion, response JSON parsing, or partial result construction.
- The diagnostic does not include raw generated module bodies, raw response JSON, search parameters, credentials, cookies, auth JSON, private page content, local rollout paths, or account material.

## Rationale For Upstream Suitability

The custom first-page ListPages retry path expects exactly one returned slot for one submitted `ListPagesModule` request. When that positional contract is broken, wikidot.py should report the response-count failure directly instead of retrying an incidental Python indexing error and collapsing it into a generic fetch failure.

## Scope

This slice does not change retry policy, `site.amc_request(...)` behavior, request construction, successful ListPages parsing, private-site handling, additional-page retry handling, source iteration, publish behavior, live Wikidot behavior, or upstream filing state.
