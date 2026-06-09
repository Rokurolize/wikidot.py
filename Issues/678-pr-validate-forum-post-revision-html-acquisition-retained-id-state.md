# PR Draft: Validate ForumPostRevision HTML Acquisition Retained Revision IDs

## Summary

`ForumPostRevisionCollection.get_htmls()` and `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` already reject non-`ForumPostRevision` collection entries, validate retained post/thread ownership, deduplicate duplicate revision IDs, and validate direct `ForumPostRevision(id=...)` construction. The HTML acquisition paths still grouped, cached, and requested by retained `revision.id` values directly. If a valid `ForumPostRevision` is later mutated, rehydrated, or fixture-loaded with corrupted retained ID state, `None`, strings, floats, booleans, negative integers, or unhashable values can reach duplicate-cache grouping or AMC request payload construction instead of producing the same deterministic revision-ID diagnostics used elsewhere.

This change validates each retained `ForumPostRevision.id` with the existing revision-ID validator before revision HTML acquisition uses it for cache reuse, duplicate grouping, request payloads, or response fan-out. Malformed retained IDs now raise `ValueError("id must be an integer")`, negative retained IDs now raise `ValueError("id must be non-negative")`, valid zero revision IDs remain accepted, duplicate cached HTML reuse is preserved, and HTML acquisition requests are still batched by valid revision ID.

## Outcome

Forum post revision HTML acquisition no longer sends, groups, hashes, or reuses corrupted retained revision IDs. Valid parser-created revisions, directly constructed valid revisions, direct `get_htmls()`, cached-list `acquire_all_for_posts(..., with_html=True)`, duplicate revision HTML dedupe, duplicate cached HTML reuse, lazy `ForumPostRevision.html`, forum post revision-list acquisition, and adjacent forum/site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision HTML capture, duplicate revision cache reuse, cached revision-list acquisition, migration checks, moderation summaries, or local fixtures that construct, persist, mutate, or rehydrate `ForumPostRevision` objects before HTML acquisition.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision HTML acquisition as a practical workflow surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md), [582-pr-validate-forum-post-revision-html-target-post-thread.md](582-pr-validate-forum-post-revision-html-target-post-thread.md), [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md), and [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md) establish revision HTML acquisition, retry behavior, dedupe, cached reuse, response diagnostics, optional HTML batch controls, direct identity validation, retained post/thread validation, and lookup-only retained-ID validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issues 057 and 058 deduplicate duplicate revision IDs before HTML fetches, but they do not validate mutated retained `revision.id` values. Issue 131 reuses cached duplicate HTML, but it still relies on the retained ID as a cache key. Issues 581 and 582 validate retained post/thread state before HTML acquisition, not retained revision IDs. Issue 638 validates direct constructor identity fields, but it cannot cover a valid revision whose `id` is corrupted after construction and then acquired. Issue 675 validates retained `ForumPostRevision.id` and `rev_no` during collection lookup only; it does not cover HTML acquisition grouping, duplicate cached HTML reuse, optional `with_html=True` request payloads, or response fan-out.

## Related Issue / Non-Duplicate Analysis

