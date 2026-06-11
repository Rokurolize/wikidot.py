# PR: Validate page revision source and HTML response payloads

## Summary

`PageRevisionCollection.get_sources()` and `PageRevisionCollection.get_htmls()` should validate that decoded `history/PageSourceModule` and `history/PageVersionModule` response payloads are mappings before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 216, which covers mapping page revision source/HTML responses where `body` is missing, and the existing body-type tests, which cover present non-string `body` values. It is also distinct from Issue 222, which covers batched `history/PageRevisionListModule` revision-list response bodies rather than direct source or rendered HTML revision reads.

## Problem Statement

`PageRevisionCollection.get_sources()` retrieves revision source HTML through `history/PageSourceModule`, and `PageRevisionCollection.get_htmls()` retrieves rendered revision HTML through `history/PageVersionModule`. Both public collection methods are also reached through lazy `PageRevision.source` and `PageRevision.html` access.

If either decoded response payload was a list, string, or other non-mapping value, the path raised raw `AttributeError: 'list' object has no attribute 'get'` before wikidot.py could attach site, page, revision ID, and expected payload shape context.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify page revision source and rendered HTML access as practical browser-free workflows: retry-aware revision source/HTML fetches, duplicate revision request deduplication, cached duplicate source/HTML reuse, source parser context, lazy failure visibility, missing response-body diagnostics, and response body type diagnostics all exist as prior local slices.

The immediate source evidence before this slice was `PageRevisionCollection._acquire_sources(...)` and `PageRevisionCollection._acquire_htmls(...)` calling `response.json().get("body")` directly. RED runs reproduced the gap with list payloads for both source and rendered HTML acquisition, failing with raw `AttributeError` before the existing missing-body or body-type diagnostics could run.

The local fix is committed as `9b6e124`.

## Affected Workflows

- Browser-free page revision source inspection through `PageRevisionCollection.get_sources()` and lazy `PageRevision.source`.
- Browser-free rendered revision HTML inspection through `PageRevisionCollection.get_htmls()` and lazy `PageRevision.html`.
- Corpus, audit, migration, and review tools that collect historical page revisions without a browser.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode each source/HTML response once, require a `dict`, and raise `NoElementException` with site, page, revision ID, expected type, and actual type context when the payload root is malformed.

Keep existing missing-`body`, non-string-`body`, retry-exhausted, duplicate revision-ID, cached duplicate reuse, source parsing, HTML separator trimming, direct HTML body fallback, and successful parsing behavior unchanged.

## Implementation Notes

The patch adds a decoded-payload type guard inside the source response processor and the HTML response processor before reading `body`.

The regression tests assert that list payloads raise:

```text
Page revision source response payload is malformed for site: test-site, page: test-page, revision: 100 (expected=dict, actual=list)
Page revision HTML response payload is malformed for site: test-site, page: test-page, revision: 100 (expected=dict, actual=list)
```

Existing missing-body and non-string-body messages still run after the payload-root guard for valid mapping payloads.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_malformed_response_payload_type_includes_site_page_revision_and_type_context -q
uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_malformed_response_payload_type_includes_site_page_revision_and_type_context -q
uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_missing_response_body_includes_site_page_and_revision_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_malformed_response_payload_type_includes_site_page_revision_and_type_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_malformed_response_body_type_includes_site_page_revision_and_type_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_skips_failed_retry_response tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_deduplicates_duplicate_revision_ids tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_missing_response_body_includes_site_page_and_revision_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_malformed_response_payload_type_includes_site_page_revision_and_type_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_malformed_response_body_type_includes_site_page_revision_and_type_context tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_skips_failed_retry_response tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_htmls_deduplicates_duplicate_revision_ids -q
uv run pytest tests/unit/test_page_revision.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
source RED: failed with AttributeError before the fix
source focused GREEN: 4 passed
HTML RED: failed with AttributeError before the fix
focused source/HTML matrix: 12 passed
page revision module: 179 passed
full unit suite: 3932 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on page revision source and rendered HTML reads. Valid mapping payloads and existing missing-`body`, malformed-`body`, retry-exhausted, duplicate revision-ID, cached duplicate reuse, parser, separator trimming, direct body fallback, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/page/revision identifiers and type names. It does not include raw response JSON, generated revision source, rendered HTML, revision comments, account material, cookies, tokens, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable page revision context. It follows the response-shape validation style already used in adjacent module helpers, keeps the public API unchanged, and is covered by regressions through the public collection APIs.

## Acceptance Criteria

- `PageRevisionCollection.get_sources()` validates that decoded source response payloads are mappings before reading `body`.
- `PageRevisionCollection.get_htmls()` validates that decoded rendered HTML response payloads are mappings before reading `body`.
- Non-mapping source payloads raise `NoElementException` with site, page, revision ID, expected type, and actual type context.
- Non-mapping rendered HTML payloads raise `NoElementException` with site, page, revision ID, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry-exhausted, duplicate revision-ID, cached duplicate reuse, parser, separator trimming, direct HTML body fallback, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `9b6e124`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- No raw response JSON, generated revision source, rendered HTML, revision comments, account material, cookies, tokens, or auth JSON were captured in this draft.
