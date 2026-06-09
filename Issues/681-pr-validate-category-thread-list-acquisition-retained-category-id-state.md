# PR Draft: Validate Category Thread-List Acquisition Retained Category IDs

## Summary

`ForumThreadCollection.acquire_all_in_category(category)` already rejects non-`ForumCategory` inputs, retries category thread-list requests, skips an already cached `category._threads` collection, stores successful direct acquisitions back into the category cache, validates direct `ForumCategory(id=...)` construction, and validates `ForumCategory._threads` cache ownership. The acquisition method still used retained `category.id` directly before cache return, first-page request construction, additional-page request construction, exhausted-retry diagnostics, response-body diagnostics, parser context, and final cache assignment. If a valid `ForumCategory` is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, strings, floats, booleans, negative integers, or unhashable values can reach the cache fast path or AMC payload construction instead of producing the same deterministic category-ID diagnostics used elsewhere.

This change validates the retained `ForumCategory.id` with the existing forum-category ID validator before category thread-list acquisition uses it. Malformed retained IDs now raise `ValueError("id must be an integer")`, negative retained IDs now raise `ValueError("id must be non-negative")`, valid zero category IDs remain accepted, cached direct acquisition remains guarded before cache return, first-page and additional-page requests use the validated category ID, and existing category thread-list parsing, pagination, retry, and cache behavior remain unchanged.

## Outcome

Category thread-list acquisition no longer sends, diagnoses, paginates, or returns cached data through corrupted retained category IDs. Valid direct acquisition, cached direct acquisition, lazy `category.threads`, `reload_threads()`, zero-ID compatibility, pagination, parser diagnostics, retry behavior, category thread-cache ownership validation, forum post-list acquisition, forum post-revision acquisition, and adjacent site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category indexes, generated discussion migration ledgers, moderation summaries, cached category thread lists, or local fixtures that construct, persist, mutate, or rehydrate `ForumCategory` objects before thread-list acquisition.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread-list acquisition as a practical workflow surface. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md), [668-pr-validate-forum-category-threads-cache-retained-category-id-state.md](668-pr-validate-forum-category-threads-cache-retained-category-id-state.md), and [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md) establish category thread-list retry behavior, cached skip behavior, parser diagnostics, exhausted-fetch diagnostics, direct acquisition cache consistency, direct category-ID validation, retained `_threads` cache ownership validation, and lookup-only retained-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issues 034, 136, and 227 cover retry, cached skip, and direct acquisition cache consistency, but they do not validate mutated retained `category.id` values before the cache fast path, first-page request payload, additional-page payloads, or exhausted-retry diagnostics use them. Issues 169 and 211 improve diagnostics after acquisition has started, not retained category-ID validation before acquisition. Issue 644 validates direct `ForumCategory(id=...)` construction, but it cannot cover a valid category whose `id` is corrupted after construction and then acquired. Issue 668 validates retained category IDs during `_threads` cache ownership checks, but it does not cover `ForumThreadCollection.acquire_all_in_category(category)` acquisition request and cache-return boundaries. Issue 670 validates retained category IDs during `ForumCategoryCollection.find(id)` lookup only.

