# PR Draft: Validate Forum Category Threads Assignments

## Summary

`ForumCategory.threads` is a public property that lazily acquires and caches a category's `ForumThreadCollection`. The setter documented `value` as `ForumThreadCollection`, but it accepted any object. A caller could assign `category.threads = None`, `category.threads = True`, `category.threads = "3001"`, `category.threads = {"id": 3001}`, or `category.threads = []`, causing the public property to store malformed local category-thread cache state. A caller could also mutate an otherwise valid `ForumThreadCollection` after construction and then assign the collection with non-`ForumThread` entries.

This change validates direct `ForumCategory.threads` assignments. Invalid non-collection assignments now raise `ValueError("category.threads must be ForumThreadCollection")`, and mutated collection entries now raise `ValueError("category.threads list entries must be ForumThread")`, before mutating `_threads`. Existing category thread acquisition, direct thread acquisition, cached helper reuse, reload behavior, create-thread cache invalidation, forum thread collection initialization, and adjacent forum post/revision workflows remain unchanged.

## Outcome

Manually constructed, fixture-created, duplicate-reused, or ledger-rehydrated `ForumCategory` objects can no longer silently corrupt their cached category thread list through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free category thread listings, forum thread inventories, moderation review tooling, migration scripts, translation audits, local fixtures, or external ledgers that construct `ForumCategory` objects and seed their thread caches directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread acquisition and cached thread lists as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), and [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md) establish thread listing, cached category-thread reuse, direct thread acquisition, parser diagnostics, category cache synchronization, ID validation, and collection initialization as active operational boundaries.

Those prior slices are not duplicates. Issues034, 107, 110, 136, 158, 169, 214, 227, 291, 292, and 326 improved category thread list acquisition, cached helper reuse, formatting preservation, parser diagnostics, and response diagnostics. Issue268 synchronizes category cache updates after forum replies, Issue379 validates thread lookup IDs, Issue407 rejects boolean create-thread IDs, Issue423 validates `ForumThreadCollection(...)` construction, and Issue424 validates `ForumCategoryCollection(...)` construction. None of them validates direct public `ForumCategory.threads = ...` assignment before category-thread cache replacement, and constructor validation alone cannot protect a collection that is mutated after construction.

