# PR Draft: Validate Page Vote Collection Page Ownership

## Summary

`PageVoteCollection` validates the collection `page`, validates its `votes` container and entries, and each `PageVote` validates its own retained `page`, but the public collection constructor did not ensure contained votes belong to the collection page. A caller could construct or rehydrate `PageVoteCollection(page_a, [vote_from_page_b])`; the resulting collection represented `page_a` while storing a valid vote retained from `page_b`.

This change validates vote entry ownership at the public `PageVoteCollection.__init__` boundary after page and entry validation and before storing list state. Votes whose retained `vote.page` is not the collection page now raise `ValueError("votes must belong to the collection page")`. Valid same-page collections, empty collections, `find(...)`, WhoRated parsing, lazy `Page.votes`, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page/source/revision/file/site workflows remain unchanged.

## Outcome

Page vote collections reject different-page vote entries before local collection state can represent one page while storing another page's votes.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free WhoRated inventories, rating audit ledgers, moderation reports, duplicate cached vote reuse, lazy `Page.votes`, vote/cancel cache invalidation checks, generated migration ledgers, or local tests that construct `PageVoteCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page votes and page-owned vote collections as practical workflow surfaces. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md), and [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md) establish vote reads, parser diagnostics, response diagnostics, public write-value validation, lookup validation, cache invalidation, assignment validation, vote field validation, collection parent validation, and adjacent ownership hardening as active operational boundaries.

This slice is not a duplicate of those issues. Issue 470 validates the explicit `PageVoteCollection.page` field type, Issue 444 validates each `PageVote.page` field type, Issue 418 validates the collection's `votes` container and entries, and Issue 416 validates direct `Page.votes = ...` assignment. None validates a valid `PageVote` entry whose retained `vote.page` is individually valid but does not match the collection page that will own the collection state.

No upstream issue was filed from this local workspace.

## Changes

- Add a page-vote collection ownership preflight at `PageVoteCollection.__init__`.
- Reject different-page vote entries with `ValueError("votes must belong to the collection page")`.
- Add a public regression using a valid vote retained from a different page on the same site.
- Preserve valid same-page vote collections, empty collections, lookup, parser-created collections, duplicate cached vote reuse, direct assignment validation, vote/cancel cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Page vote parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVoteCollection(page_a, [vote_from_page_b])` must reject the different-page vote with `ValueError("votes must belong to the collection page")` before storing collection list state. |
| R2 | Valid same-page vote collections and valid empty collections must remain valid. |
| R3 | Existing `PageVoteCollection.find(...)`, WhoRated parsing, lazy `Page.votes`, duplicate cached vote reuse, direct `Page.votes` assignment validation, vote/cancel cache invalidation, and adjacent page source/revision/file/site workflows must remain unchanged. |
| R4 | Focused RED/GREEN, page-vote module coverage, page/page-vote coverage, adjacent page/page-revision/page-file/page-vote/site tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Different-page vote entries fail at the public collection constructor boundary. | `TestPageVoteCollection.test_init_rejects_vote_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("votes must belong to the collection page")`. | Accepting the different-page vote, storing a collection for `page_a` that contains a vote retained from `page_b`, or deferring failure to lookup/cache code rejects this local completion claim. | `PageVoteCollection.__init__` | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Valid page-owned vote collection semantics stay green. | `tests/unit/test_page_votes.py` passed 45 tests after the ownership preflight. | Rejecting valid same-page votes, empty vote collections, or preserving a different stored collection page rejects this local completion claim. | Page vote collections | `tests/unit/test_page_votes.py` |
| R3 | Existing page vote and adjacent page workflows remain green. | Page/page-vote coverage passed 341 tests, adjacent page/page-revision/page-file/page-vote/site coverage passed 823 tests, and the full unit suite passed 2691 tests. | Regressing WhoRated parsing, vote lookup, duplicate cached vote reuse, lazy `Page.votes`, direct vote assignment validation, vote/cancel cache invalidation, page source/revision/file behavior, or site/page workflows rejects this local completion claim. | Page vote and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_file.py`, `tests/unit/test_site.py`, `tests/unit` |
| R4 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, full `pyright`, and `git diff --check` passed. Full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted; full mypy found no issues in 87 source files. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic valid `Page` and `PageVote` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `b0fa6b7 fix(page_votes): validate vote collection page ownership`.

- RED target-page ownership: `uv run pytest tests/unit/test_page_votes.py::TestPageVoteCollection::test_init_rejects_vote_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused ownership regression: `uv run pytest tests/unit/test_page_votes.py::TestPageVoteCollection::test_init_rejects_vote_from_different_page -q` passed 1 test.
- Page vote module coverage: `uv run pytest tests/unit/test_page_votes.py -q` passed 45 tests.
- Page/page-vote coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py -q` passed 341 tests.
- Adjacent page/page-revision/page-file/page-vote/site tests: `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 823 tests.
- `uv run pytest tests/unit -q` passed 2691 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageVoteCollection(page_a, [vote_from_page_b])` raises `ValueError("votes must belong to the collection page")` before storing collection list state.
- `PageVoteCollection(page=<valid Page>, votes=[])` and `PageVoteCollection(page=<valid Page>, votes=[same_page_vote])` remain valid.
- Existing `PageVoteCollection.find(...)`, WhoRated parsing, parser diagnostics, lazy `Page.votes`, duplicate cached vote reuse, direct `Page.votes` assignment validation, vote/cancel cache invalidation, and adjacent page source/revision/file/site behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVoteCollection.page` and each retained `PageVote.page` should describe the same owning page for browser-free WhoRated inventories, duplicate cached vote reuse, lazy vote state, lookup error context, rating audit ledgers, and local vote-cache invalidation checks. Parser paths already create votes from the owning page; constructor ownership validation keeps mismatched rehydrated records, fixtures, or generated ledgers from silently carrying another page's votes under the collection page.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid vote from another page could be accepted by `PageVoteCollection(page, [vote])` without ownership rejection.
- Existing local drafts covered vote-list acquisition, duplicate request deduplication, cached duplicate vote reuse, parser user/value diagnostics, response-body diagnostics, public vote-value validation, collection votes/entry validation, search-user validation, direct vote-field validation, direct collection-parent validation, and direct page-votes assignment validation, but did not cover comparing each valid `PageVote.page` to the collection page.
- This slice only validates page-vote collection target-page ownership at collection initialization. It does not change WhoRated parsing, vote value conversion, collection lookup semantics, page vote mutation behavior, cache invalidation behavior, page source/revision/file behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, voter identities, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally uses object identity. A page-owned vote collection should contain `PageVote` objects retained from the exact owning `Page` object, matching parser-created votes and duplicate cached vote clones. It does not infer a collection page from the first vote, coerce page-like objects, compare by fullname alone, verify remote site membership, or change live client authentication; those are separate parser, lookup, and workflow concerns.
