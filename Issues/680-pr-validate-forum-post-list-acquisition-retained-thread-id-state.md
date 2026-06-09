# PR Draft: Validate ForumPost List Acquisition Retained Thread IDs

## Summary

`ForumPostCollection.acquire_all_in_thread(thread)` and `ForumPostCollection.acquire_all_in_threads(threads)` already reject non-`ForumThread` inputs, reject mixed-site post-list batches, retry thread post-list requests, deduplicate duplicate thread IDs, skip cached post lists, reuse cached duplicate post lists, and validate direct `ForumThread(id=...)` construction. The post-list acquisition paths still used retained `thread.id` values directly for direct result lookup, cached collection maps, duplicate grouping, result keys, first-page and additional-page request payloads, exhausted-retry diagnostics, pagination response fan-out, and final `_posts` cache assignment. If a valid `ForumThread` is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, strings, floats, booleans, negative integers, or unhashable values can reach cache grouping or AMC payload construction instead of producing the same deterministic thread-ID diagnostics used elsewhere.

This change validates each retained `ForumThread.id` with the existing forum-thread ID validator before forum post-list acquisition uses it. Malformed retained IDs now raise `ValueError("thread_id must be an integer")`, negative retained IDs now raise `ValueError("thread_id must be non-negative")`, valid zero thread IDs remain accepted, cached direct acquisition remains guarded before cache return, duplicate post-list dedupe and cached duplicate reuse are preserved, and post-list requests are still batched by valid thread ID.

## Outcome

Forum post-list acquisition no longer sends, groups, hashes, keys, diagnoses, or caches through corrupted retained thread IDs. Valid direct acquisition, cached direct acquisition, batch acquisition, duplicate thread-ID dedupe, cached duplicate post-list reuse, pagination, parser diagnostics, retry behavior, thread-site validation, mixed-site batch rejection, forum thread/category/post-revision workflows, and adjacent site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum thread reads, discussion migration ledgers, moderation summaries, duplicate post-list cache reuse, cached `ForumThread.posts` access, or local fixtures that construct, persist, mutate, or rehydrate `ForumThread` objects before post-list acquisition.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post-list acquisition as a practical workflow surface. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), [575-pr-validate-forum-post-list-thread-site.md](575-pr-validate-forum-post-list-thread-site.md), [584-pr-reject-mixed-site-forum-post-list-batches.md](584-pr-reject-mixed-site-forum-post-list-batches.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), and [673-pr-validate-forum-thread-collection-retained-id-state.md](673-pr-validate-forum-thread-collection-retained-id-state.md) establish post-list acquisition, retry behavior, duplicate/cached post-list reuse, parser diagnostics, exhausted-fetch diagnostics, response-body diagnostics, direct acquisition cache consistency, retained thread-site validation, mixed-site rejection, direct thread-ID validation, retained `_posts` cache ownership validation, and lookup-only retained-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issues 036, 059, 134, 141, and 228 cover retry, duplicate fetch reduction, cached post-list skip, cached duplicate reuse, and direct acquisition cache consistency, but they do not validate mutated retained `thread.id` values before cache maps, duplicate grouping, request payloads, result keys, or final cache assignment use them. Issues 160, 171, and 208 improve parser, exhausted-fetch, and response-body diagnostics after acquisition has started, not retained thread-ID validation before acquisition. Issue 575 validates retained `thread.site` before post-list acquisition, and Issue 584 rejects mixed-site post-list batches, but neither validates retained parent thread IDs. Issue 642 validates direct `ForumThread(id=...)` construction, but it cannot cover a valid thread whose `id` is corrupted after construction and then acquired. Issue 665 validates retained `ForumThread.id` when reading the `ForumThread._posts` property cache owner state, but it does not cover `ForumPostCollection.acquire_all_in_thread(s)` request and result keys. Issue 673 validates retained `ForumThread.id` during `ForumThreadCollection.find(id)` lookup only.

## Related Issue / Non-Duplicate Analysis

