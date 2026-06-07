# PR Draft: Validate ForumCategory Threads Cache

## Summary

`ForumCategory._threads` is the optional cached `ForumThreadCollection` behind the public `ForumCategory.threads` property. It is used by lazy category thread-list reads, direct category thread-list acquisition cache population, create-thread cache invalidation, reply-side category cache synchronization, generated forum migration ledgers, local fixtures, and rehydrated category records. Earlier local slices validated category thread-list fetching, direct acquisition caching, `ForumThreadCollection` constructor inputs, collection parent sites, `ForumCategory.threads` assignment, individual `ForumCategory` scalar fields, and the direct `ForumCategory.site` field, but direct `ForumCategory(..., _threads=...)` construction still accepted malformed cached values such as booleans, strings, raw lists, dictionaries, arbitrary objects, and post-construction mutated collections.

This change validates the direct constructor's optional thread cache during `ForumCategory.__post_init__`. `_threads=None` remains valid for categories that have not acquired threads yet, real `ForumThreadCollection` objects remain valid, and malformed non-null values now raise stable `ValueError` diagnostics before they can make `ForumCategory.threads` return malformed local cache state.

## Outcome

Directly constructed `ForumCategory` objects now fail early when optional cached thread state is malformed, while preserving lazy category thread-list acquisition for `_threads=None` and preserving valid preloaded `ForumThreadCollection` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum inventories, generated discussion migration ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumCategory` objects.

## Current Evidence

Forum-category and category-thread drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), and [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md) establish category thread-list reads, cache reuse, direct acquisition caching, and cache invalidation as active operational surfaces.

Constructor and state-integrity drafts [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), and [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md) establish the local pattern for validating direct record, collection, cache-assignment, and parent-state boundaries instead of relying only on parser-created objects.

Adjacent constructor-cache drafts [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md), [492-pr-validate-page-constructor-votes-cache.md](492-pr-validate-page-constructor-votes-cache.md), [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md), and [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md) establish the direct optional-cache validation pattern that accepts `None`, accepts the annotated cache object shape, and rejects malformed cache objects or mutated entries without adding ownership checks.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 434. Issue 434 validates assignment through the public `category.threads = ...` setter and preserves an existing valid cache on failed assignment. This slice validates direct dataclass construction before a malformed `_threads` value can be stored.

This is not a duplicate of Issue 227. Issue 227 populates `category._threads` after successful direct `ForumThreadCollection.acquire_all_in_category(category)` reads. This slice validates direct constructor input before cached state exists.

This is not a duplicate of Issue 136. Issue 136 skips fetching when `category._threads` is already populated. This slice ensures such prepopulated constructor cache values have the expected object and entry shape.

This is not a duplicate of Issue 423. Issue 423 validates the `ForumThreadCollection(site, threads=...)` constructor's `threads` container and entries. This slice validates whether `ForumCategory(_threads=...)` contains the expected cache object at all.

This is not a duplicate of Issue 475. Issue 475 validates the optional explicit parent site stored on a `ForumThreadCollection`. This slice validates the separate cache slot stored on a `ForumCategory` record.

This follows the Page constructor-cache pattern from Issues 490 through 493 and the forum-thread post cache pattern from Issue 504, but applies it to the forum-category thread-list cache.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached threads validation for direct `ForumCategory(...)` construction.
- Preserve `_threads=None` for categories that should lazily acquire threads.
- Preserve valid `ForumThreadCollection` objects without coercion.
- Reject booleans, strings, raw lists, dictionaries, arbitrary non-collection objects, and collections mutated with malformed entries using stable `ValueError` diagnostics.
- Add constructor tests for malformed direct `_threads` values, valid optional thread cache state, and malformed cached collection entries.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached forum-thread state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory(_threads=...)` must accept `None` and real `ForumThreadCollection` objects. |
| R2 | `ForumCategory(_threads=...)` must reject non-`None` non-`ForumThreadCollection` values with `ValueError("category.threads must be ForumThreadCollection or None")`. |
| R3 | `ForumCategory(_threads=...)` must reject `ForumThreadCollection` objects containing non-`ForumThread` entries with `ValueError("category.threads list entries must be ForumThread")`. |
| R4 | Valid category construction, lazy `ForumCategory.threads`, direct `ForumThreadCollection.acquire_all_in_category(...)`, successful direct acquisition cache population, create-thread cache invalidation, reply-side category cache synchronization, `ForumThreadCollection` construction validation, parser-created categories, and forum category/thread/post/revision workflows must remain unchanged. |
| R5 | This slice must not change category thread-list acquisition, thread-detail acquisition, parser selectors, response diagnostics, thread ordering, collection ownership inference, cache invalidation semantics, live request behavior, or unrelated constructor fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid `ForumThreadCollection` cached thread values remain accepted. | `TestForumCategoryBasic.test_init_accepts_valid_threads_cache` passed after validation was added, preserving a valid cached collection and returning it through `category.threads`. Existing constructors continue to use `_threads=None`. | Rejecting missing cached threads, triggering thread-list lookup during construction, or coercing valid collection objects rejects this local completion claim. | `ForumCategory` constructor cached-thread state | `tests/unit/test_forum_category.py` |
| R2 | Malformed optional cached thread values fail at the constructor boundary. | `TestForumCategoryBasic.test_init_rejects_malformed_threads_cache` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, raw lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `ForumCategory` constructor cached-thread state | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Mutated thread collections with malformed entries fail at the constructor boundary. | `TestForumCategoryBasic.test_init_rejects_malformed_threads_cache_entries` failed RED for 4 malformed entries because a mutated `ForumThreadCollection` was accepted, then passed GREEN after entry validation was added. | Trusting a mutated collection, storing malformed entries, or deferring failure to lazy `ForumCategory.threads`, direct acquisition cache reuse, create/reply cache handling, or generated ledgers rejects this local completion claim. | `ForumCategory` constructor cached-thread entries | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R4 | Existing category/thread workflows remain green. | `tests/unit/test_forum_category.py` passed 90 tests, adjacent forum tests passed 471 tests, and the full unit suite passed 2246 tests. | Regressing lazy category thread acquisition, direct category thread-list acquisition, successful direct acquisition cache population, collection construction validation, create-thread cache invalidation, reply-side category cache synchronization, parser-created categories, direct thread reads, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit` |
| R5 | Broader thread-list semantics remain outside scope. | Existing acquisition, parser, cache invalidation, collection, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing request construction, parser conversion, response diagnostics, thread ordering, collection parent inference, thread-detail lookup, reply behavior, cache invalidation, or live request behavior rejects this local completion claim. | ForumCategory constructor scope | `src/wikidot/module/forum_category.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `fbcf440 fix(forum_category): validate threads cache`.

