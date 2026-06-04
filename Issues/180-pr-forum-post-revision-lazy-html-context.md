# PR Draft: Include Context In Lazy Forum Post Revision HTML Failures

## Summary

`ForumPostRevision.html` lazily fetches rendered revision HTML through retry-aware `ForumPostRevisionCollection.get_htmls()`. A previous local slice made that property fail visibly when retry exhaustion left the requested revision uncached, but the resulting `UnexpectedException` only named the forum post revision ID.

This follow-up keeps lazy retry behavior, batch partial-success behavior, duplicate revision-ID handling, cached reads, revision HTML response parsing, request payloads, retry policy, and exception type unchanged, but includes site unix name and post ID alongside the revision ID in lazy exhausted-retry failures.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), and [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), because those drafts established retry-aware forum post revision HTML acquisition, duplicate/cached behavior, visible lazy HTML failures, contextual forum post revision-list failures, and the matching page-revision lazy context rule.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name, post ID, and revision ID when lazy `ForumPostRevision.html` retry acquisition leaves rendered HTML uncached.
- Tighten the existing lazy HTML exhausted-retry regression to assert site/post/revision context.
- Preserve cached property reads, retry-aware lazy acquisition, batch partial-success semantics, duplicate revision-ID grouping, revision HTML response parsing, request payloads, retry policy, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision lazy HTML failure context
- Test tightening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy `ForumPostRevision.html` still fails visibly when retry acquisition leaves HTML uncached. | `TestForumPostRevisionHtml.test_html_property_raises_when_retry_is_exhausted` returns `(None,)` from retry fetches and expects `UnexpectedException`. | Returning `None`, silently caching placeholder HTML, or changing the retry module payload rejects this local completion claim. |
| Lazy HTML failures identify the site, post, and revision. | The focused regression asserts `Cannot retrieve forum post revision HTML for site: test-site, post: 5001, revision: 9001`. | The RED test failed before the fix because the message only named revision `9001`. |
| Forum post revision behavior remains green. | `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 39 tests. | Regressions in revision-list parsing, optional `with_html=True`, duplicate/cached revision HTML handling, or lazy HTML behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `413a5a2 fix(forum_post_revision): include context in lazy html failures`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_raises_when_retry_is_exhausted -q` failed before the fix because the message only named revision `9001`.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 39 tests.
- `uv run pytest tests/unit -q` passed 725 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevision.html` still performs lazy retry-aware acquisition when `_html` is unset.
- `ForumPostRevision.html` still raises `UnexpectedException` if `_html` remains unset after that acquisition attempt.
- The lazy HTML failure names the site unix name, post ID, and revision ID.
- Cached HTML values still return without an AMC request.
- Batch `ForumPostRevisionCollection.get_htmls()` behavior remains unchanged.
- `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post revision HTML is often inspected through the single-revision property after selecting an edit-history row. When that lazy read exhausts retry, logs should identify the site and post as well as the revision so callers can diagnose the failed edit-history item without keeping raw response HTML, post text, credentials, or local rollout details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post revision HTML reads as a practical read-heavy surface: retry-aware acquisition, duplicate revision HTML deduplication, cached duplicate reuse, optional `with_html=True`, and visible lazy HTML failures.
- Recent context slices showed that compact site/post/revision identifiers improve multi-surface ledgers without changing successful behavior.
- This slice only claims lazy forum post revision HTML failure diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, raw post text, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, batch partial-success behavior, duplicate revision-ID grouping, cached duplicate reuse, revision-list parsing, optional `with_html=True` acquisition, forum post source fetching, edit/reply mutation methods, or live Wikidot behavior. It only adds site/post/revision context to existing lazy exhausted-retry HTML failures.
