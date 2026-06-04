# PR Draft: Include Page Context In Direct Vote Failures

## Summary

`Page.votes` is the direct single-page rating/vote-list path used by callers that inspect page rating history before moderation, audit, or corpus reconciliation. When retry-aware acquisition exhausted without populating `_votes`, the property raised `NotFoundException("Cannot find page votes")`, which hid the affected page name in plain-text logs.

This follow-up keeps the existing exception type and acquisition behavior, but includes `page.fullname` in the failure message: `Cannot find page votes: <fullname>`. The change aligns direct vote-list failures with the page-context direction already used by source collection failures, direct source reads, direct revision-list reads, and direct file-list reads.

## Related Issue

Builds on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [149-pr-page-source-failure-context.md](149-pr-page-source-failure-context.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), and [151-pr-page-file-failure-context.md](151-pr-page-file-failure-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Make `Page.votes` include `self.fullname` when automatic vote-list acquisition leaves `_votes` unset.
- Add a focused direct vote-list exhausted-retry test that asserts the page-context message.
- Preserve vote request construction, retry behavior, WhoRated parsing, cache behavior, duplicate-page handling, and `PageVoteCollection` ownership.

## Type Of Change

- Bug fix / diagnostics improvement
- Vote-list error-context ergonomics
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy single-page vote-list failures identify the affected page. | `TestPageProperties.test_votes_property_includes_page_context_when_retry_is_exhausted` asserts `Cannot find page votes: test-page` after `amc_request_with_retry(...)` returns `None`. | The RED test failed before the fix because the exception message was only `Cannot find page votes`. |
| Vote-list acquisition behavior remains unchanged. | The focused test also asserts the same `pagerate/WhoRatedPageModule` request body, `amc_request(...)` is not called, and `_votes` remains `None`. | A change that alters request construction, retry use, cache population, or exhausted-retry state rejects this local completion claim. |
| Adjacent page and page-vote behavior remains green. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py -q` passed 117 tests. | Regressions in WhoRated parsing, duplicate response reuse, cached vote propagation, `PageVoteCollection` behavior, or page property behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `8e7e29f fix(page): include page name in vote failures`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_votes_property_includes_page_context_when_retry_is_exhausted -q` failed before the fix because `Page.votes` raised `Cannot find page votes` without the page fullname.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_votes_property_includes_page_context_when_retry_is_exhausted -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py -q` passed 117 tests.
- `uv run pytest tests/unit -q` passed 714 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `Page.votes` still performs lazy retry-aware vote-list acquisition through `PageCollection(...).get_page_votes()`.
- If lazy acquisition does not populate `_votes`, `Page.votes` raises `NotFoundException("Cannot find page votes: <fullname>")`.
- Successful vote-list acquisition, WhoRated parsing, `PageVoteCollection` ownership, duplicate-page response reuse, cached vote propagation, and vote value conversion remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Vote-list failures often appear in moderation, audit, and corpus reconciliation logs where the vote collection itself is unavailable. The exception should identify the affected page without requiring callers to reconstruct the `Page` object from surrounding state, especially because adjacent direct source, revision, and file failure paths already provide this context.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts already needed visible retry-exhaustion failures and cache/deduplication behavior for page detail collections, including votes.
- Recent source, revision, and file failure work showed that page-context messages make plain-text logs and resumable ledgers easier to triage without inspecting raw objects.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.source`, `Page.revisions`, `Page.files`, WhoRated parsing, vote mutation behavior, request batching, or live Wikidot behavior. Similar context improvements may still be possible in other direct property paths, but this closes the obvious direct source/revision/file/vote page-context gap.