- RED type guard: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_malformed_threads_cache -q` failed 5 tests before the fix; every malformed `_threads` value reported `DID NOT RAISE`.
- GREEN type guard: the same focused command passed 5 tests after optional cache type validation was added.
- RED entry guard: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_malformed_threads_cache_entries -q` failed 4 tests before the entry guard because mutated `ForumThreadCollection` entries were accepted.
- GREEN entry guard: the same focused command passed 4 tests after cached collection entry validation was added.
- Cache trio: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_malformed_threads_cache tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_accepts_valid_threads_cache tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_malformed_threads_cache_entries -q` passed 10 tests.
- Constructor/property block: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic -q` passed 46 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 90 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 471 tests.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2246 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategory(_threads=None)` remains valid and lazy category thread-list acquisition remains available.
- `ForumCategory(_threads=ForumThreadCollection(...))` remains valid and `category.threads` returns the cached object without a lookup.
- `ForumCategory(_threads=True)`, `ForumCategory(_threads="3001")`, `ForumCategory(_threads=[])`, `ForumCategory(_threads={"threads": []})`, and `ForumCategory(_threads=object())` raise `ValueError("category.threads must be ForumThreadCollection or None")` when every other constructor field is valid.
- `ForumCategory(_threads=collection_mutated_with_non_thread)` raises `ValueError("category.threads list entries must be ForumThread")` when every other constructor field is valid.
- Existing parser-created categories, direct category fixtures, category thread-list reads, direct thread-detail reads, lazy `ForumCategory.threads`, direct `ForumThreadCollection` acquisition, direct acquisition cache population, create-thread cache invalidation, reply-side category cache synchronization, `ForumThreadCollection` construction validation, forum post behavior, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not validate collection ownership, thread parser contents, live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with ownership validation between `category` and `threads.site`. Mitigation: the validator checks object shape and entries only, matching adjacent Page and forum-thread cache validators; ownership matching remains outside scope.
- Risk: Valid cached thread collections could accidentally trigger network fetches during construction. Mitigation: the valid-cache test asserts `category.threads is threads`, and the constructor validator does not call acquisition helpers.
