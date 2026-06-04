# PR Draft: Include Site Context In Forum Post Lazy Source Failures

## Summary

`ForumPost.source` is the single-post lazy source accessor for `forum/sub/ForumEditPostFormModule`. The accessor already performs retry-aware acquisition through `ForumPostCollection.get_post_sources()`, keeps retry-exhausted entries uncached, and raises when the requested post remains unresolved. The failure message identified the post ID, but not the Wikidot site: `Source textarea is not found for post: ...`.

This follow-up preserves lazy source acquisition, cached source reads, batch partial-success semantics, edit-form textarea scoping, duplicate source reuse, edit behavior, and reply behavior, but includes site unix name and post ID when the lazy source accessor remains unresolved after acquisition.

## Related Issue

Builds on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), and [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), because those drafts established retry-aware source fetching, duplicate/cached source behavior, and post-specific lazy source diagnostics. It also follows [173-pr-forum-post-edit-form-fetch-failure-context.md](173-pr-forum-post-edit-form-fetch-failure-context.md), which aligned adjacent edit-form fetch failures with site/post context.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name and post ID when lazy `ForumPost.source` remains unresolved after retry-aware acquisition.
- Strengthen the lazy source exhausted-retry regression to assert the contextual message.
- Preserve cached source reads, retry-aware source acquisition, batch partial-success behavior, duplicate source reuse, edit-form textarea scoping, edit behavior, post-list parsing, and replies.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post lazy source failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A lazy `ForumPost.source` read that remains unresolved after retry-aware acquisition still raises `NoElementException`. | `TestForumPostSource.test_source_property_raises_when_retry_is_exhausted` raises after `amc_request_with_retry(...)` returns `(None,)`. | A change that returns `None`, an empty string, or silently marks source as cached rejects this local completion claim. |
| The lazy source failure identifies the failed site and post. | The focused test asserts `Source textarea is not found for site: test-site, post: 5001`. | The RED test failed before the fix because the message only named the post ID. |
| Forum post workflows remain green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests. | Regressions in source fetching, edit-form retry, edit-form control scoping, lazy source, post-list parsing, edit-with-title, or reply behavior reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4c7fc20 fix(forum_post): include site in lazy source failures`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostSource::test_source_property_raises_when_retry_is_exhausted -q` failed before the fix because the lazy source message only named the post ID.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostSource::test_source_property_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_post.py -q` passed 48 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPost.source` still performs lazy retry-aware source acquisition when `_source` is unset.
- If source remains unresolved after acquisition, the accessor raises `NoElementException`.
- That exception includes the site unix name and post ID.
- Cached source reads, batch source partial-success behavior, duplicate source reuse, edit-form textarea scoping, edit behavior, post-list parsing, and replies remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post source reads are common after selecting posts from thread lists. When a lazy source read cannot populate source text, wikidot.py should continue to fail visibly and identify both the site and post so caller logs can route the failure without storing raw edit-form HTML, AMC responses, or post bodies.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established retry-aware forum post source fetching, duplicate/cached source behavior, and post-specific lazy source diagnostics.
- Recent forum exhausted-retry context slices showed that site-specific failure messages improve multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to list parser/source collection helpers and direct property/parser failure messages as follow-up leads, but this slice only claims lazy `ForumPost.source` diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw edit-form HTML, raw AMC responses, and post contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change source-fetch request payloads, retry policy, cached source behavior, duplicate source propagation, edit-form textarea parsing, batch partial-success semantics, edit behavior, post-list parsing, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds site context to an existing lazy forum post source failure.
