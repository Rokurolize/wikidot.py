# PR Draft: Validate Forum Post Source Acquisition Retained IDs

## Summary

`ForumPostCollection.get_post_sources()` already rejects non-post entries, rejects posts from another thread, retries source-form fetches, deduplicates duplicate post IDs, reuses cached duplicate sources, validates direct `ForumPost(id=...)` and `ForumThread(id=...)` construction, and preserves valid cached source text. The source acquisition path still used retained `post.id` and parent `thread.id` values directly for cached-source maps, duplicate grouping, edit-form request payloads, response-body diagnostics, source-textarea diagnostics, and final source assignment. If a valid post or thread is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, strings, floats, booleans, negative integers, or unhashable values can reach source acquisition internals instead of producing the same deterministic ID diagnostics used elsewhere.

This change validates retained source-acquisition IDs before they are used. Malformed retained post IDs now raise `ValueError("id must be an integer")`, negative retained post IDs raise `ValueError("id must be non-negative")`, malformed retained thread IDs raise `ValueError("thread_id must be an integer")`, negative retained thread IDs raise `ValueError("thread_id must be non-negative")`, valid zero post/thread IDs remain accepted, cached-source fast paths remain guarded before cache return, and successful source acquisition still uses the existing retry, dedupe, cache-reuse, and parsing behavior.

## Outcome

Forum post source acquisition no longer groups, hashes, requests, diagnoses, or assigns source text through corrupted retained post or thread IDs. Valid source fetching, cached-source skipping, cached duplicate source reuse, duplicate request dedupe, lazy `ForumPost.source`, source response diagnostics, source textarea scoping, forum post-list acquisition, forum post revision acquisition, edit/reply workflows, and adjacent site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum source inspection, moderation ledgers, migration fixtures, duplicate source-cache reuse, local tests, or serialized and rehydrated `ForumPost` / `ForumPostCollection` records before calling `get_post_sources()` or lazy `ForumPost.source`.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post source acquisition as a practical workflow surface. Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), [672-pr-validate-forum-post-collection-retained-id-state.md](672-pr-validate-forum-post-collection-retained-id-state.md), and [680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md](680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md) establish source acquisition retry behavior, duplicate request reduction, cached duplicate reuse, source diagnostics, direct post/thread ID validation, retained cache ownership validation, lookup-only retained post-ID validation, and post-list acquisition retained thread-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issues 043, 055, and 125 cover retry, duplicate source request reduction, and cached duplicate source reuse, but they do not validate mutated retained `post.id` or `thread.id` before source-cache maps, duplicate groups, edit-form payloads, diagnostics, or source assignment use them. Issues 161, 175, and 209 improve diagnostics after source acquisition has started, not retained ID validation before acquisition. Issues 641 and 642 validate direct post/thread construction, but they cannot cover valid objects whose IDs are corrupted after construction and then acquired. Issue 665 validates retained thread IDs at the `ForumThread._posts` cache boundary, Issue 672 validates retained post IDs during collection lookup, and Issue 680 validates retained thread IDs during post-list acquisition; none covers the forum post source-acquisition request/cache boundary.

## Related Issue / Non-Duplicate Analysis

