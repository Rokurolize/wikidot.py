# PR Draft: Validate Forum Category Threads Cache Retained Category ID State

## Summary

`ForumCategory._threads` validates that a cached `ForumThreadCollection` belongs to the receiving category, but the cache ownership helper compared retained `ForumCategory.id` values directly. After local fixture, serialized, or rehydrated state has been mutated incorrectly, booleans and floats can satisfy Python equality against integer category IDs, while strings, lists, and negative IDs are reported as generic cache ownership mismatches instead of corrupted retained category-ID state.

This change validates both the receiving `ForumCategory.id` and each cached thread entry's retained `thread.category.id` before comparing cache ownership. Malformed retained category IDs now raise `ValueError("id must be an integer")`, negative retained category IDs now raise `ValueError("id must be non-negative")`, valid zero-ID same-category caches remain accepted, valid different-category caches still raise `ValueError("category.threads must belong to the category")`, malformed cache shape diagnostics remain unchanged, and no forum fetch or live Wikidot behavior changes.

## Outcome

Directly constructed and directly assigned `ForumCategory` thread caches can no longer accept or misclassify corrupted retained category IDs before exposing cached thread state through `category.threads`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum category inventories, generated discussion migration ledgers, moderation exports, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumCategory` objects.

## Current Evidence

Local rollout-backed drafts already established forum category thread caches as a practical boundary. [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md), [590-pr-validate-forum-thread-collection-site-ownership.md](590-pr-validate-forum-thread-collection-site-ownership.md), and [596-pr-validate-forum-category-threads-cache-ownership.md](596-pr-validate-forum-category-threads-cache-ownership.md) cover cached category thread reads, direct acquisition caching, reply-side cache synchronization, setter shape validation, optional `_threads` cache shape, collection site ownership, and cache ownership for valid comparable IDs. [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md) and [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md) cover direct `ForumCategory.id` constructor state. [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), and [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md) cover analogous retained-ID hardening in adjacent forum cache and collection boundaries.

This slice is not a duplicate of those drafts. Issue 596 validates that a `ForumCategory._threads` cache belongs to the receiving category when retained category IDs are valid comparable integers, but it does not reject corrupted retained `ForumCategory.id` values before comparison. Issues 452 and 644 validate direct construction of `ForumCategory(id=...)`; they cannot cover a category object whose ID was corrupted after construction and then reused as a cache owner or cached thread entry. Issues 665, 666, and 667 cover forum thread/post/revision owner IDs, not category thread-cache owner IDs.

## Related Issue / Non-Duplicate Analysis

Builds directly on [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md), [596-pr-validate-forum-category-threads-cache-ownership.md](596-pr-validate-forum-category-threads-cache-ownership.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), and [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate the receiving `ForumCategory.id` before comparing direct `category.threads = ...` cache ownership.
- Validate each cached thread entry's retained `thread.category.id` before comparing constructor and setter cache ownership.
- Reject malformed retained category IDs such as `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained category IDs such as `-1` with `ValueError("id must be non-negative")`.
- Preserve valid same-category caches, valid zero-ID caches, valid different-category ownership diagnostics, malformed cache shape diagnostics, lazy thread acquisition, direct category thread acquisition, create-thread cache invalidation, reply-side category cache synchronization, and adjacent forum workflows.

## Type Of Change

