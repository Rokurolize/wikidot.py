# PR Draft: Validate Forum Thread Posts Cache Retained Thread ID State

## Summary

`ForumThread._posts` cache ownership validation verifies that a cached `ForumPostCollection` and its entries belong to the receiving `ForumThread`, but the ownership helper compared retained `ForumThread.id` values directly. After local fixture, serialized, or rehydrated state has been mutated incorrectly, booleans and floats could satisfy Python equality against integer thread IDs, while strings, lists, or negative IDs were reported as generic posts-cache ownership mismatches instead of deterministic retained thread-ID corruption.

This change validates both the receiving thread ID and each cached parent/entry thread ID before comparing posts-cache ownership. Malformed retained IDs now raise `ValueError("thread_id must be an integer")`, negative retained IDs now raise `ValueError("thread_id must be non-negative")`, valid different-thread caches still raise `ValueError("thread.posts must belong to the thread")`, valid same-thread caches including zero-ID state remain accepted, and no forum fetch or live Wikidot behavior changes.

## Outcome

Direct `ForumThread(..., _posts=...)` construction can no longer accept or misclassify cached post collections whose retained parent or entry thread IDs are corrupted.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum thread reads, cached duplicate thread-post reuse, generated forum ledgers, migration fixtures, local tests, or rehydrated `ForumThread` / `ForumPostCollection` records before exposing `ForumThread.posts`.

## Current Evidence

Local rollout-backed drafts already established forum thread post caches as a practical boundary. [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md), and [595-pr-validate-forum-thread-posts-cache-ownership.md](595-pr-validate-forum-thread-posts-cache-ownership.md) cover cached thread-post reuse, collection parent shape, direct `_posts` cache shape, collection ownership, and direct thread posts-cache ownership for valid comparable IDs.

This slice is not a duplicate of those drafts. Issue 595 validates that the cached collection parent and cached post entries point at the same logical thread/site as the receiving `ForumThread`, but it assumes the retained `thread.id` values are already valid integers. This slice validates corrupted retained thread-ID state before the Issue 595 ownership comparison so booleans, floats, strings, lists, and negative IDs cannot be accepted by Python equality or hidden behind a generic wrong-thread diagnostic.

## Related Issue / Non-Duplicate Analysis

