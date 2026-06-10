# PR Draft: Validate Page Revisions Cache Page Fullnames

## Summary

`Page.revisions` cache ownership validates that a retained `PageRevisionCollection.page` and each cached `PageRevision.page` belong to the receiving `Page` by retained site and compatible page identity. Existing hardening validates the cache shape, revision entries, wrong-owner revision caches, retained owner page IDs, and adjacent `Page.source` and `PageRevision.source` source-owner fullnames. One retained revisions-cache owner identity gap remained: if the receiving page ID and a cached parent or entry page ID were both loaded and equal, `_validate_page_cache_owner(...)` returned before checking whether the retained cache-owner `fullname` was still a string.

This change validates retained `page.revisions.page.fullname` for direct `Page(..., _revisions=...)` construction and direct `page.revisions = ...` assignment. Malformed retained revisions-cache owner fullnames now raise `ValueError("page.revisions.page.fullname must be a string")` before the revisions cache is stored or replaced. Valid same-logical-page revision caches, valid loaded-ID ownership, valid wrong-owner diagnostics, unloaded-ID fullname fallback, lazy revision acquisition, duplicate cached revision reuse, revision source/HTML workflows, and adjacent page/source/file/vote/site workflows remain unchanged.

## Outcome

Direct page revisions caches can no longer store or replace a `PageRevisionCollection` or cached `PageRevision` whose retained owner page has malformed fullname state just because retained page IDs match. Setter failures preserve the previous valid cache and do not perform page-ID lookup, AMC request work, revision fetching, source fetching, HTML fetching, or live Wikidot access.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct `Page(..., _revisions=...)` construction, `page.revisions = ...`, generated revision-list fixtures, duplicate cached revision reuse, browser-free page history reads, migration scripts, revision comparison tooling, publication audits, or rehydrated page revision records.

## Current Evidence

