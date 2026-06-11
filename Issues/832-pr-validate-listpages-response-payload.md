# PR: Validate ListPages response payloads

## Summary

`PageCollection.search_pages()` should validate that decoded `list/ListPagesModule` response payloads are mappings before reading `body` on both first-page and additional-page ListPages reads.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 220, which covers mapping ListPages responses where `body` is missing, Issue 330, which covers present non-string `body` values, and Issue 403, which covers the raw Ajax Module Connector envelope before module-level response parsing.

## Problem Statement

`PageCollection.search_pages()` retrieves generated ListPages markup, parses the first page, detects pager targets, and optionally fetches additional ListPages offsets. The shared `_listpages_response_body(...)` helper previously called `response.json().get("body")` directly.

If a decoded ListPages response payload was a list, string, or other non-mapping value, the path raised a raw `AttributeError` before wikidot.py could attach site and offset context.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify ListPages as a core browser-free workflow: large source collection, page lookup, source iteration, publish verification, first-page retry, additional-page retry, bounded pagination, field parsing, text spacing, missing response-body diagnostics, and response body type diagnostics all exist as prior local slices.

The immediate source evidence before this slice was `PageCollection._listpages_response_body(...)` calling `response.json().get("body")` while both first-page and additional-page call sites depended on that helper. The RED run reproduced the first-page gap with a list payload and failed with `AttributeError: 'list' object has no attribute 'get'`. After the shared helper fix, an additional-page regression proved the same guard applies to paginated reads and reports the derived additional offset.

The local fix is committed as `c6e3a66`.

## Affected Workflows

- Browser-free page search through `PageCollection.search_pages()`.
- Source iteration and large page inventory workflows that start from ListPages.
- Publish verification and page lookup flows that depend on ListPages search behavior.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode each ListPages response once in `_listpages_response_body(...)`, require a `dict`, and raise `NoElementException` with site, offset, expected type, and actual type context when the payload root is malformed.

Keep existing missing-`body`, non-string-`body`, retry-exhausted, private-site mapping, pager detection, offset preservation, limit capping, field parsing, and successful parsing behavior unchanged.

## Implementation Notes

The patch adds a decoded-payload type guard inside `_listpages_response_body(...)`. Because first-page and additional-page search paths already share this helper, both paths now get the same payload-root diagnostic before `body` lookup.

The regression tests assert that list payloads raise:

```text
ListPages response payload is malformed for site: test-site, offset: 500 (expected=dict, actual=list)
ListPages response payload is malformed for site: test-site, offset: 600 (expected=dict, actual=list)
```

Existing missing-body and non-string-body messages still run after the payload-root guard for valid mapping payloads.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_first_response_payload_type_includes_site_offset_and_type_context -q
uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_additional_response_payload_type_includes_site_offset_and_type_context -q
uv run pytest tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_basic tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_retries_transient_first_page_failures tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_raises_when_first_page_retry_is_exhausted tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_first_response_body_includes_site_and_offset_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_first_response_payload_type_includes_site_offset_and_type_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_first_response_body_type_includes_site_offset_and_type_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_pagination_preserves_query_offset tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_additional_pager_requests_use_retry tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_failed_retry_additional_page_raises tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_missing_additional_response_body_includes_site_and_offset_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_additional_response_payload_type_includes_site_offset_and_type_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_malformed_additional_response_body_type_includes_site_offset_and_type_context tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_limit_within_first_page_skips_additional_pager_requests tests/unit/test_page.py::TestPageCollectionSearchPages::test_search_pages_limit_caps_additional_pager_requests -q
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
first-page RED: failed with AttributeError before the fix
first-page focused GREEN: 4 passed
additional-page regression: 1 passed after shared helper fix
focused ListPages response matrix: 14 passed
page module: 484 passed
full unit suite: 3934 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on ListPages reads. Valid mapping payloads and existing missing-`body`, malformed-`body`, retry-exhausted, private-site mapping, parser, pager, offset, limit, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/offset identifiers and type names. It does not include raw response JSON, generated ListPages HTML, page titles, tags, search parameters, account material, cookies, tokens, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable site/offset context. It follows the response-shape validation style already used in adjacent module helpers, keeps the public API unchanged, and is covered by first-page and additional-page regressions through `PageCollection.search_pages()`.

## Acceptance Criteria

- `PageCollection.search_pages()` validates that decoded first-page ListPages response payloads are mappings before reading `body`.
- Additional ListPages response payloads use the same mapping validation before reading `body`.
- Non-mapping first-page payloads raise `NoElementException` with site, offset, expected type, and actual type context.
- Non-mapping additional-page payloads raise `NoElementException` with site, derived offset, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry-exhausted, private-site mapping, parser, pager, offset, limit, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `c6e3a66`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- No raw response JSON, generated ListPages HTML, page titles, tags, search parameters, account material, cookies, tokens, or auth JSON were captured in this draft.
