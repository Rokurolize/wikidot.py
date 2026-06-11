# PR: Validate page file response payloads

## Summary

`PageCollection.get_page_files()` should validate that decoded `files/PageFilesModule` response payloads are mappings before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 224, which covers mapping batched page-file responses where `body` is missing. It is also distinct from Issue 334, which covers present non-string `body` values, Issue 824, which covers direct page-file reads, and Issues 833 through 835, which cover page source, page revision-list, and page vote payload roots.

## Problem Statement

`PageCollection.get_page_files()` batches file-list reads for pages whose file cache is still empty, groups duplicate page IDs, reuses cached duplicate file collections, and parses generated file-list markup into page-owned `PageFileCollection` objects.

If a decoded `files/PageFilesModule` response payload was a list, string, or other non-mapping value, the loop raised raw `AttributeError: 'list' object has no attribute 'get'` before wikidot.py could attach site, page, page ID, and expected payload shape context. That raw failure bypassed the existing missing-`body` and non-string-`body` diagnostics.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify page-file acquisition as a practical browser-free workflow: direct file reads, batched file reads, retry-aware fetches, duplicate file-list request reuse, cached duplicate file reuse, scoped file row parsing, file URL construction, file-size parsing, malformed body diagnostics, and direct page-file payload-root diagnostics all exist as prior local slices.

The immediate source evidence before this slice was `PageCollection._acquire_page_files(...)` calling `response.json().get("body")` inside the batched file response loop. The RED run reproduced the gap with a list-valued decoded response and failed with raw `AttributeError` before the existing file response-body checks could run.

The local fix is committed as `39d74c2`.

## Affected Workflows

- Browser-free page attachment retrieval through `PageCollection.get_page_files()`.
- Lazy `Page.files` paths that delegate through page file acquisition.
- Attachment inventory, archive, publication verification, and migration workflows that need contextual page failures.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode each file response once, require a `dict`, and raise `NoElementException` with site, page, page ID, expected type, and actual type context when the payload root is malformed.

Keep the existing batch semantics: skip retry-exhausted `None` responses, preserve cached duplicate file reuse, preserve duplicate page-ID grouping, and keep existing missing-`body`, non-string-`body`, file row parsing, URL construction, size parsing, and successful parsing behavior unchanged for valid mapping payloads.

## Implementation Notes

The patch adds a decoded-payload type guard in the existing `PageCollection._acquire_page_files(...)` response loop before reading `body`.

The regression test configures `PageCollection.get_page_files()` with one page and a mocked response whose `json()` value is a list. It asserts that the public collection API raises:

```text
Page file response payload is malformed for site: test-site, page: test-page (id=12345, expected=dict, actual=list)
```

It also asserts that the legacy plain `amc_request` path is not used and that malformed payloads do not populate `page._files`.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_malformed_response_payload_type_includes_site_page_and_type_context -q
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_batches_missing_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_skips_already_acquired_pages tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_skips_failed_retry_response tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_missing_response_body_includes_site_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_malformed_response_payload_type_includes_site_page_and_type_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_malformed_response_body_type_includes_site_page_and_type_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_deduplicates_duplicate_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_files_reuses_cached_duplicate_page_files -q
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
focused GREEN: 8 passed
page module: 488 passed
full unit suite: 3938 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on batched page-file reads. Valid mapping payloads and existing missing-`body`, malformed-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, file row parsing, file URL construction, size parsing, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/page/page-ID identifiers and type names. It does not include raw response JSON, generated file-list HTML, file names, file URLs, page titles, account material, cookies, tokens, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable page-file context. It follows the response-shape validation style already used in adjacent module helpers, preserves the public API, and is covered by a regression through the public collection API.

## Acceptance Criteria

- `PageCollection.get_page_files()` validates that decoded batched file response payloads are mappings before reading `body`.
- Non-mapping payloads raise `NoElementException` with site, page, page ID, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, file row parsing, URL construction, size parsing, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `39d74c2`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw response JSON, generated file-list HTML, file names, file URLs, page titles, account material, cookies, tokens, or auth JSON were captured in this draft.
