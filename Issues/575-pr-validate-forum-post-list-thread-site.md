# PR Draft: Validate Forum Post List Thread Site State

## Summary

`ForumPostCollection.acquire_all_in_threads(...)` is the shared read path behind direct forum post-list acquisition and lazy `ForumThread.posts`. Existing local slices validate caller-provided thread objects, forum-thread construction, cached post collections, post-list retry behavior, response-body diagnostics, parser context, duplicate/cache behavior, and reply-side cache invalidation. One retained-state boundary still trusted each target thread's parent site after construction: if a caller, fixture, or rehydrated thread object replaced `thread.site` with a malformed non-`Site` object, post-list acquisition could reach mocked retry request handling and fail later with an unrelated `zip(...)` length error instead of reporting the parent-state problem.

This change revalidates target `thread.site` values inside `ForumPostCollection.acquire_all_in_threads(...)` after cache reuse has selected the threads that actually need a fetch and before the first `ForumViewThreadPostsModule` request is built. Malformed post-list read-time thread parent state now raises `ValueError("site must be a Site")`. Empty batches, fully cached batches, valid post-list reads, retry diagnostics, parser behavior, source/revision workflows, and adjacent forum workflows remain unchanged.

## Outcome

Forum post-list acquisition now has explicit read-time parent-site preflight before malformed retained thread state can influence request routing, retry handling, parser diagnostics, or lazy `ForumThread.posts` cache population.

## Current Evidence

Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), and [574-pr-validate-forum-thread-reply-site.md](574-pr-validate-forum-thread-reply-site.md) establish forum post-list reads, retained parent state, and adjacent action/read-time site validation as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 503 validates `ForumThread(site=...)` at construction time. Issue 363 validates the `thread` argument type before post-list acquisition, but not the retained site on a valid thread object. Issues 446 and 474 validate forum-post and forum-post-collection parent thread fields, not the site on target forum threads. Issue 504 validates the optional cached `ForumThread._posts` object, not uncached post-list request routing. Issue 574 validates reply action-time site state, not post-list read-time acquisition. This slice covers mutated retained `ForumThread.site` at forum post-list fetch time, not constructor input validation, thread-object input shape, cached post-list shape, post parser behavior, reply actions, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Add a forum-post module parent-site validator with the existing `ValueError("site must be a Site")` diagnostic.
- Revalidate target uncached threads' retained `site` values inside `ForumPostCollection.acquire_all_in_threads(...)` before request work.
- Preserve cached no-request behavior by validating only threads that actually need a post-list fetch.
- Add a regression for a mutated non-`Site` target thread parent that previously reached mocked retry request handling.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.acquire_all_in_threads(...)` must reject a mutated non-`Site` `thread.site` on uncached target threads with `ValueError("site must be a Site")` before retry request work. |
| R2 | Empty batches and fully cached batches must retain their existing no-request behavior. |
| R3 | Existing thread-object input validation must keep precedence before retained-site validation. |
| R4 | Valid post-list acquisition, duplicate/cache behavior, retry diagnostics, parser diagnostics, lazy `ForumThread.posts`, source/revision workflows, and adjacent forum behavior must remain stable. |
| R5 | Focused RED/GREEN, acquisition tests, forum-post tests, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained target thread parent state fails before retry request work. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_rejects_mutated_thread_site_before_fetch` failed RED with `ValueError("zip() argument 2 is shorter than argument 1")` after mocked retry request handling, then passed GREEN after target thread sites were revalidated. | Calling `amc_request_with_retry`, coercing malformed parents, returning partial data, caching an empty collection, or deferring failure to zip/parser diagnostics rejects this local completion claim. | `ForumPostCollection.acquire_all_in_threads(...)` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Cached no-request behavior remains unchanged. | Existing cached and duplicate-cache acquisition tests stayed green in focused acquisition coverage. | Rejecting fully cached batches, issuing requests for cached threads, or changing duplicate cached post-list reuse rejects this local completion claim. | Forum post-list cache reuse | `tests/unit/test_forum_post.py` |
| R3 | Thread-object input validation precedence remains unchanged. | `test_acquire_all_in_threads_rejects_non_list_threads_before_fetch`, `test_acquire_all_in_threads_rejects_non_thread_entries_before_fetch`, and `test_acquire_all_in_thread_rejects_non_thread_before_fetch` stayed green. | Reading `thread.site` before rejecting non-list or non-`ForumThread` inputs rejects this local completion claim. | Forum post-list public input preflight | `tests/unit/test_forum_post.py` |
| R4 | Adjacent workflows remain stable. | `tests/unit/test_forum_post.py` passed 152 tests, adjacent forum workflow tests passed 512 tests, and the full unit suite passed 2673 tests. | Regressing post-list parsing, first-page or paginated retry handling, response-body diagnostics, duplicate cache reuse, source acquisition, edit behavior, lazy `ForumThread.posts`, forum thread behavior, forum category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic mutated thread state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `8edcf31 fix(forum_post): validate thread post-list site`.

- RED post-list site validation: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_mutated_thread_site_before_fetch -q` failed before the fix with `ValueError("zip() argument 2 is shorter than argument 1")` after the malformed site reached mocked retry request handling.
- GREEN focused regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_mutated_thread_site_before_fetch -q` passed.
- Focused acquisition coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 31 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 152 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 512 tests.
- `uv run pytest tests/unit -q` passed 2673 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_threads(...)` rejects mutated malformed target `thread.site` values with `ValueError("site must be a Site")` before retry request work.
- Empty and fully cached post-list batches retain no-request behavior.
- Existing thread input validation remains earlier than retained-site validation.
- Valid post-list acquisition, duplicate/cache behavior, retry diagnostics, parser diagnostics, source/revision workflows, and lazy `ForumThread.posts` behavior remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `ForumThread.site` state reached mocked post-list retry request handling and then raised an unrelated `zip()` length error instead of the existing parent-site diagnostic.
- This slice only validates retained forum-thread parent state before uncached post-list read work. It does not change thread construction, direct thread acquisition, thread-list parsing, direct thread-detail parsing, collection lookup semantics, URL generation, reply actions, forum category behavior, forum post parser behavior, forum post source/revision behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, and live Wikidot account details out of upstream discussion.