Builds directly on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), [575-pr-validate-forum-post-list-thread-site.md](575-pr-validate-forum-post-list-thread-site.md), [584-pr-reject-mixed-site-forum-post-list-batches.md](584-pr-reject-mixed-site-forum-post-list-batches.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), and [673-pr-validate-forum-thread-collection-retained-id-state.md](673-pr-validate-forum-thread-collection-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate direct retained `thread.id` before `ForumPostCollection.acquire_all_in_thread(thread)` performs the final result lookup or delegates to batch acquisition.
- Validate batch retained `thread.id` values once before `ForumPostCollection.acquire_all_in_threads(threads)` uses them for cached collection maps, duplicate grouping, result keys, first-page request payloads, exhausted-retry diagnostics, additional-page request payloads, pagination result extension, or final `_posts` cache assignment.
- Reject malformed retained IDs such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject negative retained IDs with `ValueError("thread_id must be non-negative")`.
- Preserve valid zero retained thread IDs for direct and batch post-list acquisition.
- Preserve cached direct acquisition, duplicate thread-ID dedupe, cached duplicate post-list reuse, pagination, parser diagnostics, retry behavior, retained thread-site validation, mixed-site batch rejection, and adjacent forum/site workflows.

## Type Of Change

- State validation
- Forum post-list acquisition hardening
- Retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.acquire_all_in_thread(thread)` must reject retained `thread.id` values such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before request construction or cache return. |
| R2 | `ForumPostCollection.acquire_all_in_threads(threads)` must reject retained `thread.id` values such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before cache maps, duplicate grouping, result keys, request construction, pagination extension, or cache assignment use them. |
| R3 | Both post-list acquisition paths must reject retained `thread.id=-1` with `ValueError("thread_id must be non-negative")` before acquisition uses it. |
| R4 | Valid retained thread ID `0` must remain accepted for direct and batch post-list acquisition and must produce request payloads with `"t": "0"`. |
| R5 | Cached direct acquisition, duplicate thread-ID dedupe, cached duplicate post-list reuse, pagination, parser diagnostics, retry behavior, retained thread-site validation, mixed-site batch rejection, and adjacent forum/site workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content. |
| R7 | Focused RED/GREEN, forum-post tests, adjacent forum/site workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct retained parent thread IDs fail before request construction or cache return. | `test_acquire_all_in_thread_rejects_malformed_retained_thread_ids_before_fetch` and `test_acquire_all_in_thread_rejects_malformed_cached_retained_thread_ids_before_cache_return` failed RED for six retained values, then passed GREEN after retained thread-ID validation was added. | Sending malformed IDs, returning a cached collection for an invalid ID, accepting booleans/floats, coercing values, raising response-body parser failures, raising raw `zip()` length failures, or calling AMC rejects this local completion claim. | Direct forum post-list acquisition | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Malformed batch retained parent thread IDs fail before cache maps, duplicate grouping, request construction, result keys, pagination extension, or cache assignment use them. | `test_acquire_all_in_threads_rejects_malformed_retained_thread_ids_before_fetch` failed RED for six retained values, then passed GREEN. | Sending malformed IDs, using malformed IDs as result keys, accepting booleans/floats, coercing values, raising unrelated `zip()` or unhashable errors, or calling AMC rejects this local completion claim. | Batch forum post-list acquisition | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Negative retained parent thread IDs fail with the existing non-negative diagnostic before acquisition uses them. | `test_acquire_all_in_thread_rejects_negative_retained_thread_id_before_fetch`, `test_acquire_all_in_thread_rejects_negative_cached_retained_thread_id_before_cache_return`, and `test_acquire_all_in_threads_rejects_negative_retained_thread_id_before_fetch` failed RED as wrong acquisition failures, then passed GREEN. | Treating negative retained IDs as request IDs, cache keys, result keys, or ordinary lookup misses rejects this local completion claim. | Forum post-list acquisition | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Valid zero retained parent thread IDs remain accepted for both acquisition modes. | `test_acquire_all_in_thread_accepts_zero_retained_thread_id` and `test_acquire_all_in_threads_accepts_zero_retained_thread_id` passed RED and GREEN. | Rejecting zero IDs or changing valid zero-ID request payloads rejects this local completion claim. | Forum post-list acquisition | `tests/unit/test_forum_post.py` |
| R5 | Existing forum post-list behavior and adjacent forum/site workflows remain green. | `tests/unit/test_forum_post.py` passed 227 tests, adjacent forum/site coverage passed 1102 tests, and full unit coverage passed 3308 tests. | Regressing cached direct acquisition, duplicate post-list dedupe, cached duplicate reuse, pagination, parser diagnostics, retry behavior, retained thread-site validation, mixed-site rejection, forum thread/category/post-revision behavior, or site behavior rejects this local completion claim. | Forum post-list workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private forum content, rendered forum HTML, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, full forum-post and adjacent tests passed, full unit passed, ruff passed, format check passed, mypy passed, temporary pyright passed, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `dd24cbe fix(forum_post): validate post-list acquisition thread ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_thread_accepts_zero_retained_thread_id tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_thread_rejects_malformed_retained_thread_ids_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_thread_rejects_negative_retained_thread_id_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_thread_rejects_malformed_cached_retained_thread_ids_before_cache_return tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_thread_rejects_negative_cached_retained_thread_id_before_cache_return tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_accepts_zero_retained_thread_id tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_malformed_retained_thread_ids_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_negative_retained_thread_id_before_fetch -q` failed 21 retained malformed/negative stored thread-ID cases while 2 zero-ID compatibility guards passed.
- GREEN: the same focused command passed 23 tests after post-list acquisition retained thread-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 227 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1102 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3308 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_thread(thread)` raises `ValueError("thread_id must be an integer")` when the stored thread's retained `thread.id` is `None`, `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- `ForumPostCollection.acquire_all_in_thread(thread)` raises the same malformed-ID diagnostic before returning an already cached `_posts` collection for an invalid retained thread ID.
- `ForumPostCollection.acquire_all_in_threads(threads)` raises `ValueError("thread_id must be an integer")` when any stored thread's retained `thread.id` is `None`, `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- Both post-list acquisition paths raise `ValueError("thread_id must be non-negative")` when a stored thread's retained `thread.id` is `-1`.
- Valid retained thread ID `0` still produces forum post-list request payloads with `"t": "0"`.
- Existing cached direct acquisition, duplicate thread-ID dedupe, cached duplicate post-list reuse, pagination, response-body diagnostics, parser diagnostics, retry behavior, retained thread-site validation, mixed-site batch rejection, forum thread/category/post-revision behavior, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated records with malformed retained IDs now fail before post-list acquisition. Mitigation: corrupted retained identity state should be corrected before request construction; deterministic diagnostics are preferable to invalid cache keys, unhashable failures, bool/float equality surprises, or malformed AMC payloads.
- Risk: Duplicate thread-ID dedupe or cached duplicate reuse could accidentally diverge if validation changes key handling. Mitigation: the implementation validates IDs once, preserves original thread order, and continues grouping/cache-copying by integer thread ID.
- Risk: Pagination could accidentally use raw retained IDs on additional pages after first-page validation. Mitigation: additional page requests carry the validated thread ID alongside the thread object, and existing pagination coverage remains green.
- Risk: Diagnostics could expose private forum context. Mitigation: the new diagnostics include only the field name and expected/range constraint, and exhausted-fetch diagnostics continue using existing site/thread/page context without forum post text, rendered HTML, account details, or private thread content.

## Dependencies

- Existing `_validate_thread_id(...)` remains the canonical forum thread ID validator through `_validate_forum_thread_id(...)`.
- Existing `ForumThread(id=...)` constructor validation remains unchanged.
- Existing forum post-list parser, response-body diagnostics, retry plumbing, cached duplicate reuse, pagination, retained thread-site validation, and mixed-site rejection remain unchanged.
- Existing forum thread/category/post-revision and site workflows remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered forum post-list acquisition boundary.

## Upstream-Safe Motivation

Forum post-list acquisition uses retained parent thread IDs for cache reuse, duplicate grouping, request payload construction, result maps, pagination, and cache assignment. Those retained IDs should satisfy the same integer/non-negative contract as directly constructed threads before they leave local state. Validating stored fields prevents corrupted local state from becoming invalid request IDs or incidental cache keys, while preserving valid zero IDs, cached direct acquisition, duplicate post-list dedupe, cached duplicate reuse, pagination, retry behavior, parser diagnostics, and all forum/site behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post-list acquisition as a practical workflow through forum thread reads, retry-aware fetches, duplicate fetch reduction, cached direct acquisition, cached duplicate reuse, response diagnostics, pagination, and generated forum-history ledgers.
- Existing local drafts covered forum post-list acquisition reliability, dedupe, cached reuse, direct acquisition cache consistency, parser diagnostics, retry/failure context, response diagnostics, retained thread-site validation, mixed-site rejection, direct constructor identity validation, retained `_posts` cache owner validation, and collection lookup retained-ID validation; they did not validate retained stored `ForumThread.id` before post-list acquisition cache grouping or request construction.
- The focused RED failure showed malformed retained IDs could reach acquisition internals as raw `zip()` length failures or unhashable key errors instead of deterministic thread-ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, cached invalid direct acquisition, zero-ID compatibility, direct acquisition, batch acquisition, adjacent forum/site workflows, and full unit compatibility.
- This slice only validates retained stored parent thread IDs at the post-list acquisition boundary. It does not change parser field extraction, forum post source/edit behavior, forum post revision acquisition internals, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered forum HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained thread IDs once in batch acquisition and then reuses those validated integer IDs for cache lookup, duplicate grouping, request payloads, result keys, pagination response handling, diagnostics, and cache assignment. The direct acquisition wrapper validates before using the final result key as well. This keeps the change local to the post-list acquisition boundary while preserving the existing public API surface.
