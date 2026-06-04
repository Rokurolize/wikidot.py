# PR Draft: Include Page Context In Direct Revision Failures

## Summary

`Page.revisions` is the direct single-page revision-list path used by callers that inspect one page's history before deciding whether to fetch revision source/HTML or reconcile publish state. When retry-aware acquisition exhausted without populating `_revisions`, the property raised `NotFoundException("Cannot find page revisions")`, which hid the affected page name in plain-text logs.

This follow-up keeps the existing exception type and acquisition behavior, but includes `page.fullname` in the failure message: `Cannot find page revisions: <fullname>`. The change aligns direct revision-list failures with the page-context direction already used by source collection failures and recent direct source-read improvements.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), and [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Make `Page.revisions` include `self.fullname` when automatic revision-list acquisition leaves `_revisions` unset.
- Update the focused direct revision-list exhausted-retry test to assert the page-context message.
- Preserve revision request construction, retry behavior, revision-list parsing, cache behavior, duplicate-page handling, and revision source/HTML acquisition behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Revision-list error-context ergonomics
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy single-page revision-list failures identify the affected page. | `TestPageProperties.test_revisions_property_includes_page_context_when_retry_is_exhausted` asserts `Cannot find page revisions: test-page` after `amc_request_with_retry(...)` returns `None`. | The RED test failed before the fix because the exception message was only `Cannot find page revisions`. |
| Revision-list acquisition behavior remains unchanged. | The focused test also asserts the same `history/PageRevisionListModule` request body, `amc_request(...)` is not called, and `_revisions` remains `None`. | A change that alters request construction, retry use, cache population, or exhausted-retry state rejects this local completion claim. |
| Adjacent page and page-revision behavior remains green. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 141 tests. | Regressions in page revision parsing, duplicate response reuse, lazy revision source/HTML failures, or page property behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `05f2e40 fix(page): include page name in revision failures`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_revisions_property_includes_page_context_when_retry_is_exhausted -q` failed before the fix because `Page.revisions` raised `Cannot find page revisions` without the page fullname.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_revisions_property_includes_page_context_when_retry_is_exhausted -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 141 tests.
- `uv run pytest tests/unit -q` passed 713 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.revisions` still performs lazy retry-aware revision-list acquisition through `PageCollection(...).get_page_revisions()`.
- If lazy acquisition does not populate `_revisions`, `Page.revisions` raises `NotFoundException("Cannot find page revisions: <fullname>")`.
- Successful revision-list acquisition, duplicate-page response reuse, `PageRevisionCollection` ownership, and lazy revision source/HTML paths remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Revision-list failures often appear in logs near source verification, history reconciliation, and large page-corpus processing. The exception should identify the affected page without requiring callers to reconstruct the `Page` object from surrounding state, especially because adjacent source-read failure paths already provide this context.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts already needed visible retry-exhaustion failures for direct page revisions and lazy revision source/HTML paths.
- Recent source failure work showed that page-context messages make plain-text logs and resumable ledgers easier to triage without inspecting raw objects.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.files`, `Page.votes`, `Page.latest_revision`, request batching, revision parsing, revision source/HTML fetching, mutation methods, or live Wikidot behavior. Similar direct property context improvements remain plausible follow-up slices.
