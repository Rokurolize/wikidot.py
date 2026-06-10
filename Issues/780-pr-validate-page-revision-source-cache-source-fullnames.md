# PR Draft: Validate Page Revision Source Cache Source Fullnames

## Summary

`PageRevision.source` cache ownership validates that a retained `PageSource.page` belongs to the revision's `Page` by retained site and compatible page identity. Existing hardening validates the `PageSource` object, revision source-cache ownership, retained owner page IDs, same-logical-page source wrappers, wrong-owner revision source caches, and direct page source-cache source-owner fullnames. One retained revision source-owner identity gap remained: if the revision page ID and cached source owner page ID were both loaded and equal, `_validate_revision_source_belongs_to_page(...)` returned before checking whether `revision.source.page.fullname` was still a string.

This change validates retained `revision.source.page.fullname` for direct `PageRevision(..., _source=...)` construction and direct `revision.source = ...` assignment. Malformed retained source-owner fullnames now raise `ValueError("revision.source.page.fullname must be a string")` before the revision source cache is stored or replaced. Valid same-logical-page revision source caches, valid loaded-ID ownership, valid wrong-owner diagnostics, unloaded-ID fullname fallback, zero-ID compatibility, lazy revision source acquisition, bulk source fetching, duplicate source-cache reuse, revision HTML workflows, and adjacent page/source/site workflows remain unchanged.

## Outcome

Direct revision source caches can no longer store or replace a successful `PageSource` whose owner page has malformed fullname state just because its retained page ID matches the revision page ID. Setter failures preserve the previous valid cache and do not perform page-ID lookup, AMC request work, source fetching, or live Wikidot access.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct `PageRevision(..., _source=...)` construction, `revision.source = ...`, `PageRevisionCollection.get_sources()`, generated revision-source fixtures, duplicate cached source reuse, browser-free revision source reads, migration scripts, source comparison tooling, or rehydrated revision records.

## Current Evidence

