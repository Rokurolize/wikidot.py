# PR: Validate recent changes response payload

## Summary

`Site.get_recent_changes()` should validate that decoded `changes/SiteChangesListModule` response payloads are mappings before reading `body` on both first-page and paginated recent-changes reads.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 218, which covers mapping recent-changes responses where `body` is missing, Issue 336, which covers present non-string `body` values, and Issue 403, which covers the raw Ajax Module Connector envelope before module-level response parsing.

## Problem Statement

`Site.get_recent_changes()` fetches generated recent-changes pages, reads each response `body`, parses change rows, and optionally fetches additional pages. The first-page and paginated paths previously called `response.json().get("body")` directly.

If a decoded recent-changes response payload was a list, string, or other non-mapping value, the path raised a raw `AttributeError` before wikidot.py could attach site and recent-changes page context.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify recent-changes inspection as a practical browser-free workflow: retry-aware recent-changes fetches, batched pagination, comment-pager filtering, parser context, text spacing, recent-change scalar validation, missing response-body diagnostics, and response-body type diagnostics all exist as prior local slices.

The immediate source evidence before this slice was `Site.get_recent_changes()` calling `response.json().get("body")` in both first-page and paginated loops while adjacent module helpers already used explicit response-shape diagnostics. RED runs reproduced the gap with list payloads on page 1 and page 2, both failing with `AttributeError: 'list' object has no attribute 'get'`.

The local fix is committed as `7549550`.

## Affected Workflows

- Browser-free recent-changes inspection through `Site.get_recent_changes()`.
- Corpus, audit, archival, and moderation tools that scan site edit activity.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode each recent-changes response once, require a `dict`, and raise `NoElementException` with site, page, expected type, and actual type context when the payload root is malformed.

Keep existing missing-`body`, non-string-`body`, retry-exhausted, parser, pager, pagination, limit, and successful parsing behavior unchanged.

## Implementation Notes

The patch adds a local `response_body(response, page_no)` helper inside `Site.get_recent_changes()` and reuses it for both the first page and later pages.

The regression tests assert that list payloads raise:

```text
Recent changes response payload is malformed for site: test, page: 1 (expected=dict, actual=list)
Recent changes response payload is malformed for site: test, page: 2 (expected=dict, actual=list)
```

The helper preserves the existing missing-body and body-type messages after the payload-root guard.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_malformed_response_payload_type_includes_site_context -q
uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_malformed_response_payload_type_includes_site_context -q
uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_missing_response_body_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_malformed_response_body_type_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_first_page_malformed_response_payload_type_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_missing_response_body_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_malformed_response_body_type_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_malformed_response_payload_type_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_paginated_pages tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_only_pages_needed_for_limit -q
uv run pytest tests/unit/test_site.py -q
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
paginated RED: failed with AttributeError before the fix
focused GREEN: 11 passed
site module: 379 passed
full unit suite: 3930 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on recent-changes reads. Valid mapping payloads and the existing missing-`body`, malformed-`body`, retry-exhausted, parser, pager, pagination, limit, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/page identifiers and type names. It does not include raw response JSON, generated recent-changes HTML, edit comments, page titles, account material, cookies, tokens, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable site/page context. It removes duplicated response-body validation between first-page and paginated paths, is covered by first-page and paginated regressions, and follows the response-shape validation style already used in adjacent module helpers.

## Acceptance Criteria

- `Site.get_recent_changes()` validates that decoded recent-changes response payloads are mappings before reading `body`.
- Non-mapping first-page payloads raise `NoElementException` with site, page 1, expected type, and actual type context.
- Non-mapping paginated payloads raise `NoElementException` with site, affected page, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry-exhausted, parser, pager, pagination, limit, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `7549550`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- No raw response JSON, generated recent-changes HTML, edit comments, page titles, account material, cookies, tokens, or auth JSON were captured in this draft.
