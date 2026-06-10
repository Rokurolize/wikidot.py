# PR Draft: Validate Page Files Cache Page Fullnames

## Summary

`Page.files` cache ownership validates that a retained `PageFileCollection.page` and each cached `PageFile.page` belong to the receiving `Page` by retained site and compatible page identity. Existing hardening validates file-list acquisition, parser diagnostics, direct `PageFile` fields, collection initialization, file collection page ownership, direct files-cache ownership, retained cache-owner page IDs, and adjacent `Page.revisions`, `Page.votes`, `Page.source`, and `PageRevision.source` retained fullnames. One retained files-cache owner identity gap remained: if the receiving page ID and cached parent or entry page ID were both loaded and equal, `_validate_page_cache_owner(...)` returned before checking whether the retained cache-owner `fullname` was still a string.

This change validates retained `page.files.page.fullname` for direct `Page(..., _files=...)` construction. Malformed retained files-cache owner fullnames now raise `ValueError("page.files.page.fullname must be a string")` before the files cache is stored. Valid same-logical-page file caches, valid loaded-ID ownership, valid wrong-owner diagnostics, unloaded-ID fullname fallback, lazy file acquisition, duplicate cached file reuse, file lookup workflows, and adjacent page/source/revision/vote/site workflows remain unchanged.

## Outcome

Direct page files caches can no longer store a `PageFileCollection` or cached `PageFile` whose retained owner page has malformed fullname state just because retained page IDs match. The failure occurs during direct `Page(..., _files=...)` construction and does not perform page-ID lookup, AMC request work, file fetching, source fetching, revision fetching, vote fetching, or live Wikidot access.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct `Page(..., _files=...)` construction, generated attachment fixtures, cached duplicate file reuse, browser-free attachment inventories, migration scripts, publication review tooling, asset audits, or rehydrated file records.

## Current Evidence