Builds directly on [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md), [582-pr-validate-forum-post-revision-html-target-post-thread.md](582-pr-validate-forum-post-revision-html-target-post-thread.md), [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md), and [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md). It also follows the adjacent retained state hardening pattern from [666-pr-validate-forum-post-revisions-cache-retained-id-state.md](666-pr-validate-forum-post-revisions-cache-retained-id-state.md), [667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md](667-pr-validate-forum-post-revision-collection-retained-owner-id-state.md), [676-pr-validate-page-revision-collection-retained-id-state.md](676-pr-validate-page-revision-collection-retained-id-state.md), and [677-pr-validate-page-revision-acquisition-retained-id-state.md](677-pr-validate-page-revision-acquisition-retained-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate every retained `revision.id` before forum post revision HTML acquisition uses it for duplicate cached HTML lookup, target grouping, request payload construction, or response application.
- Reject malformed retained IDs such as `None`, `True`, `False`, `"9001"`, `9001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject negative retained IDs with `ValueError("id must be non-negative")`.
- Preserve valid zero retained revision IDs for direct `get_htmls()` and cached-list `acquire_all_for_posts(..., with_html=True)` acquisition.
- Preserve duplicate revision HTML dedupe and duplicate cached HTML reuse by grouping and cache-copying through validated integer revision IDs.
- Preserve existing revision-list acquisition, retry behavior, response diagnostics, lazy HTML reads, parser behavior, retained post/thread validation, and adjacent forum/site workflows.

## Type Of Change

- State validation
- Forum post revision HTML acquisition hardening
- Retained identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.get_htmls()` must reject retained `revision.id` values such as `None`, `True`, `False`, `"9001"`, `9001.0`, and `[]` with `ValueError("id must be an integer")` before request construction. |
| R2 | `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` must reject cached retained `revision.id` values such as `None`, `True`, `False`, `"9001"`, `9001.0`, and `[]` with `ValueError("id must be an integer")` before request construction. |
| R3 | Both HTML acquisition paths must reject retained `revision.id=-1` with `ValueError("id must be non-negative")` before request construction. |
| R4 | Valid retained revision ID `0` must remain accepted for direct and cached-list HTML acquisition. |
| R5 | Duplicate revision HTML dedupe, duplicate cached HTML reuse, valid revision-list acquisition, lazy `ForumPostRevision.html`, parser diagnostics, retained post/thread validation, and adjacent forum/site workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered revision HTML, or private forum content. |
| R7 | Focused RED/GREEN, forum-post-revision tests, adjacent forum/site workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained direct HTML-acquisition revision IDs fail before grouping, hashing, request construction, or retry plumbing. | `test_get_htmls_rejects_malformed_retained_revision_ids_before_fetch` failed RED for six retained values, then passed GREEN after retained-ID validation was added. | Sending malformed IDs, accepting booleans/floats, raising unrelated `zip()` or unhashable errors, coercing values, or calling AMC rejects this local completion claim. | Direct forum post revision HTML acquisition | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Malformed cached-list `with_html=True` retained revision IDs fail before grouping, hashing, request construction, or retry plumbing. | `test_acquire_all_for_posts_with_html_rejects_malformed_cached_revision_ids_before_fetch` failed RED for six retained values, then passed GREEN. | Sending malformed IDs, accepting booleans/floats, raising unrelated `zip()` or unhashable errors, coercing values, or calling AMC rejects this local completion claim. | Cached-list forum post revision HTML acquisition | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Negative retained IDs fail with the existing non-negative diagnostic before acquisition uses them. | `test_get_htmls_rejects_negative_retained_revision_id_before_fetch` and `test_acquire_all_for_posts_with_html_rejects_negative_cached_revision_id_before_fetch` failed RED as wrong acquisition failures, then passed GREEN. | Treating negative retained IDs as request IDs, ordinary misses, cache keys, or coercible values rejects this local completion claim. | Forum post revision HTML acquisition | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Valid zero retained IDs remain accepted for both acquisition modes. | `test_get_htmls_accepts_zero_retained_revision_id` and `test_acquire_all_for_posts_with_html_accepts_zero_retained_revision_id` passed RED and GREEN. | Rejecting zero IDs or changing valid zero-ID request payloads rejects this local completion claim. | Forum post revision HTML acquisition | `tests/unit/test_forum_post_revision.py` |
| R5 | Existing forum post revision behavior and adjacent forum/site workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 203 tests, adjacent forum/site coverage passed 1063 tests, and full unit coverage passed 3269 tests. | Regressing retry behavior, response diagnostics, duplicate HTML dedupe, duplicate cached HTML reuse, lazy HTML reads, revision-list acquisition, retained post/thread validation, forum post/thread/category behavior, or site behavior rejects this local completion claim. | Forum post revision workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft excludes private content. | Using credentials, cookies, auth JSON, raw rollout paths, private forum content, rendered revision HTML, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, full forum-post-revision and adjacent tests passed, full unit passed, ruff passed, format check passed, mypy passed, temporary pyright passed, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `cf73ece fix(forum_post_revision): validate html acquisition retained ids`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_accepts_zero_retained_revision_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_rejects_malformed_cached_revision_ids_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_rejects_negative_cached_revision_id_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_accepts_zero_retained_revision_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_malformed_retained_revision_ids_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_negative_retained_revision_id_before_fetch -q` failed 14 retained malformed/negative stored ID cases while 2 zero-ID compatibility guards passed.
- GREEN: the same focused command passed 16 tests after HTML acquisition retained-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 203 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_site.py -q` passed 1063 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 3269 tests.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPostRevisionCollection.get_htmls()` raises `ValueError("id must be an integer")` when a stored revision's retained `revision.id` is `None`, `True`, `False`, `"9001"`, `9001.0`, or `[]`.
- `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` raises `ValueError("id must be an integer")` when a cached stored revision's retained `revision.id` is `None`, `True`, `False`, `"9001"`, `9001.0`, or `[]`.
- Both HTML acquisition paths raise `ValueError("id must be non-negative")` when a stored revision's retained `revision.id` is `-1`.
- Valid retained revision ID `0` still produces forum revision HTML request payloads with `"revisionId": 0`.
- Existing valid HTML fetch, duplicate revision HTML dedupe, duplicate cached HTML reuse, response-content diagnostics, lazy `ForumPostRevision.html`, revision-list acquisition, retained post/thread validation, forum post/thread/category behavior, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, upstream PRs, rendered revision HTML, or private forum content.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated records with malformed retained IDs now fail before HTML acquisition. Mitigation: corrupted retained identity state should be corrected before request construction; deterministic diagnostics are preferable to invalid cache keys, unhashable failures, bool/float equality surprises, or malformed AMC payloads.
- Risk: Duplicate cached HTML reuse could accidentally diverge if validation changes grouping order. Mitigation: the implementation validates IDs once, preserves original revision order, and continues grouping/copying by integer revision ID.
- Risk: Diagnostics could expose private forum context. Mitigation: the new diagnostics include only the field name and expected/range constraint, not forum post text, rendered HTML, site names, account details, or private thread content.

## Dependencies

- Existing `_validate_revision_id(...)` remains the canonical forum post revision ID validator.
- Existing `ForumPostRevision(id=...)` constructor validation remains unchanged.
- Existing `ForumPostRevisionCollection.find(id)` retained-ID lookup validation from Issue 675 remains unchanged.
- Existing revision HTML response parsing, optional `with_html=True` behavior, and duplicate cached HTML reuse behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, or complexity candidates outside this now-covered forum post revision HTML acquisition boundary.

## Upstream-Safe Motivation

Forum post revision HTML acquisition uses retained revision IDs for cache reuse, request grouping, and AMC payload construction. Those retained IDs should satisfy the same integer/non-negative contract as directly constructed revisions before they leave local state. Validating stored fields prevents corrupted local state from becoming invalid request IDs or incidental cache keys, while preserving valid zero IDs, duplicate HTML dedupe, duplicate cached HTML reuse, retry behavior, and all parser/network behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post revision HTML acquisition as a practical workflow through forum edit-history reads, duplicate fetch reduction, cached duplicate HTML reuse, lazy HTML access, response diagnostics, optional `with_html=True` cached-list acquisition, and generated forum-history ledgers.
- Existing local drafts covered forum post revision acquisition reliability, HTML retries, dedupe, cached reuse, lazy failure context, response diagnostics, parsed identity fields, direct constructor identity validation, retained post/thread validation, and lookup-only retained-ID validation; they did not validate retained stored `ForumPostRevision.id` before HTML acquisition grouping or request construction.
- The focused RED failure showed malformed retained IDs could reach acquisition internals as wrong `zip()` failures, unhashable key errors, or malformed payload candidates instead of deterministic revision-ID diagnostics. The GREEN regressions cover malformed rejection, negative rejection, zero-ID compatibility, direct HTML acquisition, cached-list `with_html=True` acquisition, adjacent forum/site workflows, and full unit compatibility.
- This slice only validates retained stored revision IDs at the loaded HTML acquisition boundary. It does not change revision-list acquisition, parser field extraction, cached revision collections, lazy HTML semantics, forum post source/edit behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, rendered revision HTML, private thread text, private forum post content, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained IDs once in each HTML acquisition path and then reuses those validated integer IDs for acquired-cache indexing, target grouping, request payloads, and response application. This keeps the change local to the HTML acquisition boundary while preserving the existing public API surface.
