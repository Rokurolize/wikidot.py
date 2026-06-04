# PR Draft: Include Site Context In Vote Mismatch Errors

## Summary

`PageCollection.get_page_votes()` parses `pagerate/WhoRatedPageModule` responses by pairing direct `span.printuser` voter elements with direct colored vote-value spans inside the generated WhoRated column-count container. Earlier local work made malformed user/value count mismatches fail with the affected page fullname and observed counts, but the message still did not identify the Wikidot site: `User and value count mismatch for page: scp-001 (users=1, values=2)`.

This follow-up keeps the existing mismatch failure behavior, parser boundary, duplicate page-ID grouping, cached duplicate reuse, value conversion, retry behavior, and exception type unchanged. It only adds the site unix name to the existing malformed WhoRated mismatch message: `User and value count mismatch for site: <site>, page: <fullname> (users=<n>, values=<m>)`.

## Related Issue

Builds on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), and [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md). Those drafts established vote acquisition as retry-aware, duplicate-aware, parser-scoped, visible on exhausted lazy reads, and already page-contextual for mismatch failures.

No upstream issue was filed from this local workspace.

## Changes

- Include `site.unix_name`, representative page fullname, and observed user/value element counts in malformed WhoRated mismatch errors.
- Tighten the existing malformed WhoRated structure regression to assert site/page/count context.
- Preserve successful vote parsing, direct-child WhoRated scoping, non-vote colored span filtering, retry behavior, cached duplicate vote reuse, duplicate page propagation, value conversion, lazy `Page.votes` behavior, and exception type.

## Type Of Change

- Bug fix / diagnostics improvement
- Vote-list parser ledger context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed WhoRated structures still fail instead of fabricating vote data. | `TestPageCollectionAcquire.test_acquire_votes_mismatch_includes_site_context` asserts an `UnexpectedException` for one voter and two value spans. | Returning partial votes, padding/truncating counts, or accepting mismatched user/value spans rejects this local completion claim. |
| The mismatch error identifies the affected site, page, and observed counts. | The focused regression asserts `User and value count mismatch for site: test-site, page: test-page (users=1, values=2)`. | The RED test failed before the fix because the message only named the page and counts. |
| Adjacent page, vote, and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 193 tests. | Regressions in valid WhoRated parsing, non-vote colored span filtering, duplicate vote propagation, cached duplicate vote reuse, page properties, or site page workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `f082274 fix(page): include site in vote mismatch errors`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_site_context -q` failed before the fix because the parser raised `User and value count mismatch for page: test-page (users=1, values=2)`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_site_context -q`.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 193 tests.
- `uv run pytest tests/unit -q` passed 735 tests.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A WhoRated response whose generated vote-list container has unequal direct voter and vote-value counts still raises `UnexpectedException`.
- The raised mismatch message includes the site unix name, page fullname, and observed `users` and `values` counts.
- Successful vote parsing, parser scoping to the generated vote-list container, non-vote colored span filtering, duplicate page ID grouping, cached duplicate vote reuse, retry behavior, and lazy `Page.votes` remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Vote-list failures can appear during moderation, audit, or corpus reconciliation runs where many pages across more than one Wikidot site are hydrated in batches. A malformed WhoRated module response should still fail, but the failure should identify the site, page, and mismatch shape so callers can triage the affected page without saving raw AMC HTML in logs.

## Local Evidence, Not For Upstream Paste

- Earlier local vote drafts established WhoRated parsing as a practical read-heavy surface for page-detail hydration and moderation-style inspection.
- The parser-boundary fix in Issue 093 deliberately preserved structural mismatch detection; Issue 154 made the preserved failure page-specific. This slice only adds the remaining site discriminator.
- Recent site-context slices showed the same low-risk pattern: add compact site/object identifiers to existing plain-text exceptions without changing successful behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `Page.votes`, `PageCollection._acquire_page_votes(...)` request construction, WhoRated container discovery, value conversion, duplicate page propagation, cached duplicate reuse, vote mutation behavior, live Wikidot behavior, or mutation methods. It only adds site/page/count context to an existing parser mismatch failure.
