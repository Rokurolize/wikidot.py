# PR: Validate forum post revision HTML response payloads

## Summary

Forum post revision HTML acquisition should validate that decoded `forum/sub/ForumPostRevisionModule` response payloads are mappings before reading `content`.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 217 and Issue 821, which cover forum post revision-list response bodies and non-mapping revision-list payload roots. It is also distinct from local Issue 300, which covers mapping rendered-HTML responses where `content` is missing, and from the retained-state and collection-entry issues that validate revision objects before request construction.

## Problem Statement

`ForumPostRevisionCollection.get_htmls()` retrieves rendered HTML for uncached forum post revisions through `forum/sub/ForumPostRevisionModule`. The same shared parsing helper is also used by `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` and lazy `ForumPostRevision.html`.

If a decoded rendered-HTML response payload was a list, string, or other non-mapping value, `_revision_html_content(...)` attempted `.get("content")` on that value and raised raw `AttributeError: 'list' object has no attribute 'get'`. That failure bypassed the existing site/post/revision missing-`content` diagnostic and did not classify the response root as malformed module data.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify forum post revision HTML as a practical read surface for edit-history inspection, moderation ledgers, translation review tooling, archival jobs, migration checks, and generated comparison workflows.

Existing local drafts already hardened revision-list response bodies, revision-list payload roots, HTML retry behavior, duplicate revision HTML request deduplication, cached duplicate HTML reuse, lazy HTML failure visibility, lazy failure context, missing rendered-HTML `content`, retained revision IDs, retained post/thread/site state, and collection entries. The immediate uncovered source evidence before this slice was `_revision_html_content(revision, data)` accepting the decoded HTML response payload and reading `data.get("content")` without first validating that `data` is a mapping.

The local fix is committed as `587f723`.

## Affected Workflows

- Direct rendered revision HTML acquisition through `ForumPostRevisionCollection.get_htmls()`.
- Optional rendered HTML acquisition through `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)`.
- Lazy single-revision rendered HTML reads through `ForumPostRevision.html`.
- Moderation, archive, migration, translation-review, and diff workflows that compare historical forum post content.
- Generated fixtures, response adapters, and recorded-response tests that synthesize rendered revision HTML payloads.

## Proposed Fix

Validate rendered-HTML response payload roots inside the shared `_revision_html_content(...)` helper. If the decoded payload is not a `dict`, raise `NoElementException` with site, post, revision, expected type, and actual type context before reading `content`.

Keep existing behavior unchanged for valid mapping payloads: missing `content` diagnostics, string conversion of present content, retry partial-success behavior, duplicate request deduplication, cached duplicate HTML reuse, direct `get_htmls()`, optional `with_html=True`, lazy `revision.html`, revision-list acquisition, and HTML cache assignment remain unchanged.

## Implementation Notes

The patch changes `_revision_html_content(...)` to accept `object`, validate the root as a mapping, and then continue using the existing `content` extraction path.

The regression test configures `ForumPostRevisionCollection.get_htmls()` with a mocked rendered-HTML response whose `json()` value is a list. It asserts that the public collection API raises:

```text
Forum post revision HTML response payload is malformed for site: test-site, post: 5001, revision: 9001 (expected=dict, actual=list)
```

It also asserts that plain `amc_request` is not used and that the revision HTML cache remains unset.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_malformed_response_payload_type_includes_site_post_revision_context -q
uv run pytest tests/unit/test_forum_post_revision.py -q -k "get_htmls_malformed_response_payload_type or get_htmls_retries_transient_fetch_failures or get_htmls_skips_failed_retry_response or get_htmls_deduplicates_duplicate_revision_ids or get_htmls_reuses_cached_duplicate_revision_html or get_htmls_accepts_zero_retained_revision_id or acquire_all_for_posts_with_html_missing_response_content or acquire_all_for_posts_with_html_retries_transient_html_failures or html_property_missing_response_content or html_property_raises_when_retry_is_exhausted"
uv run pytest tests/unit/test_forum_post_revision.py -q
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
forum_post_revision module: 232 passed
full unit suite: 3942 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

The complexity scan reported only pre-existing hotspots outside the changed constant-time rendered-HTML payload guard.

## Compatibility And Risk Notes

The change only affects malformed decoded rendered-HTML payload roots on forum post revision HTML reads. Valid mapping payloads and existing missing-`content`, retry-exhausted, partial-success retry, duplicate request dedupe, cached duplicate reuse, lazy property failure, optional `with_html=True`, and successful HTML cache assignment behavior retain their current behavior.

The diagnostic intentionally includes only site/post/revision identifiers and type names. It does not include raw response JSON, rendered revision HTML, forum post source, forum post content, page content, account material, cookies, tokens, passwords, secrets, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces incidental Python container errors with a domain exception at the rendered forum-post-revision HTML response boundary. It follows the response-shape validation style already used for forum post revision-list responses and page revision HTML responses, preserves public behavior for valid responses, and is covered by a regression through the public `ForumPostRevisionCollection.get_htmls()` API.

## Acceptance Criteria

- Forum post revision HTML acquisition validates decoded rendered-HTML response payloads are mappings before reading `content`.
- Non-mapping payloads raise `NoElementException` with site, post, revision, expected type, and actual type context.
- Malformed rendered-HTML payloads do not populate revision HTML caches.
- Existing missing-`content`, retry, duplicate request, cached duplicate, lazy property, optional `with_html=True`, and successful HTML behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `587f723`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw response JSON, rendered revision HTML, forum post source, forum post content, page content, account material, cookies, tokens, passwords, secrets, or auth JSON were captured in this draft.
