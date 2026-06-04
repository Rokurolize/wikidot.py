# PR Draft: Include Post ID In Lazy Forum Post Source Errors

## Summary

`ForumPost.source` is the single-post lazy source accessor for `forum/sub/ForumEditPostFormModule`. The collection helper already leaves retry-exhausted batch entries uncached and, when malformed edit-form HTML is returned, raises `Source textarea is not found for post: <id>`. The single-post lazy property still raised the generic `Source textarea is not found.` if its own acquisition attempt left `_source` unset.

This follow-up keeps the existing failure behavior and batch partial-success semantics, but includes the post ID in the lazy property's final `NoElementException`. That makes exhausted or unresolved single-post source reads identifiable from plain logs without saving raw edit-form HTML or forum post content.

## Related Issue

Builds on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), and [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), because those drafts established forum post source reads and post-list parsing as practical read-heavy forum workflows.

This also follows the lazy-property failure visibility pattern from [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), and the page source/file/vote context drafts [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), [151-pr-page-file-failure-context.md](151-pr-page-file-failure-context.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), and [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Change `ForumPost.source` so the final unresolved-source `NoElementException` says `Source textarea is not found for post: <id>`.
- Strengthen the existing retry-exhaustion test to assert the post-specific message.
- Preserve cached source behavior, collection source fetching, retry-aware requests, partial-success batch behavior, direct edit-form textarea scoping, and mutation paths.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post source error-context ergonomics
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A lazy `ForumPost.source` read that remains unresolved after retry-aware acquisition still raises `NoElementException`. | `TestForumPostSource.test_source_property_raises_when_retry_is_exhausted` raises after `amc_request_with_retry(...)` returns `(None,)`. | A change that returns `None`, an empty string, or silently marks source as cached rejects this local completion claim. |
| The lazy source failure identifies the affected post. | The focused test asserts `Source textarea is not found for post: 5001`. | The RED test failed before the fix because the exception message was only `Source textarea is not found.` |
| Batch source acquisition keeps partial-success semantics. | `uv run pytest tests/unit/test_forum_post.py -q` passed 47 tests, including `test_get_post_sources_skips_failed_retry_response`. | A change that raises from `ForumPostCollection.get_post_sources()` on a single `None` retry result rejects this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 89 tests. | Regressions in post-list parsing, pagination, thread post access, source fetching, or edit behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1546b41 fix(forum_post): include post id in lazy source errors`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostSource::test_source_property_raises_when_retry_is_exhausted -q` failed before the fix because the exception message was only `Source textarea is not found.`
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostSource::test_source_property_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_post.py -q` passed 47 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py -q` passed 89 tests.
- `uv run pytest tests/unit -q` passed 719 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPost.source` still performs its existing lazy source acquisition when `_source` is unset.
- If the lazy acquisition does not populate `_source`, the property raises `NoElementException` with the affected post ID.
- `ForumPostCollection.get_post_sources()` still preserves partial-success behavior for batch callers.
- Cached source reads, successful source parsing, edit-form textarea scoping, duplicate source reuse, post-list parsing, and edit/reply mutation behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post source reads are a common follow-up after selecting a post from a thread. When a single lazy source read cannot populate source text, wikidot.py should continue to fail visibly, but the failure should identify the affected post so maintainers and caller logs can distinguish one unresolved post from another without storing raw edit-form HTML or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post source reads as a retry-aware read path with deduplication, cached duplicate reuse, and direct edit-form textarea scoping.
- Recent parser and lazy-property context slices showed that object-specific failure messages improve resumable local ledgers without changing successful behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/forum_post.py` as an audit-worthy parser/acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw edit-form HTML, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change source request payloads, retry policy, batch source acquisition, partial-success handling, source textarea parsing, source caching, duplicate-source reuse, post-list parsing, `ForumPost.edit(...)`, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds the post ID to an existing unresolved lazy-source exception.
