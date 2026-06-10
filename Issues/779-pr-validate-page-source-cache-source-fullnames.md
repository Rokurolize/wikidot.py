# PR Draft: Validate Page Source Cache Source Fullnames

## Summary

`Page.source` cache ownership validates that a retained `PageSource.page` belongs to the receiving `Page` by retained site and compatible page identity. Existing hardening validates the `PageSource` object, source text, direct source-cache ownership, retained owner page IDs, same-logical-page source wrappers, and wrong-owner source caches. One retained source-owner identity gap remained: if the receiving page ID and cached source owner page ID were both loaded and equal, the shared cache-owner helper returned before checking whether `source.page.fullname` was still a string.

This change validates retained `page.source.page.fullname` for direct `Page(..., _source=...)` construction and direct `page.source = ...` assignment. Malformed retained source-owner fullnames now raise `ValueError("page.source.page.fullname must be a string")` before the source cache is stored or replaced. Valid same-logical-page source caches, valid loaded-ID ownership, valid wrong-owner diagnostics, unloaded-ID fullname fallback, zero-ID compatibility, lazy source acquisition, duplicate cache reuse, source iterators, publish verification, and adjacent page workflows remain unchanged.

## Outcome

Direct page source caches can no longer store or replace a successful `PageSource` whose owner page has malformed fullname state just because its retained page ID matches the receiving page ID. Setter failures preserve the previous valid cache and do not perform page-ID lookup, AMC request work, source fetching, or live Wikidot access.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct `Page(..., _source=...)` construction, `page.source = ...`, generated source-cache fixtures, duplicate cached source reuse, source comparison tooling, browser-free page source reads, publish source verification, migration scripts, or rehydrated page records.

## Current Evidence

