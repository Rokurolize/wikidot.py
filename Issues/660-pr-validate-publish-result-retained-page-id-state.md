# PR Draft: Validate Publish Result Retained Page ID State

## Summary

`PagePublishResult` validates its explicit `page_id` and validates that a loaded result `page._id` matches that explicit ID, but the coherence check read retained `page._id` directly. A corrupted or rehydrated result page could therefore pass malformed retained identity into the comparison. The most visible bug was boolean equality: `page._id=True` with `page_id=1` and `page._id=False` with `page_id=0` were accepted because Python booleans compare equal to integers.

This change validates the retained optional `page._id` with the existing page constructor ID validator before comparing it to the explicit publish-result `page_id`. Malformed retained IDs now raise deterministic `ValueError("page.id must be an integer or None")`, negative retained IDs now raise `ValueError("page.id must be non-negative or None")`, loaded valid mismatches still raise `ValueError("page_id must match the result page")`, unloaded pages still keep explicit result IDs without lookup, and zero-ID compatibility remains intact.

## Outcome

Publish-result ledger rows can no longer silently accept malformed retained result-page identity or misclassify corrupted `Page._id` as a normal loaded-page mismatch.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)`, `PagePublishResult`, `PagePublishResult.as_dict()`, browser-free publish audit ledgers, source-verification reports, retry records, generated page inventories, migration scripts, serialized result rows, or rehydrated `Page` fixtures.

## Current Evidence

Local rollout-backed drafts establish publish result rows and page identity as practical durable ledger surfaces. [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [232-pr-publish-verification-request-status.md](232-pr-publish-verification-request-status.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md), [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md), [441-pr-validate-publish-result-page-field.md](441-pr-validate-publish-result-page-field.md), [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), [651-pr-validate-non-negative-publish-result-page-ids.md](651-pr-validate-non-negative-publish-result-page-ids.md), and [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md) cover audit export, status fields, page fields, explicit result page IDs, valid-ID coherence, non-negative result IDs, and public `Page.id` retained-state validation.

This slice is not a duplicate of those drafts. Issue 435 validates the explicit `PagePublishResult.page_id` field. Issue 441 validates the `page` object type. Issue 603 validates loaded-page/result-ID coherence when retained `page._id` is already a valid ID. Issue 651 validates the explicit result `page_id` range, especially when the retained page is unloaded. Issue 658 validates the public `Page.id` getter, but publish-result construction intentionally avoids `Page.id` so unloaded result pages do not trigger a page-ID lookup. None of those drafts validates corrupted retained `page._id` before the side-effect-free publish-result coherence comparison.

## Related Issue / Non-Duplicate Analysis

Builds directly on [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), [651-pr-validate-non-negative-publish-result-page-ids.md](651-pr-validate-non-negative-publish-result-page-ids.md), [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md), and [659-pr-validate-source-result-page-id-retained-state.md](659-pr-validate-source-result-page-id-retained-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `page._id` inside `PagePublishResult` page/page-ID coherence before comparing it to the explicit `page_id`.
- Reject malformed retained IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer or None")`.
- Reject negative retained IDs such as `-1` with `ValueError("page.id must be non-negative or None")`.
- Preserve `page._id is None` as side-effect-free unloaded result-page state.
- Preserve `page._id == 0`, valid positive retained IDs, explicit `page_id` validation, valid loaded mismatch diagnostics, publish-result status fields, aggregate properties, and audit export.

## Type Of Change

