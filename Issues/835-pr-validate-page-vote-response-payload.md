# PR: Validate page vote response payloads

## Summary

`PageCollection.get_page_votes()` should validate that decoded `pagerate/WhoRatedPageModule` response payloads are mappings before reading `body`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 223, which covers mapping page vote responses where `body` is missing. It is also distinct from Issue 333, which covers present non-string `body` values, and Issues 833 and 834, which cover page source and page revision-list payload roots.

## Problem Statement

`PageCollection.get_page_votes()` batches WhoRated reads for pages whose vote cache is still empty, groups duplicate page IDs, reuses cached duplicate vote collections, and parses generated vote markup into page-owned `PageVoteCollection` objects.

If a decoded `pagerate/WhoRatedPageModule` response payload was a list, string, or other non-mapping value, the loop raised raw `AttributeError: 'list' object has no attribute 'get'` before wikidot.py could attach site, page, page ID, and expected payload shape context. That raw failure bypassed the existing missing-`body` and non-string-`body` diagnostics.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify page vote acquisition as a practical browser-free workflow: duplicate vote-list request elimination, cached duplicate vote reuse, scoped WhoRated parsing, vote value diagnostics, malformed body diagnostics, vote cache invalidation, direct vote assignment validation, and vote actor/client validation all exist as prior local slices.

The immediate source evidence before this slice was `PageCollection._acquire_page_votes(...)` calling `response.json().get("body")` inside the batched vote response loop. The RED run reproduced the gap with a list-valued decoded response and failed with raw `AttributeError` before the existing vote response-body checks could run.

The local fix is committed as `666f90c`.

## Affected Workflows

- Browser-free page vote retrieval through `PageCollection.get_page_votes()`.
- Lazy `Page.votes` paths that delegate through page vote acquisition.
- Rating audit, moderation review, publication verification, and inventory workflows that need contextual page failures.
- Generated fixtures, response adapters, and recorded-response tests that return decoded module payloads to wikidot.py.

## Proposed Fix

Decode each vote response once, require a `dict`, and raise `NoElementException` with site, page, page ID, expected type, and actual type context when the payload root is malformed.

Keep the existing batch semantics: skip retry-exhausted `None` responses, preserve cached duplicate vote reuse, preserve duplicate page-ID grouping, and keep existing missing-`body`, non-string-`body`, WhoRated container parsing, non-vote span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, and successful parsing behavior unchanged for valid mapping payloads.

## Implementation Notes

The patch adds a decoded-payload type guard in the existing `PageCollection._acquire_page_votes(...)` response loop before reading `body`.

The regression test configures `PageCollection.get_page_votes()` with one page and a mocked response whose `json()` value is a list. It asserts that the public collection API raises:

```text
Page vote response payload is malformed for site: test-site, page: test-page (id=12345, expected=dict, actual=list)
```

It also asserts that the legacy plain `amc_request` path is not used and that malformed payloads do not populate `page._votes`.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_response_payload_type_includes_site_page_and_type_context -q
uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_success tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_missing_response_body_includes_site_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_response_payload_type_includes_site_page_and_type_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_response_body_type_includes_site_page_and_type_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_ignores_non_vote_colored_spans tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_site_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_value_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_skips_already_acquired_pages tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_deduplicates_duplicate_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_reuses_cached_duplicate_page_votes -q
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
focused GREEN: 10 passed
page module: 487 passed
full unit suite: 3937 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

## Compatibility And Risk Notes

The change only affects malformed decoded payload roots on page vote reads. Valid mapping payloads and existing missing-`body`, malformed-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, WhoRated container discovery, non-vote colored span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, and successful parsing cases retain their current behavior.

The diagnostic intentionally includes only site/page/page-ID identifiers and type names. It does not include raw response JSON, generated WhoRated HTML, user names, vote values, page titles, account material, cookies, tokens, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with domain exceptions that include actionable vote-list context. It follows the response-shape validation style already used in adjacent module helpers, preserves the public API, and is covered by a regression through the public collection API.

## Acceptance Criteria

- `PageCollection.get_page_votes()` validates that decoded vote response payloads are mappings before reading `body`.
- Non-mapping payloads raise `NoElementException` with site, page, page ID, expected type, and actual type context.
- Existing missing-`body`, non-string-`body`, retry-exhausted, duplicate page-ID, cached duplicate reuse, WhoRated container discovery, non-vote colored span filtering, user/value mismatch diagnostics, user parsing, vote value parsing, and successful parsing behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `666f90c`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw response JSON, generated WhoRated HTML, user names, vote values, page titles, account material, cookies, tokens, or auth JSON were captured in this draft.
