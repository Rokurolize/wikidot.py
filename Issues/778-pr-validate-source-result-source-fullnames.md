# PR Draft: Validate Source Result Source Fullnames

## Summary

`PageSourceResult` validates successful source ownership by comparing the retained result `Page` with the retained `PageSource.page`. Existing hardening validates the result page, result page site, result page fullname, source/error outcome, source page type, retained owner page IDs, and wrong-owner source rows. One retained source-owner identity gap remained: if the result page ID and source page ID were both loaded and equal, the ownership helper returned before checking whether `source.page.fullname` was still a string.

This change validates the retained `source.page.fullname` during source-result source ownership checks. Malformed retained source-owner fullnames now raise `ValueError("source.page.fullname must be a string")` when a successful source result would otherwise accept them. Valid same-logical-page source wrappers, valid loaded-ID ownership, valid mismatched-ID diagnostics, unloaded-ID fullname fallback, failed source-result rows, source iterator generation, and ledger exports remain unchanged.

## Outcome

Successful source-result rows can no longer freeze a retained `PageSource` whose owner page has malformed fullname state just because its retained page ID matches the result page ID. The failure is reported at construction time without page-ID lookup, AMC request work, source fetching, or live Wikidot access.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)`, direct `PageSourceResult(...)` construction, `PageSourceResult.source`, generated source ledgers, migration scripts, retry rows, source comparison tooling, rehydrated audit records, or unit fixtures that reconstruct result pages and source-owner pages separately.

## Current Evidence

Local rollout-backed drafts repeatedly identify source-result rows as practical durable ledger surfaces. [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md), [440-pr-validate-source-result-page-field.md](440-pr-validate-source-result-page-field.md), [602-pr-validate-source-result-source-ownership.md](602-pr-validate-source-result-source-ownership.md), [659-pr-validate-source-result-page-id-retained-state.md](659-pr-validate-source-result-page-id-retained-state.md), [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md), [776-pr-validate-result-page-sites.md](776-pr-validate-result-page-sites.md), and [777-pr-validate-result-page-fullnames.md](777-pr-validate-result-page-fullnames.md) establish source-result rows, retained owner identity, page IDs, site fields, result-page fullname state, source ownership, and no-lookup ledger export as active local boundaries.

The focused RED test demonstrated the remaining gap: a source result accepted `PageSourceResult(page=page_with_id_371, source=PageSource(page=source_page_with_id_371_and_int_fullname, ...))` because the source ownership helper validated the retained IDs, saw them match, and returned before checking the retained source-owner fullname.

## Related Issue / Non-Duplicate Analysis

Builds on [602-pr-validate-source-result-source-ownership.md](602-pr-validate-source-result-source-ownership.md), [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md), [702-pr-validate-page-source-constructor-page.md](702-pr-validate-page-source-constructor-page.md), [776-pr-validate-result-page-sites.md](776-pr-validate-result-page-sites.md), and [777-pr-validate-result-page-fullnames.md](777-pr-validate-result-page-fullnames.md).

This is not a duplicate of Issue 602. Issue 602 added source ownership checks for valid retained IDs and fullname fallback, but loaded equal IDs short-circuit before retained source-owner fullname validation.

This is not a duplicate of Issue 661. Issue 661 validates retained result/source owner page IDs before ownership comparison, not retained `source.page.fullname` state after valid IDs match.

This is not a duplicate of Issues 776 or 777. Those slices validate the retained result page's `site` and `fullname`, not the retained `PageSource.page.fullname` stored inside a successful source result.

This is not a duplicate of Issue 702. Issue 702 validates that `PageSource.page` is a `Page`, not that the retained page's mutable identity fields remain well formed when a source result accepts the source wrapper.

This is not a duplicate of Issues 600, 601, or 663. Those slices cover page and revision source-cache ownership, not direct `PageSourceResult(...)` construction.

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `source.page.fullname` in `_validate_source_result_source_belongs_to_page(...)`.
- Preserve retained result/source page-ID validation before fullname validation.
- Preserve `ValueError("source must belong to the result page")` for valid loaded-ID mismatches.
- Preserve same-logical-page successful source wrappers when retained IDs match and the retained source-owner fullname is a string.
- Preserve unloaded-ID fallback by comparing the validated source-owner fullname against the already validated result page fullname.
- Add a focused regression for a matching-ID source wrapper whose retained `source.page.fullname` is not a string.

## Type Of Change

- Input validation
- Public result-object constructor hardening
- Source-result ownership integrity
- Retained source-owner fullname state validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult(page=page, source=PageSource(page=source_page, ...))` must reject a retained `source.page.fullname` that is not a string even when both retained page IDs are loaded and equal. |
| R2 | The new validation must not trigger `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, source fetching, or live Wikidot access. |
| R3 | Existing malformed retained result/source page-ID diagnostics and valid loaded-ID mismatch diagnostics must remain unchanged. |
| R4 | Existing valid same-logical-page source wrappers, zero-ID compatibility, unloaded-ID fullname fallback, failed source-result rows, source iterator rows, and source-result ledger exports must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, source accessor coverage, site tests, adjacent page/source tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Matching-ID source-result ownership rejects malformed retained source-owner fullname state. | `TestSitePagesAccessor.test_source_result_rejects_malformed_retained_source_page_fullname` failed RED with `DID NOT RAISE`, then passed GREEN after the validator was added. | Accepting an integer or other non-string as `source.page.fullname`, or freezing the malformed source wrapper inside `PageSourceResult.source`, rejects this local completion claim. | `PageSourceResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Constructor validation stays side-effect free. | The regression patches `PageCollection.get_page_ids`, sets `mock_site_no_http.amc_request = MagicMock()`, and asserts neither path is called. | Calling `Page.id`, acquiring page IDs, performing AMC work, fetching source, or touching live Wikidot rejects this local completion claim. | Source ownership preflight | focused test |
| R3 | Existing ownership diagnostics remain stable. | `TestSitePagesAccessor` passed 63 tests, including malformed retained result/source page IDs, negative IDs, valid mismatches, same-logical-page wrappers, zero IDs, result-page site/fullname validation, source/error outcome validation, and ledger export. | Reclassifying malformed IDs, changing valid mismatch diagnostics, accepting wrong-owner source wrappers, or changing source/error validation order rejects this local completion claim. | Source-result constructor behavior | `tests/unit/test_site.py` |
| R4 | Adjacent source-result workflows remain green. | `tests/unit/test_site.py` passed 370 tests; adjacent site/page/source/constructor/revision/file/vote suites passed 1366 tests; full unit passed 3791 tests. | Regressing source iterator order, source batching, fallback rows, page/source/revision/file/vote workflows, source text exports, result fields, or dictionary exports rejects this local completion claim. | Source-result and adjacent workflows | `tests/unit` |
| R5 | The local proof stays unit-level and private-data-free. | All tests use synthetic `Page`, `PageSource`, and mock `Site` objects only. | Using live Wikidot, credentials, cookies, auth JSON, raw private page data, private site names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `6b40fb7 fix(site): validate source result source fullnames`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_retained_source_page_fullname -q --tb=short` failed before the fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_retained_source_page_fullname -q` passed 1 test.
- Source accessor coverage: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 63 tests.
- Site coverage: `uv run pytest tests/unit/test_site.py -q` passed 370 tests.
- Adjacent site/page/source/constructor/revision/file/vote coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_constructor.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 1366 tests.
- Full unit: `uv run pytest tests/unit -q` passed 3791 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PageSourceResult` rejects a successful source wrapper whose retained `source.page.fullname` is not a string.
- The rejection uses `ValueError("source.page.fullname must be a string")`.
- The rejection occurs without page-ID lookup, AMC request work, source fetching, or live Wikidot access.
- Valid same-logical-page source wrappers with matching loaded IDs remain accepted when `source.page.fullname` is a string.
- Valid loaded-ID mismatches still raise `ValueError("source must belong to the result page")`.
- Existing malformed retained page-ID diagnostics, failed source-result rows, source iterator behavior, and ledger exports remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageSourceResult` rows are durable source-collection ledger records and also expose the retained successful `PageSource`. A row should not accept malformed retained source-owner identity solely because the retained page IDs match. Validating `source.page.fullname` inside the existing ownership preflight keeps successful rows internally coherent while preserving the side-effect-free, same-logical-page ownership design.

## Local Evidence

- Existing local drafts covered source-result fallback behavior, source-result context fields, page IDs, site fields, result-page fullname validation, source ownership for valid retained IDs, retained source-owner page-ID validation, source text validation, `PageSource.page` type validation, and page/revision source-cache ownership.
- None of those slices covered a valid `PageSource` whose retained owner page object has a malformed mutable `fullname` field at direct `PageSourceResult(...)` construction time.
- The focused RED failure showed matching retained IDs allowed the malformed retained `source.page.fullname` to bypass the fallback fullname comparison and be accepted into the frozen source result.
- This slice only validates retained source-owner fullname type at the source-result ownership boundary. It does not change `PageSource` constructor semantics, direct `Page` construction, fullname syntax rules, blank fullname handling, source fetching, source parser behavior, result page validation, publish result behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw page source text, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates retained source-owner fullname state after retained source/result page IDs have already been validated. Valid loaded-ID mismatches keep their existing ownership diagnostic, while loaded matching IDs and unloaded-ID fallback paths now require a string source-owner fullname before accepting the source result.
