# PR Draft: Validate Page Votes Cache Page Fullnames

## Summary

`Page.votes` cache ownership validates that a retained `PageVoteCollection.page` and each cached `PageVote.page` belong to the receiving `Page` by retained site and compatible page identity. Existing hardening validates the cache shape, vote entries, vote collection ownership, direct votes-cache ownership, retained cache-owner page IDs, vote user/client state, vote value parsing, and adjacent `Page.revisions`, `Page.source`, and `PageRevision.source` retained fullnames. One retained votes-cache owner identity gap remained: if the receiving page ID and cached parent or entry page ID were both loaded and equal, `_validate_page_cache_owner(...)` returned before checking whether the retained cache-owner `fullname` was still a string.

This change validates retained `page.votes.page.fullname` for direct `Page(..., _votes=...)` construction and direct `page.votes = ...` assignment. Malformed retained votes-cache owner fullnames now raise `ValueError("page.votes.page.fullname must be a string")` before the votes cache is stored or replaced. Valid same-logical-page vote caches, valid loaded-ID ownership, valid wrong-owner diagnostics, unloaded-ID fullname fallback, lazy WhoRated acquisition, duplicate cached vote reuse, vote lookup workflows, and adjacent page/source/revision/file/site workflows remain unchanged.

## Outcome

Direct page votes caches can no longer store or replace a `PageVoteCollection` or cached `PageVote` whose retained owner page has malformed fullname state just because retained page IDs match. Setter failures preserve the previous valid cache and do not perform page-ID lookup, AMC request work, WhoRated fetching, source fetching, revision fetching, file fetching, or live Wikidot access.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct `Page(..., _votes=...)` construction, `page.votes = ...`, generated WhoRated fixtures, cached duplicate vote reuse, browser-free rating audits, migration scripts, publication review tooling, or rehydrated vote records.

## Current Evidence

