# PR Draft: Include Site Context In Forum Thread Detail Fetch Failures

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, retrieves direct thread detail pages through retry-aware AMC requests. When a required thread detail response exhausted retries, the method raised `UnexpectedException("Cannot retrieve forum thread: ...")`, which identified the thread ID but not the Wikidot site.

This follow-up preserves retry-aware direct thread detail fetching, duplicate thread-ID deduplication, input-order restoration, optional category association, thread detail parser context, requested/parsed thread-ID mismatch detection, and successful direct thread lookup behavior, but includes the site unix name in exhausted thread-detail fetch failures.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), which introduced retry-aware direct thread detail fetching and explicit exhausted-retry failures. It also follows [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), and [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), because those drafts established direct thread detail acquisition, duplicate-ID handling, parser context, and category thread-list fetch context as practical rollout-backed surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include site unix name and requested thread ID when a direct thread detail retry result is exhausted.
- Strengthen the existing exhausted-retry unit test to assert `Cannot retrieve forum thread for site: test-site, thread: 3001`.
- Preserve retry-aware request construction, non-retry `amc_request(...)` avoidance, duplicate-ID deduplication, order restoration, parser-context errors, and successful thread detail parsing.

## Type Of Change

- Bug fix / diagnostics improvement
- Direct forum thread detail fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted retry direct thread-detail fetches still fail. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_raises_when_retry_is_exhausted` raises `UnexpectedException` when retry returns `None`. | A change that silently drops the failed thread or returns a fabricated thread rejects this local completion claim. |
| Exhausted-retry failures identify the failed site and thread. | The focused test asserts `Cannot retrieve forum thread for site: test-site, thread: 3001`. | The RED test failed before the fix because the message only said `Cannot retrieve forum thread: 3001`. |
| The retry-aware path is preserved. | The focused test asserts non-retry `amc_request(...)` is not called. | A change that falls back to the non-retry path rejects this local completion claim. |
| Direct thread detail behavior remains green. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 42 tests. | Regressions in direct thread lookup, duplicate-ID deduplication, category association, parser-context failures, requested/parsed mismatch handling, post access, or replies reject this local completion claim. |
| Adjacent forum workflows remain green. | `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests. | Regressions in category/thread/post/revision behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `d6a7a37 fix(forum_thread): include site in thread detail fetch failures`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_raises_when_retry_is_exhausted -q` failed before the fix because the exhausted-retry message lacked site context.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 42 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 148 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Exhausted retry-aware direct thread-detail fetches still raise `UnexpectedException`.
- The exception includes the site unix name and requested thread ID.
- Successful direct thread lookup, duplicate-ID deduplication, returned order, parser-context failures, requested/parsed thread-ID mismatch handling, optional category association, post access, and replies remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct thread detail acquisition can be called across sites and arbitrary thread IDs. The exhausted-retry failure should identify both the site and requested thread so logs can route the problem without raw AMC responses or local rollout context.

## Local Evidence, Not For Upstream Paste

- Earlier rollout-backed forum drafts established direct thread detail acquisition and duplicate-ID deduplication as practical local Codex surfaces.
- Recent context slices showed that site/thread-specific exhausted-retry messages improve multi-site ledgers without changing successful behavior.
- The refreshed complexity memo continues to keep action/read boundaries and remaining direct property/parser failure messages as follow-up leads, but this slice only claims direct thread detail exhausted-retry diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw AMC responses, and raw response bodies out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry counts, duplicate ID handling, order restoration, parser-context failures, returned `ForumThreadCollection`, optional category association, `ForumThread.posts`, `ForumThread.reply(...)`, or live Wikidot behavior. It only adds site context to the existing exhausted retry-aware direct thread detail failure.
