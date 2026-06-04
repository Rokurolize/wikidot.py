# PR Draft: Invalidate Page Vote Cache After Voting

## Summary

`Page.vote(...)` and `Page.cancel_vote(...)` update the page's local `rating` after Wikidot returns a successful rating action response. One adjacent stale-cache gap remained: if the caller had already loaded `page.votes`, the original `Page` instance kept the old `PageVoteCollection` after a successful vote or vote cancellation. The next `page.votes` read could therefore return a pre-mutation voter list even though the rating mutation had just succeeded.

This follow-up keeps vote request construction, login checks, response `points` parsing, contextual malformed-response errors, and returned rating values intact. After a confirmed successful vote mutation, both `Page.vote(...)` and `Page.cancel_vote(...)` now invalidate the calling page object's local vote-list cache so the next `page.votes` access can fetch fresh WhoRated data.

## Related Issue

Builds on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), and [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md). Those drafts established page vote acquisition and mutation as practical workflow surfaces with cache-aware reads, duplicate reuse, parser scoping, malformed-response diagnostics, and contextual rating action parsing.

No upstream issue was filed from this local workspace.

## Changes

- Invalidate the calling `Page` object's cached `PageVoteCollection` after a successful `Page.vote(...)`.
- Invalidate the calling `Page` object's cached `PageVoteCollection` after a successful `Page.cancel_vote(...)`.
- Preserve successful returned rating values and local `rating` updates.
- Preserve malformed `points` response handling and no-local-update behavior on malformed rating responses.
- Add focused regressions for successful vote and cancel-vote cache invalidation.

## Type Of Change

- Page vote cache consistency
- Vote-list cache invalidation
- Browser-free page mutation ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A successful `Page.vote(...)` invalidates the calling page object's cached votes. | `TestPageWriteMethods.test_vote_success_invalidates_cached_votes` seeds `_votes`, performs a successful vote, and asserts `_votes is None`. | Reusing a pre-vote `PageVoteCollection` after a successful vote rejects this local completion claim. |
| A successful `Page.cancel_vote(...)` invalidates the calling page object's cached votes. | `TestPageWriteMethods.test_cancel_vote_success_invalidates_cached_votes` seeds `_votes`, performs a successful vote cancellation, and asserts `_votes is None`. | Reusing a pre-cancel `PageVoteCollection` after a successful cancellation rejects this local completion claim. |
| Successful vote mutations still return and store the parsed rating. | The focused regressions assert returned ratings, and existing `test_vote_positive` / `test_cancel_vote_success` continue asserting local rating updates. | Dropping or changing the returned rating rejects this local completion claim. |
| Malformed rating responses still fail before local mutation cache changes become observable. | Existing malformed `points` tests still assert contextual `NoElementException` and unchanged `rating`. | Clearing caches or updating rating before response parsing rejects this local completion claim. |
| Existing page write, vote acquisition, and publish-adjacent behavior remains intact. | `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_votes.py tests/unit/test_site.py::TestSitePageAccessor -q` passed 98 tests. | Regressions in page writes, WhoRated acquisition, vote parsing, or publish helpers reject this local completion claim. |
| Adjacent page, vote, and site behavior remains unchanged. | `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 230 tests. | Regressions in page, vote, or site unit tests reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `2ede1b7 fix(page): invalidate vote cache after voting`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success_invalidates_cached_votes -q` failed before the fix because `_votes` still contained the old `PageVoteCollection` after successful vote mutations.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success_invalidates_cached_votes -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_votes.py tests/unit/test_site.py::TestSitePageAccessor -q` passed 98 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 230 tests.
- `uv run --extra test pytest tests/unit -q` passed 812 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `Page.vote(...)` calls clear the calling `Page` object's cached votes after the rating response is parsed.
- Successful `Page.cancel_vote(...)` calls clear the calling `Page` object's cached votes after the rating response is parsed.
- The next `page.votes` access can acquire fresh WhoRated data instead of returning a pre-mutation cache.
- Successful vote mutations still return the parsed rating and update local `rating`.
- Failed or malformed vote attempts do not gain a new cache invalidation path before the existing exceptions are raised.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`Page.vote(...)`, `Page.cancel_vote(...)`, and `Page.votes` share the same page rating surface. A successful vote mutation can change the WhoRated list, so a caller that had already loaded `page.votes` should not keep seeing the old vote collection after the mutation completes. Invalidating the local vote cache keeps mutation workflows consistent with the existing lazy vote acquisition model without changing request payloads, returned ratings, parser behavior, or live Wikidot behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established page vote acquisition as retry-aware, cache-aware, duplicate-aware, parser-scoped, and context-rich for malformed structures and rating action responses.
- This slice intentionally targets only post-success vote-cache invalidation on the original `Page` instance; vote-list fetching, WhoRated parsing, duplicate vote reuse, rating response parsing, retry policy, and live Wikidot behavior remain separate boundaries.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved page contents, source text from real pages, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `PageCollection.get_page_votes()`, `Page.votes`, request payloads, rating value parsing, malformed-response exception messages, duplicate vote-list reuse, publish result fields, or exception handling. It only invalidates the calling `Page` object's cached vote collection after the existing successful vote mutation paths complete.