Local rollout-backed drafts already establish page file caches as practical workflow state. [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md), [589-pr-validate-page-file-collection-page-ownership.md](589-pr-validate-page-file-collection-page-ownership.md), [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md), [630-pr-validate-blank-page-file-names.md](630-pr-validate-blank-page-file-names.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [775-pr-validate-page-file-size-finite.md](775-pr-validate-page-file-size-finite.md), [781-pr-validate-page-revisions-cache-page-fullnames.md](781-pr-validate-page-revisions-cache-page-fullnames.md), and [782-pr-validate-page-votes-cache-page-fullnames.md](782-pr-validate-page-votes-cache-page-fullnames.md) cover file-list acquisition, parser scoping, cached duplicate reuse, collection shape, direct file page fields, direct file scalar/text fields, collection page fields, constructor cache shape, collection ownership, direct page files-cache ownership, blank name validation, retained owner page IDs, finite file sizes, and the adjacent revisions/votes retained fullname boundaries.

The focused RED tests demonstrated the remaining files-cache boundary gap: `Page(..., _files=PageFileCollection(parent_page_with_id_371_and_int_fullname, []))` and a mutated cached file entry whose `file.page.fullname` was an integer both completed without raising before this fix because `_validate_page_cache_owner(...)` validated retained IDs, saw them match, and returned before checking retained cache-owner fullname state.

## Related Issue / Non-Duplicate Analysis

Builds on [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [781-pr-validate-page-revisions-cache-page-fullnames.md](781-pr-validate-page-revisions-cache-page-fullnames.md), and [782-pr-validate-page-votes-cache-page-fullnames.md](782-pr-validate-page-votes-cache-page-fullnames.md).

This is not a duplicate of Issue 599. Issue 599 rejects wrong-owner files caches when retained IDs are valid and different, or when fallback fullnames differ. It did not validate malformed retained `page.files.page.fullname` when valid retained IDs match.

This is not a duplicate of Issue 662. Issue 662 validates malformed retained cache-owner page IDs before the ownership comparison, not retained cache-owner fullname state after valid IDs match.

This is not a duplicate of Issues 781 or 782. Those issues cover the page-level `Page.revisions` and `Page.votes` cache slots, not the page-level `Page.files` cache slot.

No upstream issue was filed from this local workspace.

## Changes

- Pass `page.files.page.fullname` as the retained candidate-fullname field label from `_validate_files_cache_belongs_to_page(...)`.
- Validate retained files-cache parent page fullname when retained page IDs match.
- Validate retained cached file entry page fullname when retained page IDs match.
- Preserve `ValueError("page.files must belong to the page")` for valid loaded-ID mismatches and valid fallback fullname mismatches.
- Preserve unloaded-ID fallback by comparing the validated candidate fullname against the receiving page fullname.
- Add focused constructor regressions for matching-ID files-cache parent and entry pages whose retained `fullname` is not a string.

## Type Of Change

- Input validation
- Public page files-cache constructor hardening
- Retained files-cache owner fullname state validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(..., _files=PageFileCollection(parent_page, []))` must reject a retained collection parent `fullname` that is not a string even when receiving/parent retained page IDs are loaded and equal. |
| R2 | `Page(..., _files=collection_with_file_entry)` must reject a retained cached entry `file.page.fullname` that is not a string even when receiving/entry retained page IDs are loaded and equal. |
| R3 | The new validation must not trigger `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, file fetching, source fetching, revision fetching, vote fetching, or live Wikidot access. |
| R4 | Existing malformed retained owner page-ID diagnostics and valid loaded-ID wrong-owner diagnostics must remain unchanged. |
| R5 | Existing valid same-logical-page file caches, unloaded-ID fullname fallback, lazy file acquisition, duplicate cached file reuse, file lookup, and adjacent page/source/revision/vote/site workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor coverage, page/file coverage, adjacent page/source/site tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor files-cache parent ownership rejects malformed retained parent fullname state. | `TestPageInit.test_init_rejects_files_cache_with_malformed_retained_parent_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the retained fullname field label was added. | Accepting an integer or other non-string as the cached collection parent `fullname`, or storing the malformed files cache during direct `Page(...)` construction, rejects this local completion claim. | `Page.__post_init__` files-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Constructor files-cache entry ownership rejects malformed retained entry fullname state. | `TestPageInit.test_init_rejects_files_cache_entry_with_malformed_retained_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Accepting an integer or other non-string as a cached file entry page `fullname`, or storing the malformed file entry under the page cache, rejects this local completion claim. | `Page.__post_init__` files-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Validation stays side-effect free. | The constructor regressions use synthetic retained objects only and do not invoke page acquisition. | Calling `Page.id`, acquiring page IDs, performing AMC work, fetching files, fetching sources, fetching revisions, fetching votes, mutating IDs, or touching live Wikidot rejects this local completion claim. | Page files-cache ownership preflight | focused tests |
| R4 | Existing files-cache diagnostics remain stable. | Constructor coverage passed 224 tests, including malformed cache object/entry cases, wrong-owner cache cases, malformed source/revisions/votes-cache owner fullname cases, and valid same-page cache cases. | Reclassifying malformed IDs, changing wrong-owner diagnostics, accepting wrong-owner caches, or changing direct constructor cache shape rejects this local completion claim. | Page files-cache behavior | `tests/unit/test_page_constructor.py` |
| R5 | Adjacent page workflows remain green. | Page constructor/page/page-file coverage passed 758 tests; adjacent page constructor/page/revision/source/file/vote/site coverage passed 1380 tests; full unit passed 3805 tests. | Regressing lazy file acquisition, duplicate cached file reuse, file lookup, page source/revision/vote/site workflows, or full unit coverage rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All tests use synthetic `Page`, `PageFileCollection`, `PageFile`, and mock `Site` objects only. | Using live Wikidot, credentials, cookies, auth JSON, raw private page data, private site names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a4bfaa5 fix(page): validate files cache page fullnames`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_files_cache_with_malformed_retained_parent_page_fullname tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_files_cache_entry_with_malformed_retained_page_fullname -q --tb=short` failed before the fix with two `DID NOT RAISE` failures.
- GREEN focused: the same focused command passed 2 tests after the fix and again after formatting.
- Constructor coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit -q` passed 224 tests.
- Page constructor/page/page-file coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 758 tests.
- Adjacent page constructor/page/revision/source/file/vote/site coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1380 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3805 tests after formatting.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted after formatting the edited test file.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- Direct `Page(..., _files=...)` rejects a retained files-cache parent page whose `fullname` is not a string when retained IDs match.
- Direct `Page(..., _files=...)` rejects a cached file entry whose retained `file.page.fullname` is not a string when retained IDs match.
- The rejection uses `ValueError("page.files.page.fullname must be a string")`.
- The rejection occurs without page-ID lookup, AMC request work, file fetching, source fetching, revision fetching, vote fetching, or live Wikidot access.
- Valid same-logical-page file caches with matching loaded IDs remain accepted when retained cache-owner fullnames are strings.
- Valid loaded-ID wrong-owner files caches still raise `ValueError("page.files must belong to the page")`.
- Existing malformed retained page-ID diagnostics, lazy file acquisition, duplicate cached file reuse, file lookup, and adjacent workflows remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.files` is a public lazy cache boundary used by attachment inventories, duplicate file-list reuse, file lookup, asset audits, migration workflows, publication checks, and local file fixtures. A files cache should not accept malformed retained cache-owner identity solely because retained page IDs match. Passing the existing retained-fullname field label into the shared ownership preflight keeps file caches internally coherent while preserving the side-effect-free, same-logical-page ownership design.

## Local Evidence

- Existing local drafts covered file-list acquisition, direct files-cache shape, file collection ownership, direct page files-cache ownership for valid retained IDs, malformed retained cache-owner page IDs, direct file page/scalar validation, file parser hardening, finite size validation, and adjacent source/revisions/votes retained-fullname validation.
- None of those slices covered a `PageFileCollection` parent page or cached `PageFile.page` whose mutable `fullname` field was corrupted before matching retained IDs short-circuited the files-cache ownership comparison.
- The focused RED failures showed matching retained IDs allowed malformed retained `page.files.page.fullname` to bypass the fallback fullname comparison and be accepted into the files cache.
- This slice only validates retained cache-owner fullname type for the `Page.files` constructor cache boundary. It does not add a public `files` setter, change `PageFileCollection` constructor semantics, direct `Page` identity construction, direct `Page.source` behavior, `Page.revisions` behavior, `Page.votes` behavior, fullname syntax rules, blank fullname handling, file fetching, parser behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw page source text, real attachment data from private sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained cache-owner fullname state after retained receiving/owner page IDs have already been validated. Valid loaded-ID mismatches keep their existing ownership diagnostic, while loaded matching IDs and unloaded-ID fallback paths now require a string retained owner fullname before accepting the files cache.
