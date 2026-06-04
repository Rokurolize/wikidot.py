# PR Draft: Expose Source Result Error Types

## Summary

`site.pages.iter_sources(...)` returns one `PageSourceResult` per page so large source-collection callers can persist successes and failures without losing ordering. Previous local slices added `fullname`, `wiki_text`, `error_message`, and `as_dict()` so callers no longer need to unpack the raw `Page` and `Exception` objects for common ledger fields.

This follow-up adds a read-only `PageSourceResult.error_type` property and includes the same value in `PageSourceResult.as_dict()`. Successful source results report `None`; failed results report the exception class name such as `NotFoundException` or `NoElementException`. That lets a source collection ledger group missing-source retry exhaustion separately from malformed source response parsing while preserving the existing raw `error` object and message text.

## Related Issue

Builds on [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [026-pr-source-iterator-parse-failure-isolation.md](026-pr-source-iterator-parse-failure-isolation.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), and [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageSourceResult.error_type -> str | None`.
- Include `error_type` in `PageSourceResult.as_dict()`.
- Extend source iterator result tests to cover successful and failed `error_type` values.

## Type Of Change

- Feature / ergonomics improvement
- Source collection ledger improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Failed source iterator results expose a stable exception class name without requiring callers to inspect the raw `Exception`. | `TestSitePagesAccessor.test_iter_sources_result_exposes_page_context` asserts `None` for successful results and `NotFoundException` for an unresolved failed page. | The RED test failed before the fix because `PageSourceResult` had no `error_type` attribute. |
| Ledger dictionaries include the same failure classification as the object property. | `TestSitePagesAccessor.test_iter_sources_result_exports_ledger_record` asserts `error_type` in both successful and failed `as_dict()` records. | The RED test failed before the fix because `as_dict()` only exported `fullname`, `ok`, `wiki_text`, and `error_message`. |
| Source fetching, retry, fallback, and parse-isolation behavior remain unchanged. | `uv run --extra test pytest tests/unit/test_site.py -q` passed 64 site tests, and `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 169 adjacent tests. | A change that alters iterator ordering, fallback requests, source cache behavior, or per-page failure isolation rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `c8673a5 feat(site): expose source result error type`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_page_context tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q` failed before the fix because `PageSourceResult.error_type` was missing and `as_dict()` did not export `error_type`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exposes_page_context tests/unit/test_site.py::TestSitePagesAccessor::test_iter_sources_result_exports_ledger_record -q`
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 64 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 169 tests.
- `uv run pytest tests/unit -q` passed 711 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PageSourceResult.error_type` returns `None` when `error` is `None`.
- `PageSourceResult.error_type` returns `error.__class__.__name__` when `error` is present.
- `PageSourceResult.as_dict()` includes `error_type` alongside `fullname`, `ok`, `wiki_text`, and `error_message`.
- Existing `PageSourceResult.page`, `source`, `error`, `ok`, `fullname`, `wiki_text`, and `error_message` behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Large source collection workflows often write `PageSourceResult.as_dict()` records into TSV/JSONL ledgers. Message text is useful for humans, but exception class names are a better low-cardinality field for grouping failures such as unresolved source reads versus malformed source module responses. Exposing `error_type` keeps the richer raw `error` object available while making common audit records easier to classify.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed source collection work already introduced bounded source iteration, fallback retry, per-page parse-failure isolation, source text access, page context fields, and ledger dictionaries.
- This slice came from comparing that ledger export with the remaining caller boilerplate needed to classify failures without deserializing or inspecting raw exception objects.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change ListPages discovery, source request batching, fallback retry sizing, parse failure handling, source caching, source text extraction, or the raw `PageSourceResult.error` object. It only adds a small classification field to the result object and its dictionary export.
