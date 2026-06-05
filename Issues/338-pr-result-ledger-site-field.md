# PR Draft: Include Site Field In Result Ledger Records

## Summary

`Site.pages.iter_sources(...)` and `Site.page.publish(...)` both return result objects that can be serialized into compact ledger rows with `as_dict()`. Earlier local slices added source-result and publish-result audit dictionaries, page IDs, publish URLs, and site-aware failure messages, but the successful ledger rows still lacked an explicit site field. Multi-site source collection or publishing runs therefore had to join `result.page.site.unix_name` manually, infer site from URL strings, or rely on error text that exists only on failed source rows.

This change adds side-effect-free `site` properties to `PageSourceResult` and `PagePublishResult`, and includes `"site": page.site.unix_name` in both `as_dict()` outputs. It does not change source fetching, publish sequencing, source verification, metadata writes, fallback behavior, exception handling, URL construction, or live Wikidot behavior.

## Outcome

Source-collection and publish audit rows now identify the Wikidot site directly, so callers can persist one JSONL/TSV-style row per result without repeating caller-side site joins.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators running browser-free source collection, source verification, or publishing workflows across more than one Wikidot site.

## Current Evidence

Earlier local drafts established `PageSourceResult.as_dict()` and `PagePublishResult.as_dict()` as practical ledger surfaces. Issue 195 specifically documented the ambiguity of source-result rows when a multi-site crawler sees the same page fullname on several sites, but only the unresolved-source error message gained site context. Issues 225 and 070 then made the source and publish records stronger audit rows by exposing page IDs and publish status fields. This slice closes the remaining successful-row identity gap without adding new network work.

## Related Issue

Builds on [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [204-pr-publish-source-verification-site-context.md](204-pr-publish-source-verification-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), and [231-pr-publish-result-url.md](231-pr-publish-result-url.md). Those drafts established source/publish result ledgers, site-aware diagnostics, page identity, and publish audit ergonomics as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSourceResult.site -> str`.
- Add `PagePublishResult.site -> str`.
- Include `"site"` in `PageSourceResult.as_dict()`.
- Include `"site"` in `PagePublishResult.as_dict()`.
- Strengthen focused tests for source-result and publish-result audit dictionaries.

## Type Of Change

- Ledger/audit record ergonomics improvement
- Multi-site workflow identity improvement
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageSourceResult.as_dict()` must include `site` for successful and failed source rows without triggering page-ID or source lookups. |
| R2 | `PagePublishResult.as_dict()` must include `site` and expose `PagePublishResult.site` for audit callers. |
| R3 | The new `site` value must come from `page.site.unix_name` and must not infer from URLs, error messages, raw response bodies, or local paths. |
| R4 | Existing source iterator ordering, fallback behavior, publish create/edit behavior, source verification, metadata updates, and result fields must remain unchanged. |
| R5 | Focused, adjacent, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Source-result dictionaries contain `"site": "test-site"` for both the successful and failed rows from `site.pages.iter_sources(...)`. | `TestSitePagesAccessor.test_iter_sources_result_exports_ledger_record` asserts exact dictionaries with `site`, `fullname`, `page_id`, `ok`, `wiki_text`, `error_type`, and `error_message`. | Omitting `site`, reading `Page.id`, serializing raw `Page`/`PageSource` objects, or changing row order rejects this local completion claim. | Source result ledger export | `tests/unit/test_site.py` |
| R2 | Publish-result dictionaries contain `"site": "test-site"` and `result.site` returns `"test-site"`. | `TestSitePageAccessor.test_publish_result_exports_audit_record` asserts both the property and exact audit dictionary. | Inferring the site from the URL, returning a `Site` object, omitting existing publish fields, or changing publish behavior rejects this local completion claim. | Publish result audit export | `tests/unit/test_site.py` |
| R3 | Site identity is a compact site unix name only. | Implementation reads `self.page.site.unix_name` in both result properties. | Logging raw responses, credentials, page source, private metadata payloads, local rollout paths, or account material rejects this local completion claim. | Result object properties | `src/wikidot/module/site.py` |
| R4 | Adjacent source and publish behavior remains green. | `TestSitePagesAccessor` plus `TestSitePageAccessor` passed 31 tests; `tests/unit/test_site.py tests/unit/test_page.py` passed 252 tests. | Regressions in source batching, fallback retries, parse-failure isolation, publish result fields, source verification, metadata writes, or page URL generation reject this local completion claim. | Site/page workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit passed 913 tests; ruff, format check, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ed4d6db feat(site): include site in result ledgers`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` failed before the fix because source result dictionaries omitted `"site"` and `PagePublishResult` had no `site` property.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record tests/unit/test_site.py::TestSitePageAccessor::test_publish_result_exports_audit_record -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_site.py::TestSitePageAccessor -q` passed 31 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 252 tests.
- `uv run --extra test pytest tests/unit -q` passed 913 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PageSourceResult.site` returns the wrapped page's `site.unix_name`.
- `PagePublishResult.site` returns the wrapped page's `site.unix_name`.
- `PageSourceResult.as_dict()` includes `site`, `fullname`, `page_id`, `ok`, `wiki_text`, `error_type`, and `error_message`.
- `PagePublishResult.as_dict()` includes `site`, `fullname`, `url`, `page_id`, create/edit status, source verification fields, metadata flags, and aggregate status fields.
- Reading `site` or `as_dict()` does not trigger source fetches, page-ID fetches, publish actions, metadata writes, or live Wikidot access.
- Existing source iterator and browser-free publish behavior remains unchanged.
- No browser, live Wikidot action, upstream Issue, upstream PR, push, raw response body, account material, credentials, page source, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Result-ledger rows are easiest to persist, sort, retry, and compare when each row carries the compact site identity alongside the page identity and status fields. A first-class `site` key avoids caller-side joins and URL parsing while keeping the richer result objects available for callers that need the underlying `Page`.

## Local Evidence, Not For Upstream Paste

- The broader local source collection and browser-free publishing drafts record practical workflows that wrote durable result ledgers after fetching sources or publishing pages.
- Local follow-ups already added site-aware failure diagnostics because page-only context was ambiguous in multi-site runs.
- This slice only adds compact site identity to result objects and their existing dictionaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, saved page source, and private page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not add JSON encoders, file-writing helpers, partial publish results, URL parsing, raw site objects, source text changes, retry changes, cache changes, or live Wikidot behavior changes. It only exposes the site unix name already reachable from each wrapped `Page`.
