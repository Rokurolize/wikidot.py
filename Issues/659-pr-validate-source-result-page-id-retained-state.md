# PR Draft: Validate Source Result Page ID Retained State

## Summary

`PageSourceResult.page_id` intentionally avoids `Page.id` so source-result ledger serialization does not trigger lazy page-ID lookups. That side-effect-free design is correct, but the property returned `self.page._id` directly and therefore could export malformed retained page IDs such as `True`, `"371"`, `371.0`, `[]`, or `-1` if a `Page` object had been corrupted or rehydrated after construction.

This change reuses the existing optional page-ID validator at the source-result ledger boundary. `PageSourceResult.page_id` still returns `None` for unloaded pages without calling `Page.id` or `PageCollection.get_page_ids()`, still accepts valid cached IDs including `0`, and now raises deterministic `ValueError` diagnostics before malformed retained page identity can enter `PageSourceResult.as_dict()` output.

## Outcome

Source-result ledger rows can no longer silently serialize malformed retained page IDs while preserving the side-effect-free unloaded-page behavior that Issue 225 introduced for large source-collection ledgers.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)`, `PageSourceResult.page_id`, `PageSourceResult.as_dict()`, large source collection, retry ledgers, migration scripts, archival jobs, generated page inventories, source comparison tooling, or rehydrated source-result records.

## Current Evidence

Local rollout-backed drafts repeatedly identify source-result rows and page identity as practical durable ledger surfaces. [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [440-pr-validate-source-result-page-field.md](440-pr-validate-source-result-page-field.md), [602-pr-validate-source-result-source-ownership.md](602-pr-validate-source-result-source-ownership.md), and [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md) establish source iteration, ledger export, page/site context, page-ID exposure, result-page validation, source ownership, and retained `Page.id` getter validation as active local boundaries.

This slice is not a duplicate of those drafts. Issue 225 added `PageSourceResult.page_id` and deliberately kept it side-effect-free by reading an already-loaded ID without calling `Page.id`; it did not validate malformed retained IDs. Issue 602 validates that a successful source belongs to the result page; it does not validate the exported `page_id` property. Issue 658 validates the public `Page.id` getter, but `PageSourceResult.page_id` intentionally avoids that getter to preserve no-lookup ledger serialization. Issues 413, 489, and 639 validate setter, constructor, and range inputs for normal `Page` state, not corrupted retained state at the source-result export boundary.

## Related Issue / Non-Duplicate Analysis

Builds directly on [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [602-pr-validate-source-result-source-ownership.md](602-pr-validate-source-result-source-ownership.md), [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md), and [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageSourceResult.page_id` with the existing optional page-ID validator before returning retained `page._id`.
- Reject malformed retained IDs such as `True`, `False`, `"371"`, `371.0`, and `[]` with `ValueError("page_id must be an integer or None")`.
- Reject negative retained IDs such as `-1` with `ValueError("page_id must be non-negative or None")`.
- Preserve `page._id is None` as a side-effect-free unloaded-page result of `None`.
- Preserve zero and positive retained IDs in `PageSourceResult.page_id` and `PageSourceResult.as_dict()`.
- Preserve existing source-result page/source/error/outcome/ownership validation and iterator behavior.

## Type Of Change

