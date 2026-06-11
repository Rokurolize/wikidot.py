# PR: Validate forum thread reply response counts

## Problem Statement

`ForumThread.reply(...)` sends one direct `savePost` AMC action and then immediately indexes the first returned response. Before this change, a connector, mock, or adapter that returned zero responses leaked Python's raw `IndexError("list index out of range")` before wikidot.py could explain which site, thread, and action broke the batch contract.

This was a low-context failure at an important mutation boundary. It also bypassed the existing reply diagnostics that preserve cached posts, category thread caches, and local post counters until the returned action status is confirmed.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free forum replies as practical infrastructure for moderation helpers, migration fixtures, generated forum ledgers, local tests, and write-side forum workflows. Existing local slices hardened `ForumThread.reply(...)` around text inputs, parent-post IDs, retained thread IDs, retained site/client state, category cache synchronization, action response payload shape, and action status fields. They did not validate direct `savePost` response count before indexing the returned response sequence.

The local fix is committed as `3972869`.

## Affected Workflows

- Browser-free forum replies through `ForumThread.reply(...)`.
- Generated forum migration, moderation, or ledger scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct action responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small forum thread action response-count guard. Validate that the direct `savePost` action response sequence has exactly one entry before indexing and parsing it. Raise `UnexpectedException` with site/thread/event context and expected/actual counts on mismatch.

## Implementation Notes

The change adds `_require_forum_thread_action_response_count(...)` next to the existing forum thread action-status helper. `ForumThread.reply(...)` now stores the raw `site.amc_request(...)` result, validates the count, then parses `responses[0].json()` through the existing `_require_forum_thread_action_status(...)` helper.

The guard intentionally stays local to `ForumThread.reply(...)` instead of adding a generic `Site.amc_request(...)` response-count policy. Direct action callers already have domain-specific diagnostics, and a broad site-level guard could preempt more useful page/forum/private-message context.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_action_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_forum_thread.py::TestForumThreadReply -q --tb=short
uv run pytest tests/unit/test_forum_thread.py -q --tb=short
uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix because the new regression leaked raw `IndexError` from indexing the empty response list. The focused GREEN run passed after adding the count guard. Full unit verification passed 3964 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid replies still send the same `savePost` request body and update local state only after action status is confirmed.
- Existing malformed payload, missing action status, malformed status type, explicit non-ok status, text-input, retained thread-ID, parent-post-ID, and retained site/client diagnostics remain unchanged.
- Mismatched response-count failures preserve cached posts, category post counts, category thread caches, and thread post counts.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Rationale For Upstream Suitability

Direct forum replies rely on positional correspondence between the submitted action and returned response. When that correspondence is broken, wikidot.py should report the forum action response-count failure directly instead of leaking a raw Python indexing error.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, forum request construction, reply idempotency, post-list fetching, cache invalidation on success, action status parsing, live Wikidot behavior, or upstream filing state.
