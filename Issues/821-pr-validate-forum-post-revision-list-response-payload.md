# PR Draft: Validate Forum Post Revision List Response Payload

## Summary

`ForumPostRevisionCollection.acquire_all(post)` now validates that decoded `forum/sub/ForumPostRevisionsModule` list responses are dictionaries before reading `body`. Non-mapping payloads such as `["not", "a", "mapping"]` raise contextual `NoElementException` with site, post, expected type, and actual type context instead of leaking raw `AttributeError` from `.get("body")`.

The change is intentionally narrow: valid revision-list parsing, retry exhaustion, missing `body` diagnostics, present non-string `body` diagnostics, cache assignment, batched acquisition, optional HTML acquisition, and lazy revision HTML behavior remain unchanged.

## Problem Statement

`ForumPostRevisionCollection.acquire_all(post)` fetches forum post edit-history rows from `forum/sub/ForumPostRevisionsModule`, decodes the response, extracts `body`, and parses generated revision-list HTML. Earlier local slices covered retry-aware revision fetches, duplicate fetch deduplication, cached duplicate reuse, retry-exhausted context, missing response `body`, present non-string response `body`, revision row parser context, direct post validation, retained post IDs, mixed-site batch rejection, and optional HTML acquisition. One adjacent response-boundary gap remained: if `response.json()` returned a non-dictionary payload, `_revision_list_response_body(...)` attempted `.get("body")` and leaked raw `AttributeError`.

That failure gives callers neither the affected post nor a stable wikidot.py data-shape exception. Generated fixtures, response adapters, recorded traffic, or mocked responses should be classified before field access, and malformed list payloads must not enter BeautifulSoup parsing or revision row parsing.

## Rollout Evidence

Local rollout-backed drafts identify forum post revision reads as a practical browser-free workflow: [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md), and [679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md](679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md).

This slice is not a duplicate of [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md). Issue 217 covered mapping responses with a missing `body` field.

This slice is not a duplicate of [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md). Issue 329 covered a present non-string `body` field inside a mapping, such as `{"body": ["not", "html"]}`.

Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level response-body extraction. This slice covers the decoded module payload handed to forum post revision-list parsing.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free forum post revision listing through `ForumPostRevisionCollection.acquire_all(post)`.
- Revision audit tooling that lists edit history before optional HTML acquisition.
- Generated fixtures and recorded-response tests that decode revision-list responses before returning them to wikidot.py module code.

## Proposed Fix

- Decode the revision-list response once in `_revision_list_response_body(...)`.
- Validate the decoded payload is a dictionary before reading `body`.
- Reject non-dictionary payloads with contextual `NoElementException`.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-body, body-type, parser, cache, batch, and HTML acquisition behavior.

## Implementation Notes

Implemented locally in commit `1bb2780 fix(forum_post_revision): validate list response payload`.

The implementation adds one preflight guard before `body` lookup:

```python
data = response.json()
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        "Forum post revision list response payload is malformed "
        f"for site: {post.thread.site.unix_name}, post: {post.id} "
        f"(expected=dict, actual={type(data).__name__})"
    )

body = data.get("body")
```

The RED regression mocked `ForumPostRevisionCollection.acquire_all(post)`'s response as `["not", "a", "mapping"]`. Before the fix, the helper leaked `AttributeError: 'list' object has no attribute 'get'`. After the fix, the same case raises contextual `NoElementException` before revision parsing and leaves the post revision cache unset.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary forum post revision-list payloads fail before `body` lookup. | `test_acquire_all_malformed_response_payload_type_includes_site_post_and_type_context` failed RED with raw `AttributeError`, then passed GREEN. | Reaching `.get("body")`, leaking `AttributeError`, coercing the payload, or treating a list as a revision-list response rejects this claim. |
| Missing `body` in a dictionary keeps the existing Issue 217 diagnostic. | Focused GREEN included `test_acquire_all_missing_response_body_includes_site_and_post_context`. | Reclassifying `{}` as the payload-type branch or changing the missing-body message rejects this claim. |
| Present non-string `body` keeps the existing Issue 329 diagnostic. | Focused GREEN included `test_acquire_all_malformed_response_body_type_includes_site_post_and_type_context`. | Reclassifying `{"body": ["not", "html"]}` as a payload-type error or dropping `field=body` rejects this claim. |
| Malformed payloads do not seed the post revision cache. | The new regression asserts `_revisions is None` after the malformed payload failure. | Assigning an empty collection, entering revision parsing, or hiding the site/post context rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3918 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, complexity scan, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, complexity, provenance, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `1bb2780 fix(forum_post_revision): validate list response payload`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_response_payload_type_includes_site_post_and_type_context -q` failed before the fix with raw `AttributeError: 'list' object has no attribute 'get'`.
- GREEN focused: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_response_payload_type_includes_site_post_and_type_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_post_and_type_context -q` passed 3 tests.
- Forum post revision module coverage: `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 231 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3918 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused complexity scan of `src/wikidot/module/forum_post_revision.py` reported no obvious complexity hotspots.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(post)` with `response.json()` returning `["not", "a", "mapping"]` raises `NoElementException` matching `Forum post revision list response payload is malformed for site: test-site, post: 5001 (expected=dict, actual=list)`.
- `{}` still raises the existing missing-body message.
- `{"body": ["not", "html"]}` still raises the existing malformed body-type message with `field=body`, `expected=str`, and `actual=list`.
- The malformed payload branch decodes the response JSON once, leaves `_revisions` unset, and does not include raw response data.
- Valid revision-list parsing, retry exhaustion, batched acquisition, duplicate handling, optional HTML acquisition, and lazy HTML behavior remain unchanged.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `AttributeError` from malformed synthetic list responses. Mitigation: the public module expects a body-bearing result object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This only covers direct `acquire_all(post)` evidence. Mitigation: the shared helper is also used by batched acquisition, so the guard applies consistently without adding duplicate tests for every caller in this slice.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, post, expected type, and actual type while avoiding raw response data that could contain private forum content.

## Dependencies

- Forum post revision-list responses remain expected to decode as JSON objects with string `body`.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.
- `BeautifulSoup` remains responsible only after a validated string response body is available.

## Open Questions

None for this local slice. Similar non-mapping list-payload guards remain useful on other `.json().get("body")` read helpers, but each surface should receive its own duplicate check against the existing missing-body and body-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed forum post revision-list responses without changing successful list parsing, request construction, retry policy, cache behavior, batched acquisition, or optional revision HTML behavior.

## Local Evidence

- Local rollout-backed forum post revision drafts established revision-list acquisition, response-body parsing, retry context, duplicate handling, optional HTML acquisition, and revision row parser diagnostics as practical workflow surfaces.
- Existing local drafts covered missing forum post revision-list body context, present non-string forum post revision-list body values, raw connector envelope status typing, retained post IDs, cache ownership, and mixed-site batch rejection. They did not cover a decoded forum post revision-list payload that is not a mapping before `body` lookup.
- This slice only validates forum post revision-list payload shape. It does not change request construction, retry behavior, revision parser structure, optional HTML acquisition, lazy HTML behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw forum content, raw response bodies, private site data, and private source text out of upstream discussion.
