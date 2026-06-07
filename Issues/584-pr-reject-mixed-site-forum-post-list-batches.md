# PR Draft: Reject Mixed-Site Forum Post-List Batches

## Summary

`ForumPostCollection.acquire_all_in_threads(...)` validated each target thread's retained `site` field, but it still selected `target_sites[0]` as the single request site for every uncached thread in the batch. If caller code mixed valid `ForumThread` objects from different `Site` objects, the method could route another site's `ForumViewThreadPostsModule` request through the first site and then fail with unrelated response-iteration diagnostics, or worse, parse wrong-site data if thread IDs overlapped.

This change rejects mixed-site forum post-list batches before request work. Same-site direct acquisition, duplicate thread-ID handling, cached post-list reuse, all-cached batches, pagination, retry-exhausted diagnostics, response-body diagnostics, parser behavior, source acquisition, editing, and adjacent forum workflows remain unchanged.

## Outcome

Forum post-list batch reads now fail explicitly with `ValueError("threads must belong to the same Site")` before a mixed-site input can send post-list requests through the wrong site.

## Current Evidence

Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), [575-pr-validate-forum-post-list-thread-site.md](575-pr-validate-forum-post-list-thread-site.md), and [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md) establish forum post-list acquisition as a retry-aware, cache-aware, duplicate-aware, direct-cache-populating, and retained-parent-safe workflow surface.

This slice is not a duplicate of those issues. Issue 575 validates malformed local `thread.site` state before post-list acquisition. Issue 583 rejects mixed-site forum post revision batches. This slice covers a different valid-object routing problem: every thread and site is individually valid, but the post-list batch spans more than one `Site` object while the implementation has only one request site and an `id`-keyed result.

No upstream issue was filed from this local workspace.

## Changes

- Add a same-site preflight for forum post-list batch request sites.
- Apply it before `ForumPostCollection.acquire_all_in_threads(...)` first-page requests.
- Add a regression for mixed-site uncached thread post-list batches.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.acquire_all_in_threads([...])` must reject valid uncached threads from different `Site` objects with `ValueError("threads must belong to the same Site")` before AMC request work or thread post-cache mutation. |
| R2 | Valid same-site direct acquisition, duplicate thread-ID handling, cached post-list reuse, all-cached batches, pagination, retry-exhausted diagnostics, response-body diagnostics, parser behavior, source acquisition, and editing must remain stable. |
| R3 | Adjacent forum category, forum thread, forum post, and forum post revision workflows must remain stable. |
| R4 | Focused RED/GREEN, acquisition-class, full forum-post module, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mixed-site uncached post-list batches fail before side-effect surfaces. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_rejects_mixed_site_threads_before_fetch` failed RED by routing through the first site's mocked retry helper and surfacing `zip() argument 2 is shorter than argument 1`, then passed GREEN with `ValueError("threads must belong to the same Site")`, no request call, and no `_posts` cache mutation. | Calling either site's AMC helpers, accepting mixed valid site objects, mutating `_posts`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostCollection.acquire_all_in_threads(...)` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Valid same-site forum post-list workflows remain unchanged. | Full `tests/unit/test_forum_post.py` passed 157 tests, including same-site direct acquisition, cached skips, duplicate reuse, pagination, retry failures, response diagnostics, parser behavior, source reads, and edit behavior. | Regressing same-site post-list acquisition, cached post-list reuse, duplicate thread handling, pagination, retry failure handling, response-body diagnostics, source acquisition, edit behavior, or parser behavior rejects this local completion claim. | Forum post workflows | `tests/unit/test_forum_post.py` |
| R3 | Adjacent workflows remain stable. | Adjacent forum workflow tests passed 525 tests, and the full unit suite passed 2686 tests. | Regressing forum category, forum thread, forum post, or forum post revision behavior rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R4 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic valid `Site` and `ForumThread` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ec721e6 fix(forum_post): reject mixed-site post-list batches`.

- RED mixed-site post-list routing: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_mixed_site_threads_before_fetch -q` failed before the fix because mixed valid site objects reached the first site's mocked retry helper and surfaced `zip() argument 2 is shorter than argument 1` instead of `ValueError("threads must belong to the same Site")`.
- GREEN focused regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_mixed_site_threads_before_fetch -q` passed 1 test.
- Acquisition-class coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 32 tests.
- Full forum-post module: `uv run pytest tests/unit/test_forum_post.py -q` passed 157 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 525 tests.
- `uv run pytest tests/unit -q` passed 2686 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Mixed-site `ForumPostCollection.acquire_all_in_threads([...])` inputs fail with `ValueError("threads must belong to the same Site")` before post-list request work or cache mutation.
- Same-site direct acquisition, duplicate thread-ID handling, cached post-list reuse, all-cached batches, pagination, retry-exhausted diagnostics, response-body diagnostics, parser behavior, source acquisition, and editing remain unchanged.
- Adjacent forum behavior remains intact.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mixed valid site objects reached the first site's mocked post-list request handling and then raised an unrelated `zip()` length diagnostic instead of a same-site batch diagnostic.
- This slice only rejects mixed-site forum post-list batches that the current one-site request implementation cannot route safely. It does not change same-site post-list acquisition, duplicate thread-ID behavior, cached post-list reuse, parser selectors, response diagnostics, source acquisition, edit behavior, live site behavior, or authentication semantics for valid same-site batches.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
