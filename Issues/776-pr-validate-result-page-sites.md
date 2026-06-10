# PR Draft: Validate Result Page Sites

## Summary

`PageSourceResult` and `PagePublishResult` are ledger-friendly result objects used by browser-free source collection and publishing workflows. Existing constructor hardening validates the wrapped `page` object, page IDs, source ownership, source/error outcome state, publish status booleans, and retained page-ID state. One retained-state boundary remained: a valid `Page` whose public `site` field was later replaced with a dictionary, mock, or other non-`Site` value could still become a successful frozen result row. Later `site`, `url`, or `as_dict()` access would then fail outside the constructor boundary or derive ledger state from malformed page ownership.

This change validates `page.site` during `PageSourceResult.__post_init__` and `PagePublishResult.__post_init__`. Malformed retained page sites now raise `ValueError("page.site must be a Site")` before result state is accepted. Valid source-result rows, failed source-result rows, publish-result rows, site/url/fullname/page-ID fields, source ownership checks, publish-result status fields, source iteration, publishing, and ledger exports remain unchanged.

## Outcome

Source and publish result rows cannot carry malformed retained page-site state into durable ledger exports. The failure is reported at direct construction time without page-ID lookup, AMC request work, source fetching, publishing, metadata writes, or live Wikidot access.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.pages.iter_sources(...)`, direct `PageSourceResult(...)` construction, `Site.page.publish(...)`, direct `PagePublishResult(...)` construction, generated source/publish ledgers, migration scripts, retry rows, source verification reports, or multi-site audit exports.

## Current Evidence

Local rollout-backed drafts repeatedly identify source-result and publish-result ledgers as practical workflow surfaces. Existing drafts added source-result fallback behavior, source-result fields, page IDs, site fields, source ownership validation, retained source-owner page-ID validation, publish-result audit dictionaries, publish-result status validation, publish-result page validation, page-ID coherence, and retained publish-result page-ID validation. Those slices did not validate a retained `Page.site` after direct `Page` construction had already succeeded.

The focused RED tests demonstrated the gap: `PageSourceResult(page=page_with_dict_site, source=None, error=NotFoundException(...))` and `PagePublishResult(page=page_with_dict_site, page_id=..., ...)` both completed without raising before this fix.

## Related Issue / Non-Duplicate Analysis

Builds on [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [428-pr-validate-publish-result-status-fields.md](428-pr-validate-publish-result-status-fields.md), [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md), [440-pr-validate-source-result-page-field.md](440-pr-validate-source-result-page-field.md), [441-pr-validate-publish-result-page-field.md](441-pr-validate-publish-result-page-field.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [602-pr-validate-source-result-source-ownership.md](602-pr-validate-source-result-source-ownership.md), [603-pr-validate-publish-result-page-id-coherence.md](603-pr-validate-publish-result-page-id-coherence.md), [660-pr-validate-publish-result-retained-page-id-state.md](660-pr-validate-publish-result-retained-page-id-state.md), and [661-pr-validate-source-result-retained-owner-page-id-state.md](661-pr-validate-source-result-retained-owner-page-id-state.md).

This is not a duplicate of Issues 440 or 441. Those slices validate that `page` is a `Page` instance and explicitly leave retained site identity outside their scope.

This is not a duplicate of Issue 486. That slice validates direct `Page(site=...)` construction. It cannot cover a valid page whose mutable `site` field is later corrupted before result-row construction.

This is not a duplicate of Issues 602, 660, or 661. Those validate source ownership and retained page-ID state, not retained page-site type integrity for failure source rows or publish result rows.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared result-page-site validator in `wikidot.module.site`.
- Call it from `PageSourceResult.__post_init__` after page/source/error/outcome validation and before source ownership comparison.
- Call it from `PagePublishResult.__post_init__` after page/page-ID validation and before result state is accepted.
- Add focused regressions for malformed retained `page.site` values on source-result and publish-result construction.
- Preserve existing source-result and publish-result public fields, validation order for existing malformed inputs, and ledger exports.

## Type Of Change

- Input validation
- Public result-object constructor hardening
- Retained page-site state integrity
- Ledger/export safety improvement
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult(page=valid_page_with_malformed_site, source=None, error=Exception(...))` must raise `ValueError("page.site must be a Site")` before accepting result state. |
| R2 | `PagePublishResult(page=valid_page_with_malformed_site, page_id=..., ...)` must raise `ValueError("page.site must be a Site")` before accepting result state. |
| R3 | The new validation must not trigger page-ID lookup, source fetches, publish work, metadata writes, or AMC requests. |
| R4 | Existing source-result page, page-ID, source, error, outcome, source-ownership, source iterator, and ledger-export behavior must remain unchanged. |
| R5 | Existing publish-result page, page-ID, retained-ID, status, aggregate property, publish, and audit-export behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page source, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, source/publish result constructor coverage, site tests, adjacent page/source tests, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Source-result rows with malformed retained page-site state fail at construction. | `TestSitePagesAccessor.test_source_result_rejects_malformed_result_page_site` failed RED with `DID NOT RAISE`, then passed GREEN after the validator was added. | Accepting a dictionary or mock as `page.site`, deferring failure to `site` or `as_dict()`, or deriving site identity from malformed state rejects this local completion claim. | `PageSourceResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Publish-result rows with malformed retained page-site state fail at construction. | `TestSitePageAccessor.test_publish_result_rejects_malformed_result_page_site` failed RED with `DID NOT RAISE`, then passed GREEN after the validator was added. | Accepting malformed `page.site`, deferring failure to `url`, `site`, or `as_dict()`, or exporting a malformed owner site rejects this local completion claim. | `PagePublishResult` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Constructor validation stays side-effect free. | The focused regressions set `mock_site_no_http.amc_request = MagicMock()` and assert it is not called. | Calling `Page.id`, `amc_request`, source acquisition, publish, metadata updates, or any live network path rejects this local completion claim. | Result constructors | focused tests |
| R4 | Source-result behavior stays stable. | Focused constructor/ledger coverage passed 83 tests, including page ID, source/error outcome, source ownership, retained owner ID, zero ID, failed row, and ledger export paths. | Changing existing source-result diagnostics, source iterator order, exported keys, or source ownership semantics rejects this local completion claim. | Source result workflows | `tests/unit/test_site.py` |
| R5 | Publish-result behavior stays stable. | Focused constructor/ledger coverage passed the same 83-test command, including page ID, retained page ID, status flags, aggregate fields, zero ID, unloaded page ID, and audit export paths. | Changing existing publish-result diagnostics, aggregate status semantics, URL/site fields, audit keys, or publish behavior rejects this local completion claim. | Publish result workflows | `tests/unit/test_site.py` |
| R6 | The local proof stays unit-level and private-data-free. | All tests use synthetic `Page` objects and synthetic site names only. | Using live Wikidot, credentials, cookies, auth JSON, raw private page data, private site names, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the code commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0c8c54e fix(site): validate result page sites`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_result_page_site tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_result_page_site -q` failed before the fix with two `DID NOT RAISE` failures.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_source_result_rejects_malformed_result_page_site tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_rejects_malformed_result_page_site -q` passed 2 tests.
- Focused source/publish result constructor and ledger coverage passed 83 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 367 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_page_constructor.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 1363 tests.
- `uv run pytest tests/unit -q` passed 3788 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `PageSourceResult` rejects a result page whose retained `site` is not a `Site`.
- `PagePublishResult` rejects a result page whose retained `site` is not a `Site`.
- The rejection uses `ValueError("page.site must be a Site")`.
- The new validation does not perform network work, page-ID lookup, source acquisition, publish work, or metadata updates.
- Existing source-result and publish-result valid rows keep their existing properties and dictionary exports.
- Existing source iterator, publish, page/source/revision/file/vote, and site workflows remain green.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Result rows are durable audit objects. They should not accept malformed retained page ownership and then fail later while deriving `site`, `url`, or dictionary fields. Validating `page.site` at construction keeps source and publish ledgers internally coherent while preserving existing page-ID, source ownership, and status validation behavior.

## Local Evidence

- Local source-collection and publish drafts repeatedly use source/publish result rows as durable ledgers for browser-free workflows, source verification, retry rows, and multi-site audit exports.
- Existing local drafts covered result page shape, site fields, page IDs, retained page-ID state, source ownership, status booleans, aggregate status fields, and direct `Page(site=...)` construction. They did not cover a valid page whose mutable `site` field was corrupted before result-row construction.
- The focused RED failures showed both source-result failure rows and publish-result rows accepted malformed retained page-site state before this slice.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw page source text, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally validates only the retained result page's site type. It does not introduce cross-site identity comparisons for publish results, change source-result source ownership semantics, call `Page.id`, or require a loaded page ID. Those remain separate invariants covered by existing result and page-state validators.
