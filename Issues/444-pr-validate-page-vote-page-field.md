# PR Draft: Validate Page Vote Page Field

## Summary

`PageVote` records carry the owning `Page` object used by WhoRated parsing, lazy `Page.votes`, duplicate page vote reuse, moderation ledgers, rating audits, and cached vote invalidation workflows. Earlier local slices validated page vote acquisition, duplicate vote ownership, vote parser diagnostics, public `Page.vote(...)` values, `PageVoteCollection(...)` initialization, direct `Page.votes` assignment, and `PageVoteCollection.find(user=...)`, but the public `PageVote(...)` constructor still accepted malformed `page` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `PageVote.page` at initialization. Malformed values now raise `ValueError("page must be a Page")`. Existing WhoRated parsing, lazy `Page.votes`, duplicate cached vote reuse, collection behavior, valid vote lookup, vote mutation cache invalidation, and adjacent page workflows remain unchanged for valid `Page` objects.

## Outcome

Callers cannot silently construct vote records whose parent page is not a `Page`, while valid parser-created, fixture-created, and manually created page votes continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free vote-list reads, WhoRated audits, moderation ledgers, rating checks, duplicate page-vote cache reuse, `PageVoteCollection.find(...)`, lazy `Page.votes`, generated reports, or local tests that construct `PageVote` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page vote ownership as a practical workflow surface. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md) and [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md) explicitly preserve duplicate page ownership by creating fresh `PageVote(page, user, value)` objects for each owning page and by asserting parsed `PageVote.page` points at the owning duplicate page. Adjacent vote drafts [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), and [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md) establish vote reads, parser diagnostics, response diagnostics, lookup validation, mutation validation, cache invalidation, assignment validation, and collection constructor integrity as active operational boundaries.

Those prior slices are not duplicates. They covered vote-list fetching, retry behavior, duplicate vote-list ownership, WhoRated parser diagnostics, response diagnostics, public vote-value validation, lookup user validation, direct `Page.votes` assignment validation, and `PageVoteCollection(page, votes=...)` initialization. None validates direct `PageVote(page=...)` construction before malformed parent-page state becomes stored dataclass state.

## Related Issue

Builds directly on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), and the adjacent constructor page-field validation pattern from [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md) and [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageVote.page` validation at dataclass initialization.
- Reject non-`Page` values with `ValueError("page must be a Page")`.
- Update page-vote unit fixtures to use real `Page` objects instead of generic page mocks for valid votes.
- Keep negative test fixtures pyright-clean by typing intentionally malformed values through `Any`.
- Preserve existing WhoRated parsing, lazy `Page.votes`, duplicate cached vote reuse, collection behavior, valid vote lookup, vote mutation cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page-vote parent-page state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVote(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` when every other vote field is valid. |
| R2 | Valid `Page` instances must remain valid and preserve existing vote fields. |
| R3 | Existing WhoRated parsing, lazy `Page.votes`, duplicate cached vote reuse, collection behavior, valid lookup, vote mutation cache invalidation, and adjacent page workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, page-vote/page tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor pages fail at the public dataclass boundary. | `TestPageVote.test_init_rejects_malformed_pages` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting vote rows with non-`Page` parent state rejects this local completion claim. | PageVote constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Valid page semantics stay green. | Existing page-vote unit tests passed after the local fixture was moved to real `Page` objects. | Rejecting valid `Page` instances, coercing page-like mocks, or changing stored vote fields rejects this local completion claim. | PageVote fixtures and parser-created votes | `tests/unit/test_page_votes.py`, `tests/unit/test_page.py` |
| R3 | Existing adjacent vote workflows remain green. | `tests/unit/test_page_votes.py` passed 29 tests, `tests/unit/test_page.py` passed 250 tests, and full unit tests passed 1707 tests. | Regressing WhoRated rows, duplicate cached vote reuse, valid `find(...)`, vote mutation cache invalidation, page properties, or adjacent page workflows rejects this local completion claim. | Page vote and page workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter names from private sites, vote data from private sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `840c332 fix(page_votes): validate vote page`.

- RED: `uv run pytest tests/unit/test_page_votes.py::TestPageVote::test_init_rejects_malformed_pages -q` failed 5 tests before the fix; every malformed `page` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_page_votes.py::TestPageVote::test_init_rejects_malformed_pages -q` passed 5 tests.
- `uv run pytest tests/unit/test_page_votes.py -q` passed 29 tests.
- `uv run ruff check src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed.
- `uv run pyright src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_page.py -q` passed 250 tests.
- `uv run pytest tests/unit -q` passed 1707 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 111 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, requestutil response narrowing issues, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `PageVote(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- Valid `Page` instances remain valid as `page`.
- Existing WhoRated parsing, lazy `Page.votes`, duplicate cached vote reuse, valid `PageVoteCollection.find(...)`, direct `Page.votes` assignment validation, and vote mutation cache invalidation remain green.
- Existing page source/revision/file/property workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVote.page` is the parent context behind browser-free WhoRated reads, duplicate page vote-list reuse, vote lookup, moderation ledgers, rating audits, and vote-cache invalidation checks. Constructor validation keeps malformed local parent-page state out of vote rows while preserving parser and caller paths that construct votes from real `Page` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used page-owned duplicate vote lists and verified each parsed `PageVote.page` points at the owning duplicate page object.
- Existing local drafts covered vote-list acquisition, retry behavior, duplicate request deduplication, cached duplicate vote reuse, parser diagnostics, response-body diagnostics, collection initialization validation, direct `Page.votes` assignment validation, public vote value validation, and lookup user validation, but did not cover direct `PageVote(page=...)` construction.
- The focused RED failures showed invalid constructor page fields were accepted as dataclass state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object page values.
- This slice only validates page vote parent-page constructor input. It does not change WhoRated parsing, vote value conversion, collection lookup semantics, page vote mutation behavior, cache invalidation behavior, page source/revision/file behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, voter names from private sites, vote data from private sites, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `page` is a `Page` instance. It does not validate page IDs, page fullnames, site identity, user shape, vote value shape, rating semantics, or live client authentication at `PageVote` construction time; those are separate page object, user, vote-value, parser, and workflow concerns.
