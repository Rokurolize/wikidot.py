# PR Draft: Validate Forum Post Source Collection Thread State

## Summary

`ForumPostCollection.get_post_sources()` is the shared read path behind direct forum post source acquisition and lazy `ForumPost.source`. Existing local slices validate constructor-time `ForumPostCollection(thread=...)` inputs, collection entries, source cache state, source retry behavior, source response bodies, source textarea scoping, duplicate/cache reuse, and lazy source diagnostics. One retained-state boundary still trusted the collection parent after construction: if a caller, fixture, or rehydrated collection replaced `collection.thread` with a malformed non-`ForumThread` object, source acquisition could reach mocked retry request handling and fail later with an unrelated `zip(...)` length error instead of reporting the parent-thread problem.

This change revalidates the source-acquisition helper's `thread` argument before post-entry validation, cache inspection, duplicate grouping, or `ForumEditPostFormModule` request construction. Malformed source read-time collection parent state now raises `ValueError("thread must be a ForumThread")`. Empty parentless collections, valid source reads, cached-source no-ops, duplicate/cache behavior, response diagnostics, lazy `ForumPost.source`, edit workflows, and adjacent forum workflows remain unchanged.

## Outcome

Forum post source acquisition now has explicit read-time parent-thread preflight before malformed retained collection state can influence cache inspection, request routing, retry handling, response diagnostics, source parsing, or source-cache mutation.

## Current Evidence

Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [506-pr-validate-forum-post-source-cache.md](506-pr-validate-forum-post-source-cache.md), and [575-pr-validate-forum-post-list-thread-site.md](575-pr-validate-forum-post-list-thread-site.md) establish forum post source reads, retained parent state, and adjacent read-time validation as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 474 validates explicit non-`None` `ForumPostCollection(thread=...)` construction before malformed parents can be stored initially. Issue 367 validates source collection entries, not the retained parent thread. Issue 506 validates cached source values on individual posts. Issue 575 validates target thread sites for post-list acquisition, not source-form acquisition. This slice covers a post-construction mutated `ForumPostCollection.thread` at source read time, not constructor input validation, post entry shape, source cache values, source response shape, edit-form parsing, post-list acquisition, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate the `thread` argument at the start of `ForumPostCollection._acquire_post_sources(...)`.
- Add a regression for a mutated non-`ForumThread` collection parent that previously reached mocked retry request handling.
- Preserve valid source acquisition, cache reuse, duplicate handling, response diagnostics, lazy source reads, and adjacent forum workflows.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.get_post_sources()` must reject a mutated non-`ForumThread` `collection.thread` with `ValueError("thread must be a ForumThread")` before cache or request work. |
| R2 | Existing collection-entry validation must remain stable and reject malformed posts before request work. |
| R3 | Empty parentless collections and fully cached source reads must retain no-request behavior. |
| R4 | Valid source acquisition, duplicate/cache behavior, retry diagnostics, response diagnostics, lazy `ForumPost.source`, edit workflows, and adjacent forum behavior must remain stable. |
| R5 | Focused RED/GREEN, source-acquisition tests, forum-post tests, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained collection parent thread state fails before source request work. | `TestForumPostCollectionGetSources.test_get_post_sources_rejects_mutated_thread_before_fetch` failed RED with `ValueError("zip() argument 2 is shorter than argument 1")` after mocked retry request handling, then passed GREEN after `_acquire_post_sources(...)` revalidated `thread`. | Calling `amc_request_with_retry`, coercing malformed parents, returning partial data, caching source text, or deferring failure to zip/parser diagnostics rejects this local completion claim. | `ForumPostCollection.get_post_sources()` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Collection-entry validation remains unchanged. | `test_get_post_sources_rejects_non_post_entries_before_fetch` stayed green in focused source-acquisition coverage. | Reading source cache state or parent thread state from malformed entries before rejecting them rejects this local completion claim. | Forum post source entry preflight | `tests/unit/test_forum_post.py` |
| R3 | No-request behavior remains unchanged. | Existing empty collection, cached source, and duplicate cached source tests stayed green in focused source-acquisition coverage. | Issuing requests for empty/cached source reads or changing cached source values rejects this local completion claim. | Forum post source cache reuse | `tests/unit/test_forum_post.py` |
| R4 | Adjacent workflows remain stable. | `tests/unit/test_forum_post.py` passed 153 tests, adjacent forum workflow tests passed 513 tests, and the full unit suite passed 2674 tests. | Regressing source-form fetches, transient retry handling, response-body diagnostics, direct source textarea scoping, duplicate source reuse, lazy `ForumPost.source`, post editing, post-list reads, forum thread behavior, forum category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic mutated collection state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ff69c97 fix(forum_post): validate source collection thread`.

- RED source-collection thread validation: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_mutated_thread_before_fetch -q` failed before the fix with `ValueError("zip() argument 2 is shorter than argument 1")` after the malformed parent thread reached mocked retry request handling.
- GREEN focused regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_mutated_thread_before_fetch -q` passed.
- Focused source-acquisition coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources -q` passed 16 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 153 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 513 tests.
- `uv run pytest tests/unit -q` passed 2674 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostCollection.get_post_sources()` rejects mutated malformed `collection.thread` values with `ValueError("thread must be a ForumThread")` before cache inspection or source request work.
- Empty parentless source collections and cached source reads retain no-request behavior.
- Valid source acquisition, duplicate/cache behavior, retry diagnostics, response diagnostics, source textarea parsing, lazy `ForumPost.source`, and edit workflows remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `ForumPostCollection.thread` state reached mocked source-form retry request handling and then raised an unrelated `zip()` length error instead of the existing parent-thread diagnostic.
- This slice only validates retained forum-post collection parent state before source acquisition. It does not change thread construction, post-list parsing, source response parsing, source textarea parsing, lazy source cache semantics, post editing, reply actions, forum category behavior, forum post revision behavior, live site behavior, or authentication semantics for valid parents.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