Local rollout-backed drafts already establish page revision caches as practical workflow state. [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md), [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md), [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [779-pr-validate-page-source-cache-source-fullnames.md](779-pr-validate-page-source-cache-source-fullnames.md), and [780-pr-validate-page-revision-source-cache-source-fullnames.md](780-pr-validate-page-revision-source-cache-source-fullnames.md) cover revision-list acquisition, cached duplicate reuse, setter shape, constructor cache shape, collection ownership, direct page revisions-cache ownership, retained owner page IDs, direct page source-cache source-owner fullname validation, and page revision source-cache source-owner fullname validation.

The focused RED tests demonstrated the remaining revisions-cache boundary gap: `Page(..., _revisions=PageRevisionCollection(parent_page_with_id_371_and_int_fullname, []))`, a mutated cached revision entry whose `revision.page.fullname` was an integer, `page.revisions = PageRevisionCollection(parent_page_with_matching_id_and_int_fullname, [])`, and `page.revisions = collection_with_entry_page_matching_id_and_int_fullname` all completed without raising before this fix because `_validate_page_cache_owner(...)` validated retained IDs, saw them match, and returned before checking retained cache-owner fullname state.

## Related Issue / Non-Duplicate Analysis

Builds on [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [779-pr-validate-page-source-cache-source-fullnames.md](779-pr-validate-page-source-cache-source-fullnames.md), and [780-pr-validate-page-revision-source-cache-source-fullnames.md](780-pr-validate-page-revision-source-cache-source-fullnames.md).

This is not a duplicate of Issue 597. Issue 597 rejects wrong-owner revisions caches when retained IDs are valid and different, or when fallback fullnames differ. It did not validate malformed retained `page.revisions.page.fullname` when valid retained IDs match.

This is not a duplicate of Issue 662. Issue 662 validates malformed retained cache-owner page IDs before the ownership comparison, not retained cache-owner fullname state after valid IDs match.

This is not a duplicate of Issue 779. Issue 779 covers direct `Page.source` cache ownership and its retained `page.source.page.fullname`, not the `Page.revisions` collection parent or entry pages.

This is not a duplicate of Issue 780. Issue 780 covers direct `PageRevision.source` cache ownership and its retained `revision.source.page.fullname`, not the page-level `Page.revisions` cache slot.

No upstream issue was filed from this local workspace.

## Changes

- Pass `page.revisions.page.fullname` as the retained candidate-fullname field label from `_validate_revisions_cache_belongs_to_page(...)`.
- Validate retained revisions-cache parent page fullname when retained page IDs match.
- Validate retained cached revision entry page fullname when retained page IDs match.
- Preserve `ValueError("page.revisions must belong to the page")` for valid loaded-ID mismatches and valid fallback fullname mismatches.
- Preserve unloaded-ID fallback by comparing the validated candidate fullname against the receiving page fullname.
- Add focused constructor and setter regressions for matching-ID revisions-cache parent and entry pages whose retained `fullname` is not a string.

## Type Of Change

- Input validation
- Public page revisions-cache constructor hardening
- Public page revisions setter hardening
- Retained revisions-cache owner fullname state validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(..., _revisions=PageRevisionCollection(parent_page, []))` must reject a retained collection parent `fullname` that is not a string even when receiving/parent retained page IDs are loaded and equal. |
| R2 | `Page(..., _revisions=collection_with_revision_entry)` must reject a retained cached entry `revision.page.fullname` that is not a string even when receiving/entry retained page IDs are loaded and equal. |
| R3 | `page.revisions = PageRevisionCollection(parent_page, [])` must reject the same malformed retained parent fullname before replacing an existing valid cache. |
| R4 | `page.revisions = collection_with_revision_entry` must reject the same malformed retained entry fullname before replacing an existing valid cache. |
| R5 | The new validation must not trigger `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, revision fetching, source fetching, HTML fetching, or live Wikidot access. |
| R6 | Existing malformed retained owner page-ID diagnostics and valid loaded-ID wrong-owner diagnostics must remain unchanged. |
| R7 | Existing valid same-logical-page revision caches, unloaded-ID fullname fallback, lazy revision acquisition, duplicate cached revision reuse, revision source/HTML workflows, and adjacent page/source/file/vote/site workflows must remain unchanged. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, constructor/property coverage, adjacent page/source/site tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor revisions-cache parent ownership rejects malformed retained parent fullname state. | `TestPageInit.test_init_rejects_revisions_cache_with_malformed_retained_parent_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the retained fullname field label was added. | Accepting an integer or other non-string as the cached collection parent `fullname`, or storing the malformed revisions cache during direct `Page(...)` construction, rejects this local completion claim. | `Page.__post_init__` revisions-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Constructor revisions-cache entry ownership rejects malformed retained entry fullname state. | `TestPageInit.test_init_rejects_revisions_cache_entry_with_malformed_retained_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Accepting an integer or other non-string as a cached revision entry page `fullname`, or storing the malformed revision entry under the page cache, rejects this local completion claim. | `Page.__post_init__` revisions-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Setter revisions-cache parent ownership rejects malformed retained parent fullname state before replacement. | `TestPageProperties.test_revisions_setter_rejects_malformed_retained_parent_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Replacing the previous valid cache, accepting malformed parent fullname state, or delaying failure until later revision access rejects this local completion claim. | `Page.revisions` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Setter revisions-cache entry ownership rejects malformed retained entry fullname state before replacement. | `TestPageProperties.test_revisions_setter_rejects_malformed_retained_entry_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Replacing the previous valid cache, accepting malformed entry fullname state, or clearing the prior cache on failure rejects this local completion claim. | `Page.revisions` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Validation stays side-effect free. | The setter regressions install `amc_request_with_retry = MagicMock()` and assert it is not called; constructor regressions use synthetic retained objects only. | Calling `Page.id`, acquiring page IDs, performing AMC work, fetching revisions, fetching sources, fetching HTML, mutating IDs, or touching live Wikidot rejects this local completion claim. | Page revisions-cache ownership preflight | focused tests |
| R6 | Existing revisions-cache diagnostics remain stable. | Constructor/property coverage passed 304 tests, including malformed cache object/entry cases, wrong-owner cache cases, malformed source-cache owner ID/fullname cases, and valid same-page cache cases. | Reclassifying malformed IDs, changing wrong-owner diagnostics, accepting wrong-owner caches, or clearing prior cache on failed setter attempts rejects this local completion claim. | Page revisions-cache behavior | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R7 | Adjacent page workflows remain green. | Page constructor/page/revision coverage passed 805 tests; adjacent page constructor/page/revision/source/file/vote/site coverage passed 1374 tests; full unit passed 3799 tests. | Regressing lazy revision acquisition, duplicate cached revision reuse, revision source/HTML workflows, page source/file/vote/site workflows, or full unit coverage rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R8 | The local proof stays unit-level and private-data-free. | All tests use synthetic `Page`, `PageRevisionCollection`, `PageRevision`, `User`, and mock `Site` objects only. | Using live Wikidot, credentials, cookies, auth JSON, raw private page data, private site names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e058085 fix(page): validate revisions cache page fullnames`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_revisions_cache_with_malformed_retained_parent_page_fullname tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_revisions_cache_entry_with_malformed_retained_page_fullname tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_malformed_retained_parent_page_fullname tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_malformed_retained_entry_page_fullname -q --tb=short` failed before the fix with four `DID NOT RAISE` failures.
- GREEN focused: the same focused command passed 4 tests.
- Constructor/property coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit tests/unit/test_page.py::TestPageProperties -q` passed 304 tests.
- Page constructor/page/revision coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 805 tests.
- Adjacent page constructor/page/revision/source/file/vote/site coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1374 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3799 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after formatting the edited test file.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- Direct `Page(..., _revisions=...)` rejects a retained revisions-cache parent page whose `fullname` is not a string when retained IDs match.
- Direct `Page(..., _revisions=...)` rejects a cached revision entry whose retained `revision.page.fullname` is not a string when retained IDs match.
- Direct `page.revisions = ...` rejects the same malformed retained parent page before replacing the prior revisions cache.
- Direct `page.revisions = ...` rejects the same malformed retained entry page before replacing the prior revisions cache.
- The rejection uses `ValueError("page.revisions.page.fullname must be a string")`.
- The rejection occurs without page-ID lookup, AMC request work, revision fetching, source fetching, HTML fetching, or live Wikidot access.
- Valid same-logical-page revision caches with matching loaded IDs remain accepted when retained cache-owner fullnames are strings.
- Valid loaded-ID wrong-owner revisions caches still raise `ValueError("page.revisions must belong to the page")`.
- Existing malformed retained page-ID diagnostics, lazy revision acquisition, duplicate cached revision reuse, revision source/HTML workflows, and adjacent workflows remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.revisions` is a public mutable cache boundary used by page history reads, latest-revision lookup, duplicate revision reuse, generated fixtures, migration workflows, and source/HTML comparison tooling. A revisions cache should not accept malformed retained cache-owner identity solely because retained page IDs match. Passing the existing retained-fullname field label into the shared ownership preflight keeps revisions caches internally coherent while preserving the side-effect-free, same-logical-page ownership design.

## Local Evidence

- Existing local drafts covered revision-list acquisition, direct revisions-cache shape, direct revisions assignment shape, revisions-cache ownership for valid retained IDs, malformed retained cache-owner page IDs, page source-cache source-owner fullname validation, and page revision source-cache source-owner fullname validation.
- None of those slices covered a `PageRevisionCollection` parent page or cached `PageRevision.page` whose mutable `fullname` field was corrupted before matching retained IDs short-circuited the revisions-cache ownership comparison.
- The focused RED failures showed matching retained IDs allowed malformed retained `page.revisions.page.fullname` to bypass the fallback fullname comparison and be accepted into the revisions cache.
- This slice only validates retained cache-owner fullname type for the `Page.revisions` cache boundary. It does not change `PageRevisionCollection` constructor semantics, direct `Page` identity construction, direct `Page.source` behavior, `PageRevision.source` behavior, fullname syntax rules, blank fullname handling, revision fetching, source/HTML fetching, parser behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw page source text, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained cache-owner fullname state after retained receiving/owner page IDs have already been validated. Valid loaded-ID mismatches keep their existing ownership diagnostic, while loaded matching IDs and unloaded-ID fallback paths now require a string retained owner fullname before accepting the revisions cache.