## Related Issue / Non-Duplicate Analysis

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md), [668-pr-validate-forum-category-threads-cache-retained-category-id-state.md](668-pr-validate-forum-category-threads-cache-retained-category-id-state.md), and [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `category.id` before `ForumThreadCollection.acquire_all_in_category(category)` can return a cached `_threads` collection.
- Reuse the validated category ID for first-page and additional-page `forum/ForumViewCategoryModule` request payloads.
- Reuse the validated category ID in exhausted first-page and additional-page retry diagnostics.
- Reject malformed retained IDs such as `None`, `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained IDs with `ValueError("id must be non-negative")`.
- Preserve valid zero retained category IDs for paginated category thread-list acquisition.
- Preserve cached direct acquisition, lazy `category.threads`, `reload_threads()`, pagination, parser diagnostics, response-body diagnostics, retry behavior, category thread-cache ownership validation, and adjacent forum/site workflows.

## Type Of Change

- State validation
- Category thread-list acquisition hardening
- Retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection.acquire_all_in_category(category)` must reject retained `category.id` values such as `None`, `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")` before request construction or cache return. |
| R2 | The same acquisition path must reject retained `category.id=-1` with `ValueError("id must be non-negative")` before acquisition uses it. |
| R3 | Valid retained category ID `0` must remain accepted for first-page and additional-page category thread-list acquisition and must produce request payloads with `"c": 0`. |
| R4 | Cached direct acquisition, lazy `category.threads`, `reload_threads()`, pagination, parser diagnostics, response-body diagnostics, retry behavior, category thread-cache ownership validation, and adjacent forum/site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content. |
| R6 | Focused RED/GREEN, forum-thread tests, adjacent forum/site workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained parent category IDs fail before request construction or cache return. | `test_acquire_all_rejects_malformed_retained_category_ids_before_fetch` and `test_acquire_all_rejects_malformed_cached_retained_category_ids_before_cache_return` failed RED for six retained values, then passed GREEN after retained category-ID validation was added. | Sending malformed IDs, returning a cached collection for an invalid ID, accepting booleans/floats, coercing values, raising response-body parser failures, or calling AMC rejects this local completion claim. | Category thread-list acquisition | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Negative retained parent category IDs fail with the existing non-negative diagnostic before acquisition uses them. | `test_acquire_all_rejects_negative_retained_category_id_before_fetch` and `test_acquire_all_rejects_negative_cached_retained_category_id_before_cache_return` failed RED as wrong acquisition or cache-return behavior, then passed GREEN. | Treating negative retained IDs as request IDs, cache-return identities, or ordinary fetch failures rejects this local completion claim. | Category thread-list acquisition | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Valid zero retained parent category IDs remain accepted for first and additional pages. | `test_acquire_all_accepts_zero_retained_category_id` passed RED and GREEN, asserting both first-page and page-2 request payloads use `"c": 0`. | Rejecting zero IDs or changing valid zero-ID request payloads rejects this local completion claim. | Category thread-list acquisition | `tests/unit/test_forum_thread.py` |
| R4 | Existing category thread-list behavior and adjacent forum/site workflows remain green. | `tests/unit/test_forum_thread.py` passed 203 tests, adjacent forum/site coverage passed 1117 tests, and full unit coverage passed 3323 tests. | Regressing cached direct acquisition, lazy `category.threads`, reload semantics, pagination, parser diagnostics, response-body diagnostics, retry behavior, cache ownership validation, forum post/post-revision behavior, or site behavior rejects this local completion claim. | Forum category/thread workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private forum content, rendered forum HTML, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, full forum-thread and adjacent tests passed, full unit passed, ruff passed, format check passed, mypy passed, temporary pyright passed, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4c0c8cf fix(forum_thread): validate category thread-list acquisition ids`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_accepts_zero_retained_category_id tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_malformed_retained_category_ids_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_negative_retained_category_id_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_malformed_cached_retained_category_ids_before_cache_return tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_negative_cached_retained_category_id_before_cache_return -q` failed 14 retained malformed/negative stored category-ID acquisition cases while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 15 tests after category thread-list acquisition retained category-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 203 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1117 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3323 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(category)` raises `ValueError("id must be an integer")` when the stored category's retained `category.id` is `None`, `True`, `False`, `"1001"`, `1001.0`, or `[]`.
- The same method raises the same malformed-ID diagnostic before returning an already cached `_threads` collection for an invalid retained category ID.
- The same method raises `ValueError("id must be non-negative")` when a stored category's retained `category.id` is `-1`.
- Valid retained category ID `0` still produces first-page and additional-page category thread-list request payloads with `"c": 0`.
- Existing cached direct acquisition, lazy `category.threads`, `reload_threads()`, pagination, response-body diagnostics, parser diagnostics, retry behavior, category thread-cache ownership validation, forum post/post-revision behavior, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered forum HTML, or private forum content.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated categories with malformed retained IDs now fail before category thread-list acquisition. Mitigation: corrupted retained identity state should be corrected before request construction; deterministic diagnostics are preferable to invalid cache returns, bool/float equality surprises, or malformed AMC payloads.
- Risk: Pagination could accidentally use raw retained IDs after first-page validation. Mitigation: additional page requests reuse the validated category ID, and the zero-ID compatibility test asserts both first and additional request payloads.
- Risk: Diagnostics could expose private forum context. Mitigation: the new diagnostics include only the field name and expected/range constraint, and exhausted-fetch diagnostics continue using existing site/category/page context without forum post text, rendered HTML, account details, or private thread content.

## Dependencies

- Existing `_validate_forum_category_id(...)` remains the canonical forum category ID validator.
- Existing `ForumCategory(id=...)` constructor validation remains unchanged.
- Existing category thread-list parser, response-body diagnostics, retry plumbing, cached direct acquisition, pagination, lazy `category.threads`, `reload_threads()`, and category thread-cache ownership validation remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered category thread-list acquisition boundary.

## Upstream-Safe Motivation

Category thread-list acquisition uses retained category IDs for cache fast paths, request payload construction, pagination, and exhausted-fetch diagnostics. Those retained IDs should satisfy the same integer/non-negative contract as directly constructed categories before they leave local state. Validating stored fields prevents corrupted local state from becoming invalid request IDs or accidental cache-return identities, while preserving valid zero IDs, cached direct acquisition, pagination, retry behavior, parser diagnostics, and all forum/site behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established category thread-list acquisition as a practical workflow through forum category indexes, retry-aware fetches, cached direct acquisition, response diagnostics, pagination, and generated forum-history ledgers.
- Existing local drafts covered category thread-list acquisition reliability, cached skip behavior, direct acquisition cache consistency, parser diagnostics, retry/failure context, response diagnostics, direct constructor identity validation, retained `_threads` cache owner validation, and collection lookup retained-ID validation; they did not validate retained stored `ForumCategory.id` before acquisition cache return or request construction.
- The focused RED failure showed malformed retained IDs could reach acquisition internals as exhausted fetch failures or cached direct returns instead of deterministic category-ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, cached invalid direct acquisition, zero-ID compatibility, first and additional page acquisition, adjacent forum/site workflows, and full unit compatibility.
- This slice only validates retained stored parent category IDs at the category thread-list acquisition boundary. It does not change parser field extraction, forum post-list acquisition internals, forum post revision acquisition internals, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered forum HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates the retained category ID once at acquisition entry and then reuses that validated integer for request payloads and exhausted-retry diagnostics. The validation happens before the cache fast path so corrupted retained category identity cannot silently return cached data. This keeps the change local to the category thread-list acquisition boundary while preserving the existing public API surface.
