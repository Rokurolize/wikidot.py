# PR: Validate forum category thread creation response counts

## Summary

`ForumCategory.create_thread(...)` sends one direct `newThread` AMC action and then immediately indexes the first returned response. Before this change, a connector, mock, or adapter that returned zero responses leaked Python's raw `IndexError("list index out of range")` before wikidot.py could explain which site, category, and action broke the batch contract.

This change validates the direct forum category action response count before any returned response is parsed. A mismatch now raises `UnexpectedException("Forum category action response count mismatch ...")` with site, category, event, expected count, and actual count. Existing input validation, login checks, request construction, created-thread ID parsing, action payload/status validation, cache invalidation ordering, and successful thread creation behavior remain unchanged.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issues 719, 796, and 812, which validate `ForumCategory.create_thread(...)` input, retained state, and returned action payload/status fields after one response has already been selected. This slice validates the returned direct action batch arity before response selection and parsing.

This is distinct from local Issue 846, which validates `Site.amc_request_with_retry(...)` response counts for retry-aware reads. `ForumCategory.create_thread(...)` uses direct `site.amc_request(...)`, so it needed a category-level direct action guard.

## Problem Statement

Direct forum thread creation expects exactly one returned AMC response for the one submitted `newThread` action. If `site.amc_request(...)` returns an empty result, the old code attempted `[0]` and raised a raw `IndexError`.

That failure was low-context and bypassed the library's existing forum action diagnostics. Callers could not tell from the exception whether the problem belonged to the site, category, action response count, action payload, created thread ID, or later created-thread fetch.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free forum creation as practical infrastructure for migration fixtures, generated forum ledgers, moderation helpers, and local tests. Existing local slices hardened forum category creation around retained category IDs, action response payload shape, created thread IDs, and action status. They did not validate direct `newThread` response count before indexing the returned response sequence.

The local fix is committed as `00b6bbd`.

## Affected Workflows

- Browser-free forum thread creation through `ForumCategory.create_thread(...)`.
- Generated forum migration or moderation scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct action responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small forum category action response-count guard. Validate that the direct `newThread` action response sequence has exactly one entry before indexing and parsing it. Raise `UnexpectedException` with site/category/event context and expected/actual counts on mismatch.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_rejects_action_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread -q --tb=short
uv run pytest tests/unit/test_forum_category.py -q --tb=short
uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix because the new regression leaked raw `IndexError` from indexing the empty response list. The focused GREEN run passed after adding the count guard. Full unit verification passed 3963 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Acceptance Criteria

- `ForumCategory.create_thread(...)` raises `UnexpectedException` with site, category, event, expected count, and actual count when direct `newThread` response count differs from one.
- Mismatched response-count failures occur before parsing any returned response.
- Mismatched response-count failures preserve any cached category thread collection and do not fetch the created thread.
- Existing malformed payload, missing/invalid `threadId`, malformed action status, explicit non-ok status, and successful creation behavior remain unchanged.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, forum request construction, thread detail fetching, cache invalidation on success, action status parsing, live Wikidot behavior, or upstream filing state.

## Upstream-Safe Motivation

Direct thread creation relies on positional correspondence between the submitted action and returned response. When that correspondence is broken, wikidot.py should report the forum action response-count failure directly instead of leaking a raw Python indexing error.
