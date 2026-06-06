# PR Draft: Validate Publish Result Status Fields

## Summary

`PagePublishResult` is the audit-friendly result object returned by `Site.page.publish(...)`, but direct dataclass construction accepted malformed status fields. A caller could construct `PagePublishResult(source_matches="false")`, which reported source verification as requested while mapping the verification status to `skipped`, or construct `PagePublishResult(tags_updated="false")`, `parent_updated=1`, `metas_updated=None`, or `created=0`, which could make metadata counts, operation labels, and durable ledger rows inconsistent with the documented boolean contract.

This change validates result status fields at `PagePublishResult` initialization. `source_matches` now accepts only `True`, `False`, or `None` and rejects malformed values with `ValueError("source_matches must be a boolean or None")`. `tags_updated`, `parent_updated`, `metas_updated`, and `created` now accept only real booleans and reject malformed values with `ValueError("<field> must be a boolean")`. Existing publish sequencing, source verification, metadata writes, create/edit branching, URL/site fields, and `as_dict()` output for valid results remain unchanged.

## Outcome

Callers cannot silently create malformed publish-result ledger objects through the public constructor, while existing browser-free publishing and publish-result audit fields remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)`, direct `PagePublishResult(...)` construction in tests or local ledgers, browser-free page publishing, migration scripts, translation workflows, generated page updates, source verification, metadata updates, or durable publish audit rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify browser-free publishing and publish-result ledgers as practical workflow surfaces. Existing drafts [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), [226-pr-publish-visibility-404-context.md](226-pr-publish-visibility-404-context.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [232-pr-publish-verification-request-status.md](232-pr-publish-verification-request-status.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [346-pr-validate-publish-visibility-controls.md](346-pr-validate-publish-visibility-controls.md), [347-pr-validate-publish-source-normalizer.md](347-pr-validate-publish-source-normalizer.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), and [408-pr-reject-boolean-publish-visibility-controls.md](408-pr-reject-boolean-publish-visibility-controls.md) establish publish orchestration, source verification, visibility controls, metadata ordering, publish-result fields, and publish-result ledger exports as active operational boundaries.

Those prior slices are not duplicates. They covered publish inputs, publish sequencing, source verification, metadata side effects, visibility retry behavior, and result-field ergonomics. None of them validates direct `PagePublishResult(...)` construction before malformed status values become stored frozen dataclass state.

## Related Issue

Builds directly on [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [232-pr-publish-verification-request-status.md](232-pr-publish-verification-request-status.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), and [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.__post_init__()` validation.
- Reject malformed `source_matches` values with `ValueError("source_matches must be a boolean or None")`.
- Reject malformed `tags_updated`, `parent_updated`, `metas_updated`, and `created` values with `ValueError("<field> must be a boolean")`.
- Preserve valid `True`, `False`, and skipped-source-verification `None` semantics.
- Preserve existing publish create/edit behavior, source verification, metadata updates, visibility handling, URL/site fields, aggregate properties, and `as_dict()` output for valid results.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Publish result ledger state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PagePublishResult(source_matches="false")`, `0`, `1`, and `[]` must raise `ValueError("source_matches must be a boolean or None")` before storing result state. |
| R2 | `PagePublishResult(tags_updated=...)`, `parent_updated=...`, `metas_updated=...`, and `created=...` must reject `None`, `"false"`, `0`, and `1` with `ValueError("<field> must be a boolean")`. |
| R3 | Valid `source_matches=True`, `False`, and `None`, plus boolean metadata/create flags, must preserve existing aggregate properties and audit dictionaries. |
| R4 | Existing `Site.page.publish(...)`, source verification, metadata writes, visibility controls, create/edit branching, source-result workflows, and adjacent site/page behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, publish-result tests, adjacent site/page tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed tri-state source verification values fail at the public dataclass boundary. | `TestSitePageAccessor.test_publish_result_rejects_malformed_source_matches` failed RED for `"false"`, `0`, `1`, and `[]`, then passed GREEN after `PagePublishResult.__post_init__()` validation was added. | Accepting string, integer, list, or other non-boolean source-verification values, or emitting inconsistent requested/status fields, rejects this local completion claim. | PagePublishResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Malformed boolean publish-result status fields fail at the public dataclass boundary. | `TestSitePageAccessor.test_publish_result_rejects_malformed_boolean_status_fields` failed RED for all 16 field/value combinations, then passed GREEN after boolean field validation was added. | Accepting `None`, strings, integers, JSON-style booleans encoded as numbers, or fixture stand-ins as stored result status fields rejects this local completion claim. | PagePublishResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Valid publish-result semantics stay green. | Existing `test_publish_result_exposes_aggregate_operation_statuses` and `test_publish_result_exports_audit_record` passed with the new constructor validation. | Changing `metadata_update_count`, `metadata_updated`, `source_verification_requested`, `source_verification_status`, `source_verified`, `operation`, `url`, `site`, or `as_dict()` for valid results rejects this local completion claim. | PagePublishResult properties and ledger export | `tests/unit/test_site.py` |
| R4 | Existing publish and adjacent workflows remain green. | `TestSitePageAccessor` plus `TestSitePagesAccessor` passed 80 tests; `tests/unit/test_site.py tests/unit/test_page.py` passed 437 tests; full unit tests passed 1606 tests. | Regressing publish create/edit selection, source verification, metadata order, visibility controls, result fields, page source/revision/vote/file behavior, or source iterator behavior rejects this local completion claim. | Site/page workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted publish and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `fd6be80 fix(site): validate publish result status fields`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_source_matches -q` failed 4 tests before the source-verification fix; every malformed `source_matches` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_source_matches -q` passed 4 tests after adding `source_matches` validation.
- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_boolean_status_fields -q` failed 16 tests before status-flag validation; every malformed metadata/create status field reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_source_matches tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_boolean_status_fields -q` passed 20 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_source_matches tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_boolean_status_fields -q` passed 22 tests.
- `uv run mypy src/wikidot/module/site.py tests/unit/test_site.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_site.py::TestSitePagesAccessor -q` passed 80 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 437 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 1606 tests.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PagePublishResult(source_matches="false")`, `0`, `1`, and `[]` raise `ValueError("source_matches must be a boolean or None")`.
- `PagePublishResult(tags_updated=None)`, `parent_updated="false"`, `metas_updated=0`, `created=1`, and the covered malformed field/value combinations raise `ValueError("<field> must be a boolean")`.
- Valid `source_matches=True`, `False`, and `None`, valid boolean metadata flags, and valid `created` values continue to work.
- Existing aggregate properties, source-verification status labels, URL/site properties, operation labels, and `as_dict()` output remain unchanged for valid results.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PagePublishResult` is the durable object shape behind browser-free publish audit ledgers. Constructor validation keeps malformed local status state out of result records while preserving the existing `Site.page.publish(...)` path that constructs these fields from real boolean outcomes.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free page publishing, source verification, metadata updates, post-save visibility resolution, publish-result aggregate fields, and publish-result audit dictionaries.
- Existing local drafts covered publish orchestration, publish inputs, source normalizers, create/edit outcome, source-verification status, metadata counts, URL/site ledger fields, and visibility controls, but did not cover direct `PagePublishResult(...)` status-field construction.
- The focused RED failures showed malformed constructor values were accepted as frozen dataclass state. The GREEN regressions cover malformed `source_matches`, malformed metadata/create flags, valid aggregate properties, valid audit dictionaries, publish accessor behavior, source iterator behavior, site/page workflows, and full unit behavior.
- This slice only validates publish-result status fields. It does not change publish request construction, page saves, source refreshes, source comparisons, metadata writes, visibility retry behavior, page URL construction, site derivation, result dictionary keys, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects numeric stand-ins such as `0` and `1` for publish-result booleans. Callers loading status fields from JSON, YAML, CLI flags, spreadsheets, generated structures, or ledgers should convert them to real booleans before constructing `PagePublishResult`.