## Related Issue

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), and [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `ForumCategory.threads` value validator.
- Reject non-`ForumThreadCollection` assignments with `ValueError("category.threads must be ForumThreadCollection")`.
- Reject mutated `ForumThreadCollection` objects that contain non-`ForumThread` entries with `ValueError("category.threads list entries must be ForumThread")`.
- Validate before assigning `_threads`, so invalid assignments preserve any previously cached valid category thread collection.
- Preserve valid `ForumThreadCollection` assignments.
- Preserve existing category thread acquisition, direct thread acquisition, reload behavior, create-thread cache invalidation, and adjacent forum post/revision workflows.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local category thread cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `category.threads = None`, `category.threads = True`, `category.threads = "3001"`, `category.threads = {"id": 3001}`, and `category.threads = []` must raise `ValueError("category.threads must be ForumThreadCollection")` before mutating `_threads`. |
| R2 | Assigning a mutated `ForumThreadCollection` containing `None`, `True`, `"3001"`, or `{"id": 3001}` must raise `ValueError("category.threads list entries must be ForumThread")` before mutating `_threads`. |
| R3 | Invalid assignments after already-cached valid category threads must preserve the previous valid collection. |
| R4 | Valid `ForumThreadCollection` assignments must remain allowed. |
| R5 | Existing category thread acquisition, direct category-thread cache population, reload behavior, create-thread cache invalidation, forum thread workflows, forum post workflows, and forum post revision workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent forum tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed non-collection assignments fail before local category-thread cache mutation. | `TestForumCategoryBasic.test_threads_setter_rejects_invalid_collections` failed RED for 5 malformed assignments because the setter did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, strings, dictionaries, raw lists, arbitrary objects, or deferring failure to later thread consumers rejects this local completion claim. | Direct category thread cache setter | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Mutated `ForumThreadCollection` objects with malformed entries fail before local category-thread cache mutation. | `TestForumCategoryBasic.test_threads_setter_rejects_invalid_collection_entries` failed RED for 4 malformed entries because the setter did not raise, then passed GREEN after entry validation was added. | Trusting a post-construction mutated collection, coercing entries, or only validating the collection constructor rejects this local completion claim. | Direct category thread cache setter | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Invalid assignments preserve the previous valid cached category thread collection. | The focused GREEN tests assert the cached thread with ID `3001` is still present after every rejected assignment. | Mutating `_threads` before raising, clearing cached threads, or triggering lazy lookup to recover the value rejects this local completion claim. | Local category thread cache | `tests/unit/test_forum_category.py` |
| R4 | Valid `ForumThreadCollection` assignments remain valid. | `TestForumCategoryBasic.test_threads_setter` assigns a valid collection and asserts it is stored unchanged. | Rejecting valid collections, copying unexpectedly, accepting raw lists, or changing direct fixture setup behavior rejects this local completion claim. | ForumCategory fixtures and cache setup | `tests/unit/test_forum_category.py` |
| R5 | Existing adjacent forum workflows remain green. | Focused setter/acquisition/cache checks passed 15 tests, forum category/thread/post/revision tests passed 316 tests, and full unit tests passed 1641 tests. | Regressing category thread acquisition, direct category-thread cache population, reload behavior, create-thread cache invalidation, forum thread reads, forum post reads, forum post revision reads, or lazy revision HTML/source behavior rejects this local completion claim. | Forum category, thread, post, and revision workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, source text from real sites, forum content, thread titles, post bodies, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `eae62b0 fix(forum_category): validate threads assignments`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_invalid_collections tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_invalid_collection_entries -q` failed 9 tests before the fix; every malformed assignment reported `DID NOT RAISE`.
- GREEN: the same focused command passed 9 tests after adding setter validation.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left 2 files unchanged.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_invalid_collections tests/unit/test_forum_category.py::TestForumCategoryBasic::test_threads_setter_rejects_invalid_collection_entries tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_success tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_success_invalidates_cached_threads tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_populates_category_threads_cache -q` passed 15 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 316 tests.
- `uv run pytest tests/unit -q` passed 1641 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `category.threads = None`, `category.threads = True`, `category.threads = "3001"`, `category.threads = {"id": 3001}`, and `category.threads = []` raise `ValueError("category.threads must be ForumThreadCollection")` without changing an existing valid cached thread collection.
- Assigning a mutated `ForumThreadCollection` containing `None`, `True`, `"3001"`, or `{"id": 3001}` raises `ValueError("category.threads list entries must be ForumThread")` without changing an existing valid cached thread collection.
- `category.threads = ForumThreadCollection(site, [thread])` remains valid and stores the same collection.
- Existing category thread acquisition, direct category-thread cache population, reload behavior, create-thread cache invalidation, forum thread workflows, forum post workflows, and forum post revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategory.threads` is shared by lazy category thread reads, direct thread acquisition cache population, create-thread cache invalidation, category inventory scripts, moderation review tooling, and tests that seed category thread state directly. Direct assignment is useful for caller-created category objects and data rehydrated from external ledgers, but malformed thread cache objects should fail at the property boundary instead of silently poisoning later forum thread consumers.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used category thread listings, cached thread-list reuse, direct thread acquisition cache population, and tests that seed category thread caches directly.
- Existing local drafts covered category thread list acquisition, retry/fallback behavior, cached helper reuse, parser diagnostics, response diagnostics, reply/create-thread cache synchronization, `ForumThreadCollection` initialization validation, `ForumCategoryCollection` initialization validation, thread lookup ID validation, and boolean create-thread ID rejection, but did not cover direct `ForumCategory.threads = ...` mutation.
- The focused RED failures showed invalid direct assignments and mutated collection entries were accepted by the property setter. The GREEN regressions cover missing, boolean, string, dictionary, and raw-list values and assert the previous valid thread collection survives.
- This slice only validates direct category thread assignment shape. It does not change category thread acquisition, forum thread acquisition, create-thread behavior, forum post/revision behavior, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, forum content, thread titles, post bodies, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed category thread cache objects instead of coercing values. Callers that load category thread lists from files, generated structures, JSON, YAML, CLI flags, spreadsheets, databases, or ledgers should normalize them to `ForumThreadCollection` with only `ForumThread` entries before assigning to `ForumCategory.threads`.
