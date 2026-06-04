# PR Draft: Include Page Context In Latest Revision Failures

## Summary

`Page.latest_revision` is the direct convenience path used by callers that need the newest page revision after revision history has already been acquired. When loaded revision history had no entry matching `Page.revisions_count`, the property raised `NotFoundException("Cannot find latest revision")`, which hid both the affected page and the expected revision number in plain-text logs.

This follow-up keeps the existing exception type, lazy revision-list acquisition behavior, and latest-revision selection logic, but includes `page.fullname` and the expected `rev_no` in the failure message: `Cannot find latest revision: <fullname> (rev_no=<revisions_count>)`. The change aligns latest-revision failures with the page-context direction already used by direct source, revision-list, file-list, and vote-list failures.

## Related Issue

Builds on [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), and [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Make `Page.latest_revision` include `self.fullname` and `self.revisions_count` when no loaded revision has `rev_no == revisions_count`.
- Add a focused latest-revision miss test that asserts the page and expected revision number are present in the exception message.
- Preserve lazy revision acquisition, revision-list parsing, matching-revision return behavior, direct revision source/HTML behavior, and `PageRevisionCollection` ownership.

## Type Of Change

- Bug fix / diagnostics improvement
- Latest-revision error-context ergonomics
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Latest-revision misses identify the affected page and expected revision number. | `TestPageProperties.test_latest_revision_includes_page_context_when_not_found` asserts `Cannot find latest revision: test-page (rev_no=5)` when loaded revisions do not contain `rev_no == revisions_count`. | The RED test failed before the fix because the exception message was only `Cannot find latest revision`. |
| Latest-revision selection behavior remains unchanged. | The focused test still uses the same loaded `PageRevisionCollection` path and only changes the exhausted-match message. | A change that alters lazy acquisition, matching revision selection, revision collection ownership, or successful latest-revision return behavior rejects this local completion claim. |
| Adjacent page and page-revision behavior remains green. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 142 tests. | Regressions in revision-list parsing, direct revision source/HTML behavior, page property behavior, cached duplicate revision handling, or revision collection behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `ea1ac96 fix(page): include page name in latest revision failures`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_latest_revision_includes_page_context_when_not_found -q` failed before the fix because `Page.latest_revision` raised `Cannot find latest revision` without the page fullname or expected revision number.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_latest_revision_includes_page_context_when_not_found -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 142 tests.
- `uv run pytest tests/unit -q` passed 714 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.latest_revision` still performs lazy revision-list acquisition through `self.revisions`.
- If no loaded revision has `rev_no == revisions_count`, `Page.latest_revision` raises `NotFoundException("Cannot find latest revision: <fullname> (rev_no=<revisions_count>)")`.
- Successful latest-revision lookup, revision-list parsing, cached duplicate revision-list reuse, direct revision source/HTML behavior, and `PageRevisionCollection` ownership remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Latest-revision failures often appear in audit, corpus reconciliation, or moderation flows where the revision collection is present but inconsistent with the page metadata. The exception should identify both the affected page and the revision number that was expected, without requiring callers to reconstruct the `Page` object or revision-count state from surrounding logs.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts already needed visible page revision acquisition failures, cached duplicate revision handling, and lazy revision source/HTML failure visibility.
- Recent source, revision-list, file-list, and vote-list failure work showed that page-context messages make plain-text logs and resumable ledgers easier to triage without inspecting raw objects.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.revisions`, revision-list parsing, `PageRevision.source`, `PageRevision.html`, direct source/file/vote paths, request batching, or live Wikidot behavior. Similar context improvements may still be possible in other direct property paths, but this closes the obvious direct latest-revision page-context gap.
