# PR Draft: Validate ForumThread Posts Cache

## Summary

`ForumThread._posts` is the optional cached `ForumPostCollection` behind the public `ForumThread.posts` property. It is used by lazy post-list reads, direct post-list acquisition cache population, duplicate thread-post cache reuse, reply cache invalidation, generated forum migration ledgers, local fixtures, and rehydrated forum-thread records. Earlier local slices validated forum post-list fetching, direct acquisition caching, `ForumPostCollection` constructor inputs, collection parent threads, loaded collection entries before source acquisition, individual `ForumPost.thread`, and direct `ForumThread` identity/text/count/creator/time/category/site fields, but direct `ForumThread(..., _posts=...)` construction still accepted malformed cached values such as booleans, strings, raw lists, dictionaries, arbitrary objects, and post-construction mutated collections.

This change validates the direct constructor's optional posts cache during `ForumThread.__post_init__`. `_posts=None` remains valid for threads that have not acquired posts yet, real `ForumPostCollection` objects remain valid, and malformed non-null values now raise stable `ValueError` diagnostics before they can make `ForumThread.posts` return malformed local cache state.

## Outcome

Directly constructed `ForumThread` objects now fail early when optional cached post state is malformed, while preserving lazy post acquisition for `_posts=None` and preserving valid preloaded `ForumPostCollection` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum inventories, generated discussion migration ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumThread` objects.

## Current Evidence

Forum-thread and post-list drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), and [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md) establish thread post-list reads, cache reuse, direct acquisition caching, and cache invalidation as active operational surfaces.

Constructor and state-integrity drafts [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), and [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md) establish the local pattern for validating direct record and collection state instead of relying only on parser-created objects.

Adjacent page constructor-cache drafts [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md), [492-pr-validate-page-constructor-votes-cache.md](492-pr-validate-page-constructor-votes-cache.md), and [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md) establish the direct optional-cache validation pattern that accepts `None`, accepts the annotated cache object shape, and rejects malformed cache objects or mutated entries without adding ownership checks.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 228. Issue 228 populates `thread._posts` after successful direct `ForumPostCollection.acquire_all_in_thread(s)` reads. This slice validates direct dataclass construction before a malformed cache value can be stored.

This is not a duplicate of Issue 422. Issue 422 validates the `ForumPostCollection(thread, posts=...)` constructor's `posts` container and entries. This slice validates whether `ForumThread(_posts=...)` contains the expected cache object at all.

This is not a duplicate of Issue 474. Issue 474 validates the optional explicit parent thread stored on a `ForumPostCollection`. This slice validates the separate cache slot stored on a `ForumThread` record.

This is not a duplicate of Issue 367. Issue 367 validates collection entries before `ForumPostCollection.get_post_sources()` performs cache or request work. This slice rejects malformed cached entries at `ForumThread` construction before `thread.posts` can return that mutated collection.

This follows the Page constructor-cache pattern from Issues 490 through 493, but applies it to the forum-thread post-list cache.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached posts validation for direct `ForumThread(...)` construction.
- Preserve `_posts=None` for threads that should lazily acquire posts.
- Preserve valid `ForumPostCollection` objects without coercion.
- Reject booleans, strings, raw lists, dictionaries, arbitrary non-collection objects, and collections mutated with malformed entries using stable `ValueError` diagnostics.
- Add constructor tests for malformed direct `_posts` values, valid optional post cache state, and malformed cached collection entries.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached forum-post state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(_posts=...)` must accept `None` and real `ForumPostCollection` objects. |
| R2 | `ForumThread(_posts=...)` must reject non-`None` non-`ForumPostCollection` values with `ValueError("thread.posts must be ForumPostCollection or None")`. |
| R3 | `ForumThread(_posts=...)` must reject `ForumPostCollection` objects containing non-`ForumPost` entries with `ValueError("thread.posts list entries must be ForumPost")`. |
| R4 | Valid thread construction, lazy `ForumThread.posts`, direct `ForumPostCollection.acquire_all_in_thread(s)`, successful direct acquisition cache population, duplicate cached thread-post reuse, reply cache invalidation, `ForumPostCollection` construction validation, parser-created threads, and forum category/thread/post/revision workflows must remain unchanged. |
| R5 | This slice must not change post-list acquisition, source acquisition, parser selectors, response diagnostics, post ordering, collection ownership inference, cache invalidation semantics, live request behavior, or unrelated constructor fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid `ForumPostCollection` cached post values remain accepted. | `TestForumThreadBasic.test_init_accepts_valid_posts_cache` passed after validation was added, preserving a valid cached collection and returning it through `thread.posts`. Existing constructors continue to use `_posts=None`. | Rejecting missing cached posts, triggering post-list lookup during construction, or coercing valid collection objects rejects this local completion claim. | `ForumThread` constructor cached-post state | `tests/unit/test_forum_thread.py` |
| R2 | Malformed optional cached post values fail at the constructor boundary. | `TestForumThreadBasic.test_init_rejects_malformed_posts_cache` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, raw lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `ForumThread` constructor cached-post state | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Mutated post collections with malformed entries fail at the constructor boundary. | `TestForumThreadBasic.test_init_rejects_malformed_posts_cache_entries` failed RED because a valid collection mutated with `object()` was accepted, then passed GREEN after entry validation was added. | Trusting a mutated collection, storing malformed entries, or deferring failure to lazy `ForumThread.posts`, duplicate cached thread-post reuse, post source reads, or generated ledgers rejects this local completion claim. | `ForumThread` constructor cached-post entries | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R4 | Existing thread/post workflows remain green. | `tests/unit/test_forum_thread.py` passed 132 tests, adjacent forum tests passed 461 tests, and the full unit suite passed 2236 tests. | Regressing lazy post acquisition, direct post-list acquisition, successful direct acquisition cache population, cached duplicate thread-post reuse, collection construction validation, reply cache invalidation, parser-created threads, category thread reads, direct thread reads, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit` |
| R5 | Broader post-list semantics remain outside scope. | Existing acquisition, parser, cache invalidation, collection, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing request construction, parser conversion, response diagnostics, post ordering, collection parent inference, source acquisition, reply behavior, cache invalidation, or live request behavior rejects this local completion claim. | ForumThread constructor scope | `src/wikidot/module/forum_thread.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5da32ca fix(forum_thread): validate posts cache`.

- RED type guard: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache -q` failed 5 tests before the fix; every malformed `_posts` value reported `DID NOT RAISE`.
- GREEN type guard: the same focused command passed 5 tests after optional cache type validation was added.
- RED entry guard: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache_entries -q` failed before the entry guard because a mutated `ForumPostCollection` was accepted.
- GREEN entry guard: the same focused command passed after cached collection entry validation was added.
- Cache trio: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_accepts_valid_posts_cache tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache_entries -q` passed 7 tests.
- Adjacent constructor checks: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_posts_cache_entries tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_sites tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_thread_id tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_string_title tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_string_description tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_post_count tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_by tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_at tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_categories -q` passed 41 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 132 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 461 tests.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2236 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(_posts=None)` remains valid and lazy post acquisition remains available.
- `ForumThread(_posts=ForumPostCollection(...))` remains valid and `thread.posts` returns the cached object without a lookup.
- `ForumThread(_posts=True)`, `ForumThread(_posts="5001")`, `ForumThread(_posts=[])`, `ForumThread(_posts={"posts": []})`, and `ForumThread(_posts=object())` raise `ValueError("thread.posts must be ForumPostCollection or None")` when every other constructor field is valid.
- `ForumThread(_posts=collection_mutated_with_non_post)` raises `ValueError("thread.posts list entries must be ForumPost")` when every other constructor field is valid.
- Existing parser-created threads, direct thread fixtures, category thread-list reads, direct thread-detail reads, lazy `ForumThread.posts`, direct and batched `ForumPostCollection` acquisition, direct acquisition cache population, duplicate cached thread-post reuse, reply cache invalidation, `ForumPostCollection` construction validation, forum post source behavior, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not validate collection ownership, post parser contents, live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with ownership validation between `thread` and `posts.thread`. Mitigation: the validator checks object shape and entries only, matching adjacent Page cache validators; ownership matching remains outside scope.
- Risk: Valid cached post collections could accidentally trigger network fetches during construction. Mitigation: the valid-cache test asserts `thread.posts is posts`, and the constructor validator does not call acquisition helpers.
- Risk: Mutated cached collections could still reach later source reads through post-construction mutation. Mitigation: this slice closes the direct constructor bypass; existing source-acquisition entry validation remains responsible for later collection mutations before request work.

