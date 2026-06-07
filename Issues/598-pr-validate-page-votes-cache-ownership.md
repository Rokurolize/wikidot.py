# PR Draft: Validate Page Votes Cache Ownership

## Summary

`Page._votes` is the optional cached `PageVoteCollection` behind the public `Page.votes` property and setter. Issue 492 validated the direct constructor cache shape and non-vote entries, Issue 416 validated malformed public `page.votes = ...` assignments, and Issue 588 validated vote-entry ownership at the `PageVoteCollection(page, votes)` constructor boundary. One direct cache-slot gap remained: a caller could construct a valid `PageVoteCollection` for another page and pass it as `Page(..., _votes=...)`, or assign another page's collection through `page.votes = ...`. A caller could also mutate a valid collection after construction so it contained a `PageVote` retained from another page before storing it on the receiving `Page`. The receiving page then exposed cached vote state for a different page.

This change validates cached vote ownership during `Page.__post_init__` and during direct `page.votes = ...` assignment after existing cache type and entry checks. Cached vote collections now compare the collection parent page and every cached vote's retained page against the receiving page by the same retained `Site` object and compatible page identity: matching page IDs when both sides have IDs, otherwise matching `fullname`. Mismatches raise `ValueError("page.votes must belong to the page")` before the malformed cache is stored. Valid same-page cached vote collections, `_votes=None`, existing malformed-cache diagnostics, lazy vote acquisition, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page/revision/file/site workflows remain unchanged.

## Outcome

Directly constructed and directly assigned `Page` vote caches reject wrong-page vote collections before `Page.votes` can expose cross-page cached state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free WhoRated inventories, rating audit ledgers, moderation reports, generated migration records, publication verification reports, local fixtures, adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

Prior cache and ownership drafts establish the surrounding behavior. [492-pr-validate-page-constructor-votes-cache.md](492-pr-validate-page-constructor-votes-cache.md) validates the optional `_votes` cache object shape and non-vote entries. [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md) validates public `page.votes = ...` assignment shape and preserves an existing cache on malformed assignments. [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md) validates `PageVoteCollection` constructor entry ownership. [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md), [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md), [595-pr-validate-forum-thread-posts-cache-ownership.md](595-pr-validate-forum-thread-posts-cache-ownership.md), [596-pr-validate-forum-category-threads-cache-ownership.md](596-pr-validate-forum-category-threads-cache-ownership.md), and [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md) establish retained-owner and direct cache-slot ownership hardening as active operational boundaries.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 492. Issue 492 rejects malformed `_votes` values and collections containing non-`PageVote` entries; it does not compare a cached collection's retained page or cached vote parent pages with the `Page` being constructed.

This is not a duplicate of Issue 416. Issue 416 rejects malformed direct `Page.votes` setter assignments and non-vote entries while preserving the previous valid cache; it does not reject valid collections whose retained pages belong to another page.

This is not a duplicate of Issue 588. Issue 588 protects `PageVoteCollection(page, votes)` from initially storing votes whose retained page differs from the collection page. This slice covers the separate `Page` cache slot and public setter, including empty collections for another page and collections that were valid at construction but later mutated before being assigned to a `Page`.

No upstream issue was filed from this local workspace.

## Changes

- Add cached vote ownership validation for direct `Page(...)` construction.
- Add the same ownership validation to the public `page.votes = ...` setter before `_votes` mutation.
- Reject cached `PageVoteCollection` objects whose own `page` describes a different page.
- Reject cached vote entries whose retained `vote.page` describes a different page.
- Preserve `_votes=None`, valid same-page cached collections, existing malformed-cache diagnostics, lazy vote acquisition, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Public cache setter behavior hardening
- Cached page vote ownership integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_votes=PageVoteCollection(other_page, []))` must reject the different cached collection page with `ValueError("page.votes must belong to the page")` before storing cached state. |
| R2 | `Page(_votes=collection_mutated_with_vote_from_other_page)` must reject the different retained vote page with the same diagnostic before storing cached state. |
| R3 | `page.votes = PageVoteCollection(other_page, [])` must reject the different cached collection page before replacing the existing cache. |
| R4 | `page.votes = collection_mutated_with_vote_from_other_page` must reject the different retained vote page before replacing the existing cache. |
| R5 | Valid same-page cached vote collections must remain accepted and `page.votes` must return the cached collection without triggering acquisition. |
| R6 | Existing malformed `_votes` and setter diagnostics from Issues 492 and 416 must remain unchanged. |
| R7 | Existing lazy vote-list acquisition, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page/revision/file/site workflows must remain unchanged. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cached collection parent pages from another page fail at the constructor boundary. | `TestPageInit.test_init_rejects_votes_cache_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after `Page.__post_init__` called the ownership preflight. | Accepting `PageVoteCollection(other_page, [])`, storing the mismatched cache, or deferring the failure to `page.votes` rejects this local completion claim. | `Page._votes` cache parent state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Valid cached collections that are mutated with another page's vote fail at the same constructor boundary. | `TestPageInit.test_init_rejects_votes_cache_entry_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after each cached vote's retained page was checked. | Accepting a same-page collection with a different-page vote entry or returning it through `page.votes` rejects this local completion claim. | `Page._votes` cache entry ownership | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Direct setter assignments from another page fail before replacing the previous cache. | `TestPageProperties.test_votes_setter_rejects_collection_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after the setter reused the ownership preflight. | Replacing a valid cache with another page's collection or clearing the previous cache on failure rejects this local completion claim. | `Page.votes` setter parent state | `tests/unit/test_page.py` |
| R4 | Direct setter assignments with another page's retained vote fail before replacing the previous cache. | `TestPageProperties.test_votes_setter_rejects_collection_entry_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN after cached entries were checked for retained-page ownership. | Replacing a valid cache with a different-page vote entry or clearing the previous cache on failure rejects this local completion claim. | `Page.votes` setter entry ownership | `tests/unit/test_page.py` |
| R5 | Valid same-page constructor caches remain accepted. | The focused constructor group passed valid optional vote-cache coverage and still returns the cached collection. | Rejecting a valid preloaded same-page vote cache or triggering vote acquisition during construction rejects this local completion claim. | `Page._votes` cache access | `tests/unit/test_page_constructor.py` |
| R6 | Existing malformed-cache and malformed-assignment diagnostics remain stable. | The focused constructor and setter groups also passed malformed `_votes`, malformed setter value, and malformed collection-entry tests from Issues 492 and 416. | Changing existing diagnostics, accepting non-collection values, or accepting non-vote cache entries rejects this local completion claim. | `Page` vote cache shape validation | `tests/unit/test_page.py`, `tests/unit/test_page_constructor.py` |
| R7 | Adjacent page workflows remain green. | Direct page constructor/page/page_votes coverage passed 507 tests, adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site coverage passed 997 tests, and full unit coverage passed 2717 tests. | Regressing lazy `Page.votes`, duplicate cached vote reuse, vote/cancel cache invalidation, page revision/file/source behavior, site accessors, or parser-created page behavior rejects this local completion claim. | Page workflows | `tests/unit` |
| R8 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `Page`, `PageVoteCollection`, and `PageVote` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `01be2d3 fix(page): validate votes cache ownership`.

