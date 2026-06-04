# PR Draft: Validate Forum Post Source Response Bodies

## Summary

`ForumPostCollection.get_post_sources()` and lazy `ForumPost.source` retrieve post source text through `forum/sub/ForumEditPostFormModule` and then parse the returned edit form for `textarea[name='source']`. Earlier local slices made that path retry-aware, deduplicated duplicate post IDs, reused cached duplicate source text, skipped cached sources, scoped source textarea parsing to the direct edit-form child, and added site/post context for exhausted lazy source fetches and missing source textarea parse failures. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before source form parsing could report the affected post.

This follow-up keeps retry exhaustion, skipped `None` retry results, cached-source skipping, duplicate post-ID deduplication, cached duplicate source reuse, direct source textarea scoping, source text extraction, edit behavior, replies, post-list parsing, and `ForumPost.source` caching unchanged. It only treats a missing forum post source response `body` as a malformed source response and raises `NoElementException` with site/post context before edit-form parsing or source textarea extraction.

## Related Issue

Builds on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), and [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md). Those drafts established forum post source acquisition as retry-aware, cache-sensitive, duplicate-aware, edit-form scoped, and diagnosable.

No upstream issue was filed from this local workspace.

## Changes

- Add a small forum post source response-body helper that reads `response.json().get("body")`.
- Convert missing source edit-form response `body` into site/post-specific `NoElementException`.
- Preserve skipped `None` retry responses, cached-source fast paths, duplicate source propagation, source textarea parsing, lazy source behavior, edit behavior, replies, and post-list parsing.
- Add a focused regression for missing forum post source response body handling.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post source response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A forum post source response without JSON `body` still fails before edit-form parsing or source textarea extraction. | `TestForumPostCollectionGetSources.test_get_post_sources_missing_response_body_includes_site_and_post_context` returns `{}` from the source AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates empty source text, or marks the source as acquired rejects this local completion claim. |
| Malformed source response errors identify the affected site and post. | The focused regression asserts `Forum post source response body is not found for site: test-site, post: 5001`. | A generic parser exception without site/post context rejects this local completion claim. |
| Retry-exhausted `None` responses remain distinct from malformed JSON body responses. | Existing `test_get_post_sources_skips_failed_retry_response` and lazy source retry exhaustion tests remain green. | A change that turns skipped `None` retry responses into body-validation failures rejects this local completion claim. |
| Existing forum post source behavior remains green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 54 tests. | Regressions in retry behavior, cached-source skipping, duplicate source reuse, direct source textarea scoping, edit behavior, replies, or post-list parsing reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_category.py -q` passed 154 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `f2f01b6 fix(forum_post): validate source response bodies`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_response_body_includes_site_and_post_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_success tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_direct_source_textarea_includes_context tests/unit/test_forum_post.py::TestForumPostSource::test_source_property_calls_api -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 54 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_category.py -q` passed 154 tests.
- `uv run pytest tests/unit -q` passed 744 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Forum post source requests still use `forum/sub/ForumEditPostFormModule`, the same thread ID, and the same post ID.
- Missing source response JSON `body` raises `NoElementException` naming the site and post.
- Missing response-body handling does not fabricate source text, mark the post source as acquired, or convert retry-exhausted `None` responses into malformed-body failures.
- Successful source retrieval, retry behavior, cached-source skipping, duplicate post-ID deduplication, cached duplicate source reuse, direct source textarea scoping, lazy `ForumPost.source`, edit behavior, replies, and post-list parsing remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post source acquisition depends on Wikidot returning a JSON `body` field before edit-form parsing can start. If that field is missing, wikidot.py should report a structured malformed-response failure with the site and post ID, so caller logs can route failures without preserving raw response JSON, edit-form HTML, post source text, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post source acquisition as retry-aware, duplicate-aware, cached-source-aware, edit-form scoped, and backed by site/post parser context.
- The immediately prior forum post-list response slice showed the same raw `KeyError` failure mode at an adjacent `forum_post.py` AMC response-body boundary.
- Recent context slices showed that compact site/post identifiers improve resumable ledgers without changing successful behavior or storing raw post source text.
- The refreshed complexity memo continues to list parser/source collection helpers as follow-up leads, but this slice only claims forum post source response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, edit-form HTML, post source text, and private deployment details out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, cached-source behavior, duplicate post-ID handling, source textarea parser behavior, returned `ForumPostCollection`, lazy `ForumPost.source` caching, edit behavior, replies, post-list parsing, or live Wikidot behavior. It only converts missing forum post source response `body` fields into site/post-context `NoElementException` failures before parser work.