Local rollout-backed drafts already establish page vote caches as practical workflow state. [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [492-pr-validate-page-constructor-votes-cache.md](492-pr-validate-page-constructor-votes-cache.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [669-pr-validate-page-vote-lookup-retained-user-id-state.md](669-pr-validate-page-vote-lookup-retained-user-id-state.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [772-pr-validate-whorated-vote-value-ascii-shape.md](772-pr-validate-whorated-vote-value-ascii-shape.md), and [781-pr-validate-page-revisions-cache-page-fullnames.md](781-pr-validate-page-revisions-cache-page-fullnames.md) cover vote-list acquisition, parser scoping, cached duplicate reuse, setter shape, collection initialization, direct vote page fields, collection page fields, constructor cache shape, collection ownership, direct page votes-cache ownership, retained owner page IDs, retained vote-user IDs, generated vote-value shape, and the adjacent revisions-cache retained fullname boundary.

The focused RED tests demonstrated the remaining votes-cache boundary gap: `Page(..., _votes=PageVoteCollection(parent_page_with_id_371_and_int_fullname, []))`, a mutated cached vote entry whose `vote.page.fullname` was an integer, `page.votes = PageVoteCollection(parent_page_with_matching_id_and_int_fullname, [])`, and `page.votes = collection_with_entry_page_matching_id_and_int_fullname` all completed without raising before this fix because `_validate_page_cache_owner(...)` validated retained IDs, saw them match, and returned before checking retained cache-owner fullname state.

## Related Issue / Non-Duplicate Analysis

Builds on [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [781-pr-validate-page-revisions-cache-page-fullnames.md](781-pr-validate-page-revisions-cache-page-fullnames.md), [779-pr-validate-page-source-cache-source-fullnames.md](779-pr-validate-page-source-cache-source-fullnames.md), and [780-pr-validate-page-revision-source-cache-source-fullnames.md](780-pr-validate-page-revision-source-cache-source-fullnames.md).

This is not a duplicate of Issue 598. Issue 598 rejects wrong-owner votes caches when retained IDs are valid and different, or when fallback fullnames differ. It did not validate malformed retained `page.votes.page.fullname` when valid retained IDs match.

This is not a duplicate of Issue 662. Issue 662 validates malformed retained cache-owner page IDs before the ownership comparison, not retained cache-owner fullname state after valid IDs match.

This is not a duplicate of Issue 781. Issue 781 covers the page-level `Page.revisions` cache slot and its retained collection/entry page owners, not the page-level `Page.votes` cache slot.

This is not a duplicate of Issues 779 or 780. Those issues cover source-cache source-owner fullnames for `Page.source` and `PageRevision.source`, not WhoRated vote-cache collection or entry page owners.

No upstream issue was filed from this local workspace.

## Changes

- Pass `page.votes.page.fullname` as the retained candidate-fullname field label from `_validate_votes_cache_belongs_to_page(...)`.
- Validate retained votes-cache parent page fullname when retained page IDs match.
- Validate retained cached vote entry page fullname when retained page IDs match.
- Preserve `ValueError("page.votes must belong to the page")` for valid loaded-ID mismatches and valid fallback fullname mismatches.
- Preserve unloaded-ID fallback by comparing the validated candidate fullname against the receiving page fullname.
- Add focused constructor and setter regressions for matching-ID votes-cache parent and entry pages whose retained `fullname` is not a string.

## Type Of Change

- Input validation
- Public page votes-cache constructor hardening
- Public page votes setter hardening
- Retained votes-cache owner fullname state validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(..., _votes=PageVoteCollection(parent_page, []))` must reject a retained collection parent `fullname` that is not a string even when receiving/parent retained page IDs are loaded and equal. |
| R2 | `Page(..., _votes=collection_with_vote_entry)` must reject a retained cached entry `vote.page.fullname` that is not a string even when receiving/entry retained page IDs are loaded and equal. |
| R3 | `page.votes = PageVoteCollection(parent_page, [])` must reject the same malformed retained parent fullname before replacing an existing valid cache. |
| R4 | `page.votes = collection_with_vote_entry` must reject the same malformed retained entry fullname before replacing an existing valid cache. |
| R5 | The new validation must not trigger `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, WhoRated fetching, source fetching, revision fetching, file fetching, or live Wikidot access. |
| R6 | Existing malformed retained owner page-ID diagnostics and valid loaded-ID wrong-owner diagnostics must remain unchanged. |
| R7 | Existing valid same-logical-page vote caches, unloaded-ID fullname fallback, lazy WhoRated acquisition, duplicate cached vote reuse, vote lookup, and adjacent page/source/revision/file/site workflows must remain unchanged. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, constructor/property coverage, page/vote coverage, adjacent page/source/site tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor votes-cache parent ownership rejects malformed retained parent fullname state. | `TestPageInit.test_init_rejects_votes_cache_with_malformed_retained_parent_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the retained fullname field label was added. | Accepting an integer or other non-string as the cached collection parent `fullname`, or storing the malformed votes cache during direct `Page(...)` construction, rejects this local completion claim. | `Page.__post_init__` votes-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Constructor votes-cache entry ownership rejects malformed retained entry fullname state. | `TestPageInit.test_init_rejects_votes_cache_entry_with_malformed_retained_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Accepting an integer or other non-string as a cached vote entry page `fullname`, or storing the malformed vote entry under the page cache, rejects this local completion claim. | `Page.__post_init__` votes-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Setter votes-cache parent ownership rejects malformed retained parent fullname state before replacement. | `TestPageProperties.test_votes_setter_rejects_malformed_retained_parent_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Replacing the previous valid cache, accepting malformed parent fullname state, or delaying failure until later vote access rejects this local completion claim. | `Page.votes` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Setter votes-cache entry ownership rejects malformed retained entry fullname state before replacement. | `TestPageProperties.test_votes_setter_rejects_malformed_retained_entry_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Replacing the previous valid cache, accepting malformed entry fullname state, or clearing the prior cache on failure rejects this local completion claim. | `Page.votes` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Validation stays side-effect free. | The setter regressions install `amc_request_with_retry = MagicMock()` and assert it is not called; constructor regressions use synthetic retained objects only. | Calling `Page.id`, acquiring page IDs, performing AMC work, fetching WhoRated data, fetching sources, fetching revisions, fetching files, mutating IDs, or touching live Wikidot rejects this local completion claim. | Page votes-cache ownership preflight | focused tests |
| R6 | Existing votes-cache diagnostics remain stable. | Constructor/property coverage passed 308 tests, including malformed cache object/entry cases, wrong-owner cache cases, malformed source/revisions-cache owner fullname cases, and valid same-page cache cases. | Reclassifying malformed IDs, changing wrong-owner diagnostics, accepting wrong-owner caches, or clearing prior cache on failed setter attempts rejects this local completion claim. | Page votes-cache behavior | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R7 | Adjacent page workflows remain green. | Page constructor/page/page-votes coverage passed 696 tests; adjacent page constructor/page/revision/source/file/vote/site coverage passed 1378 tests; full unit passed 3803 tests. | Regressing lazy WhoRated acquisition, duplicate cached vote reuse, vote lookup, page source/revision/file/site workflows, or full unit coverage rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R8 | The local proof stays unit-level and private-data-free. | All tests use synthetic `Page`, `PageVoteCollection`, `PageVote`, `User`, and mock `Site` objects only. | Using live Wikidot, credentials, cookies, auth JSON, raw private page data, private site names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4769459 fix(page): validate votes cache page fullnames`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_votes_cache_with_malformed_retained_parent_page_fullname tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_votes_cache_entry_with_malformed_retained_page_fullname tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_malformed_retained_parent_page_fullname tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_malformed_retained_entry_page_fullname -q --tb=short` failed before the fix with four `DID NOT RAISE` failures.
- GREEN focused: the same focused command passed 4 tests after the fix and again after formatting.
- Constructor/property coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit tests/unit/test_page.py::TestPageProperties -q` passed 308 tests.
- Page constructor/page/page-votes coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_votes.py -q` passed 696 tests.
- Adjacent page constructor/page/revision/source/file/vote/site coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1378 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3803 tests after formatting.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after formatting the edited test files.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- Direct `Page(..., _votes=...)` rejects a retained votes-cache parent page whose `fullname` is not a string when retained IDs match.
- Direct `Page(..., _votes=...)` rejects a cached vote entry whose retained `vote.page.fullname` is not a string when retained IDs match.
- Direct `page.votes = ...` rejects the same malformed retained parent page before replacing the prior votes cache.
- Direct `page.votes = ...` rejects the same malformed retained entry page before replacing the prior votes cache.
- The rejection uses `ValueError("page.votes.page.fullname must be a string")`.
- The rejection occurs without page-ID lookup, AMC request work, WhoRated fetching, source fetching, revision fetching, file fetching, or live Wikidot access.
- Valid same-logical-page vote caches with matching loaded IDs remain accepted when retained cache-owner fullnames are strings.
- Valid loaded-ID wrong-owner votes caches still raise `ValueError("page.votes must belong to the page")`.
- Existing malformed retained page-ID diagnostics, lazy WhoRated acquisition, duplicate cached vote reuse, vote lookup, and adjacent workflows remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.votes` is a public mutable cache boundary used by WhoRated reads, duplicate vote-list reuse, rating audits, migration workflows, and local vote fixtures. A votes cache should not accept malformed retained cache-owner identity solely because retained page IDs match. Passing the existing retained-fullname field label into the shared ownership preflight keeps vote caches internally coherent while preserving the side-effect-free, same-logical-page ownership design.

## Local Evidence

- Existing local drafts covered vote-list acquisition, direct votes-cache shape, direct votes assignment shape, vote collection ownership, direct page votes-cache ownership for valid retained IDs, malformed retained cache-owner page IDs, vote user/client validation, vote value parsing, and adjacent source/revisions retained-fullname validation.
- None of those slices covered a `PageVoteCollection` parent page or cached `PageVote.page` whose mutable `fullname` field was corrupted before matching retained IDs short-circuited the votes-cache ownership comparison.
- The focused RED failures showed matching retained IDs allowed malformed retained `page.votes.page.fullname` to bypass the fallback fullname comparison and be accepted into the votes cache.
- This slice only validates retained cache-owner fullname type for the `Page.votes` cache boundary. It does not change `PageVoteCollection` constructor semantics, direct `Page` identity construction, direct `Page.source` behavior, `Page.revisions` behavior, `PageRevision.source` behavior, fullname syntax rules, blank fullname handling, WhoRated fetching, parser behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw page source text, real WhoRated data from private sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained cache-owner fullname state after retained receiving/owner page IDs have already been validated. Valid loaded-ID mismatches keep their existing ownership diagnostic, while loaded matching IDs and unloaded-ID fallback paths now require a string retained owner fullname before accepting the votes cache.
