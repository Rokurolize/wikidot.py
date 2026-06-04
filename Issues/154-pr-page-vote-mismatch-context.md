# PR Draft: Include Page Context In Vote Mismatch Errors

## Summary

`PageCollection.get_page_votes()` parses `pagerate/WhoRatedPageModule` responses by pairing direct `span.printuser` voter elements with direct colored vote-value spans inside the generated WhoRated column-count container. When the generated structure is malformed and the voter/value counts do not match, the parser intentionally raises `UnexpectedException`, but the old message only said `User and value count mismatch`.

This follow-up keeps the existing mismatch failure behavior and parser boundary, but includes the affected page fullname and observed element counts in the error message: `User and value count mismatch for page: <fullname> (users=<n>, values=<m>)`. That makes vote-list parser failures diagnosable from plain-text logs without inspecting the raw AMC body or reconstructing which page ID produced the malformed module response.

## Related Issue

Builds on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), and [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Make WhoRated user/value mismatch errors include the first affected page fullname for the response's page ID.
- Include the observed voter and value element counts in the mismatch message.
- Add a focused malformed WhoRated structure test that asserts page context and counts.
- Preserve successful vote parsing, direct-child WhoRated scoping, retry behavior, cached duplicate vote reuse, duplicate page propagation, value conversion, and lazy `Page.votes` behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Vote-list parser error-context ergonomics
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed WhoRated structures still fail instead of fabricating vote data. | `TestPageCollectionAcquire.test_acquire_votes_mismatch_includes_page_context` asserts an `UnexpectedException` for one voter and two value spans. | A change that silently truncates, pads, or otherwise returns votes from a mismatched structure rejects this local completion claim. |
| The mismatch error identifies the affected page and observed counts. | The focused test asserts `User and value count mismatch for page: test-page (users=1, values=2)`. | The RED test failed before the fix because the exception message was only `User and value count mismatch`. |
| Normal and adjacent vote behavior remains green. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py -q` passed 118 tests. | Regressions in valid WhoRated parsing, non-vote colored span filtering, duplicate vote propagation, cached duplicate vote reuse, or `PageVoteCollection` behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `0e9e1be fix(page): include page context in vote mismatch errors`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_page_context -q` failed before the fix because the parser raised `User and value count mismatch` without page context or counts.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_page_context -q`
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py -q` passed 118 tests.
- `uv run pytest tests/unit -q` passed 715 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A WhoRated response whose generated vote-list container has unequal direct voter and vote-value counts still raises `UnexpectedException`.
- The raised mismatch message includes the affected page fullname and the observed `users` and `values` counts.
- Successful vote parsing, parser scoping to the generated vote-list container, non-vote colored span filtering, duplicate page ID grouping, cached duplicate vote reuse, retry behavior, and lazy `Page.votes` remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Vote-list failures can appear during moderation, audit, or corpus reconciliation runs where many pages are hydrated in batches. A malformed WhoRated module response should still fail, but the failure should identify the page and the shape of the mismatch so callers can triage the affected page without saving raw AMC HTML in logs.

## Local Evidence, Not For Upstream Paste

- Earlier local vote drafts established WhoRated parsing as a practical read-heavy surface for page-detail hydration and moderation-style inspection.
- The parser-boundary fix in Issue 093 deliberately preserved structural mismatch detection; this slice only makes that preserved failure more actionable.
- Recent page-context work for source, revision, file, vote, and latest-revision failures showed that page-specific errors improve plain-text logs and resumable ledgers.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.votes`, `PageCollection._acquire_page_votes(...)` request construction, WhoRated container discovery, value conversion, duplicate page propagation, cached duplicate reuse, vote mutation behavior, or live Wikidot behavior. It only adds page and count context to an existing parser mismatch failure.
