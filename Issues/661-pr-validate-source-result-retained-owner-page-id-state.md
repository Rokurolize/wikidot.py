# PR Draft: Validate Source Result Retained Owner Page ID State

## Summary

`PageSourceResult` validates that a successful `PageSource` belongs to the result `Page`, but the ownership check compared retained `page._id` values directly. That left the same retained-state gap as the publish-result coherence boundary: booleans and floats could compare equal to integers, while strings, lists, or negative IDs could be misreported as ordinary source/page ownership mismatches.

This change validates both retained optional page IDs before the source-result ownership comparison. Malformed retained IDs on either the result page or the source page now raise `ValueError("page.id must be an integer or None")`, negative retained IDs now raise `ValueError("page.id must be non-negative or None")`, valid mismatched IDs still raise `ValueError("source must belong to the result page")`, unloaded IDs still fall back to `fullname`, and zero-ID same-logical-page ownership remains valid.

## Outcome

Successful source-result rows can no longer combine a result page and source page whose retained owner IDs are corrupted, accepted by Python numeric equality, or masked as a generic page/source mismatch.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)`, `PageSourceResult`, `PageSourceResult.as_dict()`, large source collection, retry ledgers, migration scripts, archival jobs, generated page inventories, source comparison tooling, direct test fixtures, or rehydrated source-result records.

## Current Evidence

Local rollout-backed drafts repeatedly identify source-result rows and source ownership as practical durable ledger surfaces. [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [440-pr-validate-source-result-page-field.md](440-pr-validate-source-result-page-field.md), [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md), [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [602-pr-validate-source-result-source-ownership.md](602-pr-validate-source-result-source-ownership.md), [659-pr-validate-source-result-page-id-retained-state.md](659-pr-validate-source-result-page-id-retained-state.md), and [660-pr-validate-publish-result-retained-page-id-state.md](660-pr-validate-publish-result-retained-page-id-state.md) establish source iteration, ledger export, page/site context, source cache ownership, source-result ownership, source-result page-ID export, and adjacent retained publish-result ID validation as active local boundaries.

This slice is not a duplicate of those drafts. Issue 602 validates valid-ID source ownership and allows same-logical-page source wrappers, but it assumes retained IDs are comparable. Issue 659 validates the exported `PageSourceResult.page_id` property, not the successful source ownership comparison. Issues 600 and 601 validate source caches stored on `Page` and `PageRevision`, not direct `PageSourceResult(...)` construction. Issue 660 validates the analogous publish-result page/page-ID coherence boundary. None validates malformed retained result-page or source-page IDs before `PageSourceResult` ownership comparison.

## Related Issue / Non-Duplicate Analysis

Builds directly on [602-pr-validate-source-result-source-ownership.md](602-pr-validate-source-result-source-ownership.md), [659-pr-validate-source-result-page-id-retained-state.md](659-pr-validate-source-result-page-id-retained-state.md), and [660-pr-validate-publish-result-retained-page-id-state.md](660-pr-validate-publish-result-retained-page-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained result-page and source-page `page._id` values before comparing source ownership IDs.
- Reject malformed retained IDs such as `True`, `False`, `"371"`, `371.0`, and `[]` with `ValueError("page.id must be an integer or None")`.
- Reject negative retained IDs such as `-1` with `ValueError("page.id must be non-negative or None")`.
- Preserve `source must belong to the result page` for valid mismatched IDs, mismatched sites, malformed retained source page objects, and mismatched fullnames when either ID is unloaded.
- Preserve same-logical-page source wrappers, zero-ID compatibility, source-result page-ID export, source iterator ledger export, failure rows, and existing constructor diagnostics.

## Type Of Change

- Input validation
- Source-result ledger state integrity
- Retained page-ID hardening
- Source ownership validation
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult(...)` must reject malformed retained result-page IDs such as `True`, `False`, `"371"`, `371.0`, and `[]` with `ValueError("page.id must be an integer or None")` before source ownership comparison. |
| R2 | `PageSourceResult(...)` must reject malformed retained source-page IDs such as `True`, `False`, `"371"`, `371.0`, and `[]` with the same diagnostic before source ownership comparison. |
| R3 | `PageSourceResult(...)` must reject negative retained result-page or source-page IDs such as `-1` with `ValueError("page.id must be non-negative or None")`. |
| R4 | Malformed, negative, and unloaded retained source ownership checks must not call `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, or live Wikidot. |
| R5 | Existing same-logical-page ownership, zero IDs, valid mismatch diagnostics, source-result page-ID export, source iterator ledger export, failure rows, constructor diagnostics, publish-result adjacency, site workflows, and adjacent page/source workflows must remain green. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, source-result accessor tests, publish-result accessor tests, site tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained result-page IDs fail before source ownership comparison. | `test_source_result_rejects_malformed_retained_result_page_ids` failed RED for five malformed result-page values: booleans and `371.0` were accepted, while `"371"` and `[]` raised the generic source ownership mismatch; the test passed GREEN after retained result-page ID validation. | Accepting boolean retained result IDs, accepting float equality, coercing strings/lists, or returning the generic source ownership diagnostic rejects this local completion claim. | `PageSourceResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Malformed retained source-page IDs fail before source ownership comparison. | `test_source_result_rejects_malformed_retained_source_page_ids` failed RED for five malformed source-page values with the same accepted or generic-mismatch behavior, then passed GREEN after retained source-page ID validation. | Accepting malformed source-page IDs, allowing Python numeric equality to prove ownership, or returning the generic source ownership diagnostic rejects this local completion claim. | `PageSourceResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Negative retained result/source page IDs fail before source ownership comparison. | `test_source_result_rejects_negative_retained_result_page_id` and `test_source_result_rejects_negative_retained_source_page_id` failed RED with generic mismatch diagnostics, then passed GREEN after retained ID validation. | Accepting negative retained IDs, coercing them, or classifying them as ordinary cross-page source ownership mismatch rejects this local completion claim. | `PageSourceResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Validation remains side-effect-free. | New malformed and negative tests patch `PageCollection.get_page_ids` and assert it is not called; all regressions use synthetic `Page`, `PageSource`, and `PageSourceResult` objects only. | Calling `Page.id`, performing page-ID lookup, mutating retained IDs, or performing AMC work rejects this local completion claim. | Source-result ownership preflight | `tests/unit/test_site.py` |
| R5 | Existing source-result and adjacent workflows remain green. | Focused source-result constructor/ledger coverage passed 37 tests, `TestSitePagesAccessor` passed 60 tests, `TestSitePageAccessor` passed 98 tests, `tests/unit/test_site.py` passed 330 tests, adjacent site/page/source/constructor/file/revision/votes suites passed 1143 tests, and full unit passed 3024 tests. | Regressing valid same-logical-page ownership, zero IDs, source iterator order, ledger dictionaries, source-result page-ID export, publish results, page source/revision/vote/file workflows, site workflows, or any unit test rejects this local completion claim. | Source-result and adjacent workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_page_source.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7217dc7 fix(site): validate source result retained owner ids`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_pages tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_source tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_source_from_different_page tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_accepts_source_from_same_logical_page tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_retained_result_page_ids tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_negative_retained_result_page_id tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_retained_source_page_ids tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_negative_retained_source_page_id tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_accepts_zero_retained_source_page_ids tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_error tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_ambiguous_outcomes tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_does_not_trigger_lookup tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_rejects_malformed_retained_page_ids tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_rejects_negative_retained_page_id tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_accepts_zero_retained_page_id tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` failed 12 retained ownership cases before the fix; 25 constructor, page-ID export, zero-ID, ledger, and ownership guards passed.
- GREEN: the same focused command passed 37 tests after validating retained result/source page IDs before source ownership comparison.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 60 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 98 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 330 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 1143 tests.
- `uv run pytest tests/unit -q` passed 3024 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageSourceResult(page=page_one, source=PageSource(page_two, ...))` raises `ValueError("page.id must be an integer or None")` when either retained `page._id` value is `True`, `False`, `"371"`, `371.0`, or `[]`.
- The same constructor raises `ValueError("page.id must be non-negative or None")` when either retained `page._id` value is `-1`.
- Malformed and negative retained source ownership checks do not call `PageCollection.get_page_ids()`, AMC helpers, or live Wikidot.
- Same-logical-page source wrappers with `page._id == 0` and `source.page._id == 0` remain valid.
- Valid same-logical-page source wrappers with positive IDs remain valid.
- Valid loaded cross-page source wrappers still raise `ValueError("source must belong to the result page")`.
- Existing failed source-result rows with `source=None`, page-ID export, source iterator ledger export, publish-result adjacency, site workflows, and adjacent page/source workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageSourceResult` rows are designed as durable source-collection ledger records. Their ownership check should remain side-effect-free and allow reconstructed same-logical-page wrappers, but it should not allow corrupted retained page IDs to prove ownership. Validating retained optional IDs before comparison preserves the no-lookup design while preventing impossible page identity from producing successful source rows.