- RED cached collection page ownership: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_votes_cache_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED cached vote entry ownership: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_votes_cache_entry_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED setter collection ownership: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_collection_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- RED setter entry ownership: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_collection_entry_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused constructor vote-cache coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_votes tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_votes tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_vote_entries tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_votes_cache_from_different_page tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_votes_cache_entry_from_different_page -q` passed 9 tests.
- GREEN focused setter vote-cache coverage: `uv run pytest tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_invalid_collections tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_invalid_collection_entries tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_collection_from_different_page tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_collection_entry_from_different_page -q` passed 11 parameterized tests.
- Direct page constructor/page/page_votes coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_votes.py -q` passed 507 tests.
- Adjacent page/page-constructor/page-revision/page-file/page-source/page_votes/site tests: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 997 tests.
- `uv run pytest tests/unit -q` passed 2717 tests.
- `uv run ruff format` left 87 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(_votes=PageVoteCollection(other_page, []))` raises `ValueError("page.votes must belong to the page")` before storing cached state.
- `Page(_votes=same-page-collection-mutated-with-other-page-vote)` raises the same diagnostic before storing cached state.
- `page.votes = PageVoteCollection(other_page, [])` raises the same diagnostic and leaves the previous cache unchanged.
- `page.votes = same-page-collection-mutated-with-other-page-vote` raises the same diagnostic and leaves the previous cache unchanged.
- `Page(_votes=PageVoteCollection(same_logical_page, []))` remains valid for constructor-time preloaded cache use where the new `Page` instance cannot be referenced before construction.
- Existing `_votes=None`, malformed `_votes` object rejection, non-vote cache-entry rejection, direct setter malformed object rejection, direct setter non-vote entry rejection, lazy vote acquisition, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page/revision/file/site behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page._votes` is a direct cache slot and `Page.votes` is a public assignment boundary for browser-free WhoRated inventories and generated rating audit ledgers. If the cached collection or one of its retained vote entries belongs to another page, callers can read coherent-looking but cross-page vote state through `Page.votes`. Constructor-time and setter-time ownership validation keep direct fixtures, rehydrated records, and generated caches from silently storing another page's votes under the current page.

## Local Evidence, Not For Upstream Paste

- The constructor RED failures showed `Page` could accept an empty `PageVoteCollection` whose collection parent page was another page and a same-page collection mutated after construction with another page's valid vote.
- The setter RED failures showed direct assignment could replace an existing valid cache with another page's collection or another page's retained vote entry.
- Existing local drafts covered vote-list acquisition, parser diagnostics, response diagnostics, optional `_votes` cache shape, setter shape, vote collection target ownership, and adjacent revision/file cache ownership, but did not validate that cached vote collections stored on a `Page` belong to that page.
- This slice only validates cached vote ownership during `Page` construction and direct assignment. It does not change WhoRated parsing, vote value conversion, collection lookup semantics, page vote mutation behavior, cache invalidation behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, voter identities, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The constructor ownership check intentionally allows same-logical-page preloaded vote collections because a caller cannot create a collection whose `page is new_page` before `new_page` exists. The comparison therefore requires the same retained `Site` object and uses page IDs when both sides have them; if either side lacks an ID, it falls back to `fullname`. Different-site, different-ID, and different-fullname cache evidence are rejected.