Builds directly on [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md), and [595-pr-validate-forum-thread-posts-cache-ownership.md](595-pr-validate-forum-thread-posts-cache-ownership.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate the receiving `ForumThread.id` before comparing cached posts ownership.
- Validate each cached collection parent and cached post entry `ForumThread.id` before comparing it to the receiving thread ID.
- Reject malformed retained thread IDs such as `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject negative retained thread IDs such as `-1` with `ValueError("thread_id must be non-negative")`.
- Preserve valid same-thread caches, valid zero-ID same-thread caches, valid different-thread ownership diagnostics, malformed cache object diagnostics, malformed cache-entry diagnostics, lazy thread post acquisition, cached duplicate thread-post reuse, forum post source/edit behavior, and adjacent forum workflows.

## Type Of Change

- Input validation
- Retained forum-thread ID hardening
- Forum posts-cache ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(..., _posts=ForumPostCollection(parent_thread, []))` must reject malformed retained cached parent `thread.id` values such as `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before posts-cache ownership comparison. |
| R2 | `ForumThread(..., _posts=ForumPostCollection(parent_thread, [post]))` must reject malformed retained cached post-entry `post.thread.id` values such as `True`, `False`, `"3001"`, `3001.0`, and `[]` with the same diagnostic before posts-cache ownership comparison. |
| R3 | The same constructor must reject negative retained cached parent or entry `thread.id` values such as `-1` with `ValueError("thread_id must be non-negative")`. |
| R4 | Valid same-thread cached post collections, valid zero-ID same-thread caches, valid different-thread ownership mismatches, malformed cache shape diagnostics, and adjacent forum workflows must remain green. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-thread module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed cached collection parent thread IDs fail before ownership comparison. | `test_init_rejects_posts_cache_with_malformed_retained_parent_thread_ids` failed RED for five malformed values: booleans and `3001.0` were accepted, while `"3001"` and `[]` raised generic `thread.posts` ownership mismatch. The test passed GREEN after retained target/cached thread ID validation. | Accepting booleans or floats, returning generic ownership mismatch for corrupted retained IDs, coercing strings/lists, or storing the cache rejects this local completion claim. | `ForumThread._posts` cache parent state | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Malformed cached post-entry thread IDs fail before ownership comparison. | `test_init_rejects_posts_cache_entry_with_malformed_retained_thread_ids` failed RED for five malformed values with the same accepted or generic-mismatch behavior, then passed GREEN after retained entry thread ID validation. | Accepting malformed entry thread IDs, relying on Python numeric equality, or storing the entry under `thread.posts` rejects this local completion claim. | `ForumThread._posts` cache entry state | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Negative cached parent and entry thread IDs fail before ownership comparison. | `test_init_rejects_posts_cache_with_negative_retained_parent_thread_id` and `test_init_rejects_posts_cache_entry_with_negative_retained_thread_id` failed RED with generic ownership mismatch, then passed GREEN after retained ID validation. | Treating negative IDs as ordinary wrong-thread ownership, accepting them, or coercing them rejects this local completion claim. | Forum posts-cache ownership validation | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R4 | Existing cache ownership behavior remains compatible. | Focused GREEN coverage passed 16 tests, `tests/unit/test_forum_thread.py` passed 180 tests, adjacent forum/category/post/revision/site coverage passed 926 tests, and full unit passed 3083 tests. | Regressing valid same-thread caches, zero IDs, different-thread diagnostics, malformed cache shape diagnostics, lazy post acquisition, cached duplicate thread-post reuse, forum post source/edit behavior, or any unit test rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c9a0d38 fix(forum_thread): validate posts cache retained thread ids`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_accepts_valid_posts_cache tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_from_different_thread tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_with_malformed_retained_parent_thread_ids tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_with_negative_retained_parent_thread_id tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_entry_from_different_thread tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_entry_with_malformed_retained_thread_ids tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_posts_cache_entry_with_negative_retained_thread_id -q` failed 12 retained parent/entry thread-ID cases before the fix; 3 valid-cache and valid different-thread ownership guards passed.
- GREEN: the same focused command plus zero-ID compatibility passed 16 tests after validating target and cached thread IDs before ownership comparison.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 180 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 926 tests.
- `uv run pytest tests/unit -q` passed 3083 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations because `pyright` is configured but not installed as a project executable in this local environment.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(..., _posts=ForumPostCollection(parent_thread, []))` raises `ValueError("thread_id must be an integer")` when the cached parent thread's retained `id` is `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- The same constructor raises `ValueError("thread_id must be non-negative")` when the cached parent thread's retained `id` is `-1`.
- `ForumThread(..., _posts=ForumPostCollection(thread, [post]))` raises the same malformed and negative retained-ID diagnostics when the cached post entry's retained `post.thread.id` is corrupted.
- Valid same-thread cached post collections still initialize and return the retained cache through `thread.posts`.
- Valid same-thread cached post collections with retained thread ID `0` remain accepted.
- Valid different-thread cached collections and cached entries still raise `ValueError("thread.posts must belong to the thread")`.
- Existing malformed `_posts` object and malformed `_posts` entry diagnostics remain unchanged.
- Existing forum category, thread, post, revision, and site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread._posts` is a direct cache slot for browser-free forum reads, discussion migration ledgers, duplicate cached thread-post reuse, and local fixture reconstruction. Ownership validation already protects against another thread's post list being stored under the current thread, but corrupted retained thread IDs should fail as corrupted identity state before Python equality can accept booleans/floats or generic ownership mismatch can hide strings/lists/negative IDs. Validating retained thread IDs before comparison keeps the existing ownership contract precise without changing network behavior or parser selectors.

## Local Evidence

- Existing local drafts covered forum thread post-list retry behavior, duplicate thread-post request reduction, cached duplicate post reuse, optional `_posts` cache shape, collection constructor ownership, and direct `_posts` ownership for valid comparable IDs.
- None of those drafts covered malformed retained `ForumThread.id` values inside the direct posts-cache ownership helper because the helper compared `posts_thread.id != thread.id` directly.
- The focused RED failure showed booleans and floats could be accepted as retained parent/entry thread IDs when they compared equal to explicit integers, while strings, lists, and negative IDs could be misreported as ordinary `thread.posts` ownership mismatches. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, valid same-thread compatibility, valid cross-thread mismatch diagnostics, adjacent forum workflows, and full unit compatibility.
- This slice only validates retained thread IDs at the `ForumThread._posts` cache-owner boundary. It does not change forum thread parsing, post-list fetching, collection constructor semantics, public post lookup, lazy cache invalidation, forum post source/edit behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses the existing `_validate_thread_id(...)` semantics. That preserves zero as valid non-negative identity state and keeps invalid retained IDs on the same diagnostic path as malformed direct `ForumThread.id` constructor input.