## Local Evidence

- Existing local drafts covered source-result page/source/error shape, exclusive outcome state, page-ID ledger export, site fields, source ownership for valid retained IDs, PageSource cache ownership, PageRevision source cache ownership, source-result retained page-ID export, and publish-result retained page-ID coherence.
- None of those drafts covered the source ownership comparison itself using malformed retained result/source `page._id` values because it bypasses `Page.id` to preserve unloaded-page fallback behavior.
- The focused RED failure showed booleans and floats could be accepted as retained owner IDs when they compared equal to explicit integers, while strings, lists, and negative IDs could be misreported as ordinary ownership mismatches. The GREEN regressions cover malformed rejection on both sides, negative rejection on both sides, no lazy lookup, no AMC work, zero-ID compatibility, valid same-logical-page compatibility, valid cross-page mismatch diagnostics, source-result page-ID export, and adjacent publish-result compatibility.
- This slice only validates retained optional page IDs at the source-result ownership boundary. It does not change `Page.id`, page-ID acquisition URLs, source fetching, fallback retry behavior, source parser behavior, source-result outcome validation, source-result page-ID export, publish result behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates the retained optional IDs instead of calling `Page.id`. Unloaded source-result ownership checks still fall back to `fullname`, which preserves the previous same-logical-page reconstruction behavior without introducing network lookup.
