# PR Draft: Validate Non-Negative Publish Result Page IDs

## Summary

`PagePublishResult` is the audit-friendly result object returned by `Site.page.publish(...)` and used directly by tests, generated publish ledgers, migration records, source-verification reports, and retry rows. Existing local drafts validate `page_id` as a non-boolean integer, validate coherence when the retained `Page` already has a loaded `_id`, and validate direct `Page`/create-edit page IDs as non-negative. One result-record boundary remained open: a direct `PagePublishResult(page=Page(_id=None), page_id=-1, ...)` could store and export an impossible negative saved-page ID.

This change rejects negative `PagePublishResult.page_id` values during construction with `ValueError("page_id must be non-negative")`. It deliberately preserves the existing malformed-type diagnostic, loaded-page coherence diagnostic, unloaded-page construction for valid IDs, zero-ID compatibility, aggregate status properties, URL/site properties, and `as_dict()` output for valid result rows.

## Outcome

Publish result records can no longer store negative page IDs, while valid direct rows, rows with unloaded `Page` objects, and normal `Site.page.publish(...)` outputs keep their existing behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page publishing, source verification, metadata updates, generated publish audit ledgers, retry ledgers, migration scripts, local fixtures, or serialized and rehydrated `PagePublishResult` records.

## Current Evidence

