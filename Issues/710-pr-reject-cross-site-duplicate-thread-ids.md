# PR Draft: Reject Cross-Site Duplicate Forum Thread IDs

## Summary

`ForumPostCollection.acquire_all_in_threads(...)` deduplicates forum post-list requests by retained `ForumThread.id`, which is correct for duplicate thread objects from the same `Site`. One adjacent batch-boundary gap remained: if caller or rehydrated state supplied two valid `ForumThread` objects with the same numeric ID but different retained `Site` objects, the method treated the second thread as an ordinary duplicate before same-site validation could see it. The returned `dict[int, ForumPostCollection]` also cannot represent two different site/thread pairs with the same integer key.

This change validates that duplicate retained thread IDs in a post-list batch belong to the same `Site` object before cache maps, ID-only deduplication, request construction, or cache reuse. Same-site duplicate ID dedupe, same-site cached duplicate reuse, mixed-site different-ID rejection, direct acquisition, pagination, parser diagnostics, response diagnostics, source acquisition, edit behavior, and adjacent forum workflows remain unchanged.

## Outcome

Forum post-list batches no longer silently collapse cross-site thread objects that share the same retained thread ID. Valid same-site duplicates are still fetched or cache-reused once, while cross-site ID collisions now fail with `ValueError("threads must belong to the same Site")` before either site's AMC helpers are called.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `ForumThread.posts`, `ForumPostCollection.acquire_all_in_thread(...)`, or `ForumPostCollection.acquire_all_in_threads(...)` in browser-free forum inventories, migration ledgers, moderation tooling, translation review scripts, cached post-list reuse, or rehydrated thread records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post-list acquisition, duplicate thread batching, cached thread-post reuse, retained parent validation, and mixed-site request routing as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), [575-pr-validate-forum-post-list-thread-site.md](575-pr-validate-forum-post-list-thread-site.md), [584-pr-reject-mixed-site-forum-post-list-batches.md](584-pr-reject-mixed-site-forum-post-list-batches.md), and [680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md](680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md) establish this as an active read boundary.

This slice is not a duplicate of those drafts. Issue 584 rejects mixed-site uncached batches where different retained thread IDs would be routed through one request site. Issue 680 validates malformed or negative retained thread IDs before grouping, request payloads, result keys, or cache assignment. Issues 059, 134, and 141 intentionally preserve same-site duplicate ID dedupe and cached duplicate reuse. This slice covers the remaining collision case where the ID value is valid but the duplicated ID belongs to a different retained `Site`, making ID-only dedupe unsafe.

No upstream issue was filed from this local workspace.

## Changes

- Add a preflight that scans duplicate retained thread IDs and requires every duplicate ID to point at the same retained `Site` object.
- Run that preflight immediately after thread input and retained thread-ID validation, before cache maps and seen-ID dedupe.
- Preserve same-site duplicate ID dedupe and later cached duplicate collection copying.
- Add a regression for two valid `ForumThread` objects with the same `id` and different `Site` objects.

## Type Of Change

