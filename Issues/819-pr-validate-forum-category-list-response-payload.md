# PR Draft: Validate Forum Category List Response Payload

## Summary

`ForumCategoryCollection.acquire_all(site)` now validates that decoded `forum/ForumStartModule` list responses are dictionaries before reading `body`. Non-mapping payloads such as `["not", "a", "mapping"]` raise contextual `NoElementException` with site, expected type, and actual type context instead of leaking raw `AttributeError` from `.get("body")`.

The change is intentionally narrow: valid category-list parsing, empty forum indexes, retry exhaustion, missing `body` diagnostics, present non-string `body` diagnostics, nested category-table filtering, row parse context, category thread access, and create-thread action handling remain unchanged.

## Problem Statement

`ForumCategoryCollection.acquire_all(site)`, also exposed through `site.forum.categories`, fetches the forum start module, decodes the AMC response, extracts `body`, and parses generated forum category HTML. Earlier local slices covered retry-aware forum category list fetches, empty result handling, nested category table filtering, title/description spacing, site/row parse context, missing response `body`, present non-string response `body`, direct site validation, retained category IDs, collection ownership, and create-thread response shape. One adjacent response-boundary gap remained: if `response.json()` returned a non-dictionary payload, `_category_list_response_body(...)` attempted `.get("body")` and leaked raw `AttributeError`.

That failure gives callers neither the affected site nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and malformed list payloads must not enter BeautifulSoup parsing or category row parsing.

## Rollout Evidence

Local rollout-backed drafts identify forum category list reads and forum thread creation as practical browser-free workflows: [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [542-pr-validate-forum-category-acquire-site.md](542-pr-validate-forum-category-acquire-site.md), [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md), and [812-pr-validate-forum-category-create-response-payload.md](812-pr-validate-forum-category-create-response-payload.md).

This slice is not a duplicate of [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md). Issue 211 covered mapping responses with a missing `body` field.

This slice is not a duplicate of [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md). Issue 322 covered a present non-string `body` field inside a mapping, such as `{"body": ["not html"]}`.

This slice is not a duplicate of [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md) or [812-pr-validate-forum-category-create-response-payload.md](812-pr-validate-forum-category-create-response-payload.md). Those drafts cover `ForumCategory.create_thread(...)` action responses consumed after a category already exists, not the category-list response consumed by `ForumCategoryCollection.acquire_all(site)`.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level response-body extraction. This slice covers the decoded module payload handed to forum category list parsing.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free forum category listing through `ForumCategoryCollection.acquire_all(site)` and `site.forum.categories`.
- Forum tooling that lists categories before reading threads or creating new threads.
- Generated fixtures and recorded-response tests that decode forum list responses before returning them to wikidot.py module code.

## Proposed Fix

- Decode the forum category list response once in `_category_list_response_body(...)`.
- Validate the decoded payload is a dictionary before reading `body`.
- Reject non-dictionary payloads with contextual `NoElementException`.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-body, body-type, empty-list, parser, category thread, and create-thread behavior.

## Implementation Notes

Implemented locally in commit `5c639c0 fix(forum_category): validate list response payload`.

The implementation adds one preflight guard before `body` lookup:

```python
data = response.json()
if not isinstance(data, dict):
    raise NoElementException(
        "Forum category list response payload is malformed "
        f"for site: {_site_name(site)} (expected=dict, actual={type(data).__name__})"
    )

body = data.get("body")
```

The RED regression mocked `ForumCategoryCollection.acquire_all(site)`'s list response as `["not", "a", "mapping"]`. Before the fix, the helper leaked `AttributeError: 'list' object has no attribute 'get'`. After the fix, the same case raises contextual `NoElementException` before category parsing.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary forum category list payloads fail before `body` lookup. | `test_acquire_all_malformed_response_payload_type_includes_site_context` failed RED with raw `AttributeError`, then passed GREEN. | Reaching `.get("body")`, leaking `AttributeError`, coercing the payload, or treating a list as a category-list response rejects this claim. |
| Missing `body` in a dictionary keeps the existing Issue 211 diagnostic. | Focused GREEN included `test_acquire_all_missing_response_body_includes_site_context`. | Reclassifying `{}` as the payload-type branch or changing the missing-body message rejects this claim. |
| Present non-string `body` keeps the existing Issue 322 diagnostic. | Focused GREEN included `test_acquire_all_malformed_response_body_type_includes_site_context`. | Reclassifying `{"body": ["not html"]}` as a payload-type error or dropping `field=body` rejects this claim. |
| Malformed payloads do not enter forum category parsing. | The new regression fails before BeautifulSoup or row parsing; adjacent focused body tests remained green. | Entering parser work, returning an empty collection, or hiding the site context rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3916 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, complexity scan, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, complexity, provenance, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `5c639c0 fix(forum_category): validate list response payload`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_response_payload_type_includes_site_context -q` failed before the fix with raw `AttributeError: 'list' object has no attribute 'get'`.
- GREEN focused: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_response_payload_type_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_context -q` passed 3 tests.
- Forum category module coverage: `uv run pytest tests/unit/test_forum_category.py -q` passed 160 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3916 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused complexity scan of `src/wikidot/module/forum_category.py` reported no obvious complexity hotspots.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumCategoryCollection.acquire_all(site)` with `response.json()` returning `["not", "a", "mapping"]` raises `NoElementException` matching `Forum category list response payload is malformed for site: test-site (expected=dict, actual=list)`.
- `{}` still raises the existing missing-body message.
- `{"body": ["not html"]}` still raises the existing malformed body-type message with `field=body`, `expected=str`, and `actual=list`.
- The malformed payload branch decodes the response JSON once and does not include raw response data.
- Valid category-list parsing, empty-forum handling, retry exhaustion, direct site validation, row parse diagnostics, category thread access, reload behavior, and create-thread action behavior remain unchanged.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `AttributeError` from malformed synthetic list responses. Mitigation: the public module expects a body-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with create-thread response payload validation. Mitigation: Issues 719 and 812 cover `ForumCategory.create_thread(...)`; this slice only covers the list payload consumed by `ForumCategoryCollection.acquire_all(site)`.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, expected type, and actual type while avoiding raw response data that could contain private forum content.

## Dependencies

- Forum category list responses remain expected to decode as JSON objects with string `body`.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.
- `BeautifulSoup` remains responsible only after a validated string response body is available.

## Open Questions

None for this local slice. Similar non-mapping list-payload guards may be useful on other `.json().get("body")` read helpers, but each surface should receive its own duplicate check against the existing missing-body and body-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed forum category list responses without changing successful list parsing, request construction, login checks, parser behavior, category thread access, or create-thread actions.

## Local Evidence

- Local rollout-backed forum category drafts established category listing, body parsing, row context, title/description preservation, count parsing, direct acquire validation, and create-thread moderation as practical workflow surfaces.
- Existing local drafts covered missing forum category list body context, present non-string forum category list body values, malformed create-thread statuses, non-mapping create-thread payloads, and raw connector envelope status typing. They did not cover a decoded forum category list payload that is not a mapping before `body` lookup.
- This slice only validates forum category list payload shape. It does not change request construction, login checks, retry behavior, category parser structure, forum thread creation handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw forum content, raw response bodies, private site data, and private source text out of upstream discussion.