Publish-result drafts [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [232-pr-publish-verification-request-status.md](232-pr-publish-verification-request-status.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md), [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md), [441-pr-validate-publish-result-page-field.md](441-pr-validate-publish-result-page-field.md), and [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md) establish `PagePublishResult` as a practical durable ledger boundary.

This slice is not a duplicate of [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md), [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), or [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md). Issue 435 rejects missing, boolean, string, float, list, and other non-integer `page_id` values, but still accepts negative integers. Issue 603 rejects a valid integer `page_id` that contradicts an already-loaded retained `Page._id`, but it intentionally preserves explicit result IDs for pages whose `_id` is still unloaded. Issue 639 validates direct `Page._id`, `Page.id` assignment, and `Page.create_or_edit(..., page_id=...)`, not publish-result ledger rows.

## Related Issue / Non-Duplicate Analysis

Builds directly on [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md), [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), and [639-pr-validate-non-negative-page-ids.md](639-pr-validate-non-negative-page-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject negative `PagePublishResult.page_id` values with `ValueError("page_id must be non-negative")`.
- Validate the non-negative range after the existing non-boolean integer type check and before page/page-id coherence validation.
- Preserve `ValueError("page_id must be an integer")` for malformed non-integer and boolean values.
- Preserve `ValueError("page_id must match the result page")` for loaded-page/result-ID mismatches.
- Preserve valid unloaded-page construction, zero page IDs, positive page IDs, aggregate properties, URL/site properties, operation labels, source-verification properties, metadata properties, and `as_dict()` output.
- Leave live Wikidot behavior, pushes, upstream Issues, and upstream PRs unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Publish result ledger state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PagePublishResult(page=Page(_id=None), page_id=-1, ...)` and `page_id=-100` must raise `ValueError("page_id must be non-negative")` before storing result state or triggering page-ID lookup. |
| R2 | Existing malformed non-integer and boolean `page_id` diagnostics must remain `ValueError("page_id must be an integer")`. |
| R3 | Existing loaded-page/result-ID mismatch diagnostics must remain `ValueError("page_id must match the result page")`. |
| R4 | `page_id=0` must remain valid for compatibility, and valid positive unloaded-page result IDs must remain valid without network side effects. |
| R5 | Existing aggregate status properties, source-verification properties, URL/site properties, operation labels, metadata properties, and `as_dict()` output must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, page source text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, publish-result/page-accessor tests, adjacent site/page/search tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative publish-result page IDs cannot become result state. | `test_publish_result_rejects_negative_page_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_publish_result_page_id(...)` rejected values below zero. | Accepting negative values, coercing them to zero, relying on loaded-page coherence, or triggering page-ID lookup rejects this local completion claim. | `PagePublishResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Existing malformed-type diagnostics remain stable. | `test_publish_result_rejects_malformed_page_ids` passed in the focused RED and GREEN commands. | Changing `page_id must be an integer`, accepting booleans, or coercing strings/floats/lists rejects this local completion claim. | Publish-result page-ID type validation | `tests/unit/test_site.py` |
| R3 | Existing page/page-ID coherence diagnostics remain stable. | `test_publish_result_rejects_page_id_that_does_not_match_page` passed in the focused RED and GREEN commands. | Replacing the loaded-page mismatch diagnostic with a range diagnostic, accepting contradictory rows, or deferring failure to `as_dict()` rejects this local completion claim. | Publish-result coherence validation | `tests/unit/test_site.py` |
| R4 | Zero and valid unloaded-page IDs remain valid without network side effects. | `test_publish_result_accepts_zero_page_id` and `test_publish_result_accepts_page_id_when_page_id_is_unloaded` passed in focused coverage, and the unloaded-page test asserts no AMC request. | Rejecting zero, requiring loaded page IDs, calling `Page.id`, mutating `page._id`, or performing AMC work rejects this local completion claim. | Result-row compatibility | `tests/unit/test_site.py` |
| R5 | Publish-result properties and adjacent workflows stay green. | The publish/page accessor class passed 92 tests, adjacent site/page/search suites passed 656 tests, and the full unit suite passed 2947 tests. | Regressing aggregate status properties, audit dictionaries, source verification, metadata fields, page/source workflows, search behavior, or any existing unit test rejects this local completion claim. | Site/page workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_search_pages_query.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Page` and `PagePublishResult` objects only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page-accessor tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `033d451 fix(site): validate publish result page id range`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_page_ids tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_negative_page_ids tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_accepts_zero_page_id tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_page_id_that_does_not_match_page tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_accepts_page_id_when_page_id_is_unloaded tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_boolean_status_fields tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed 2 negative publish-result page-ID cases before the fix; 27 malformed/coherence/zero/status/audit guards stayed green.
- GREEN: the same focused command passed 29 tests after the non-negative guard was added.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left both files unchanged.
- Re-running the same focused command after formatting passed 29 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 92 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_search_pages_query.py -q` passed 656 tests.
- `uv run pytest tests/unit -q` passed 2947 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PagePublishResult(page=Page(_id=None), page_id=-1, ...)` raises `ValueError("page_id must be non-negative")`.
- `PagePublishResult(page=Page(_id=None), page_id=-100, ...)` raises the same error.
- The negative-page-ID validation does not call AMC, does not call `Page.id`, and does not mutate `page._id`.
- `PagePublishResult(page_id=None)`, booleans, strings, floats, and lists still raise `page_id must be an integer`.
- A loaded retained page with a different valid integer `page_id` still raises `page_id must match the result page`.
- `page_id=0` remains valid when the retained page identity also carries zero.
- Valid positive `page_id` values for unloaded pages remain valid and do not trigger page-ID lookup.
- Existing publish-result aggregate properties and `as_dict()` output remain unchanged for valid rows.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PagePublishResult` rows are durable publish ledgers. A negative page ID is impossible saved-page identity state but previously looked like a valid integer to the result constructor, especially when the retained `Page` object had not loaded its own ID. Non-negative validation keeps publish result rows internally plausible without requiring a stronger positive-only invariant or triggering network lookups for unloaded pages.

## Local Evidence

- Local rollout-backed drafts repeatedly use browser-free publishing, post-save page-ID resolution, source verification, metadata updates, publish-result aggregate fields, and publish-result audit dictionaries.
- Existing local drafts covered publish-result page-ID type validation, retained-page/result-ID coherence, and direct `Page`/create-edit non-negative page IDs, but did not cover negative integer `PagePublishResult.page_id` values when the retained `Page` is unloaded.
- The focused RED failure showed negative publish-result page IDs were accepted as stored result state before this slice.
- This slice only validates non-negative publish-result page IDs. It does not change publish request construction, page saves, source refreshes, source comparisons, metadata writes, visibility retry behavior, page URL construction, site derivation, result dictionary keys, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative publish-result page IDs only. It does not require positive IDs and does not force unloaded retained pages to resolve their IDs, preserving the side-effect-free ledger-construction behavior added by the prior coherence slice.