- Input validation
- Retained forum-category ID hardening
- Forum category thread-cache ownership integrity
- Public dataclass constructor behavior hardening
- Public cache setter behavior hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory(..., _threads=threads)` must reject malformed retained `thread.category.id` values such as `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")` before cache ownership comparison. |
| R2 | The same constructor must reject negative retained `thread.category.id` values such as `-1` with `ValueError("id must be non-negative")` before cache ownership comparison. |
| R3 | `category.threads = threads` must reject malformed retained receiving `category.id` values with `ValueError("id must be an integer")` before replacing the existing cache. |
| R4 | The same setter must reject negative retained receiving `category.id` values with `ValueError("id must be non-negative")` before replacing the existing cache. |
| R5 | `category.threads = threads` must reject malformed and negative retained cached entry `thread.category.id` values with the same retained-ID diagnostics before replacing the existing cache. |
| R6 | Valid same-category caches, valid zero-ID caches, valid different-category ownership mismatches, malformed cache shape diagnostics, lazy thread acquisition, and adjacent forum workflows must remain green. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, forum-category module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed cached entry category IDs fail before constructor cache ownership comparison. | `test_init_rejects_threads_cache_entry_with_malformed_retained_category_ids` failed RED for five malformed values: booleans and `1001.0` were accepted, while `"1001"` and `[]` raised generic cache ownership mismatch. The test passed GREEN after retained entry category ID validation. | Accepting booleans or floats, returning generic ownership mismatch for corrupted retained entry category IDs, coercing strings/lists, or storing the cache rejects this local completion claim. | `ForumCategory._threads` cached entry category state | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Negative cached entry category IDs fail before constructor cache ownership comparison. | `test_init_rejects_threads_cache_entry_with_negative_retained_category_id` failed RED with generic ownership mismatch, then passed GREEN after retained entry category ID validation. | Treating negative category IDs as ordinary wrong-category ownership, accepting them, or coercing them rejects this local completion claim. | `ForumCategory._threads` cached entry category state | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Malformed retained receiving category IDs fail before direct setter replacement. | `test_threads_setter_rejects_malformed_retained_parent_category_ids` failed RED for five malformed values with accepted or generic-mismatch behavior, then passed GREEN after validating the receiving category ID before ownership comparison. | Replacing a valid cache, accepting bools/floats, returning generic ownership mismatch for strings/lists, or coercing malformed parent IDs rejects this local completion claim. | `ForumCategory.threads` setter parent state | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R4 | Negative retained receiving category IDs fail before direct setter replacement. | `test_threads_setter_rejects_negative_retained_parent_category_id` failed RED with generic ownership mismatch, then passed GREEN after retained parent category ID validation. | Replacing a valid cache, accepting negative parent category IDs, coercing them, or classifying them as ordinary ownership mismatch rejects this local completion claim. | `ForumCategory.threads` setter parent state | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R5 | Malformed and negative retained cached entry category IDs fail before direct setter replacement. | `test_threads_setter_rejects_entry_with_malformed_retained_category_ids` and `test_threads_setter_rejects_entry_with_negative_retained_category_id` failed RED with accepted or generic-mismatch behavior, then passed GREEN after retained entry category ID validation. | Replacing a valid cache with corrupted retained entry IDs, relying on Python numeric equality, coercing values, or returning generic mismatch rejects this local completion claim. | `ForumCategory.threads` setter entry state | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R6 | Existing compatible behavior remains compatible. | `test_init_accepts_threads_cache_with_zero_retained_category_ids` passed RED and GREEN. Focused GREEN coverage passed 19 tests, `tests/unit/test_forum_category.py` passed 130 tests, adjacent forum/site coverage passed 1007 tests, and full unit passed 3164 tests. | Regressing zero-ID compatibility, valid same-category caches, valid different-category diagnostics, malformed cache shape diagnostics, lazy thread acquisition, create-thread cache invalidation, reply-side cache synchronization, adjacent forum behavior, or any unit test rejects this local completion claim. | Forum category thread cache and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c0bb353 fix(forum_category): validate threads cache owner ids`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_accepts_threads_cache_with_zero_retained_category_ids tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_threads_cache_entry_with_malformed_retained_category_ids tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_threads_cache_entry_with_negative_retained_category_id tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_malformed_retained_parent_category_ids tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_negative_retained_parent_category_id tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_entry_with_malformed_retained_category_ids tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_entry_with_negative_retained_category_id -q` failed 18 retained parent/entry category-ID cases before the fix; the zero-ID compatibility guard passed.
- GREEN: the same focused command passed 19 tests after validating receiving and cached entry retained category IDs before cache ownership comparison.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 130 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1007 tests.
- `uv run pytest tests/unit -q` passed 3164 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategory(..., _threads=ForumThreadCollection(site, [thread]))` raises `ValueError("id must be an integer")` when the cached thread's retained `thread.category.id` is `True`, `False`, `"1001"`, `1001.0`, or `[]`.
- The same constructor raises `ValueError("id must be non-negative")` when the cached thread's retained `thread.category.id` is `-1`.
- `category.threads = threads` raises `ValueError("id must be an integer")` and leaves the previous cache unchanged when the receiving category's retained `id` is `True`, `False`, `"1001"`, `1001.0`, or `[]`.
- `category.threads = threads` raises `ValueError("id must be non-negative")` and leaves the previous cache unchanged when the receiving category's retained `id` is `-1`.
- `category.threads = threads` raises the same malformed and negative retained-ID diagnostics and leaves the previous cache unchanged when a cached thread entry's retained `thread.category.id` is corrupted.
- Valid same-category caches still initialize and assign.
- Valid same-category caches with retained category ID `0` remain accepted.
- Valid different-category caches still raise `ValueError("category.threads must belong to the category")`.
- Existing malformed `_threads` object rejection, non-thread cache-entry rejection, direct setter malformed object rejection, direct setter non-thread entry rejection, lazy thread acquisition, direct category thread-list acquisition, create-thread cache invalidation, reply-side category cache synchronization, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategory._threads` is a direct cache slot and public setter for browser-free category thread inventories, generated moderation ledgers, migration audits, and local fixture reconstruction. Ownership validation already protects against one category's threads being stored under another category, but corrupted retained category IDs should fail as corrupted identity state before Python equality can accept booleans/floats or generic ownership mismatch can hide strings/lists/negative IDs. Validating retained category IDs before comparison keeps the existing cache ownership contract precise without changing network behavior or parser selectors.

## Local Evidence

- Existing local drafts covered category thread-list fetches, cached direct category thread acquisition, reply-side category cache synchronization, setter shape validation, optional `_threads` cache shape validation, `ForumThreadCollection` site ownership, and `ForumCategory._threads` ownership for valid comparable IDs.
- None of those drafts covered malformed retained `ForumCategory.id` values inside `ForumCategory._threads` cache ownership because the helper compared `thread_category.id != category.id` directly.
- The focused RED failure showed booleans and floats could be accepted as retained parent or entry category IDs when they compared equal to explicit integers, while strings, lists, and negative IDs could be misreported as ordinary cache ownership mismatches.
- This slice only validates retained category IDs at the `ForumCategory._threads` cache ownership boundary. It does not change forum category parsing, thread-list fetching, direct cache shape semantics, lazy cache invalidation, create-thread request behavior, reply behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses the existing `_validate_forum_category_id(...)` semantics. That preserves zero as valid non-negative identity state and keeps invalid retained IDs on the same diagnostic paths as malformed direct `ForumCategory.id` constructor input.
