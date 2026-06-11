# PR: Validate page revision-list response payloads

## Summary

`PageCollection.get_page_revisions()` should validate that decoded `history/PageRevisionListModule` response payloads are mappings before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 222, which covers mapping page revision-list responses where `body` is missing. It is also distinct from Issue 831, which covers page revision source and rendered HTML payload roots, and Issue 833, which covers page source payload roots rather than revision-list payload roots.

## Problem Statement

`PageCollection.get_page_revisions()` batches revision-list reads for pages whose revision history is still uncached, groups duplicate page IDs, preserves cached duplicate revision collections, and parses revision rows into page-owned `PageRevisionCollection` objects.

If a decoded `history/PageRevisionListModule` response payload was a list, string, or other non-mapping value, the loop raised raw `AttributeError: 'list' object has no attribute 'get'` before wikidot.py could attach site, page, page ID, and expected payload shape context. That raw failure bypassed the existing missing-`body` and non-string-`body` diagnostics.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify page revision acquisition as a core browser-free workflow: batched revision fetching, retry-aware revision source and rendered HTML reads, cached duplicate revision reuse, revision row parsing, revision parser context, missing revision-list response-body diagnostics, and revision source/rendered HTML payload-root diagnostics all exist as prior local slices.

The immediate source evidence before this slice was `PageCollection._acquire_page_revisions(...)` calling `response.json().get("body")` inside the batched revision-list response loop. The RED run reproduced the gap with a list-valued decoded response and failed with raw `AttributeError` before the existing revision-list response-body checks could run.

The local fix is committed as `7ff73b0`.

## Affected Workflows

- Browser-free page revision history retrieval through `PageCollection.get_page_revisions()`.
- Lazy `Page.revisions` paths that delegate through page revision acquisition.
- Revision audit, publication verification, corpus extraction, and history inspection workflows that need contextual page failures.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode each revision-list response once, require a `dict`, and raise `NoElementException` with site, page, page ID, expected type, and actual type context when the payload root is malformed.

Keep the existing batch semantics: skip retry-exhausted `None` responses, preserve cached duplicate revision reuse, preserve duplicate page-ID grouping, and keep existing missing-`body`, non-string-`body`, row parsing, user parsing, date parsing, and successful parsing behavior unchanged for valid mapping payloads.

## Implementation Notes

The patch adds a decoded-payload type guard in the existing `PageCollection._acquire_page_revisions(...)` response loop before reading `body`.

The regression test configures `PageCollection.get_page_revisions()` with one page and a mocked response whose `json()` value is a list. It asserts that the public collection API raises:

```text
Page revision list response payload is malformed for site: test-site, page: test-page (id=12345, expected=dict, actual=list)
```

It also asserts that the legacy plain `amc_request` path is not used and that malformed payloads do not populate `page._revisions`.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_response_payload_type_includes_site_page_and_type_context -q
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_success tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_missing_response_body_includes_site_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_response_payload_type_includes_site_page_and_type_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_response_body_type_includes_site_page_and_type_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_skips_already_acquired_pages tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_deduplicates_duplicate_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_reuses_cached_duplicate_page_revisions -q
uv run pytest tests/unit/test_page.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
RED: failed with AttributeError before the fix
focused GREEN: 7 passed
page module: 486 passed
full unit suite: 3936 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on page revision-list reads. Valid mapping payloads and existing missing-`body`, malformed-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, revision row parsing, user parsing, date parsing, source/html clone preservation, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/page/page-ID identifiers and type names. It does not include raw response JSON, generated revision-list HTML, revision comments, page titles, account material, cookies, tokens, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable revision-list context. It follows the response-shape validation style already used in adjacent module helpers, preserves the public API, and is covered by a regression through the public collection API.

## Acceptance Criteria

- `PageCollection.get_page_revisions()` validates that decoded revision-list response payloads are mappings before reading `body`.
- Non-mapping payloads raise `NoElementException` with site, page, page ID, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, revision row parsing, user parsing, date parsing, source/html clone preservation, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `7ff73b0`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw response JSON, generated revision-list HTML, revision comments, page titles, account material, cookies, tokens, or auth JSON were captured in this draft.
