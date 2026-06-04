# PR Draft: Include Site Context In Forum Post Source Form Parse Errors

## Summary

`ForumPostCollection.get_post_sources()` fetches `forum/sub/ForumEditPostFormModule` for uncached forum posts and parses the generated edit form for the direct `textarea[name='source']`. When a malformed edit form lacked that direct source textarea, the helper raised `NoElementException("Source textarea is not found for post: ...")`, which identified the post but not the Wikidot site.

This follow-up preserves retry-aware source acquisition, cached source reads, duplicate source reuse, batch partial-success behavior for failed retry responses, edit-form direct-child scoping, lazy `ForumPost.source`, edit behavior, and reply behavior, but includes site unix name and post ID when a fetched edit form is malformed.

## Related Issue

Builds on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), and [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), because those drafts established retry-aware source fetching, duplicate/cached source behavior, edit-form direct-child scoping, and lazy source diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name and post ID when `ForumPostCollection.get_post_sources()` receives an edit form without a direct source textarea.
- Add a malformed edit-form regression that nests the source textarea under a child element and asserts the contextual failure.
- Preserve cached source reads, retry-aware source acquisition, failed-retry partial-success behavior, duplicate source reuse, edit-form textarea scoping, lazy source behavior, edit behavior, post-list parsing, and replies.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post source form parse failure context
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A fetched edit form missing the generated direct source textarea still raises `NoElementException`. | `TestForumPostCollectionGetSources.test_get_post_sources_missing_direct_source_textarea_includes_context` replaces the direct textarea with a nested one and expects an exception. | A change that reads nested preview/source markup, returns an empty source, or silently caches source rejects this local completion claim. |
| The malformed source-form failure identifies the failed site and post. | The focused test asserts `Source textarea is not found for site: test-site, post: 5001`. | The RED test failed before the fix because the message only named the post ID. |
| Forum post workflows remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 49 tests. | Regressions in source fetching, edit-form retry, edit-form control scoping, lazy source, post-list parsing, edit-with-title, or reply behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 149 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `5f45759 fix(forum_post): include site in source form parse errors`.

- Initial focused command used the wrong class nodeid and collected no tests, then the corrected nodeid was used.
- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_direct_source_textarea_includes_context -q` failed before the fix because the malformed source-form message only named the post ID.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_direct_source_textarea_includes_context -q`
- `uv run pytest tests/unit/test_forum_post.py -q` passed 49 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 149 tests.
- `uv run pytest tests/unit -q` passed 723 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostCollection.get_post_sources()` still fetches source forms through retry-aware AMC for uncached posts.
- Malformed fetched edit forms without a direct source textarea still raise `NoElementException`.
- That exception includes the site unix name and post ID.
- Cached source reads, duplicate source reuse, failed-retry partial-success behavior, edit-form direct-child scoping, lazy source behavior, edit behavior, post-list parsing, and replies remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post source reads can run across many sites and posts. If Wikidot returns malformed edit-form markup, wikidot.py should keep rejecting nested or missing source controls and identify both site and post so caller logs can route the failure without storing raw edit-form HTML, AMC responses, or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established retry-aware forum post source fetching, duplicate/cached source behavior, edit-form direct-child scoping, and lazy source diagnostics.
- Recent forum context slices showed that site-specific failure messages improve multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to list parser/source collection helpers and direct property/parser failure messages as follow-up leads, but this slice only claims source form parse diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw edit-form HTML, raw AMC responses, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change source-fetch request payloads, retry policy, cached source behavior, duplicate source propagation, failed-retry partial-success behavior, edit-form textarea parsing rules, lazy source behavior, edit behavior, post-list parsing, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds site context to an existing malformed forum post source-form parse failure.
