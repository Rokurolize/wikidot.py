# PR: Validate forum post revision HTML content type

## Summary

Forum post revision HTML acquisition should reject decoded `forum/sub/ForumPostRevisionModule` responses whose `content` field is present but not a string.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 300, which covers missing or `None` rendered-HTML `content`, and from local Issue 839, which covers non-mapping rendered-HTML response payload roots. This slice covers mapping payloads where `content` exists but carries a non-string value.

## Problem Statement

`ForumPostRevisionCollection.get_htmls()` retrieves rendered HTML for uncached forum post revisions through `forum/sub/ForumPostRevisionModule`. The same shared parsing helper is also used by `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` and lazy `ForumPostRevision.html`.

Before this change, `_revision_html_content(...)` handled missing `content` contextually, but accepted any present value by returning `str(content)`. A malformed payload such as `{"content": ["not-html"]}` could therefore be stored as the literal string representation of a list and marked as acquired HTML.

That behavior hides response-shape drift and gives downstream archive, moderation, migration, and comparison tooling fabricated rendered HTML instead of a clear domain exception.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify forum post revision HTML as a practical read surface for edit-history inspection, moderation ledgers, translation review tooling, archival jobs, migration checks, and generated comparison workflows.

Existing local drafts already hardened revision-list response bodies, revision-list payload roots, rendered-HTML payload roots, missing rendered-HTML `content`, HTML retry behavior, duplicate revision HTML request deduplication, cached duplicate HTML reuse, lazy HTML failure visibility, lazy failure context, retained revision IDs, retained post/thread/site state, and collection entries. The immediate uncovered source evidence before this slice was `_revision_html_content(revision, data)` validating only payload root shape and missing `content`, then coercing present non-string content with `str(content)`.

The local fix is committed as `3a664fd`.

## Affected Workflows

- Direct rendered revision HTML acquisition through `ForumPostRevisionCollection.get_htmls()`.
- Optional rendered HTML acquisition through `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)`.
- Lazy single-revision rendered HTML reads through `ForumPostRevision.html`.
- Moderation, archive, migration, translation-review, and diff workflows that compare historical forum post content.
- Generated fixtures, response adapters, and recorded-response tests that synthesize rendered revision HTML payloads.

## Proposed Fix

Validate the rendered-HTML response `content` field inside the shared `_revision_html_content(...)` helper. If `content` is present but not a string, raise `NoElementException` with site, post, revision, field, expected type, and actual type context before assigning any HTML cache.

Keep existing behavior unchanged for valid string content, including explicit empty-string content. Keep the existing missing-`content` diagnostic for absent and `None` values.

## Implementation Notes

The patch changes `_revision_html_content(...)` from:

```text
return str(content)
```

to an explicit string guard:

```text
if not isinstance(content, str):
    raise NoElementException(... field=content, expected=str, actual=<type> ...)
return content
```

The regression test configures `ForumPostRevisionCollection.get_htmls()` with a mocked rendered-HTML response whose `json()` value is `{"content": ["not-html"]}`. It asserts that the public collection API raises:

```text
Forum post revision HTML response content is malformed for site: test-site, post: 5001, revision: 9001 (field=content, expected=str, actual=list)
```

It also asserts that plain `amc_request` is not used and that the revision HTML cache remains unset.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_malformed_response_content_type_includes_site_post_revision_context -q --tb=short
uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_malformed_response_content_type_includes_site_post_revision_context -q
uv run pytest tests/unit/test_forum_post_revision.py -q
uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
RED: failed with DID NOT RAISE before the fix
focused GREEN: 1 passed
forum_post_revision module: 234 passed
forum adjacent suite: 937 passed
full unit suite: 3945 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

The complexity scan reported only pre-existing hotspots outside the changed constant-time rendered-HTML field guard.

## Compatibility And Risk Notes

The change only affects malformed decoded rendered-HTML payloads where `content` is present but not a string. Valid string HTML, explicit empty-string HTML, existing missing-`content`, non-mapping payload root, retry-exhausted, partial-success retry, duplicate request dedupe, cached duplicate reuse, lazy property failure, optional `with_html=True`, and successful HTML cache assignment behavior retain their current behavior.

The diagnostic intentionally includes only site/post/revision identifiers and type names. It does not include raw response JSON, rendered revision HTML, forum post source, forum post content, page content, account material, cookies, tokens, passwords, secrets, or auth JSON.

## Rationale For Upstream Suitability

The patch replaces silent malformed-content coercion with a domain exception at the rendered forum-post-revision HTML response boundary. It follows the response-shape validation style already used for forum post revision-list responses, page revision HTML responses, and rendered revision HTML payload roots, preserves public behavior for valid responses, and is covered by a regression through the public `ForumPostRevisionCollection.get_htmls()` API.

## Acceptance Criteria

- Forum post revision HTML acquisition validates decoded rendered-HTML response `content` is a string before assigning revision HTML caches.
- Present non-string `content` values raise `NoElementException` with site, post, revision, field, expected type, and actual type context.
- Malformed rendered-HTML content does not populate revision HTML caches.
- Existing missing-`content`, non-mapping payload, retry, duplicate request, cached duplicate, lazy property, optional `with_html=True`, and successful HTML behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `3a664fd`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `61074d5ce62c253930498bdb5a517a1ca63e4263c9a9c251fb6f37cb78f7b4ec`.
- No raw response JSON, rendered revision HTML, forum post source, forum post content, page content, account material, cookies, tokens, passwords, secrets, or auth JSON were captured in this draft.