Local rollout-backed drafts already establish revision source caches as practical workflow state. [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [334-pr-deduplicate-revision-detail-requests.md](334-pr-deduplicate-revision-detail-requests.md), [439-pr-validate-revision-source-cache.md](439-pr-validate-revision-source-cache.md), [491-pr-validate-revision-constructor-source-field.md](491-pr-validate-revision-constructor-source-field.md), [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [663-pr-validate-page-revision-source-cache-retained-page-id-state.md](663-pr-validate-page-revision-source-cache-retained-page-id-state.md), [702-pr-validate-page-source-constructor-page.md](702-pr-validate-page-source-constructor-page.md), [778-pr-validate-source-result-source-fullnames.md](778-pr-validate-source-result-source-fullnames.md), and [779-pr-validate-page-source-cache-source-fullnames.md](779-pr-validate-page-source-cache-source-fullnames.md) cover revision source fetch/retry behavior, duplicate detail reuse, source-cache shape, constructor source-cache shape, source-cache ownership, retained owner page IDs, `PageSource.page` type, source-result source-owner fullname validation, and direct page source-cache source-owner fullname validation.

The focused RED tests demonstrated the remaining revision boundary gap: both `PageRevision(..., _source=PageSource(source_page_with_id_12345_and_int_fullname, ...))` and `revision.source = PageSource(source_page_with_matching_id_and_int_fullname, ...)` completed without raising before this fix because `_validate_revision_source_belongs_to_page(...)` validated retained IDs, saw them match, and returned before checking retained source-owner fullname state.

## Related Issue / Non-Duplicate Analysis

Builds on [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [663-pr-validate-page-revision-source-cache-retained-page-id-state.md](663-pr-validate-page-revision-source-cache-retained-page-id-state.md), [702-pr-validate-page-source-constructor-page.md](702-pr-validate-page-source-constructor-page.md), [778-pr-validate-source-result-source-fullnames.md](778-pr-validate-source-result-source-fullnames.md), and [779-pr-validate-page-source-cache-source-fullnames.md](779-pr-validate-page-source-cache-source-fullnames.md).

This is not a duplicate of Issue 601. Issue 601 rejects wrong-owner revision source caches when retained IDs are valid and different, or when fallback fullnames differ. It did not validate malformed retained `revision.source.page.fullname` when valid retained IDs match.

This is not a duplicate of Issue 663. Issue 663 validates malformed retained revision/source owner page IDs before the cache-owner comparison, not retained source-owner fullname state after valid IDs match.

This is not a duplicate of Issue 702. Issue 702 validates that `PageSource.page` is a `Page`, not that the retained page's mutable identity fields remain well formed when a revision source cache accepts the source wrapper.

This is not a duplicate of Issue 778. Issue 778 covers direct `PageSourceResult(...)` construction, not direct `PageRevision(..., _source=...)` construction or `revision.source = ...` cache replacement.

This is not a duplicate of Issue 779. Issue 779 covers direct `Page(..., _source=...)` construction and `page.source = ...`, not revision source-cache construction or replacement.

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `revision.source.page.fullname` in `_validate_revision_source_belongs_to_page(...)`.
- Preserve retained revision/source page-ID validation before fullname validation.
- Preserve `ValueError("revision.source must belong to the revision page")` for valid loaded-ID mismatches.
- Preserve same-logical-page revision source wrappers when retained IDs match and the retained source-owner fullname is a string.
- Preserve unloaded-ID fallback by comparing the validated source-owner fullname against the revision page fullname.
- Add focused constructor and setter regressions for matching-ID revision source caches whose retained `revision.source.page.fullname` is not a string.

## Type Of Change

- Input validation
- Public revision source-cache constructor hardening
- Public revision source setter hardening
- Retained source-owner fullname state validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(..., _source=PageSource(source_page, ...))` must reject a retained `source.page.fullname` that is not a string even when revision/source retained page IDs are loaded and equal. |
| R2 | `revision.source = PageSource(source_page, ...)` must reject the same malformed retained source-owner fullname before replacing an existing valid cache. |
| R3 | The new validation must not trigger `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, source fetching, revision source fetching, or live Wikidot access. |
| R4 | Existing malformed retained owner page-ID diagnostics and valid loaded-ID wrong-owner diagnostics must remain unchanged. |
| R5 | Existing valid same-logical-page revision source caches, zero-ID compatibility, unloaded-ID fullname fallback, lazy revision source acquisition, bulk revision source fetching, revision HTML behavior, duplicate source-cache reuse, and adjacent page/source/site workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, revision class/file coverage, adjacent page/source/site tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor revision source-cache ownership rejects malformed retained source-owner fullname state. | `TestPageRevision.test_init_rejects_source_cache_with_malformed_retained_source_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after source-owner fullname validation. | Accepting an integer or other non-string as `revision.source.page.fullname`, or storing the malformed source cache during direct `PageRevision(...)` construction, rejects this local completion claim. | `PageRevision.__post_init__` source-cache validation | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Setter revision source-cache ownership rejects malformed retained source-owner fullname state before replacement. | `TestPageRevision.test_source_setter_rejects_malformed_retained_source_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the same validator was added. | Replacing the previous valid cache, accepting malformed `revision.source.page.fullname`, or delaying failure until later source access rejects this local completion claim. | `PageRevision.source` setter | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Validation stays side-effect free. | The setter regression asserts the previous valid cache is preserved and both regressions assert `amc_request_with_retry` is not called. | Calling `Page.id`, acquiring page IDs, performing AMC work, fetching source, mutating IDs, or touching live Wikidot rejects this local completion claim. | Revision source-cache ownership preflight | focused tests |
| R4 | Existing revision source-cache diagnostics remain stable. | `TestPageRevision` passed 99 tests and full `test_page_revision.py` passed 177 tests, including malformed `_source`, malformed setter values, wrong-owner source caches, malformed retained target/source IDs, negative IDs, zero IDs, and valid same-logical-page source caches. | Reclassifying malformed IDs, changing wrong-owner diagnostics, accepting wrong-owner sources, or clearing prior cache on failed setter attempts rejects this local completion claim. | Page revision source-cache behavior | `tests/unit/test_page_revision.py` |
| R5 | Adjacent page/source workflows remain green. | Adjacent page revision/page/page constructor/page source/page file/page votes/site coverage passed 1370 tests; full unit passed 3795 tests. | Regressing lazy source acquisition, bulk revision source fetching, revision HTML behavior, duplicate cache reuse, page/source/file/vote/site workflows, or full unit coverage rejects this local completion claim. | Revision and adjacent workflows | `tests/unit` |
| R6 | The local proof stays unit-level and private-data-free. | All tests use synthetic `Page`, `PageSource`, `PageRevision`, `User`, and mock `Site` objects only. | Using live Wikidot, credentials, cookies, auth JSON, raw private page data, private site names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `88dc816 fix(page_revision): validate source cache source fullnames`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_source_cache_with_malformed_retained_source_page_fullname tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_malformed_retained_source_page_fullname -q --tb=short` failed before the fix with two `DID NOT RAISE` failures.
- GREEN focused: the same focused command passed 2 tests.
- Revision class coverage: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision -q` passed 99 tests.
- Revision file coverage: `uv run pytest tests/unit/test_page_revision.py -q` passed 177 tests.
- Adjacent page revision/page/page constructor/page source/page file/page votes/site coverage: `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1370 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3795 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- Direct `PageRevision(..., _source=...)` rejects a retained source-owner page whose `fullname` is not a string when retained IDs match.
- Direct `revision.source = ...` rejects the same malformed retained source-owner page before replacing the prior source cache.
- The rejection uses `ValueError("revision.source.page.fullname must be a string")`.
- The rejection occurs without page-ID lookup, AMC request work, source fetching, revision source fetching, or live Wikidot access.
- Valid same-logical-page revision source caches with matching loaded IDs remain accepted when `source.page.fullname` is a string.
- Valid loaded-ID wrong-owner revision source caches still raise `ValueError("revision.source must belong to the revision page")`.
- Existing malformed retained page-ID diagnostics, lazy source acquisition, bulk revision source fetching, duplicate source-cache reuse, revision HTML behavior, and adjacent workflows remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.source` is a public mutable cache boundary used by revision source reads, duplicate detail reuse, generated fixtures, migration workflows, and source comparison tooling. A revision source cache should not accept malformed retained source-owner identity solely because retained page IDs match. Validating `revision.source.page.fullname` inside the existing ownership preflight keeps revision source caches internally coherent while preserving the side-effect-free, same-logical-page ownership design.

## Local Evidence

- Existing local drafts covered revision source fetch/retry behavior, direct revision source-cache shape, direct revision source assignment shape, revision source-cache ownership for valid retained IDs, malformed retained owner page IDs, duplicate revision detail reuse, `PageSource.page` type validation, source-result source-owner fullname validation, and direct page source-cache source-owner fullname validation.
- None of those slices covered a valid `PageSource` whose retained owner page object has a malformed mutable `fullname` field at direct `PageRevision(..., _source=...)` construction time or direct `revision.source = ...` assignment time.
- The focused RED failures showed matching retained IDs allowed malformed retained `revision.source.page.fullname` to bypass the fallback fullname comparison and be accepted into the revision source cache.
- This slice only validates retained source-owner fullname type for the `PageRevision.source` cache boundary. It does not change `PageSource` constructor semantics, direct `Page` identity construction, direct `Page.source` behavior, source-result behavior, fullname syntax rules, blank fullname handling, source fetching, source parser behavior, revision HTML behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw page source text, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained source-owner fullname state after retained revision/source page IDs have already been validated. Valid loaded-ID mismatches keep their existing ownership diagnostic, while loaded matching IDs and unloaded-ID fallback paths now require a string source-owner fullname before accepting the revision source cache.
