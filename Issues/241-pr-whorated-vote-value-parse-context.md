# PR Draft: Include Context In WhoRated Vote Value Parse Errors

## Summary

`PageCollection.get_page_votes()` parses `pagerate/WhoRatedPageModule` responses by pairing direct `span.printuser` voter elements with direct colored vote-value spans inside the generated WhoRated column-count container. Earlier local slices made page vote acquisition retry-aware, duplicate-aware, cache-aware, response-body-aware, structurally scoped, and site/page/count-aware for user/value mismatches. One adjacent value parser gap remained: a malformed vote value that was neither `+`, `-`, nor an integer still reached direct `int(...)` conversion and leaked a raw Python `ValueError` without the affected site, page, page ID, field, or value.

This follow-up keeps successful WhoRated parsing unchanged, but routes vote-value text through a small parser helper. Malformed vote values now raise `NoElementException` with site, representative page fullname, page ID, field name, and raw value context, so plain-text logs can identify the broken generated vote value without retaining raw WhoRated HTML, voter names, or site content.

## Related Issue

Builds on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), and [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md). Those drafts established WhoRated acquisition as a practical read-heavy surface and established the adjacent diagnostic pattern for malformed generated vote structures.

No upstream issue was filed from this local workspace.

## Changes

- Add a small WhoRated vote-value parser that preserves `+`, `-`, and integer value semantics.
- Convert malformed vote value text into `NoElementException` with site, page, page ID, field, and raw value context.
- Add a focused regression for a generated WhoRated response whose first vote value is `not-a-vote`.
- Preserve page-ID acquisition, retry behavior, request payloads, cached vote reuse, duplicate page-ID grouping, direct WhoRated container scoping, non-vote colored span filtering, user/value count mismatch behavior, user parsing, valid vote value parsing, duplicate page propagation, and lazy `Page.votes`.

## Type Of Change

- Bug fix / diagnostics improvement
- WhoRated parser error-context ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed generated WhoRated vote values fail with wikidot.py's contextual parser exception rather than a raw integer conversion exception. | `TestPageCollectionAcquire.test_acquire_votes_malformed_value_includes_site_page_and_value_context` mutates the first vote value to `not-a-vote` and asserts `NoElementException`. | A raw `ValueError`, fabricated zero, silent vote skip, or partially populated vote collection rejects this local completion claim. |
| The malformed vote-value error identifies the affected site, page, page ID, field, and raw value. | The focused regression asserts `WhoRated vote value is malformed for site: test-site, page: test-page (id=12345, field=vote_value, value=not-a-vote)`. | Omitting site, page fullname, page ID, field, or raw value makes the failure ambiguous and rejects this local completion claim. |
| Malformed vote values do not populate page votes. | The focused regression asserts `mock_page_with_id._votes is None` after the exception. | Assigning an empty, partial, or fabricated `PageVoteCollection` after malformed value parsing rejects this local completion claim. |
| Valid WhoRated parsing and malformed-structure diagnostics remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_value_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_ignores_non_vote_colored_spans tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_site_context -q` passed 3 tests. | Regressions in valid `+`/`-` parsing, non-vote colored span filtering, or user/value mismatch errors reject this local completion claim. |
| Existing page vote collection behavior remains green. | `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_votes.py -q` passed 50 tests. | Regressions in page ID acquisition, cached vote reuse, duplicate vote propagation, retry behavior, vote collection behavior, or lazy votes reject this local completion claim. |
| Adjacent page and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 214 tests. | Regressions in page properties, page mutation helpers, site page accessors, publish helpers, or vote mutation behavior reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `70f5b66 fix(page): report malformed whorated vote values`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_value_includes_site_page_and_value_context -q` failed before the fix with raw `ValueError: invalid literal for int() with base 10: 'not-a-vote'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_value_includes_site_page_and_value_context -q` passed 1 test.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_value_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_ignores_non_vote_colored_spans tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_site_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_votes.py -q` passed 50 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 214 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run pytest tests/unit -q` passed 788 tests.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A generated WhoRated response whose vote value text is neither `+`, `-`, nor an integer raises `NoElementException`.
- The malformed vote-value message includes the site `unix_name`, representative page fullname, page ID, affected field name, and raw malformed value.
- The affected page's `_votes` cache remains unset after malformed value parsing.
- Successful WhoRated parsing, direct vote-list scoping, non-vote colored span filtering, user/value mismatch behavior, cached vote reuse, duplicate page propagation, retry behavior, page-ID acquisition, lazy `Page.votes`, vote mutation behavior, and `PageVoteCollection` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

WhoRated is a page-detail read path used by page inspection, moderation review, source-audit ledgers, and publication-adjacent page hydration. If Wikidot emits a malformed generated vote value, wikidot.py should fail rather than inventing a vote or leaking a generic Python conversion error. The failure should identify the site, page, field, and raw value so maintainers can triage from logs without storing raw WhoRated HTML, voter names, credentials, or private site content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page vote acquisition as a practical workflow surface by improving retry behavior, duplicate page-ID request grouping, cached duplicate vote reuse, WhoRated structural scoping, mismatch diagnostics, direct property failure context, and response-body validation.
- Adjacent parser-value slices showed that field/value-aware `NoElementException` messages improve resumable plain-text diagnostics without changing successful parser output or live Wikidot behavior.
- The refreshed complexity scanner continues to flag shared parser/acquisition paths as hotspots, but this slice deliberately avoids broad parser rewrites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw WhoRated HTML, voter names, vote data, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change WhoRated request construction, paging, retry policy, page-ID acquisition, direct vote-list scoping, mismatch classification, user parsing, `PageVote` construction, cached vote reuse, duplicate page propagation, vote mutation methods, or live Wikidot behavior. It only converts malformed generated vote value text into contextual parser errors.
