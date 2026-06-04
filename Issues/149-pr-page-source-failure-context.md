# PR Draft: Include Page Context In Direct Source Failures

## Summary

`Page.source` and `Page.refresh_source()` are the direct single-page source-read paths used by callers that inspect one page and by browser-free publishing code that verifies a saved page through `ViewSourceModule`. When retry-aware acquisition exhausted without populating `_source`, both methods raised `NotFoundException("Cannot find page source")`, which hid the affected page name in plain-text logs.

This follow-up keeps the existing exception type and acquisition behavior, but includes `page.fullname` in the failure message: `Cannot find page source: <fullname>`. The high-level source iterator already reports per-page source failures with this context; this change aligns direct source reads and explicit source refreshes with that ledger-friendly surface.

## Related Issue

Builds on [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), and [147-pr-source-result-error-type.md](147-pr-source-result-error-type.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared internal source-missing exception helper on `Page`.
- Make `Page.source` include `self.fullname` when automatic source acquisition leaves `_source` unset.
- Make `Page.refresh_source()` include `self.fullname` when explicit source refresh leaves `_source` unset.
- Add focused tests for both direct source failure paths.

## Type Of Change

- Bug fix / diagnostics improvement
- Source collection and publish verification ergonomics
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy single-page source failures identify the affected page. | `TestPageProperties.test_source_property_includes_page_context_when_retry_is_exhausted` asserts `Cannot find page source: test-page` after `amc_request_with_retry(...)` returns `None`. | The RED test failed before the fix because the exception message was only `Cannot find page source`. |
| Explicit source refresh failures identify the affected page. | `TestPageProperties.test_refresh_source_includes_page_context_when_retry_is_exhausted` asserts the same contextual message for `Page.refresh_source()`. | The RED test failed before the fix because `refresh_source()` used the same generic message. |
| Source acquisition, retry behavior, successful source parsing, source iterator records, and publish-adjacent behavior remain unchanged. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 171 tests. | A change that alters request bodies, retry use, cache population, iterator failures, or publish verification rejects this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `df7d0fd fix(page): include page name in source failures`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_source_property_includes_page_context_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_refresh_source_includes_page_context_when_retry_is_exhausted -q` failed before the fix because both paths raised `Cannot find page source` without the page fullname.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_source_property_includes_page_context_when_retry_is_exhausted tests/unit/test_page.py::TestPageProperties::test_refresh_source_includes_page_context_when_retry_is_exhausted -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 171 tests.
- `uv run pytest tests/unit -q` passed 713 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.source` still performs lazy retry-aware source acquisition through `PageCollection(...).get_page_sources()`.
- If lazy acquisition does not populate `_source`, `Page.source` raises `NotFoundException("Cannot find page source: <fullname>")`.
- `Page.refresh_source()` still clears the local source cache and reuses the same collection source acquisition path.
- If explicit refresh does not populate `_source`, `Page.refresh_source()` raises `NotFoundException("Cannot find page source: <fullname>")`.
- Successful source acquisition and existing source iterator result fields remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Source-fetch failures often land in simple text logs before callers persist richer objects. Direct `Page.source` and `Page.refresh_source()` failures should identify the affected page the same way high-level source iterator failures already do, especially because `refresh_source()` is used for post-save source verification in browser-free publishing workflows.

## Local Evidence, Not For Upstream Paste

- Local source collection drafts already needed per-page failure messages, structured source result records, and failure type grouping for resumable source ledgers.
- Browser-free publishing drafts use `Page.refresh_source()` as the post-save verification primitive, so a failed source refresh should be diagnosable without reconstructing the page object from surrounding code.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change source request construction, retry policy, source text extraction, source cache semantics, page ID lookup, source iterator fallback behavior, publish result behavior, or mutation methods. It only changes the message on the existing `NotFoundException` failure path for direct page source reads.
