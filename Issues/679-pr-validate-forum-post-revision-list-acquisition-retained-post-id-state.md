# PR Draft: Validate ForumPostRevision List Acquisition Retained Post IDs

## Summary

`ForumPostRevisionCollection.acquire_all(post)` and `ForumPostRevisionCollection.acquire_all_for_posts(posts, ...)` already reject non-`ForumPost` inputs, validate retained thread/site ownership before network fetches, deduplicate duplicate post IDs, skip cached revision lists, reuse cached duplicate revision lists, and validate direct `ForumPost(id=...)` construction. The revision-list acquisition paths still used retained `post.id` values directly for cache maps, duplicate grouping, request payload construction, response result keys, exhausted-retry diagnostics, and cache assignment. If a valid `ForumPost` is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, strings, floats, booleans, negative integers, or unhashable values can reach cache grouping or AMC payload construction instead of producing the same deterministic post-ID diagnostics used elsewhere.

This change validates each retained `ForumPost.id` with the existing forum-post ID validator before forum post revision-list acquisition uses it. Malformed retained IDs now raise `ValueError("id must be an integer")`, negative retained IDs now raise `ValueError("id must be non-negative")`, valid zero post IDs remain accepted, cached and duplicate revision-list behavior is preserved, and revision-list requests are still batched by valid post ID.

## Outcome

Forum post revision-list acquisition no longer sends, groups, hashes, keys, or caches through corrupted retained post IDs. Valid direct acquisition, cached direct acquisition, batch acquisition, duplicate post-ID dedupe, cached duplicate reuse, optional `with_html=True` follow-up HTML acquisition, parser diagnostics, retry behavior, forum post/thread/category workflows, and adjacent site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, moderation summaries, duplicate revision-list cache reuse, cached `with_html=True` revision acquisition, or local fixtures that construct, persist, mutate, or rehydrate `ForumPost` objects before revision-list acquisition.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision-list acquisition as a practical workflow surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md), [672-pr-validate-forum-post-collection-retained-id-state.md](672-pr-validate-forum-post-collection-retained-id-state.md), and [678-pr-validate-forum-post-revision-html-acquisition-retained-id-state.md](678-pr-validate-forum-post-revision-html-acquisition-retained-id-state.md) establish revision-list acquisition, retry behavior, duplicate/cached revision-list reuse, response diagnostics, input object validation, retained thread/site validation, direct post-ID validation, retained cache owner validation, lookup-only retained-ID validation, and revision HTML retained-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issues 056, 135, 142, 143, and 229 cover duplicate and cached revision-list behavior, but they do not validate mutated retained `post.id` values before cache maps, duplicate grouping, request payloads, or result keys use them. Issue 364 validates that the supplied object is a `ForumPost`, not that its retained ID remains valid after construction. Issues 580 and 583 validate retained thread/site state before revision-list acquisition, not retained parent post IDs. Issue 641 validates direct `ForumPost(id=...)` construction, but it cannot cover a valid post whose `id` is corrupted after construction and then acquired. Issues 666 and 667 validate retained cache-owner state around `post.revisions` and revision collection ownership, but they do not cover revision-list acquisition request keys. Issue 672 validates retained `ForumPost.id` during `ForumPostCollection.find(id)` lookup only. Issue 678 validates retained `ForumPostRevision.id` before HTML acquisition, not retained parent `ForumPost.id` before revision-list acquisition.

## Related Issue / Non-Duplicate Analysis