## Dependencies

- `ForumPostCollection` remains the annotated cache object behind `ForumThread.posts`.
- `ForumPostCollection` constructor validation remains responsible for normal collection construction from `posts=...`.
- Existing acquisition helpers remain responsible for populating `_posts` only after successful reads and preserving failure behavior.

## Open Questions

None for this local slice. Collection ownership matching between a preloaded `ForumPostCollection.thread` and the newly constructed `ForumThread` remains outside scope, matching the adjacent Page cache validators that do not validate cached object ownership identity.

## Upstream-Safe Motivation

Cached thread posts are a shared state surface for forum inventories, discussion migration ledgers, duplicate post-list cache reuse, lazy post reads, reply cache invalidation, and generated moderation or translation tooling. Direct construction is useful for fixtures and rehydrated records, but malformed cached post values should fail at construction instead of making `ForumThread.posts` return unusable state.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free thread post-list reads, cached direct acquisition, duplicate cached thread-post reuse, reply cache invalidation, generated forum inventory ledgers, forum migration checks, moderation tooling, and tests that seed post collections directly.
- Existing local drafts covered thread-post fetch retry behavior, duplicate thread-post request reduction, cache reuse, direct acquisition cache population, post edit cache invalidation, parser diagnostics, response diagnostics, `ForumPostCollection` constructor validation, collection parent-thread validation, source-acquisition entry validation, individual `ForumPost.thread`, and direct `ForumThread` field validation, but did not cover direct optional cached-post construction on `ForumThread`.
- Existing unit fixtures already relied on `_posts=None` being valid for lazy post acquisition and `ForumPostCollection` being valid for preloaded post records, so this change validates only malformed non-null values and mutated entries.
- This slice does not change parser extraction, thread acquisition, post acquisition, source acquisition, reply payloads, response diagnostics, duplicate cache behavior, cache invalidation semantics, collection parent inference, live Wikidot behavior, site client internals, or unrelated constructor fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, page source text, private messages, and private site data out of upstream discussion.

## Additional Notes

The validator deliberately does not change `ForumPostCollection.acquire_all_in_thread(...)`, batched post-list acquisition, or lazy `ForumThread.posts` acquisition behavior. The direct `_posts` constructor field is the stored cache field and therefore accepts only the annotated cache object shape plus `None`, while existing forum-post collection constructors remain responsible for normal collection construction and parent inference semantics.