Builds directly on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md](665-pr-validate-forum-thread-posts-cache-retained-thread-id-state.md), [672-pr-validate-forum-post-collection-retained-id-state.md](672-pr-validate-forum-post-collection-retained-id-state.md), and [680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md](680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained parent `thread.id` before source acquisition can return already cached source state or construct `forum/sub/ForumEditPostFormModule` requests.
- Validate each retained `post.id` before building cached-source maps, duplicate-source groups, edit-form request payloads, response-body diagnostics, source-textarea diagnostics, or source assignment maps.
- Reuse the validated integer thread ID and post IDs for edit-form request payloads and diagnostics.
- Reject malformed retained post IDs such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained post IDs with `ValueError("id must be non-negative")`.
- Reject malformed retained thread IDs such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")`.
- Reject negative retained thread IDs with `ValueError("thread_id must be non-negative")`.
- Preserve valid zero retained post/thread IDs for source acquisition request payloads.
- Preserve cached-source skipping, duplicate post-ID dedupe, cached duplicate source reuse, retry behavior, failed-response skip behavior, source textarea scoping, lazy `ForumPost.source`, and adjacent forum/site workflows.

## Type Of Change

- State validation
- Forum post source-acquisition hardening
- Retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.get_post_sources()` must reject retained `post.id` values such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")` before source request construction or cached-source return. |
| R2 | The same path must reject retained `post.id=-1` with `ValueError("id must be non-negative")` before acquisition uses it. |
| R3 | The same path must reject retained parent `thread.id` values such as `None`, `True`, `False`, `"3001"`, `3001.0`, and `[]` with `ValueError("thread_id must be an integer")` before source request construction or cached-source return. |
| R4 | The same path must reject retained parent `thread.id=-1` with `ValueError("thread_id must be non-negative")` before acquisition uses it. |
| R5 | Valid retained post ID `0` and retained thread ID `0` must remain accepted and must produce source edit-form request payloads with `"postId": 0` and `"threadId": 0`. |
| R6 | Cached-source skipping, duplicate post-ID dedupe, cached duplicate source reuse, retry behavior, failed-response skip behavior, response-body diagnostics, source textarea scoping, lazy `ForumPost.source`, source property failure behavior, post-list acquisition, revision acquisition, edit/reply workflows, and adjacent forum/site workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content. |
| R8 | Focused RED/GREEN, forum-post tests, adjacent forum/site workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained post IDs fail before source request construction or cached-source return. | `test_get_post_sources_rejects_malformed_retained_post_ids_before_fetch` and `test_get_post_sources_rejects_malformed_cached_retained_post_ids_before_cache_return` failed RED for six retained values, then passed GREEN after retained post-ID validation was added. | Sending malformed post IDs, using them as cache keys, accepting booleans/floats, coercing values, raising `zip()` length failures, raising unhashable-key errors, or silently returning cached source rejects this local completion claim. | Forum post source acquisition | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Negative retained post IDs fail with the existing non-negative diagnostic before acquisition uses them. | `test_get_post_sources_rejects_negative_retained_post_id_before_fetch` and `test_get_post_sources_rejects_negative_cached_retained_post_id_before_cache_return` failed RED as wrong acquisition or cache-return behavior, then passed GREEN. | Treating negative retained post IDs as request IDs, cache keys, duplicate groups, or valid cached rows rejects this local completion claim. | Forum post source acquisition | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Malformed retained parent thread IDs fail before source request construction or cached-source return. | `test_get_post_sources_rejects_malformed_retained_thread_ids_before_fetch` and `test_get_post_sources_rejects_malformed_cached_retained_thread_ids_before_cache_return` failed RED for six retained values, then passed GREEN after retained thread-ID validation was added. | Sending malformed thread IDs, accepting booleans/floats, coercing values, raising `zip()` length failures, or silently returning cached source rejects this local completion claim. | Forum post source acquisition parent thread | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Negative retained parent thread IDs fail with the existing non-negative diagnostic before acquisition uses them. | `test_get_post_sources_rejects_negative_retained_thread_id_before_fetch` and `test_get_post_sources_rejects_negative_cached_retained_thread_id_before_cache_return` failed RED as wrong acquisition or cache-return behavior, then passed GREEN. | Treating negative retained thread IDs as request IDs, valid ownership, or valid cached-source rows rejects this local completion claim. | Forum post source acquisition parent thread | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R5 | Valid zero retained post/thread IDs remain accepted for source acquisition. | `test_get_post_sources_accepts_zero_retained_post_and_thread_ids` passed RED and GREEN, asserting the request payload uses `"threadId": 0` and `"postId": 0`. | Rejecting zero IDs or changing valid zero-ID source request payloads rejects this local completion claim. | Forum post source acquisition payload | `tests/unit/test_forum_post.py` |
| R6 | Existing source behavior and adjacent forum/site workflows remain green. | Source/property coverage passed 50 tests, `tests/unit/test_forum_post.py` passed 256 tests, adjacent forum/site coverage passed 1146 tests, and full unit coverage passed 3352 tests. | Regressing cached-source skipping, duplicate post-ID dedupe, cached duplicate source reuse, retry behavior, failed-response skip behavior, source response diagnostics, source textarea scoping, lazy `ForumPost.source`, post-list acquisition, revision acquisition, edit/reply behavior, forum category/thread/revision behavior, site behavior, or any unit test rejects this local completion claim. | Forum post source and adjacent workflows | `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private forum content, rendered forum HTML, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, full forum-post and adjacent tests, full unit, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c1847af fix(forum_post): validate source acquisition ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources -k retained -q` selected 29 retained source-acquisition tests; 28 malformed/negative retained-ID cases failed before the fix while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 29 tests after retained source-acquisition ID validation was added.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources tests/unit/test_forum_post.py::TestForumPostSource -q` passed 50 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 256 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1146 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3352 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPostCollection.get_post_sources()` raises `ValueError("id must be an integer")` when a stored post's retained `post.id` is `None`, `True`, `False`, `"5001"`, `5001.0`, or `[]`.
- The same method raises the same malformed-ID diagnostic before returning already cached source for an invalid retained post ID.
- The same method raises `ValueError("id must be non-negative")` when a stored post's retained `post.id` is `-1`.
- The same method raises `ValueError("thread_id must be an integer")` when the parent thread's retained `thread.id` is `None`, `True`, `False`, `"3001"`, `3001.0`, or `[]`.
- The same method raises the same malformed-thread-ID diagnostic before returning already cached source for an invalid retained thread ID.
- The same method raises `ValueError("thread_id must be non-negative")` when the parent thread's retained `thread.id` is `-1`.
- Valid retained post ID `0` and retained thread ID `0` still produce source edit-form request payloads with `"postId": 0` and `"threadId": 0`.
- Existing cached-source skipping, duplicate post-ID dedupe, cached duplicate source reuse, retry behavior, failed-response skip behavior, response-body diagnostics, source textarea scoping, lazy `ForumPost.source`, post-list acquisition, revision acquisition, edit/reply behavior, and adjacent forum/site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated posts or parent threads with malformed retained IDs now fail before source acquisition. Mitigation: corrupted retained identity state should be corrected before request construction; deterministic diagnostics are preferable to invalid cache keys, bool/float equality surprises, unhashable-key failures, zip-length failures, malformed AMC payloads, or silent cached-source returns.
- Risk: Duplicate source dedupe or cached duplicate source reuse could accidentally diverge if validation changes key handling. Mitigation: the implementation validates IDs once, preserves first-seen request order, and continues grouping/cache-copying by integer post ID.
- Risk: Diagnostics could expose private forum context. Mitigation: the new diagnostics include only the field name and expected/range constraint, and existing source response diagnostics continue using site/post context without forum source text, rendered HTML, account details, or private thread content.

## Dependencies

- Existing `_validate_post_id(...)` remains the canonical forum post ID validator.
- Existing `_validate_forum_thread_id(...)` remains the canonical forum thread ID validator.
- Existing `ForumPost(id=...)` and `ForumThread(id=...)` constructor validation remains unchanged.
- Existing source response-body diagnostics, source textarea scoping, retry plumbing, cached duplicate source reuse, duplicate source request dedupe, lazy `ForumPost.source`, edit behavior, reply behavior, forum post-list acquisition, and forum post-revision acquisition remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered forum post source-acquisition boundary.

## Upstream-Safe Motivation

Forum post source acquisition uses retained parent thread IDs and retained post IDs for cache reuse, duplicate grouping, edit-form request payloads, diagnostics, and source assignment. Those retained IDs should satisfy the same integer/non-negative contract as directly constructed posts and threads before they leave local state. Validating stored fields prevents corrupted local state from becoming invalid request IDs or incidental cache keys, while preserving valid zero IDs, retry behavior, cached-source semantics, duplicate-source dedupe, parser diagnostics, and all forum/site behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post source acquisition as a practical workflow through forum source inspection, retry-aware fetches, duplicate request reduction, cached duplicate reuse, response diagnostics, and generated forum-history ledgers.
- Existing local drafts covered source acquisition reliability, duplicate source request reduction, cached duplicate source reuse, source response diagnostics, source form parsing diagnostics, direct constructor identity validation, retained thread-post cache owner validation, retained post collection lookup validation, and post-list acquisition retained thread-ID validation; they did not validate retained stored `ForumPost.id` or source-acquisition parent `ForumThread.id` before source acquisition cache maps or request construction.
- The focused RED failure showed malformed retained IDs could reach acquisition internals as `zip()` length failures, unhashable-key failures, malformed request payloads, or silent cached-source returns instead of deterministic ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, cached invalid source state, zero-ID compatibility, source property behavior, adjacent forum/site workflows, and full unit compatibility.
- This slice only validates retained stored IDs at the forum post source-acquisition boundary. It does not change parser field extraction, source text contents, edit-form save behavior, forum post-list acquisition internals, forum post revision acquisition internals, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered forum HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained IDs once at source acquisition entry and then reuses those validated integers for cached-source maps, duplicate grouping, request payloads, diagnostics, and source assignment. The validation happens before cached-source fast paths so corrupted retained identity cannot silently return cached data. This keeps the change local to the source-acquisition boundary while preserving the existing public API surface.
