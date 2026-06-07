# PR Draft: Validate Publish Result Page ID Coherence

## Summary

`PagePublishResult` is the audit-friendly result object returned by `Site.page.publish(...)` and also useful for direct tests, generated publish ledgers, migration records, source-verification reports, and retry rows. Issue 435 validates the `page_id` type, Issue 441 validates that `page` is a real `Page`, and Issue 070 exports both values through `as_dict()`. One coherence gap remained: direct construction could combine `page=Page(_id=12345, fullname="page-a")` with `page_id=67890`. The result object then exported one loaded page identity alongside a different saved-page ID.

This change validates publish-result page identity during `PagePublishResult.__post_init__` after existing `page_id`, status-field, and `page` shape checks. When the retained `page._id` is already loaded, it must equal the explicit `page_id`. Mismatches raise `ValueError("page_id must match the result page")` before contradictory result state is stored. When `page._id is None`, the constructor preserves the explicit result `page_id` without triggering page-ID lookup or mutating the retained `Page`. Valid publish rows, audit dictionaries, aggregate status properties, create/edit publish paths, source verification, and metadata-update behavior remain unchanged.

## Outcome

Directly constructed publish-result rows cannot combine a loaded `Page` object for one page ID with a different exported `page_id`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.page.publish(...)`, direct `PagePublishResult(...)` construction in tests or local ledgers, browser-free publishing, source verification logs, migration scripts, generated page inventories, metadata update reports, retry ledgers, or durable publish audit exports.

## Current Evidence

Prior publish-result drafts establish the surrounding behavior. [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md) adds the publish helper. [024-pr-publish-create-outcome.md](024-pr-publish-create-outcome.md) adds the create/edit outcome field. [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md) adds aggregate status properties. [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md) exports publish-result page identity and status fields through `as_dict()`. [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md) validates status fields. [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md) validates `page_id` shape, and [441-pr-validate-publish-result-page-field.md](441-pr-validate-publish-result-page-field.md) validates the result page field while explicitly leaving page IDs, page fullnames, site identity, and cached state outside scope. [489-pr-validate-page-constructor-id-field.md](489-pr-validate-page-constructor-id-field.md) validates direct `Page._id` shape, but it does not validate publish-result coherence between a valid page object and a valid result page ID.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 435. Issue 435 rejects non-integer, boolean, and missing `page_id` values; it does not validate whether a valid integer `page_id` matches the retained `Page`.

This is not a duplicate of Issue 441. Issue 441 validates that `PagePublishResult.page` is a `Page` instance and explicitly does not validate page IDs, page fullnames, site identity, or cached state.

This is not a duplicate of Issue 489. Issue 489 validates optional `Page._id` cache shape on `Page` construction; it does not validate the relationship between a `Page` object and a separate `PagePublishResult.page_id`.

This is not a duplicate of Issues 017, 024, 028, or 070. Those slices cover publish orchestration and result-field ergonomics, not direct constructor identity coherence.

No upstream issue was filed from this local workspace.

## Changes

- Add `PagePublishResult` page-ID coherence validation for direct construction.
- Reject result rows where the retained `page._id` is loaded and differs from `page_id`.
- Preserve explicit `page_id` values for pages whose `_id` cache is still unloaded.
- Preserve existing malformed `page_id`, malformed status-field, malformed `page`, aggregate status, audit export, source-verification, create/edit, and metadata update behavior.
- Preserve side-effect-free construction: the new check does not call `Page.id`, perform AMC lookup, or mutate `page._id`.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Publish-result ledger identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PagePublishResult(page=Page(_id=12345), page_id=67890, ...)` must reject the mismatched loaded page ID with `ValueError("page_id must match the result page")` before storing result state. |
| R2 | `PagePublishResult(page=Page(_id=None), page_id=12345, ...)` must remain valid and must not trigger page-ID lookup or mutate the retained `Page`. |
| R3 | Existing malformed `page_id`, malformed `page`, malformed `source_matches`, malformed boolean status fields, aggregate status properties, and audit export behavior must remain unchanged. |
| R4 | Existing publish create/edit sequencing, post-save page-ID resolution, source verification, metadata updates, and source/page/revision/search workflows must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Loaded page-ID mismatches fail at the public constructor boundary. | `TestSitePageAccessor.test_publish_result_rejects_page_id_that_does_not_match_page` failed RED with `DID NOT RAISE`, then passed GREEN after `PagePublishResult.__post_init__` called the coherence preflight. | Accepting `page._id=12345` with `page_id=67890`, exporting an audit row with contradictory page identity, or deferring the mismatch to later property access rejects this local completion claim. | `PagePublishResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Unloaded pages preserve explicit result IDs without network side effects. | `TestSitePageAccessor.test_publish_result_accepts_page_id_when_page_id_is_unloaded` passed with `page._id is None` and a mocked `amc_request` that was not called. | Calling `Page.id`, performing AMC lookup, mutating `page._id`, or rejecting unloaded pages with valid explicit `page_id` values rejects this local completion claim. | `PagePublishResult` constructor | `tests/unit/test_site.py` |
| R3 | Existing constructor diagnostics and audit exports stay stable. | Focused publish-result constructor coverage passed 35 tests covering malformed pages, malformed page IDs, mismatched page IDs, unloaded page IDs, malformed `source_matches`, malformed booleans, aggregate status, and audit export. | Changing `ValueError("page_id must be an integer")`, `ValueError("page must be a Page")`, `ValueError("source_matches must be a bool or None")`, boolean-field diagnostics, aggregate properties, or `as_dict()` output rejects this local completion claim. | Publish-result validation order and exports | `tests/unit/test_site.py` |
| R4 | Existing site/page/source/revision/search workflows remain green. | `tests/unit/test_site.py` passed 286 tests. Adjacent site/page/page-source/page-revision/search coverage passed 753 tests, and full unit coverage passed 2728 tests. | Regressing publish paths, create/edit page-ID resolution, source verification, metadata updates, source iterator behavior, page source caches, page revision caches, search pagination, or adjacent page workflows rejects this local completion claim. | Site and page workflows | `tests/unit` |
| R5 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic valid `Page` and `PagePublishResult` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `3bb7e5e fix(site): validate publish result page id coherence`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_page_id_that_does_not_match_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN regression: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_page_id_that_does_not_match_page -q` passed 1 test.
- Focused publish-result constructor coverage: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_pages tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_source_matches tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_page_ids tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_page_id_that_does_not_match_page tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_accepts_page_id_when_page_id_is_unloaded tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_boolean_status_fields tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exposes_aggregate_operation_statuses tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 35 tests.
- Site coverage: `uv run pytest tests/unit/test_site.py -q` passed 286 tests.
- Adjacent site/page/source/revision/search coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_revision.py tests/unit/test_search_pages_query.py -q` passed 753 tests.
- `uv run pytest tests/unit -q` passed 2728 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PagePublishResult(page=Page(_id=12345), page_id=67890, ...)` raises `ValueError("page_id must match the result page")` before storing result state.
- `PagePublishResult(page=Page(_id=None), page_id=12345, ...)` remains valid and leaves `page._id is None`.
- Constructor validation does not call `Page.id`, perform AMC lookup, or mutate retained page state.
- Existing `page_id` type validation, `page` shape validation, `source_matches` validation, boolean status validation, aggregate status properties, and `as_dict()` output remain unchanged.
- Existing `Site.page.publish(...)` create/edit flows, post-save page-ID resolution, source verification, metadata updates, page source/revision/search workflows, and adjacent unit coverage remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PagePublishResult` is the durable object shape behind browser-free publish audit ledgers. It carries both a retained `Page` object and an explicit saved-page ID. If those identities disagree after the page ID is already loaded, downstream ledgers can persist a contradictory successful publish row. Constructor coherence validation keeps direct fixtures, rehydrated rows, and generated ledgers internally consistent while preserving unloaded-page construction and the normal publish path that resolves `page_id` from the saved page.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `PagePublishResult(page=loaded_page, page_id=different_id, ...)` construction silently accepted a contradictory row.
- Existing local drafts covered browser-free publishing, create/edit outcome, aggregate result fields, audit export, source-match status, page-ID type validation, page-field shape validation, and direct `Page._id` shape validation, but did not validate that a loaded result page ID matches the explicit publish-result page ID.
- This slice only validates constructor-time coherence when `page._id` is already loaded. It does not change publish request construction, source verification, metadata writes, post-save visibility polling, page-ID acquisition, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally reads the private `_id` cache rather than the public `Page.id` property. `Page.id` may perform a network lookup when the cache is empty, while publish-result construction should remain a side-effect-free ledger operation. The new rule is therefore strict only when the page already knows its ID and permissive when the result row legitimately carries the saved page ID for an otherwise unloaded `Page`.