Builds directly on [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md), [641-pr-validate-non-negative-forum-post-ids.md](641-pr-validate-non-negative-forum-post-ids.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md), [672-pr-validate-forum-post-collection-retained-id-state.md](672-pr-validate-forum-post-collection-retained-id-state.md), and [678-pr-validate-forum-post-revision-html-acquisition-retained-id-state.md](678-pr-validate-forum-post-revision-html-acquisition-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate direct retained `post.id` before `ForumPostRevisionCollection.acquire_all(post)` checks the direct `_revisions` cache, constructs request payloads, or formats exhausted-retry diagnostics.
- Validate batch retained `post.id` values once before `ForumPostRevisionCollection.acquire_all_for_posts(posts, ...)` uses them for cached collection maps, duplicate grouping, result keys, request payloads, response fan-out, or cache assignment.
- Reject malformed retained IDs such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained IDs with `ValueError("id must be non-negative")`.
- Preserve valid zero retained post IDs for direct and batch revision-list acquisition.
- Preserve cached direct acquisition, duplicate post-ID dedupe, cached duplicate revision-list reuse, optional `with_html=True` HTML acquisition, parser diagnostics, retry behavior, retained thread/site validation, and adjacent forum/site workflows.

## Type Of Change

- State validation
- Forum post revision-list acquisition hardening
- Retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.acquire_all(post)` must reject retained `post.id` values such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")` before request construction or cache return. |
| R2 | `ForumPostRevisionCollection.acquire_all_for_posts(posts, ...)` must reject retained `post.id` values such as `None`, `True`, `False`, `"5001"`, `5001.0`, and `[]` with `ValueError("id must be an integer")` before cache maps, duplicate grouping, result keys, request construction, or cache assignment use them. |
| R3 | Both revision-list acquisition paths must reject retained `post.id=-1` with `ValueError("id must be non-negative")` before acquisition uses it. |
| R4 | Valid retained post ID `0` must remain accepted for direct and batch revision-list acquisition and must produce request payloads with `"postId": 0`. |
| R5 | Cached direct acquisition, duplicate post-ID dedupe, cached duplicate revision-list reuse, valid `with_html=True` HTML acquisition, parser diagnostics, retry behavior, retained thread/site validation, and adjacent forum/site workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered revision HTML, or private forum content. |
| R7 | Focused RED/GREEN, forum-post-revision tests, adjacent forum/site workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct retained parent post IDs fail before request construction or cache return. | `test_acquire_all_rejects_malformed_retained_post_ids_before_fetch` failed RED for six retained values, then passed GREEN after retained post-ID validation was added. | Sending malformed IDs, returning a cached collection for an invalid ID, accepting booleans/floats, coercing values, raising response-body parser failures, or calling AMC rejects this local completion claim. | Direct forum post revision-list acquisition | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Malformed batch retained parent post IDs fail before cache maps, duplicate grouping, request construction, result keys, or cache assignment use them. | `test_acquire_all_for_posts_rejects_malformed_retained_post_ids_before_fetch` failed RED for six retained values, then passed GREEN. | Sending malformed IDs, using malformed IDs as result keys, accepting booleans/floats, coercing values, raising unrelated `zip()` or unhashable errors, or calling AMC rejects this local completion claim. | Batch forum post revision-list acquisition | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Negative retained parent post IDs fail with the existing non-negative diagnostic before acquisition uses them. | `test_acquire_all_rejects_negative_retained_post_id_before_fetch` and `test_acquire_all_for_posts_rejects_negative_retained_post_id_before_fetch` failed RED as wrong acquisition failures, then passed GREEN. | Treating negative retained IDs as request IDs, cache keys, result keys, or ordinary lookup misses rejects this local completion claim. | Forum post revision-list acquisition | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Valid zero retained parent post IDs remain accepted for both acquisition modes. | `test_acquire_all_accepts_zero_retained_post_id` and `test_acquire_all_for_posts_accepts_zero_retained_post_id` passed RED and GREEN. | Rejecting zero IDs or changing valid zero-ID request payloads rejects this local completion claim. | Forum post revision-list acquisition | `tests/unit/test_forum_post_revision.py` |
| R5 | Existing forum post revision behavior and adjacent forum/site workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 219 tests, adjacent forum/site coverage passed 1079 tests, and full unit coverage passed 3285 tests. | Regressing cached direct acquisition, duplicate revision-list dedupe, cached duplicate reuse, `with_html=True` follow-up acquisition, parser diagnostics, retry behavior, retained thread/site validation, forum post/thread/category behavior, or site behavior rejects this local completion claim. | Forum post revision workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private forum content, rendered revision HTML, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, full forum-post-revision and adjacent tests passed, full unit passed, ruff passed, format check passed, mypy passed, temporary pyright passed, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f4ea207 fix(forum_post_revision): validate list acquisition post ids`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_accepts_zero_retained_post_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_malformed_retained_post_ids_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_negative_retained_post_id_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_accepts_zero_retained_post_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_malformed_retained_post_ids_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_negative_retained_post_id_before_fetch -q` failed 14 retained malformed/negative stored post-ID cases while 2 zero-ID compatibility guards passed.
- GREEN: the same focused command passed 16 tests after revision-list acquisition retained post-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 219 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_site.py -q` passed 1079 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3285 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(post)` raises `ValueError("id must be an integer")` when the stored post's retained `post.id` is `None`, `True`, `False`, `"5001"`, `5001.0`, or `[]`.
- `ForumPostRevisionCollection.acquire_all_for_posts(posts, ...)` raises `ValueError("id must be an integer")` when any stored post's retained `post.id` is `None`, `True`, `False`, `"5001"`, `5001.0`, or `[]`.
- Both revision-list acquisition paths raise `ValueError("id must be non-negative")` when a stored post's retained `post.id` is `-1`.
- Valid retained post ID `0` still produces forum post revision-list request payloads with `"postId": 0`.
- Existing cached direct acquisition, duplicate post-ID dedupe, cached duplicate revision-list reuse, response-body diagnostics, parser diagnostics, retry behavior, retained thread/site validation, optional `with_html=True` HTML acquisition, forum post/thread/category behavior, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered revision HTML, or private forum content.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated records with malformed retained IDs now fail before revision-list acquisition. Mitigation: corrupted retained identity state should be corrected before request construction; deterministic diagnostics are preferable to invalid cache keys, unhashable failures, bool/float equality surprises, or malformed AMC payloads.
- Risk: Duplicate post-ID dedupe or cached duplicate reuse could accidentally diverge if validation changes key handling. Mitigation: the implementation validates IDs once, preserves original post order, and continues grouping/cache-copying by integer post ID.
- Risk: Diagnostics could expose private forum context. Mitigation: the new diagnostics include only the field name and expected/range constraint, not forum post text, rendered HTML, site names, account details, or private thread content.

## Dependencies

- Existing `_validate_post_id(...)` remains the canonical forum post ID validator through `_validate_forum_post_id(...)`.
- Existing `ForumPost(id=...)` constructor validation remains unchanged.
- Existing forum post revision-list parser, response-body diagnostics, retry plumbing, cached duplicate reuse, and optional `with_html=True` follow-up acquisition remain unchanged.
- Existing retained thread/site validation remains unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered forum post revision-list acquisition boundary.

## Upstream-Safe Motivation

Forum post revision-list acquisition uses retained parent post IDs for cache reuse, duplicate grouping, request payload construction, result maps, and cache assignment. Those retained IDs should satisfy the same integer/non-negative contract as directly constructed posts before they leave local state. Validating stored fields prevents corrupted local state from becoming invalid request IDs or incidental cache keys, while preserving valid zero IDs, cached direct acquisition, duplicate revision-list dedupe, cached duplicate reuse, retry behavior, parser diagnostics, and all forum/site behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post revision-list acquisition as a practical workflow through forum edit-history reads, retry-aware fetches, duplicate fetch reduction, cached direct acquisition, cached duplicate reuse, response diagnostics, optional `with_html=True` follow-up HTML acquisition, and generated forum-history ledgers.
- Existing local drafts covered forum post revision acquisition reliability, dedupe, cached reuse, direct object-shape validation, retry/failure context, response diagnostics, direct constructor identity validation, retained thread/site validation, retained cache owner validation, collection lookup retained-ID validation, and revision HTML retained-ID validation; they did not validate retained stored `ForumPost.id` before revision-list acquisition cache grouping or request construction.
- The focused RED failure showed malformed retained IDs could reach acquisition internals as response-body parser failures, raw `zip()` length failures, or unhashable key errors instead of deterministic post-ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, direct acquisition, batch acquisition, adjacent forum/site workflows, and full unit compatibility.
- This slice only validates retained stored parent post IDs at the revision-list acquisition boundary. It does not change parser field extraction, revision HTML acquisition internals, forum post source/edit behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered revision HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained post IDs once in each acquisition path and then reuses those validated integer IDs for cache lookup, duplicate grouping, request payloads, result keys, response handling, and cache assignment. This keeps the change local to the revision-list acquisition boundary while preserving the existing public API surface.
