# PR Draft: Validate Forum Category Threads Cache Ownership

## Summary

`ForumCategory._threads` is the optional cached `ForumThreadCollection` behind the public `ForumCategory.threads` property and setter. Issue 505 validated the direct cache shape and non-thread entries, Issue 434 validated public setter shape, and Issue 590 validated `ForumThreadCollection` site ownership. One cache ownership gap remained: a caller could construct `ForumCategory(..., _threads=ForumThreadCollection(other_site, []))`, assign `category.threads = ForumThreadCollection(other_site, [])`, or mutate a valid same-site collection to contain a `ForumThread` retained from another category before passing it through the constructor or setter. The category then returned cached thread state that belonged to another site or category.

This change validates cached thread ownership during `ForumCategory.__post_init__` and during direct `category.threads = ...` assignment after the existing cache type and entry checks. Non-null cached collections now compare the collection parent site, each cached thread's retained site, and any retained thread category against the owning category by category ID and the same retained `Site` object. Mismatches raise `ValueError("category.threads must belong to the category")` before the malformed cache is stored. Valid same-category cached collections, empty no-parent `ForumThreadCollection()` values, `_threads=None`, existing malformed-cache diagnostics, lazy `ForumCategory.threads`, direct category thread-list acquisition, create-thread cache invalidation, reply-side cache synchronization, and adjacent forum workflows remain unchanged.

## Outcome

