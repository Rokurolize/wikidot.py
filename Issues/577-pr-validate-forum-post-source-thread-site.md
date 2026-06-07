# PR Draft: Validate Forum Post Source Thread Site State

## Summary

`ForumPostCollection.get_post_sources()` validates the retained collection thread before source-form acquisition, but the next retained-state boundary still trusted `thread.site`. If caller code, a test fixture, or rehydrated state replaced a valid `ForumThread.site` with a malformed object after construction, source acquisition could call that object’s retry method and fail later with an unrelated `zip(...)` length error instead of reporting the invalid site.

This change revalidates the retained source-acquisition thread site before cache inspection can route a `ForumEditPostFormModule` request. Malformed source read-time thread-site state now raises `ValueError("site must be a Site")` before retry request work. Empty parentless collections, valid source reads, cached-source no-ops, duplicate/cache behavior, response diagnostics, lazy `ForumPost.source`, edit workflows, and adjacent forum workflows remain unchanged.

## Outcome

Forum post source acquisition now has explicit read-time parent-site preflight after retained parent-thread validation and before source request construction.

## Current Evidence

Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [506-pr-validate-forum-post-source-cache.md](506-pr-validate-forum-post-source-cache.md), [575-pr-validate-forum-post-list-thread-site.md](575-pr-validate-forum-post-list-thread-site.md), and [576-pr-validate-forum-post-source-collection-thread.md](576-pr-validate-forum-post-source-collection-thread.md) establish forum post source reads, retained parent state, and adjacent site validation as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 474 validates constructor-time collection parent input. Issue 576 validates post-construction mutated `ForumPostCollection.thread` values. Issue 575 validates target thread sites for post-list acquisition, not source-form acquisition. This slice covers a valid retained source collection thread whose `thread.site` was mutated before `get_post_sources()`.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `thread.site` at the start of `ForumPostCollection._acquire_post_sources(...)` after thread validation.
- Use the validated `site` for source-form retry requests.
- Add a regression for a mutated retained source thread site that previously reached mocked retry request handling.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.get_post_sources()` must reject a mutated non-`Site` `collection.thread.site` with `ValueError("site must be a Site")` before retry request work. |
| R2 | Existing retained-thread and collection-entry validation must remain stable. |
| R3 | Empty parentless collections and fully cached source reads must retain no-request behavior. |
| R4 | Valid source acquisition, duplicate/cache behavior, retry diagnostics, response diagnostics, lazy `ForumPost.source`, edit workflows, and adjacent forum behavior must remain stable. |
| R5 | Focused RED/GREEN, source-acquisition tests, forum-post tests, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained source thread site fails before source request work. | `TestForumPostCollectionGetSources.test_get_post_sources_rejects_mutated_thread_site_before_fetch` failed RED with `ValueError("zip() argument 2 is shorter than argument 1")` after mocked retry request handling, then passed GREEN after `_acquire_post_sources(...)` revalidated `thread.site`. | Calling `amc_request_with_retry`, coercing malformed sites, returning partial data, caching source text, or deferring failure to zip/parser diagnostics rejects this local completion claim. | `ForumPostCollection.get_post_sources()` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Existing source parent and entry validation remains unchanged. | The retained-thread regression and malformed-entry regression stayed green in focused source-acquisition coverage. | Reordering validation so malformed entries or malformed retained parents can reach request work rejects this local completion claim. | Forum post source preflight | `tests/unit/test_forum_post.py` |
| R3 | No-request behavior remains unchanged. | Existing empty collection, cached source, and duplicate cached source tests stayed green in focused source-acquisition coverage. | Issuing requests for empty/cached source reads or changing cached source values rejects this local completion claim. | Forum post source cache reuse | `tests/unit/test_forum_post.py` |
| R4 | Adjacent workflows remain stable. | `tests/unit/test_forum_post.py` passed 154 tests, adjacent forum workflow tests passed 514 tests, and the full unit suite passed 2675 tests. | Regressing source-form fetches, transient retry handling, response-body diagnostics, direct source textarea scoping, duplicate source reuse, lazy `ForumPost.source`, post editing, post-list reads, forum thread behavior, forum category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic mutated collection state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `07d5791 fix(forum_post): validate source thread site`.

- RED source thread-site validation: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_mutated_thread_site_before_fetch -q` failed before the fix with `ValueError("zip() argument 2 is shorter than argument 1")` after the malformed site reached mocked retry request handling.
- GREEN focused regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_mutated_thread_site_before_fetch -q` passed.
- Focused source-acquisition coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources -q` passed 17 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 154 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 514 tests.
- `uv run pytest tests/unit -q` passed 2675 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostCollection.get_post_sources()` rejects mutated malformed `collection.thread.site` values with `ValueError("site must be a Site")` before source request work.
- Retained collection-thread validation and malformed-entry validation remain unchanged.
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

- The focused RED failure showed mutated retained `ForumPostCollection.thread.site` state reached mocked source-form retry request handling and then raised an unrelated `zip()` length error instead of the existing site diagnostic.
- This slice only validates retained forum-post source thread-site state before source acquisition. It does not change thread construction, collection parent validation, post-list parsing, source response parsing, source textarea parsing, lazy source cache semantics, post editing, reply actions, forum category behavior, forum post revision behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
