# PR Draft: Validate Forum Post Revisions Cache Retained ID State

## Summary

`ForumPost._revisions` cache ownership validation verifies that a cached `ForumPostRevisionCollection` and its entries belong to the receiving `ForumPost`, but the ownership helper compared retained `ForumPost.id` and `ForumThread.id` values directly. After local fixture, serialized, or rehydrated state has been mutated incorrectly, booleans and floats could satisfy Python equality against integer post/thread IDs, while strings, lists, or negative IDs were reported as generic revisions-cache ownership mismatches instead of deterministic retained ID corruption.

This change validates the receiving post ID, each cached parent/entry post ID, the receiving thread ID, and each cached parent/entry thread ID before comparing revisions-cache ownership. Malformed retained post IDs now raise `ValueError("id must be an integer")`, negative retained post IDs now raise `ValueError("id must be non-negative")`, malformed retained thread IDs now raise `ValueError("thread_id must be an integer")`, negative retained thread IDs now raise `ValueError("thread_id must be non-negative")`, valid different-post caches still raise `ValueError("post.revisions must belong to the post")`, valid same-post caches including zero-ID state remain accepted, and no forum fetch or live Wikidot behavior changes.

## Outcome

Direct `ForumPost(..., _revisions=...)` construction can no longer accept or misclassify cached revision collections whose retained parent or entry post/thread IDs are corrupted.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, moderation exports, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumPost` / `ForumPostRevisionCollection` records before exposing `ForumPost.revisions`.

## Current Evidence

Local rollout-backed drafts already established forum post revision caches as a practical boundary. [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [507-pr-validate-forum-post-revisions-cache.md](507-pr-validate-forum-post-revisions-cache.md), [593-pr-validate-forum-post-revision-collection-post-ownership.md](593-pr-validate-forum-post-revision-collection-post-ownership.md), and [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md) cover cached post revision reuse, direct cached revision-list skip behavior, optional `_revisions` cache shape, collection constructor ownership, and direct post revisions-cache ownership for valid comparable IDs. [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md) covers direct revision row IDs, and [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md) covers the analogous retained-ID gap for `ForumThread._posts`.

This slice is not a duplicate of those drafts. Issue 594 validates that the cached collection parent and cached revision entries point at the same logical post/thread/site as the receiving `ForumPost`, but it assumes the retained post and thread IDs are already valid integers. Issue 638 validates direct `PageRevision.id` and `ForumPostRevision.id` range semantics, not cached revision parent `ForumPost.id` or `ForumThread.id` state. Issue 665 validates retained `ForumThread.id` values at the `ForumThread._posts` boundary, not retained post/thread IDs at the `ForumPost._revisions` boundary.

## Related Issue / Non-Duplicate Analysis

Builds directly on [507-pr-validate-forum-post-revisions-cache.md](507-pr-validate-forum-post-revisions-cache.md), [593-pr-validate-forum-post-revision-collection-post-ownership.md](593-pr-validate-forum-post-revision-collection-post-ownership.md), [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), and [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate the receiving `ForumPost.id` and cached parent/entry `ForumPost.id` values before comparing revisions-cache ownership.
- Validate the receiving `ForumThread.id` and cached parent/entry `ForumThread.id` values before comparing revisions-cache ownership.
- Reject malformed retained post IDs such as `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained post IDs such as `-1` with `ValueError("id must be non-negative")`.
- Reject malformed retained thread IDs such as `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject negative retained thread IDs such as `-1` with `ValueError("thread_id must be non-negative")`.
- Preserve valid same-post cached revision collections, valid zero-ID same-post caches, valid different-post ownership diagnostics, malformed cache object diagnostics, malformed cache-entry diagnostics, lazy revision acquisition, cached duplicate revision reuse, forum post source/edit behavior, and adjacent forum workflows.

## Type Of Change

- Input validation
- Retained forum-post ID hardening
- Retained forum-thread ID hardening
- Forum post revisions-cache ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(..., _revisions=ForumPostRevisionCollection(parent_post, []))` must reject malformed retained cached parent `post.id` values such as `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")` before revisions-cache ownership comparison. |
| R2 | The same constructor must reject negative retained cached parent `post.id` values such as `-1` with `ValueError("id must be non-negative")` before revisions-cache ownership comparison. |
| R3 | `ForumPost(..., _revisions=ForumPostRevisionCollection(parent_post, []))` must reject malformed retained cached parent `post.thread.id` values such as `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before revisions-cache ownership comparison. |
| R4 | The same constructor must reject negative retained cached parent `post.thread.id` values such as `-1` with `ValueError("thread_id must be non-negative")` before revisions-cache ownership comparison. |
| R5 | `ForumPost(..., _revisions=ForumPostRevisionCollection(post, [revision]))` must reject malformed retained cached revision-entry `revision.post.id` and `revision.post.thread.id` values with the corresponding post-ID or thread-ID diagnostics before revisions-cache ownership comparison. |
| R6 | The same constructor must reject negative retained cached revision-entry `revision.post.id` and `revision.post.thread.id` values with the corresponding post-ID or thread-ID diagnostics before revisions-cache ownership comparison. |
| R7 | Valid same-post cached revision collections, valid zero-ID same-post caches, valid different-post ownership mismatches, malformed cache shape diagnostics, and adjacent forum workflows must remain green. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, forum-post module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed cached collection parent post IDs fail before ownership comparison. | `test_init_rejects_revisions_cache_with_malformed_retained_parent_post_ids` failed RED for five malformed values: booleans and `5001.0` were accepted, while `"5001"` and `[]` raised generic `post.revisions` ownership mismatch. The test passed GREEN after retained post ID validation. | Accepting booleans or floats, returning generic ownership mismatch for corrupted retained post IDs, coercing strings/lists, or storing the cache rejects this local completion claim. | `ForumPost._revisions` cache parent post state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Negative cached collection parent post IDs fail before ownership comparison. | `test_init_rejects_revisions_cache_with_negative_retained_parent_post_id` failed RED with generic ownership mismatch, then passed GREEN after retained post ID validation. | Treating negative post IDs as ordinary wrong-post ownership, accepting them, or coercing them rejects this local completion claim. | `ForumPost._revisions` cache parent post state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Malformed cached collection parent thread IDs fail before ownership comparison. | `test_init_rejects_revisions_cache_with_malformed_retained_parent_thread_ids` failed RED for five malformed values: booleans and `3001.0` were accepted, while `"3001"` and `[]` raised generic `post.revisions` ownership mismatch. The test passed GREEN after retained thread ID validation. | Accepting malformed parent thread IDs, relying on Python numeric equality, or returning generic ownership mismatch rejects this local completion claim. | `ForumPost._revisions` cache parent thread state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Negative cached collection parent thread IDs fail before ownership comparison. | `test_init_rejects_revisions_cache_with_negative_retained_parent_thread_id` failed RED with generic ownership mismatch, then passed GREEN after retained thread ID validation. | Treating negative thread IDs as ordinary wrong-post ownership, accepting them, or coercing them rejects this local completion claim. | `ForumPost._revisions` cache parent thread state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R5 | Malformed cached revision-entry post/thread IDs fail before ownership comparison. | `test_init_rejects_revisions_cache_entry_with_malformed_retained_post_ids` and `test_init_rejects_revisions_cache_entry_with_malformed_retained_thread_ids` failed RED for five malformed values each with the same accepted or generic-mismatch behavior, then passed GREEN after retained entry post/thread ID validation. | Accepting malformed entry IDs, relying on Python equality to prove ownership, coercing strings/lists, or storing the entry under `post.revisions` rejects this local completion claim. | `ForumPost._revisions` cache entry state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R6 | Negative cached revision-entry post/thread IDs fail before ownership comparison. | `test_init_rejects_revisions_cache_entry_with_negative_retained_post_id` and `test_init_rejects_revisions_cache_entry_with_negative_retained_thread_id` failed RED with generic ownership mismatch, then passed GREEN after retained entry post/thread ID validation. | Accepting negative entry IDs, coercing them, or classifying them as ordinary cross-post cache ownership rejects this local completion claim. | `ForumPost._revisions` cache entry state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R7 | Existing cache ownership behavior remains compatible. | Focused GREEN coverage passed 28 tests, `tests/unit/test_forum_post.py` passed 196 tests, adjacent forum/category/thread/post/revision/site coverage passed 951 tests, and full unit passed 3108 tests. | Regressing valid same-post caches, zero IDs, different-post diagnostics, malformed cache shape diagnostics, lazy revision acquisition, cached duplicate revision reuse, forum post source/edit behavior, or any unit test rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R8 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4d1bc7d fix(forum_post): validate revisions cache retained ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_valid_revisions_cache tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_revisions_cache_with_zero_retained_post_and_thread_ids tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_with_malformed_retained_parent_post_ids tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_with_negative_retained_parent_post_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_with_malformed_retained_parent_thread_ids tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_with_negative_retained_parent_thread_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_entry_with_malformed_retained_post_ids tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_entry_with_negative_retained_post_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_entry_with_malformed_retained_thread_ids tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_entry_with_negative_retained_thread_id tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_from_different_post tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_revisions_cache_entry_from_different_post -q` failed 24 retained parent/entry post/thread-ID cases before the fix; 4 valid-cache, zero-ID, and valid different-post ownership guards passed.
- GREEN: the same focused command passed 28 tests after validating target and cached post/thread IDs before revisions-cache ownership comparison.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 196 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 951 tests.
- `uv run pytest tests/unit -q` passed 3108 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPost(..., _revisions=ForumPostRevisionCollection(parent_post, []))` raises `ValueError("id must be an integer")` when the cached parent post's retained `id` is `True`, `False`, `"5001"`, `5001.0`, or `[]`.
- The same constructor raises `ValueError("id must be non-negative")` when the cached parent post's retained `id` is `-1`.
- The same constructor raises `ValueError("thread_id must be an integer")` when the cached parent post's retained `thread.id` is `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- The same constructor raises `ValueError("thread_id must be non-negative")` when the cached parent post's retained `thread.id` is `-1`.
- `ForumPost(..., _revisions=ForumPostRevisionCollection(post, [revision]))` raises the same malformed and negative retained-ID diagnostics when the cached revision entry's retained `revision.post.id` or `revision.post.thread.id` is corrupted.
- Valid same-post cached revision collections still initialize and return the retained cache through `post.revisions`.
- Valid same-post cached revision collections with retained post ID `0` and thread ID `0` remain accepted.
- Valid different-post cached collections and cached entries still raise `ValueError("post.revisions must belong to the post")`.
- Existing malformed `_revisions` object and malformed `_revisions` entry diagnostics remain unchanged.
- Existing forum category, thread, post, revision, and site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost._revisions` is a direct cache slot for browser-free edit-history reads, duplicate cached post-revision reuse, generated moderation ledgers, discussion migration audits, and local fixture reconstruction. Ownership validation already protects against another post's revision list being stored under the current post, but corrupted retained post/thread IDs should fail as corrupted identity state before Python equality can accept booleans/floats or generic ownership mismatch can hide strings/lists/negative IDs. Validating retained post and thread IDs before comparison keeps the existing ownership contract precise without changing network behavior or parser selectors.

## Local Evidence

- Existing local drafts covered forum post revision-list retry behavior, cached direct revision-list skips, duplicate post-revision request reduction, cached duplicate post-revision reuse, optional `_revisions` cache shape, collection constructor ownership, direct `_revisions` ownership for valid comparable IDs, direct revision ID range validation, and analogous retained-ID hardening for `ForumThread._posts`.
- None of those drafts covered malformed retained `ForumPost.id` or `ForumThread.id` values inside the direct revisions-cache ownership helper because the helper compared `revision_post.id != post.id` and `revision_thread.id != post_thread.id` directly.
- The focused RED failure showed booleans and floats could be accepted as retained parent/entry post or thread IDs when they compared equal to explicit integers, while strings, lists, and negative IDs could be misreported as ordinary `post.revisions` ownership mismatches. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, valid same-post compatibility, valid cross-post mismatch diagnostics, adjacent forum workflows, and full unit compatibility.
- This slice only validates retained post/thread IDs at the `ForumPost._revisions` cache-owner boundary. It does not change forum post parsing, revision-list fetching, collection constructor semantics, public revision lookup, lazy cache invalidation, forum post source/edit behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses the existing `_validate_post_id(...)` and `_validate_thread_id(...)` semantics. That preserves zero as valid non-negative identity state and keeps invalid retained IDs on the same diagnostic paths as malformed direct `ForumPost.id` and `ForumThread.id` constructor input.
