# PR Draft: Validate Page Vote Collection Page Field

## Summary

`PageVoteCollection` stores the parent `Page` that owns browser-free WhoRated results, cached duplicate vote-list clones, vote lookup failures, rating audit ledgers, and vote/cancel cache invalidation checks. Earlier local slices validated page vote acquisition, parser-side user and value diagnostics, public `Page.vote(...)` write values, `PageVoteCollection.find(user=...)`, the collection's `votes` container and entries, direct `Page.votes` assignment, direct `PageVote.page`, and direct `PageVote.user`/`PageVote.value`, but `PageVoteCollection(page=..., votes=...)` still accepted malformed parent pages such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates the required `PageVoteCollection.page` constructor argument before storing collection state. Malformed values now raise `ValueError("page must be a Page")`. Valid page-owned empty collections, valid page-owned vote lists, iteration, lookup, WhoRated parsing, parser diagnostics, lazy `Page.votes`, duplicate cached vote reuse, direct `Page.votes` assignment validation, vote/cancel cache invalidation, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct page vote collections with malformed parent-page state, while parser-created, fixture-created, cached-duplicate, and manually created valid vote collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free WhoRated inventories, rating audit ledgers, moderation reports, duplicate cached vote reuse, lazy `Page.votes`, vote/cancel cache invalidation, or local tests that construct `PageVoteCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page vote collections as a practical workflow surface. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), and [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md) establish vote reads, parser diagnostics, response diagnostics, public write-value validation, lookup validation, cache invalidation, assignment validation, collection entry validation, direct vote page validation, and direct vote user/value validation as active operational boundaries.

Those prior slices are not duplicates. Issue 418 validates only the collection's `votes` container and entries. Issue 444 validates the `page` field on individual `PageVote` records, not the collection parent. Issue 469 validates direct `PageVote.user` and `PageVote.value`. Issue 416 validates direct `Page.votes = ...` assignment. None validates direct `PageVoteCollection(page=...)` construction before malformed parent-page state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), and [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageVoteCollection.page` at constructor initialization.
- Reject malformed parent-page values with `ValueError("page must be a Page")`.
- Preserve valid empty collections, valid `PageVote` lists, iteration, lookup, parser-created collections, duplicate cached vote reuse, direct assignment validation, vote/cancel cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Page vote parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVoteCollection(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` when `votes` is otherwise valid. |
| R2 | Valid `Page` parent values and valid empty vote lists must remain valid. |
| R3 | Existing valid `PageVote` lists, iteration, `PageVoteCollection.find(...)`, WhoRated parsing, lazy `Page.votes`, duplicate cached vote reuse, direct `Page.votes` assignment validation, vote/cancel cache invalidation, and adjacent page workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, page-vote tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed collection parent pages fail at the public constructor boundary. | `TestPageVoteCollection.test_init_rejects_malformed_pages` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting vote collections with non-`Page` parent state rejects this local completion claim. | PageVoteCollection constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Valid empty collection semantics stay green. | Existing initialization and empty collection tests passed in the 44-test page-vote module run. | Rejecting a valid `Page` with an empty vote list or changing stored parent-page identity rejects this local completion claim. | PageVoteCollection constructor | `tests/unit/test_page_votes.py` |
| R3 | Existing adjacent page workflows remain green. | `tests/unit/test_page_votes.py` passed 44 tests, adjacent page workflow tests passed 711 tests, and full unit tests passed 1895 tests. | Regressing WhoRated parsing, parser diagnostics, lazy `Page.votes`, `PageVoteCollection.find(...)`, duplicate cached vote reuse, direct vote cache assignment, vote/cancel cache invalidation, page source/revision/file workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page vote and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `9c67e4c fix(page_votes): validate vote collection page`.

- RED: `uv run pytest tests/unit/test_page_votes.py::TestPageVoteCollection::test_init_rejects_malformed_pages -q` failed 5 tests before the fix; every malformed `page` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 5 tests after `PageVoteCollection` page validation was added.
- `uv run pytest tests/unit/test_page_votes.py -q` passed 44 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 711 tests.
- `uv run pytest tests/unit -q` passed 1895 tests.
- `uv run ruff format src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed.
- `uv run mypy src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed page-vote test file pass pyright together.

## Acceptance Criteria

- `PageVoteCollection(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- `PageVoteCollection(page=<valid Page>, votes=[])` and `PageVoteCollection(page=<valid Page>, votes=[valid_vote])` remain valid.
- Existing valid `PageVote` lists, iteration, `PageVoteCollection.find(...)`, WhoRated parsing, parser-side user/value diagnostics, direct `PageVote` field validation, direct `Page.votes` assignment validation, duplicate cached vote reuse, and vote/cancel cache invalidation remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVoteCollection.page` is the collection-level parent used by cached duplicate vote reuse, lazy vote state, lookup error context, rating audit ledgers, and local cache invalidation checks. Parser paths already create collections with valid owning pages; direct constructor validation keeps malformed collection parents out of fixtures, generated ledgers, migration comparisons, and downstream audit tooling while preserving parser and caller paths that construct valid collections.

## Local Evidence

- Local rollout evidence used browser-free vote acquisition, duplicate cached vote reuse, vote-cache invalidation, rating diagnostics, and tests that seed vote collections directly.
- Existing local drafts covered vote-list acquisition, duplicate request deduplication, cached duplicate vote reuse, parser user/value diagnostics, response-body diagnostics, public write-value validation, collection votes/entry validation, search-user validation, direct vote-field validation, and direct page-votes assignment validation, but did not cover direct `PageVoteCollection(page=...)` construction.
- The focused RED failures showed invalid constructor parent pages were accepted as collection state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object values.
- This slice only validates page-vote collection parent-page constructor input. It does not change WhoRated parsing, vote value conversion, collection lookup semantics, page vote mutation behavior, cache invalidation behavior, page source/revision/file behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, voter identities, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not compare collection parent identity with each contained vote, infer a page from the first vote, allow `None`, coerce dictionaries into pages, verify site membership, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
