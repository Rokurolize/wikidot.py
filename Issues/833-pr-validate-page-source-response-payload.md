# PR: Validate page source response payloads

## Summary

`PageCollection.get_page_sources()` should validate that decoded `viewsource/ViewSourceModule` response payloads are mappings before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 221, which covers mapping page source responses where `body` is missing, and Issue 331, which covers present non-string `body` values. It is also distinct from Issue 832, which covers ListPages response payload roots rather than ViewSource response payload roots.

## Problem Statement

`PageCollection.get_page_sources()` batches source reads for pages whose source is still uncached, groups duplicate page IDs, preserves neighboring successful source responses, and raises the first structural source error after the batch.

If a decoded `viewsource/ViewSourceModule` response payload was a list, string, or other non-mapping value, the loop raised raw `AttributeError: 'list' object has no attribute 'get'` before wikidot.py could attach site, page, page ID, and expected payload shape context. That raw failure also aborted the loop before later successful source responses could be applied.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify page source acquisition as a core browser-free workflow: source collection, source iteration, publish verification, retry-aware source fetching, cached duplicate source reuse, multiline ViewSource preservation, source parse context, missing response-body diagnostics, and response body type diagnostics all exist as prior local slices.

The immediate source evidence before this slice was `PageCollection._acquire_page_sources(...)` calling `response.json().get("body")` inside the batched source response loop. The RED run reproduced the gap with a list-valued middle response and failed with raw `AttributeError` after applying the first source but before processing the later successful source.

The local fix is committed as `7836759`.

## Affected Workflows

- Browser-free page source retrieval through `PageCollection.get_page_sources()`.
- Lazy `Page.source` and explicit `Page.refresh_source()` paths that delegate through page source acquisition.
- Source iteration, corpus extraction, source verification, and publication workflows that preserve partial batch successes.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode each source response once, require a `dict`, and record a `NoElementException` with site, page, page ID, expected type, and actual type context when the payload root is malformed.

Keep the existing batch semantics: skip retry-exhausted `None`, continue processing later successful responses after the first structural source error, and raise the first structural source error after the loop.

## Implementation Notes

The patch adds a decoded-payload type guard in the existing `PageCollection._acquire_page_sources(...)` response loop before reading `body`.

The regression test constructs a three-page batch:

```text
first response: valid source body
middle response: list-valued decoded payload
third response: valid source body
```

The test asserts that the first and third pages receive source text, the malformed page remains uncached, and the final error is:

```text
Page source response payload is malformed for site: test-site, page: malformed-payload-page (id=222, expected=dict, actual=list)
```

Existing missing-body and non-string-body messages still run after the payload-root guard for valid mapping payloads.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_malformed_response_payload_type_preserves_later_successes_with_page_context -q
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_success tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_failed_retry_response tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_preserves_later_successes_when_parse_fails tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_missing_response_body_preserves_later_successes_with_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_malformed_response_payload_type_preserves_later_successes_with_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_malformed_response_body_type_preserves_later_successes_with_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_skips_already_acquired_pages tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_deduplicates_duplicate_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_sources_reuses_cached_duplicate_page_source -q
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
focused GREEN: 9 passed
page module: 485 passed
full unit suite: 3935 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on page source reads. Valid mapping payloads and existing missing-`body`, malformed-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, parser, source normalization, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/page/page-ID identifiers and type names. It does not include raw response JSON, generated source HTML, page source text, page titles, account material, cookies, tokens, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable page source context. It follows the response-shape validation style already used in adjacent module helpers, preserves partial-success batch behavior, keeps the public API unchanged, and is covered by a regression through the public collection API.

## Acceptance Criteria

- `PageCollection.get_page_sources()` validates that decoded ViewSource response payloads are mappings before reading `body`.
- Non-mapping payloads raise `NoElementException` with site, page, page ID, expected type, and actual type context.
- Later successful source responses in the same batch are still applied before the first structural source error is raised.
- Existing missing-`body`, non-string-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, parser, source normalization, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `7836759`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- No raw response JSON, generated source HTML, page source text, page titles, account material, cookies, tokens, or auth JSON were captured in this draft.
