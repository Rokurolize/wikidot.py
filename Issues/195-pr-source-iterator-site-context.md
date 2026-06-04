# PR Draft: Include Site Context In Source Iterator Failures

## Summary

`site.pages.iter_sources(...)` is the high-level large source-collection path that yields one `PageSourceResult` per page and lets callers persist success/failure ledgers without aborting the run. Earlier local slices added page fullname context, `error_message`, `error_type`, and `as_dict()` ledger export fields. However, unresolved source failures still serialized as page-only messages such as `Cannot find page source: scp-001`, which is ambiguous when a multi-site crawler collects the same page fullname from several Wikidot sites.

This follow-up keeps page discovery, source batching, fallback retry sizing, parse-failure isolation, ordering, `PageSourceResult` fields, and exception type unchanged. It only adds the site unix name to the fallback unresolved-source error used by `PageSourceResult.error_message` and `PageSourceResult.as_dict()`: `Cannot find page source for site: <site>, page: <fullname>`.

## Related Issue

Builds on [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), and [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md). Those drafts established the iterator, page-level source failures, parse isolation, ledger-friendly result fields, direct source site context, and the large corpus source-collection workflow as practical local improvement surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Include `page.site.unix_name` and page fullname in the fallback `NotFoundException` created for unresolved `site.pages.iter_sources(...)` source results.
- Tighten `PageSourceResult.error_message` coverage to assert site/page context.
- Tighten `PageSourceResult.as_dict()` coverage to assert the same site/page error message in exported ledger records.
- Preserve search ordering, source request payloads, retry/fallback behavior, parse-failure isolation, successful source text, `error_type`, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Large source-collection ledger context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Unresolved source iterator failures still yield `PageSourceResult(ok=False, source=None, error=NotFoundException(...))` instead of aborting iteration. | `TestSitePagesAccessor.test_iter_sources_result_exposes_page_context` exhausts primary and fallback source fetches for one page and still receives ordered results. | Aborting the iterator, returning a fabricated source, changing result order, or changing the exception type rejects this local completion claim. |
| `PageSourceResult.error_message` identifies both site and page for unresolved source failures. | The focused regression asserts `Cannot find page source for site: test-site, page: page-two`. | The RED test failed before the fix because the message only said `Cannot find page source: page-two`. |
| Ledger export carries the same site/page message. | `TestSitePagesAccessor.test_iter_sources_result_exports_ledger_record` asserts the site/page message inside the failed result dictionary. | Leaving `as_dict()` with a page-only message rejects this local completion claim. |
| Adjacent source iterator and page workflows remain green. | `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 182 tests. | Regressions in iter_search, required-tag filtering, fallback source retries, parse-failure isolation, direct page source reads, or publish source verification reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4af4928 fix(site): include site in source iterator failures`.

- RED: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_page_context -q` failed before the fix because the failed source result message was `Cannot find page source: page-two`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_page_context -q`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_page_context tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` passed 2 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 182 tests.
- `uv run pytest tests/unit -q` passed 733 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `site.pages.iter_sources(...)` still yields one result per searched page in search order.
- Source request batching and fallback retries remain unchanged.
- Unresolved source fetches still become failed `PageSourceResult` objects instead of aborting iteration.
- `PageSourceResult.error_message` now names both site unix name and page fullname for unresolved source failures.
- `PageSourceResult.as_dict()` exports the same site/page error message.
- Successful source results, parse-failure isolation, `error_type`, required-tag filtering, and direct `Page.source` / `Page.refresh_source()` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large source-collection workflows often persist `PageSourceResult.as_dict()` rows to JSONL or TSV-like ledgers. When retries are exhausted, a ledger row should identify both the site and page without requiring the caller to join in extra object context or store raw response bodies. This keeps the iterator's existing strict failure behavior while making multi-site source ledgers easier to audit and resume.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified `site.pages.iter_sources(...)`, `PageSourceResult.error_message`, and `PageSourceResult.as_dict()` as practical workflow surfaces for large corpus collection and resumable ledgers.
- Recent site-context slices showed that compact site/object identifiers improve plain-text failure logs without changing successful behavior.
- This slice only claims source iterator unresolved-source diagnostics. It does not claim any live Wikidot behavior change.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change ListPages discovery, source request construction, retry counts, fallback batch sizing, parse-failure handling, source caching, `PageSourceResult` fields, or live Wikidot behavior. It only adds site unix name context to the existing unresolved-source fallback error.
