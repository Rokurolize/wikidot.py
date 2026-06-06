# PR Draft: Validate Publish Result Page IDs

## Summary

`PagePublishResult` is the audit-friendly result object returned by `Site.page.publish(...)`. Issue 428 made its status fields deterministic, but the constructor still accepted malformed `page_id` values. A caller could construct `PagePublishResult(page_id=True)`, `PagePublishResult(page_id=None)`, or `PagePublishResult(page_id="12345")`, then export an audit row whose `page_id` was not a real page identifier.

This change validates `PagePublishResult.page_id` at initialization. `page_id` now accepts only non-boolean integers and rejects malformed values with `ValueError("page_id must be an integer")`. Existing publish sequencing, source verification, metadata writes, create/edit branching, status-field validation, URL/site fields, aggregate properties, and `as_dict()` output for valid results remain unchanged.

## Outcome

Callers cannot silently create malformed publish-result ledger objects with invalid page IDs, while existing browser-free publishing and valid publish-result audit rows remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)`, direct `PagePublishResult(...)` construction in tests or local ledgers, browser-free page publishing, migration scripts, translation workflows, generated page updates, source verification, metadata updates, or durable publish audit rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify browser-free publishing and publish-result ledgers as practical workflow surfaces. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), and [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md) establish publish orchestration, page-ID state, publish-result fields, and publish-result ledger exports as active operational boundaries.

Those prior slices are not duplicates. Issues017, 024, 070, 148, 231, 257, 258, and 338 covered publish helper behavior and result-field ergonomics. Issue225 exposed loaded page IDs in source-result ledgers, Issue412 validated the write-path `page_id` argument, Issue413 validated direct `Page.id = ...` assignment, and Issue428 validated publish-result status fields. None of them validates direct `PagePublishResult(..., page_id=...)` construction before malformed page-ID state becomes stored frozen dataclass state.

## Related Issue

Builds directly on [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), and [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `PagePublishResult.page_id` validator.
- Reject `None`, booleans, strings, floats, lists, and other non-integer result page IDs with `ValueError("page_id must be an integer")`.
- Validate `page_id` before status-field validation completes object construction.
- Preserve valid non-boolean integer `page_id` values.
- Preserve existing publish create/edit behavior, source verification, metadata updates, visibility handling, status-field validation, URL/site fields, aggregate properties, and `as_dict()` output for valid results.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Publish result ledger state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PagePublishResult(page_id=None)`, `True`, `False`, `"12345"`, `12345.0`, and `[]` must raise `ValueError("page_id must be an integer")` before storing result state. |
| R2 | Valid non-boolean integer page IDs must preserve existing aggregate properties and audit dictionaries. |
| R3 | Existing publish-result status-field validation must remain unchanged. |
| R4 | Existing `Site.page.publish(...)`, source verification, metadata writes, visibility controls, create/edit branching, source-result workflows, and adjacent site/page behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, publish-result tests, adjacent site/page tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed publish-result page IDs fail at the public dataclass boundary. | `TestSitePageAccessor.test_publish_result_rejects_malformed_page_ids` failed RED for 6 malformed values because the constructor did not raise, then passed GREEN after `page_id` validation was added. | Accepting missing values, booleans, strings, floats, lists, arbitrary objects, or emitting ledger rows with non-integer page IDs rejects this local completion claim. | PagePublishResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid publish-result page ID semantics stay green. | Existing `test_publish_result_exposes_aggregate_operation_statuses` and `test_publish_result_exports_audit_record` passed with the new constructor validation. | Rejecting valid integer page IDs, changing `page_id` in `as_dict()`, or changing aggregate fields for valid results rejects this local completion claim. | PagePublishResult properties and ledger export | `tests/unit/test_site.py` |
| R3 | Existing status-field validation stays intact. | Existing malformed `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, and `created` tests passed in the focused 28-test GREEN run. | Weakening Issue 428 behavior, accepting numeric stand-ins for status fields, or changing status-field diagnostics rejects this local completion claim. | PagePublishResult constructor | `tests/unit/test_site.py` |
| R4 | Existing publish and adjacent workflows remain green. | `tests/unit/test_site.py` passed 201 tests and full unit tests passed 1647 tests. | Regressing publish create/edit selection, source verification, metadata order, visibility controls, result fields, page source/revision/vote/file behavior, or source iterator behavior rejects this local completion claim. | Site/page workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, site tests passed, full unit passed, ruff, format, mypy, source-file pyright, and whitespace checks passed; broad pyright was run and reported existing typed-invalid test fixtures unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `693b12e fix(site): validate publish result page ids`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_page_ids -q` failed 6 tests before the fix; every malformed `page_id` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_page_ids tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_source_matches tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_boolean_status_fields tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 28 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 201 tests.
- `uv run pytest tests/unit -q` passed 1647 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed on existing broad test-suite typing issues such as intentional invalid-input fixture calls and pre-existing BeautifulSoup/test fixture typing mismatches. The changed source file passes pyright.

## Acceptance Criteria

- `PagePublishResult(page_id=None)`, `True`, `False`, `"12345"`, `12345.0`, and `[]` raise `ValueError("page_id must be an integer")`.
- `PagePublishResult(page_id=12345)` remains valid.
- Existing status-field validation for `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, and `created` remains unchanged.
- Existing aggregate properties, source-verification status labels, URL/site properties, operation labels, and `as_dict()` output remain unchanged for valid results.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PagePublishResult` is the durable object shape behind browser-free publish audit ledgers. Constructor validation keeps malformed local page-ID state out of result records while preserving the existing `Site.page.publish(...)` path that constructs this field from a resolved saved page ID.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free page publishing, post-save page-ID resolution, source verification, metadata updates, publish-result aggregate fields, and publish-result audit dictionaries.
- Existing local drafts covered publish orchestration, publish inputs, result URL/site fields, source-result page-ID ledgers, create/edit page-ID inputs, direct page-ID assignment, and publish-result status fields, but did not cover direct `PagePublishResult(..., page_id=...)` construction.
- The focused RED failures showed malformed constructor page IDs were accepted as frozen dataclass state. The GREEN regressions cover missing, boolean, string, float, and list values, plus valid aggregate properties and existing status-field validation.
- This slice only validates publish-result page-ID shape. It does not change publish request construction, page saves, source refreshes, source comparisons, metadata writes, visibility retry behavior, page URL construction, site derivation, result dictionary keys, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects boolean and string page IDs instead of coercing values. Callers loading publish-result records from JSON, YAML, CLI flags, spreadsheets, generated structures, or ledgers should convert page IDs to non-boolean integers before constructing `PagePublishResult`.