Directly constructed and directly assigned `ForumCategory` thread caches reject wrong-site or wrong-category thread collections before `category.threads` can expose cross-category cached state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum category inventories, generated discussion migration ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumCategory` objects.

## Current Evidence

Prior cache and ownership drafts establish the surrounding behavior. [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md) validates the optional `_threads` cache object shape and non-thread entries. [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md) validates public `category.threads = ...` assignment shape and preserves an existing cache on malformed assignment. [590-pr-validate-forum-thread-collection-site-ownership.md](590-pr-validate-forum-thread-collection-site-ownership.md) validates `ForumThreadCollection(site, threads=...)` site ownership at collection construction. [595-pr-validate-forum-thread-posts-cache-ownership.md](595-pr-validate-forum-thread-posts-cache-ownership.md) applies the same direct cache-slot ownership rule one level lower to `ForumThread._posts`. The remaining gap was `ForumCategory._threads` construction or assignment with a valid `ForumThreadCollection` object whose retained site or entries did not match the category receiving the cache.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 505. Issue 505 rejects malformed `_threads` values and collections containing non-`ForumThread` entries; it does not compare a cached collection's retained site or cached thread parent categories with the `ForumCategory` being constructed.

This is not a duplicate of Issue 434. Issue 434 rejects malformed direct setter assignments and non-thread entries while preserving the previous valid cache; it does not reject valid collections that belong to another site or category.

This is not a duplicate of Issue 590. Issue 590 validates `ForumThreadCollection.__init__` before a collection stores mixed-site thread entries. This slice covers the separate `ForumCategory` cache slot and setter: a valid collection built for another site can still be passed to a category, and a valid collection can be mutated after construction to contain another category's thread.

No upstream issue was filed from this local workspace.

## Changes

- Add cached thread ownership validation for direct `ForumCategory(...)` construction.
- Add the same ownership validation to the public `category.threads = ...` setter before `_threads` mutation.
- Reject cached `ForumThreadCollection` objects whose own `site` belongs to a different site.
- Reject cached thread entries whose retained `thread.site` belongs to a different site.
- Reject cached thread entries whose retained `thread.category`, when present, belongs to a different category or site.
- Preserve `_threads=None`, empty no-parent thread collections, valid same-category cached collections, existing malformed-cache diagnostics, lazy thread acquisition, direct thread-list acquisition, create-thread cache invalidation, reply-side cache synchronization, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Public cache setter behavior hardening
- Cached forum-category thread ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory(_threads=ForumThreadCollection(other_site, []))` must reject the different cached collection site with `ValueError("category.threads must belong to the category")` before storing cached state. |
| R2 | `ForumCategory(_threads=collection_mutated_with_thread_from_other_category)` must reject the different retained thread category with the same diagnostic before storing cached state. |
| R3 | `category.threads = ForumThreadCollection(other_site, [])` must reject the different cached collection site before replacing the existing cache. |
| R4 | `category.threads = collection_mutated_with_thread_from_other_category` must reject the different retained thread category before replacing the existing cache. |
| R5 | Valid same-category cached thread collections must remain accepted and `category.threads` must return the cached collection without triggering acquisition. |
| R6 | Existing malformed `_threads` and setter diagnostics from Issues 505 and 434 must remain unchanged. |
| R7 | Existing lazy category thread-list acquisition, direct acquisition, create-thread cache invalidation, reply-side category cache synchronization, and adjacent forum category/thread/post/revision workflows must remain unchanged. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached collection parent sites from another site fail at the constructor boundary. | `TestForumCategoryBasic.test_init_rejects_threads_cache_from_different_site` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumCategory.__post_init__` called the ownership preflight. | Accepting `ForumThreadCollection(other_site, [])`, storing the mismatched cache, or deferring the failure to `category.threads` rejects this local completion claim. | `ForumCategory._threads` cache parent state | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Valid cached collections that are mutated with another category's thread fail at the same constructor boundary. | `TestForumCategoryBasic.test_init_rejects_threads_cache_entry_from_different_category` failed RED with `DID NOT RAISE`, then passed GREEN after each cached thread's retained site and category were checked. | Accepting a same-site collection with a different-category thread entry, returning it through `category.threads`, or relying only on collection-constructor guards rejects this local completion claim. | `ForumCategory._threads` cache entry ownership | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Wrong-site direct setter assignments fail before replacing the previous cache. | `TestForumCategoryBasic.test_threads_setter_rejects_collection_from_different_site` failed RED with `DID NOT RAISE`, then passed GREEN after the setter reused the ownership preflight. | Replacing a valid cache with a wrong-site collection or clearing the previous cache on failure rejects this local completion claim. | `ForumCategory.threads` setter parent state | `tests/unit/test_forum_category.py` |
| R4 | Direct setter assignments with another category's thread fail before replacing the previous cache. | `TestForumCategoryBasic.test_threads_setter_rejects_collection_entry_from_different_category` failed RED with `DID NOT RAISE`, then passed GREEN after each cached thread's retained category was checked. | Replacing a valid cache with a different-category thread entry or clearing the previous cache on failure rejects this local completion claim. | `ForumCategory.threads` setter entry ownership | `tests/unit/test_forum_category.py` |
| R5 | Valid same-category caches remain a cache hit. | `TestForumCategoryBasic.test_init_accepts_valid_threads_cache` passed in the focused cache group and asserts `category.threads is threads`; `test_threads_setter` remains green. | Triggering thread acquisition, replacing the cached object unexpectedly, or rejecting a valid same-category collection rejects this local completion claim. | `ForumCategory.threads` cache access | `tests/unit/test_forum_category.py` |
| R6 | Existing malformed-cache and malformed-assignment diagnostics remain stable. | The focused cache group also passed malformed constructor and setter value/entry tests from Issues 505 and 434. | Changing existing diagnostics, accepting non-collection values, or accepting non-thread cache entries rejects this local completion claim. | `ForumCategory` cache shape validation | `tests/unit/test_forum_category.py` |
| R7 | Adjacent forum workflows remain green. | `tests/unit/test_forum_category.py` passed 102 tests, adjacent forum category/thread/post/revision coverage passed 542 tests, and full unit coverage passed 2709 tests. | Regressing lazy `ForumCategory.threads`, direct category thread-list acquisition, reload, create-thread cache invalidation, reply-side category cache synchronization, forum thread/post/revision behavior, or parser-created category behavior rejects this local completion claim. | Forum workflows | `tests/unit` |
| R8 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `ForumCategory` and `ForumThread` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page/forum content from real sites, forum post source text from real sites, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `091faf8 fix(forum_category): validate threads cache ownership`.

- RED cached collection site ownership: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_threads_cache_from_different_site -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused parent-site ownership regression: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_threads_cache_from_different_site tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_accepts_valid_threads_cache -q` passed 2 tests after the collection-site branch fix.
- RED cached thread entry category ownership: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_threads_cache_entry_from_different_category -q` failed before the entry branch fix with `DID NOT RAISE`.
- GREEN focused constructor cache coverage: constructor cache ownership and shape checks passed 12 tests.
- RED setter ownership: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_collection_from_different_site tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_collection_entry_from_different_category -q` failed before the setter fix with `DID NOT RAISE`.
- GREEN focused cache and setter coverage: constructor cache ownership, setter ownership, existing shape diagnostics, and valid setter checks passed 24 tests.
- Constructor/property coverage: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic -q` passed 50 tests.
- Forum category module coverage: `uv run pytest tests/unit/test_forum_category.py -q` passed 102 tests.
- Adjacent forum category/thread/post/revision tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 542 tests.
- `uv run pytest tests/unit -q` passed 2709 tests.
- `uv run ruff format` left 87 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategory(_threads=ForumThreadCollection(other_site, []))` raises `ValueError("category.threads must belong to the category")` before storing cached state.
- `ForumCategory(_threads=same_site_collection_mutated_with_other_category_thread)` raises the same diagnostic before storing cached state.
- `category.threads = ForumThreadCollection(other_site, [])` raises the same diagnostic and leaves the previous cache unchanged.
- `category.threads = same_site_collection_mutated_with_other_category_thread` raises the same diagnostic and leaves the previous cache unchanged.
- `ForumCategory(_threads=ForumThreadCollection(same_site, [same_category_thread]))` remains valid and `category.threads` returns that cached object without a lookup.
- Existing `_threads=None`, malformed `_threads` object rejection, non-thread cache-entry rejection, direct setter malformed object rejection, direct setter non-thread entry rejection, lazy thread acquisition, direct category thread-list acquisition, create-thread cache invalidation, reply-side category cache synchronization, and adjacent forum category/thread/post/revision behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategory._threads` is a direct cache slot and public setter for browser-free category thread inventories. If the cached collection or one of its retained thread entries belongs to another site or category, callers can read coherent-looking but cross-category thread state through `category.threads`. Constructor-time and setter-time ownership validation keep direct fixtures, rehydrated records, and generated caches from silently storing another category's thread list under the current category.

## Local Evidence, Not For Upstream Paste

- The first RED failure showed `ForumCategory` could accept an empty `ForumThreadCollection` whose collection parent site was another site.
- The second RED failure showed a same-site collection mutated after construction with another category's valid thread could still be stored as `ForumCategory._threads`.
- The setter RED failures showed direct assignment could replace an existing valid cache with wrong-site or wrong-category thread collections.
- Existing local drafts covered category thread-list acquisition, parser diagnostics, response diagnostics, optional `_threads` cache shape, setter shape, collection constructor ownership, retained thread/site validation, and lower-level `ForumThread._posts` cache ownership, but did not validate that cached thread collections stored on a `ForumCategory` belong to that category.
- This slice only validates cached thread ownership during `ForumCategory` construction and direct assignment. It does not change category-list parsing, thread-list parsing, collection constructor semantics, lazy cache invalidation, create-thread request behavior, reply behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page/forum source text from real sites, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally requires the same retained `Site` object and, when a cached thread has a non-null retained category, the same category ID on that retained site. This allows empty no-parent thread collections and same-site direct thread records without category evidence, while rejecting wrong-site collections, wrong-site threads, and explicit different-category thread entries.
