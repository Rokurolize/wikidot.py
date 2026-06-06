# PR Draft: Validate Publish Result Page Field

## Summary

`PagePublishResult` is the ledger-friendly result object returned by `Site.page.publish(...)`. Prior local slices validated publish-result status fields and `page_id`, but the public constructor still accepted malformed `page` values such as `None`, booleans, strings, dictionaries, and arbitrary objects. Those malformed values could become frozen result state and later break `url`, `site`, or `as_dict()` access outside the constructor boundary.

This change validates `PagePublishResult.page` at initialization. Malformed values now raise `ValueError("page must be a Page")`. Existing publish result status fields, create/edit outcome, audit export, source-verification fields, metadata counters, and publish workflows for valid `Page` objects remain unchanged.

## Outcome

Callers cannot silently create malformed publish-result ledger objects with non-`Page` parent state, while valid publish results from create and edit flows continue to return real `Page` instances.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)`, direct `PagePublishResult(...)` construction in tests or local ledgers, browser-free page publishing, publish audit rows, migration scripts, generated page inventories, source verification logs, or metadata update reports.

## Current Evidence

Local rollout-backed drafts repeatedly identify browser-free publishing and publish-result ledgers as practical workflow surfaces. Existing drafts [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [232-pr-publish-verification-request-status.md](232-pr-publish-verification-request-status.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md), and [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md) establish publish result audit fields, operation state, metadata status, source verification state, status validation, and page-ID validation as active operational boundaries.

Those prior slices are not duplicates. They covered publish flow behavior, result audit fields, status fields, and `page_id` validation. None validates direct `PagePublishResult(page=...)` construction before malformed page state becomes stored dataclass state.

## Related Issue

Builds directly on [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [148-pr-publish-result-operation-label.md](148-pr-publish-result-operation-label.md), [231-pr-publish-result-url.md](231-pr-publish-result-url.md), [257-pr-publish-source-verification-status.md](257-pr-publish-source-verification-status.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md), and [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult.page` validation.
- Reject non-`Page` values with `ValueError("page must be a Page")`.
- Preserve existing `page_id`, `source_matches`, `tags_updated`, `parent_updated`, `metas_updated`, and `created` validation.
- Update publish-result tests so successful publish and direct publish-result construction use real `Page` objects instead of generic mocks.
- Preserve existing publish create/edit flows, source verification, metadata updates, post-save visibility retry, aggregate status properties, URL/site fields, and audit dictionary output for valid results.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Publish-result ledger parent-state integrity

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PagePublishResult(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` when every other publish-result field is valid. |
| R2 | Valid `Page` instances must remain valid and preserve existing publish-result fields and ledger exports. |
| R3 | Existing `PagePublishResult.page_id`, `source_matches`, boolean status field, and `created` validation must remain unchanged. |
| R4 | Existing `Site.page.publish(...)` create, edit, source verification, metadata update, post-save visibility retry, create/edit operation label, aggregate status, URL, site, and audit-record behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, publish-result tests, site tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor pages fail at the public dataclass boundary. | `TestSitePageAccessor.test_publish_result_rejects_malformed_pages` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting publish-result rows with non-`Page` parent state rejects this local completion claim. | PagePublishResult constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid page semantics stay green. | Existing valid publish-result aggregate status, audit dictionary, create/edit publish results, source verification, visibility retry, site tests, and full unit tests passed after the validator was added. | Rejecting valid `Page` instances, changing `url`, `site`, `page_id`, `operation`, metadata counters, source-verification fields, or `as_dict()` for valid rows rejects this local completion claim. | PagePublishResult properties and ledger export | `tests/unit/test_site.py`, `tests/unit` |
| R3 | Existing direct publish-result validators stay intact. | Focused GREEN included malformed `source_matches`, malformed `page_id`, and malformed boolean status field coverage through `TestSitePageAccessor`. | Weakening Issue 428 or Issue 435 behavior, accepting malformed status fields, accepting malformed page IDs, accepting malformed source-match state, or changing diagnostics rejects this local completion claim. | PagePublishResult constructor | `tests/unit/test_site.py` |
| R4 | Existing publish workflows remain green. | `tests/unit/test_site.py::TestSitePageAccessor` passed 71 tests, `tests/unit/test_site.py` passed 246 tests, and full unit tests passed 1692 tests. | Regressing create/edit detection, source verification, metadata updates, post-save visibility retry, audit exports, URL/site fields, or adjacent site workflows rejects this local completion claim. | Site.page.publish and adjacent site workflows | `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, publish-result tests passed, site tests passed, full unit passed, ruff, format, mypy, source-file pyright, and whitespace checks passed; pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `efec62a fix(site): validate publish result page`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_pages -q` failed 5 tests before the fix; every malformed `page` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_pages -q` passed 5 tests.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 71 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 246 tests.
- `uv run pytest tests/unit -q` passed 1692 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src/wikidot/module/site.py tests/unit/test_site.py` ran but failed with 12 existing `test_site.py` typing issues, including fixture pages with `None` values and intentional invalid-input tests. `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file passes pyright.

## Acceptance Criteria

- `PagePublishResult(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- Valid `Page` instances remain valid as `page`.
- Existing `page_id`, `source_matches`, boolean status field, and `created` validation remains unchanged.
- Existing `url`, `site`, `operation`, `metadata_update_count`, `metadata_updated`, `source_verification_requested`, `source_verification_status`, `source_verified`, and `as_dict()` behavior remains unchanged for valid rows.
- Existing `Site.page.publish(...)` create/edit paths, source verification, metadata updates, and post-save visibility retry remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PagePublishResult.page` is the parent context behind browser-free publishing, publish audit exports, generated page inventories, migration checks, source verification logs, and metadata update reports. Constructor validation keeps malformed local parent-page state out of publish-result records while preserving the existing publish path that returns real `Page` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free publish helpers, publish result audit records, URL/site exports, source verification state, metadata update counts, create/edit operation labels, status validation, and page-ID validation.
- Existing local drafts covered publish flow behavior, operation/status/audit fields, `url`, `site`, `source_matches`, metadata counters, `page_id`, and direct status validation, but did not cover direct `PagePublishResult(page=...)` construction.
- The focused RED failures showed invalid constructor page fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, dictionary, and arbitrary object page values, plus publish success paths and direct publish-result validators.
- This slice only validates publish-result parent-page constructor input. It does not change publish request construction, page saving, source verification comparison, metadata writes, post-save visibility retry policy, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `page` is a `Page` instance. It does not validate page IDs, page fullnames, site identity, cached source state, metadata freshness, or client authentication at `PagePublishResult` construction time; those are separate page object and publish workflow concerns.