Local rollout-backed drafts already establish page source caches as practical workflow state. [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md), [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [702-pr-validate-page-source-constructor-page.md](702-pr-validate-page-source-constructor-page.md), and [778-pr-validate-source-result-source-fullnames.md](778-pr-validate-source-result-source-fullnames.md) cover duplicate source-cache reuse, assignment shape, source text, constructor source-cache shape, source-cache ownership, retained owner page IDs, `PageSource.page` type, and the adjacent source-result source-owner fullname boundary.

The focused RED tests demonstrated the remaining gap: both `Page(..., _source=PageSource(source_page_with_id_371_and_int_fullname, ...))` and `page.source = PageSource(source_page_with_matching_id_and_int_fullname, ...)` completed without raising before this fix because the shared cache-owner helper validated retained IDs, saw them match, and returned before checking retained source-owner fullname state.

## Related Issue / Non-Duplicate Analysis

Builds on [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md), [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md), [702-pr-validate-page-source-constructor-page.md](702-pr-validate-page-source-constructor-page.md), and [778-pr-validate-source-result-source-fullnames.md](778-pr-validate-source-result-source-fullnames.md).

This is not a duplicate of Issue 600. Issue 600 rejects wrong-owner source caches when retained IDs are valid and different, or when fallback fullnames differ. It did not validate malformed retained `source.page.fullname` when valid retained IDs match.

This is not a duplicate of Issue 662. Issue 662 validates malformed retained owner page IDs before the cache-owner comparison, not retained source-owner fullname state after valid IDs match.

This is not a duplicate of Issue 702. Issue 702 validates that `PageSource.page` is a `Page`, not that the retained page's mutable identity fields remain well formed when a page source cache accepts the source wrapper.

This is not a duplicate of Issue 778. Issue 778 covers direct `PageSourceResult(...)` construction, not direct `Page(..., _source=...)` construction or `page.source = ...` cache replacement.

No upstream issue was filed from this local workspace.

## Changes

- Add an opt-in retained candidate-fullname field label to the shared page cache-owner helper.
- Keep existing cache-owner behavior unchanged for callers that do not pass a retained candidate-fullname field label.
- Have `Page.source` ownership validation pass `page.source.page.fullname` as the retained source-owner fullname field.
- Validate retained source-owner fullname after retained IDs are validated, preserving valid loaded-ID wrong-owner diagnostics.
- Validate retained source-owner fullname before unloaded-ID fallback comparison.
- Add focused constructor and setter regressions for matching-ID source caches whose retained `source.page.fullname` is not a string.

## Type Of Change

- Input validation
- Public page source-cache constructor hardening
- Public page source setter hardening
- Retained source-owner fullname state validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(..., _source=PageSource(source_page, ...))` must reject a retained `source.page.fullname` that is not a string even when receiving/source retained page IDs are loaded and equal. |
| R2 | `page.source = PageSource(source_page, ...)` must reject the same malformed retained source-owner fullname before replacing an existing valid cache. |
| R3 | The new validation must not trigger `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, source fetching, or live Wikidot access. |
| R4 | Existing malformed retained owner page-ID diagnostics and valid loaded-ID wrong-owner diagnostics must remain unchanged. |
| R5 | Existing valid same-logical-page source caches, zero-ID compatibility, unloaded-ID fullname fallback, lazy source acquisition, explicit source refresh, duplicate source-cache reuse, source iterators, publish verification, and adjacent page workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor/property coverage, full page tests, adjacent page/source tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor source-cache ownership rejects malformed retained source-owner fullname state. | `TestPageInit.test_init_rejects_source_cache_with_malformed_retained_source_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after opt-in source-owner fullname validation. | Accepting an integer or other non-string as `source.page.fullname`, or storing the malformed source cache during direct `Page(...)` construction, rejects this local completion claim. | `Page.__post_init__` source-cache validation | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Setter source-cache ownership rejects malformed retained source-owner fullname state before replacement. | `TestPageProperties.test_source_setter_rejects_malformed_retained_source_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Replacing the previous valid cache, accepting malformed `source.page.fullname`, or delaying failure until later source access rejects this local completion claim. | `Page.source` setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation stays side-effect free. | The setter regression patches `amc_request` and `amc_request_with_retry` and asserts neither is called; constructor regression uses synthetic objects only. | Calling `Page.id`, acquiring page IDs, performing AMC work, fetching source, mutating IDs, or touching live Wikidot rejects this local completion claim. | Source-cache ownership preflight | focused tests |
| R4 | Existing source-cache diagnostics remain stable. | Constructor/property class coverage passed 300 tests, including malformed `_source`, malformed setter values, wrong-owner source caches, malformed retained target/source IDs, negative IDs, zero IDs, and valid same-logical-page source caches. | Reclassifying malformed IDs, changing wrong-owner diagnostics, accepting wrong-owner sources, or clearing prior cache on failed setter attempts rejects this local completion claim. | Page source-cache behavior | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py` |
| R5 | Adjacent page/source workflows remain green. | Full page constructor/page coverage passed 624 tests; adjacent page constructor/page/source/revision/file/vote/site coverage passed 1368 tests; full unit passed 3793 tests. | Regressing lazy source acquisition, source refresh, duplicate cache reuse, source iterator rows, publish verification, page revision/file/vote workflows, site workflows, or full unit coverage rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All tests use synthetic `Page`, `PageSource`, and mock `Site` objects only. | Using live Wikidot, credentials, cookies, auth JSON, raw private page data, private site names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `71ed044 fix(page): validate source cache source fullnames`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_source_cache_with_malformed_retained_source_page_fullname tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_malformed_retained_source_page_fullname -q --tb=short` failed before the fix with two `DID NOT RAISE` failures.
- GREEN focused: the same focused command passed 2 tests.
- Constructor/property coverage: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit tests/unit/test_page.py::TestPageProperties -q` passed 300 tests.
- Full page constructor/page coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py -q` passed 624 tests.
- Adjacent page constructor/page/source/revision/file/vote/site coverage: `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1368 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3793 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- Direct `Page(..., _source=...)` rejects a retained source-owner page whose `fullname` is not a string when retained IDs match.
- Direct `page.source = ...` rejects the same malformed retained source-owner page before replacing the prior source cache.
- The rejection uses `ValueError("page.source.page.fullname must be a string")`.
- The rejection occurs without page-ID lookup, AMC request work, source fetching, or live Wikidot access.
- Valid same-logical-page source caches with matching loaded IDs remain accepted when `source.page.fullname` is a string.
- Valid loaded-ID wrong-owner source caches still raise `ValueError("page.source must belong to the page")`.
- Existing malformed retained page-ID diagnostics, lazy source acquisition, duplicate source-cache reuse, source iterator behavior, publish verification, and adjacent workflows remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.source` is a public mutable cache boundary used by source reads, duplicate cache reuse, generated fixtures, publishing verification, and migration workflows. A page source cache should not accept malformed retained source-owner identity solely because retained page IDs match. Opt-in fullname validation keeps the source-cache boundary coherent while preserving the shared cache-owner helper's existing behavior for unrelated cache surfaces.

## Local Evidence

- Existing local drafts covered direct source-cache shape, direct source assignment shape, source text validation, `PageSource.page` type, wrong-owner source-cache rejection for valid retained IDs, malformed retained owner page IDs, duplicate source-cache reuse, source-result source-owner fullname validation, and adjacent page revision source-cache ownership.
- None of those slices covered a valid `PageSource` whose retained owner page object has a malformed mutable `fullname` field at direct `Page(..., _source=...)` construction time or direct `page.source = ...` assignment time.
- The focused RED failures showed matching retained IDs allowed malformed retained `source.page.fullname` to bypass the fallback fullname comparison and be accepted into the page source cache.
- This slice only validates retained source-owner fullname type for the `Page.source` cache boundary. It does not change `PageSource` constructor semantics, direct `Page` identity construction, other page cache-owner surfaces, fullname syntax rules, blank fullname handling, source fetching, source parser behavior, source-result behavior, revision source-cache behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw page source text, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally makes retained candidate-fullname validation opt-in on the shared page cache-owner helper. `Page.source` passes `page.source.page.fullname`, while other cache-owner callers retain their existing diagnostics and scope for this slice.