- Input validation
- Source-result ledger state integrity
- Retained page-ID hardening
- Side-effect-free export preservation
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult.as_dict()` must reject malformed retained `page._id` values such as `True`, `False`, `"371"`, `371.0`, and `[]` with `ValueError("page_id must be an integer or None")`. |
| R2 | `PageSourceResult.as_dict()` must reject retained negative `page._id` values such as `-1` with `ValueError("page_id must be non-negative or None")`. |
| R3 | Malformed, negative, and unloaded source-result page-ID reads must not call `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, or live Wikidot. |
| R4 | `page._id is None` must still serialize as `page_id is None`, and `page._id == 0` must remain valid. |
| R5 | Existing source-result page/source/error/outcome/ownership validation, source iterator output, publish-result adjacency, site workflows, and adjacent page/source workflows must remain green. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, source-result accessor tests, publish-result accessor tests, site tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained source-result page IDs fail before ledger export. | `test_source_result_page_id_rejects_malformed_retained_page_ids` failed RED for five malformed values with `DID NOT RAISE`, then passed GREEN after `PageSourceResult.page_id` reused `_validate_optional_page_id(...)`. | Returning malformed values, coercing strings/floats, accepting booleans as integers, or changing the diagnostic rejects this local completion claim. | `PageSourceResult.page_id`, `as_dict()` | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Negative retained source-result page IDs fail before ledger export. | `test_source_result_page_id_rejects_negative_retained_page_id` failed RED for `-1` with `DID NOT RAISE`, then passed GREEN after optional page-ID validation. | Returning negative IDs, coercing them to `0`, or raising the malformed-type diagnostic for integer negatives rejects this local completion claim. | `PageSourceResult.page_id`, `as_dict()` | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Validation remains side-effect-free. | New malformed/negative tests patch `PageCollection.get_page_ids` and assert it is not called; the existing unloaded-ID test still asserts no AMC request. | Calling `Page.id`, performing page-ID lookup, mutating `page._id`, or performing AMC work rejects this local completion claim. | Source-result ledger export | `tests/unit/test_site.py` |
| R4 | Unloaded and zero page IDs remain compatible. | `test_source_result_page_id_does_not_trigger_lookup` passed for `None`, and `test_source_result_page_id_accepts_zero_retained_page_id` passed for `0` through both property and `as_dict()`. | Rejecting `None`, rejecting zero, or triggering lookup for unloaded rows rejects this local completion claim. | Side-effect-free page-ID export | `tests/unit/test_site.py` |
| R5 | Existing source-result and adjacent workflows remain green. | Focused source-result coverage passed 11 tests, `TestSitePagesAccessor` passed 47 tests, `TestSitePageAccessor` passed 92 tests, `tests/unit/test_site.py` passed 311 tests, adjacent site/page/source/constructor/file/revision/votes suites passed 1124 tests, and full unit passed 3005 tests. | Regressing source iterator order, ledger dictionaries, source ownership validation, publish results, page source/revision/vote/file workflows, site workflows, or any unit test rejects this local completion claim. | Source-result and adjacent workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_page_source.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic `Page` and `PageSourceResult` objects only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7b5349a fix(site): validate source result page ids`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_does_not_trigger_lookup tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_rejects_malformed_retained_page_ids tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_rejects_negative_retained_page_id tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_page_id_accepts_zero_retained_page_id tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_source_from_different_page tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_accepts_source_from_same_logical_page -q` failed 6 retained page-ID ledger cases before the fix; 5 no-lookup, zero, ledger-export, and ownership guards passed.
- GREEN: the same focused command passed 11 tests after validating `PageSourceResult.page_id`.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 47 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 92 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 311 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 1124 tests.
- `uv run pytest tests/unit -q` passed 3005 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageSourceResult(page=page, source=None, error=...)` followed by `as_dict()` raises `ValueError("page_id must be an integer or None")` when retained `page._id` is `True`, `False`, `"371"`, `371.0`, or `[]`.
- The same export raises `ValueError("page_id must be non-negative or None")` when retained `page._id` is `-1`.
- Malformed and negative retained page-ID reads do not call `PageCollection.get_page_ids()`, AMC helpers, or live Wikidot.
- `page._id is None` still exports `page_id is None` without lookup.
- `page._id == 0` remains valid and exports `0`.
- Existing source-result page/source/error/outcome and source ownership validators remain unchanged.
- Existing source iterator, publish-result, site, page, page-source, constructor, file, revision, and vote workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageSourceResult.as_dict()` is designed for durable source-collection ledgers. It should be safe to serialize known page identity without performing network lookups, but it should not serialize impossible page identity values. Validating the retained optional page ID at the export boundary preserves the original no-lookup contract while keeping corrupted or rehydrated page state from leaking into retry ledgers, migration records, or audit summaries.

## Local Evidence

- Existing local drafts covered source iteration, source-result page context, wiki text, error messages, error types, ledger export, page-ID ledger fields, site fields, source-result page validation, source ownership, normal Page ID setter/constructor/range validation, and retained `Page.id` getter validation.
- None of those drafts covered the deliberately side-effect-free `PageSourceResult.page_id` property returning malformed retained `_id` directly because it bypasses `Page.id`.
- The focused RED failure showed malformed and negative retained `page._id` values were accepted into `PageSourceResult.as_dict()` output. The GREEN regressions cover malformed rejection, negative rejection, no lazy lookup, no AMC work, unloaded-`None` compatibility, zero-ID compatibility, existing ledger export, and source ownership compatibility.
- This slice only validates retained optional page IDs at the source-result ledger boundary. It does not change `Page.id`, page-ID acquisition URLs, source fetching, fallback retry behavior, source parser behavior, `PageSourceResult` success/failure outcome validation, source ownership semantics, publish result behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally does not call `Page.id` because Issue 225's source-result ledger field was designed to avoid implicit page-ID lookup. The validator checks only the retained optional value already present on the `Page` object.
