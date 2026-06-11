# PR: Validate forum post edit response counts

## Problem Statement

`ForumPost.edit(...)` sends one direct `saveEditPost` AMC action after fetching and parsing the edit form, then immediately indexes the first returned response. Before this change, a connector, mock, or adapter that returned zero responses leaked Python's raw `IndexError("list index out of range")` before wikidot.py could explain which site, post, and action broke the batch contract.

This was a low-context failure at a write-side mutation boundary. It also bypassed the existing edit diagnostics that preserve the post title, source cache, revision cache, and thread post cache until the returned action status is confirmed.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free forum editing as practical infrastructure for moderation helpers, migration fixtures, local tests, and write-side forum workflows. Existing local slices hardened `ForumPost.edit(...)` around edit-form retry response counts, edit-form payload shape, current revision IDs, retained site/client state, and action response payload shape. They did not validate the direct `saveEditPost` response count before indexing the returned response sequence.

The local fix is committed as `3a4f80e`.

## Affected Workflows

- Browser-free forum post edits through `ForumPost.edit(...)`.
- Generated moderation, migration, or forum-maintenance scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct action responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small forum post action response-count guard. Validate that the direct `saveEditPost` action response sequence has exactly one entry before indexing and parsing it. Raise `UnexpectedException` with site/post/event context and expected/actual counts on mismatch.

## Implementation Notes

The change adds `_require_forum_post_action_response_count(...)` next to the existing forum post action-status helper. `ForumPost.edit(...)` now stores the raw `site.amc_request(...)` result, validates the count, then parses `save_responses[0].json()` through the existing `_require_forum_post_action_status(...)` helper.

The guard intentionally stays local to forum post action handling instead of adding a generic `Site.amc_request(...)` response-count policy. Direct action callers already have domain-specific diagnostics, and a broad site-level guard could preempt more useful page/forum/private-message context.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_rejects_action_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit -q --tb=short
uv run pytest tests/unit/test_forum_post.py -q --tb=short
uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix because the new regression leaked raw `IndexError` from indexing the empty response list. The focused GREEN run passed after adding the count guard. Full unit verification passed 3965 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid edits still send the same `saveEditPost` request body and update local state only after action status is confirmed.
- Existing malformed edit-form, current revision ID, malformed payload, missing action status, malformed status type, explicit non-ok status, retained site/client, and cache-preservation diagnostics remain unchanged.
- Mismatched response-count failures preserve the post title, cached source, cached revisions, and thread post cache.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Rationale For Upstream Suitability

Direct forum post edits rely on positional correspondence between the submitted action and returned response. When that correspondence is broken, wikidot.py should report the forum action response-count failure directly instead of leaking a raw Python indexing error.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, forum request construction, edit-form acquisition, revision ID parsing, cache invalidation on success, action status parsing, live Wikidot behavior, or upstream filing state.