- Input validation
- Publish-result ledger state integrity
- Retained page-ID hardening
- Side-effect-free constructor preservation
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PagePublishResult(...)` must reject malformed retained `page._id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("page.id must be an integer or None")` before comparing with `page_id`. |
| R2 | `PagePublishResult(...)` must reject retained negative `page._id` values such as `-1` with `ValueError("page.id must be non-negative or None")` before comparing with `page_id`. |
| R3 | Malformed, negative, and unloaded retained result-page ID reads must not call `Page.id`, `PageCollection.get_page_ids()`, AMC request helpers, or live Wikidot. |
| R4 | `page._id is None` must still allow an explicit valid result `page_id` without lookup, and `page._id == 0` must remain valid when `page_id == 0`. |
| R5 | Existing explicit `page_id` type/range validation, loaded valid-ID mismatch diagnostics, publish-result page/source/status validation, aggregate properties, audit export, source-result adjacency, site workflows, and adjacent page/source workflows must remain green. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, publish-result accessor tests, source-result accessor tests, site tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained result-page IDs fail before coherence comparison. | `test_publish_result_rejects_malformed_retained_page_ids` failed RED for five malformed values: booleans and `12345.0` were accepted, while `"12345"` and `[]` raised the generic mismatch diagnostic; the test passed GREEN after retained `page._id` was validated. | Accepting boolean retained IDs, coercing strings/floats, allowing generic mismatch to mask malformed retained state, or changing the retained-page diagnostic rejects this local completion claim. | `PagePublishResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Negative retained result-page IDs fail before coherence comparison. | `test_publish_result_rejects_negative_retained_page_id` failed RED with the generic mismatch diagnostic, then passed GREEN after optional retained page-ID validation. | Returning a mismatch diagnostic for negative retained page state, accepting negative values, or coercing them to zero rejects this local completion claim. | `PagePublishResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Validation remains side-effect-free. | New malformed and negative tests patch `PageCollection.get_page_ids` and assert it is not called; the existing unloaded-page test still asserts no AMC request and unchanged `page._id is None`. | Calling `Page.id`, performing page-ID lookup, mutating `page._id`, or performing AMC work rejects this local completion claim. | Publish-result constructor | `tests/unit/test_site.py` |
| R4 | Unloaded and zero page IDs remain compatible. | `test_publish_result_accepts_page_id_when_page_id_is_unloaded` passed for `None`, and `test_publish_result_accepts_zero_page_id` passed for `0` through both property and `as_dict()`. | Rejecting `None`, rejecting zero, or triggering lookup for unloaded result rows rejects this local completion claim. | Side-effect-free publish result rows | `tests/unit/test_site.py` |
| R5 | Existing publish-result and adjacent workflows remain green. | Focused publish-result coverage passed 35 tests, `TestSitePageAccessor` passed 98 tests, `TestSitePagesAccessor` passed 47 tests, `tests/unit/test_site.py` passed 317 tests, adjacent site/page/source/constructor/file/revision/votes suites passed 1130 tests, and full unit passed 3011 tests. | Regressing publish audit dictionaries, explicit result page-ID validation, valid loaded mismatch diagnostics, source iterator rows, source-result validation, publish paths, page source/revision/vote/file workflows, site workflows, or any unit test rejects this local completion claim. | Publish result and adjacent workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_page_source.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic `Page` and `PagePublishResult` objects only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d6e12bd fix(site): validate publish result retained page ids`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_page_ids tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_negative_page_ids tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_accepts_zero_page_id tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_page_id_that_does_not_match_page tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_retained_page_ids tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_negative_retained_page_id tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_accepts_page_id_when_page_id_is_unloaded tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_boolean_status_fields tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed 6 retained page-ID coherence cases before the fix; 29 explicit page-ID, zero, valid mismatch, unloaded, status, aggregate, and audit guards passed.
- GREEN: the same focused command passed 35 tests after validating retained `page._id` before publish-result coherence comparison.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 98 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor -q` passed 47 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 317 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_constructor.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 1130 tests.
- `uv run pytest tests/unit -q` passed 3011 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PagePublishResult(page=page, page_id=1, ...)` raises `ValueError("page.id must be an integer or None")` when retained `page._id is True`.
- `PagePublishResult(page=page, page_id=0, ...)` raises `ValueError("page.id must be an integer or None")` when retained `page._id is False`.
- The same constructor raises `ValueError("page.id must be an integer or None")` when retained `page._id` is `"12345"`, `12345.0`, or `[]`.
- The same constructor raises `ValueError("page.id must be non-negative or None")` when retained `page._id` is `-1`.
- Malformed and negative retained page-ID reads do not call `PageCollection.get_page_ids()`, AMC helpers, or live Wikidot.
- `page._id is None` still allows explicit `page_id=12345` without lookup or retained-page mutation.
- `page._id == 0` with `page_id == 0` remains valid and exports `0`.
- Existing explicit `page_id` malformed-type and non-negative diagnostics remain unchanged.
- Existing valid loaded-page/result-ID mismatches still raise `ValueError("page_id must match the result page")`.
- Existing publish-result audit export, aggregate status properties, source-result adjacency, site workflows, and adjacent page/source workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PagePublishResult` is designed as a durable browser-free publish ledger row. It must preserve side-effect-free construction for unloaded pages, but it should not use impossible retained page identity to decide whether a saved-page ID is coherent. Validating retained `page._id` before comparison keeps corrupted or rehydrated page state from becoming a successful publish result row while preserving explicit result IDs for unloaded pages.

## Local Evidence

- Existing local drafts covered publish-result audit export, status fields, site fields, explicit result `page_id` type/range validation, result page type validation, valid-ID coherence, public `Page.id` getter validation, and source-result retained page-ID validation.
- None of those drafts covered the direct `PagePublishResult` coherence check using malformed retained `page._id` without validation because it bypasses `Page.id` to preserve unloaded-page no-lookup behavior.
- The focused RED failure showed booleans could be accepted as retained page IDs when they compared equal to explicit result IDs, and other malformed or negative retained values could be misreported as ordinary page/result mismatches. The GREEN regressions cover malformed rejection, negative rejection, no lazy lookup, no AMC work, unloaded-`None` compatibility, zero-ID compatibility, explicit result-ID validation, valid mismatch validation, existing audit export, and adjacent source-result compatibility.
- This slice only validates retained optional page IDs at the publish-result coherence boundary. It does not change `Page.id`, page-ID acquisition URLs, source verification, metadata writes, post-save visibility polling, publish sequencing, source-result behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally does not call `Page.id` because unloaded publish-result pages must remain side-effect-free. The validator checks only the retained optional value already present on the `Page` object before the existing valid-ID mismatch comparison.