- Batch input validation
- Forum post-list cache/dedupe hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.acquire_all_in_threads([...])` must reject valid duplicate retained thread IDs from different `Site` objects with `ValueError("threads must belong to the same Site")` before AMC request work or `_posts` cache mutation. |
| R2 | Same-site duplicate retained thread IDs must continue to deduplicate to one request/result entry. |
| R3 | Same-site cached duplicate post-list reuse must continue to copy the cached collection for the first-seen thread without refetching. |
| R4 | Existing mixed-site different-ID rejection must remain intact. |
| R5 | Direct acquisition, pagination, retry-exhausted diagnostics, response-body diagnostics, parser behavior, source acquisition, edit behavior, and adjacent forum workflows must remain compatible. |
| R6 | Focused RED/GREEN, acquisition-class, forum-post module, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cross-site duplicate thread IDs fail before side effects. | `test_acquire_all_in_threads_rejects_duplicate_thread_ids_from_different_sites_before_fetch` failed RED with `DID NOT RAISE`, then passed GREEN with the same-site diagnostic and no AMC calls. | Silently treating the second site thread as a duplicate, calling either site's AMC helpers, mutating `_posts`, or returning a single ID-keyed result rejects this local completion claim. | `ForumPostCollection.acquire_all_in_threads(...)` duplicate-ID preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Existing same-site duplicate ID dedupe remains unchanged. | Focused GREEN included `test_acquire_all_in_threads_deduplicates_duplicate_thread_ids`. | Rejecting valid same-site duplicates, sending duplicate requests, or changing the result key rejects this local completion claim. | Same-site duplicate post-list batching | `tests/unit/test_forum_post.py` |
| R3 | Existing same-site cached duplicate reuse remains unchanged. | Focused GREEN included `test_acquire_all_in_threads_reuses_later_cached_duplicate_thread_posts`. | Refetching cached duplicates, reusing a cached collection without retargeting posts, or mutating cached revision state rejects this local completion claim. | Cached duplicate post-list reuse | `tests/unit/test_forum_post.py` |
| R4 | Mixed-site different-ID batches still reject before request work. | Focused GREEN included `test_acquire_all_in_threads_rejects_mixed_site_threads_before_fetch`. | Regressing Issue 584 by routing a mixed-site request through one site rejects this local completion claim. | Mixed-site post-list batch preflight | `tests/unit/test_forum_post.py` |
| R5 | Adjacent forum workflows remain green. | `TestForumPostCollectionAcquireAll` passed 56 tests, `tests/unit/test_forum_post.py` passed 290 tests, adjacent forum tests passed 877 tests, and full unit coverage passed 3560 tests. | Regressing direct acquisition, pagination, parser diagnostics, response diagnostics, source acquisition, edit behavior, forum category/thread/revision behavior, or site-adjacent behavior rejects this local completion claim. | Forum post-list and adjacent forum workflows | `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff check passed, full ruff format check passed, full mypy passed with no issues in 87 source files, pyright passed with 0 errors, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | The regression uses synthetic valid `Site` and `ForumThread` objects plus unit-level response mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `72c7df8 fix(forum_post): reject cross-site duplicate thread ids`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_duplicate_thread_ids_from_different_sites_before_fetch -q` failed before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_duplicate_thread_ids_from_different_sites_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_deduplicates_duplicate_thread_ids tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_mixed_site_threads_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_reuses_later_cached_duplicate_thread_posts -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll -q` passed 56 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed 290 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 877 tests.
- `uv run --extra test pytest tests/unit -q` passed 3560 tests after the final code patch.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Cross-site duplicate retained thread IDs in `ForumPostCollection.acquire_all_in_threads(...)` raise `ValueError("threads must belong to the same Site")` before AMC request work or `_posts` cache mutation.
- Same-site duplicate retained thread IDs still deduplicate to one request/result entry.
- Same-site cached duplicate post-list reuse still avoids request work and returns a collection retargeted to the first-seen thread.
- Mixed-site different-ID batches still reject before request work.
- Direct post-list acquisition, empty input behavior, cached post-list skips, pagination, retry-exhausted diagnostics, response-body diagnostics, parser behavior, source acquisition, edit behavior, and adjacent forum workflows remain green.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may intentionally batch cached threads from multiple sites. Mitigation: this slice only rejects duplicate numeric thread IDs that cannot be represented safely in the ID-keyed result map; different-ID cache-only behavior is left unchanged.
- Risk: The new preflight could interfere with same-site duplicate dedupe. Mitigation: focused coverage proves same-site duplicate IDs and cached duplicate reuse still pass.
- Risk: Cross-site object graphs can share a client while still representing different sites. Mitigation: the check compares retained `Site` object identity, matching the existing mixed-site batch guard and avoiding name/id coercion.

## Out Of Scope

Changing result keys, supporting multi-site request routing in one call, rejecting all cached mixed-site batches, changing same-site duplicate behavior, changing pagination, changing parser selectors, changing source acquisition, changing forum post edits, live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used forum post-list acquisition, duplicate thread batching, cached post-list reuse, forum migration ledgers, moderation/audit workflows, and rehydrated forum records.
- Existing local drafts covered retry behavior, duplicate same-site fetch reduction, cached post-list skip/reuse, direct acquisition cache population, malformed retained thread-site validation, mixed-site different-ID routing rejection, and malformed/negative retained thread-ID validation.
- The focused RED failure showed the same numeric thread ID from a different `Site` was silently treated as an ordinary duplicate and the second thread's site was never consulted.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private forum content, private site data, and source text from real sites out of upstream discussion.
