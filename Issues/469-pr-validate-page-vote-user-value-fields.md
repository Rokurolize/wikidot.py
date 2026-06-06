# PR Draft: Validate Page Vote User And Value Fields

## Summary

`PageVote` records carry the voter and numeric vote value used by browser-free WhoRated reads, duplicate page vote-list reuse, rating audit ledgers, moderation reports, cached vote invalidation, and generated migration snapshots. Earlier local slices validated page vote acquisition, parser-side WhoRated user and value diagnostics, public `Page.vote(...)` write values, `PageVoteCollection.find(user=...)`, `PageVoteCollection(...)` initialization, direct `Page.votes` assignment, and direct parent `PageVote.page` construction, but the public `PageVote(...)` constructor still accepted malformed direct `user` and `value` inputs such as `None`, booleans, strings, dictionaries, arbitrary objects, numeric strings, floats, and lists.

This change validates `PageVote.user` and `PageVote.value` at initialization. `user` now accepts only `AbstractUser` instances, preserving regular, deleted, anonymous, guest, and Wikidot system users returned by the shared user parser. `value` now accepts only non-boolean integers, preserving positive, negative, and other numeric rating values such as the existing five-point fixture. Malformed values raise stable diagnostics: `ValueError("user must be an AbstractUser")` and `ValueError("value must be an integer")`. Existing WhoRated parsing, parser-side user/value diagnostics, direct `PageVote.page` validation, collection lookup, collection initialization, direct `Page.votes` assignment validation, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct page vote records with malformed voter or value state, while parser-created, fixture-created, and manually created valid votes continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free WhoRated inventories, rating audit ledgers, moderation reports, duplicate cached vote reuse, lazy `Page.votes`, vote/cancel cache invalidation, or local tests that construct `PageVote` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page votes as a practical workflow surface. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), and [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md) establish vote reads, parser diagnostics, response diagnostics, public write-value validation, lookup validation, cache invalidation, assignment validation, collection constructor integrity, and direct parent-page constructor integrity as active operational boundaries.

Those prior slices are not duplicates. Issue 241 validates generated WhoRated vote-value parsing, and Issue 307 validates generated WhoRated user metadata at the parser boundary. Issue 353 validates the public `Page.vote(value=...)` write argument before remote action work. Issue 374 validates the search user passed to an already loaded vote collection. Issue 418 validates the collection's `votes` container and entries. Issue 444 validates only the parent `page` field. None validates direct `PageVote(user=..., value=...)` construction before malformed voter or value state becomes stored dataclass state in manually constructed votes, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), and [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageVote.user` validation at dataclass initialization.
- Add `PageVote.value` validation at dataclass initialization.
- Reject malformed non-user constructor values with `ValueError("user must be an AbstractUser")`.
- Reject missing, boolean, string, float, list, and other non-integer vote values with `ValueError("value must be an integer")`.
- Update local direct vote fixtures to use real `User` values instead of generic mocks.
- Preserve existing WhoRated parsing, parser diagnostics, direct `PageVote.page` validation, collection lookup, collection initialization, direct assignment validation, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page vote voter/value state integrity
- Test addition
- Test fixture cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVote(user=None)`, `True`, `"test-user"`, `{"id": 12345}`, and `object()` must raise `ValueError("user must be an AbstractUser")` when every other vote field is valid. |
| R2 | `PageVote(value=None)`, `True`, `"1"`, `1.0`, and `[]` must raise `ValueError("value must be an integer")` when every other vote field is valid. |
| R3 | Valid `AbstractUser` voter values and valid non-boolean integer values, including `5`, must remain valid and preserve existing vote fields. |
| R4 | Existing WhoRated parsing, parser-side user/value diagnostics, direct page validation, collection lookup, collection initialization, direct assignment validation, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-vote tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor users fail at the public dataclass boundary. | `TestPageVote.test_init_rejects_malformed_users` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after user validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting vote rows with non-`AbstractUser` voter state rejects this local completion claim. | PageVote constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Malformed constructor values fail at the public dataclass boundary. | `TestPageVote.test_init_rejects_malformed_values` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after value validation was added. | Accepting missing values, booleans, numeric strings, floats, lists, arbitrary objects, or emitting vote rows with non-integer value state rejects this local completion claim. | PageVote constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R3 | Valid vote user/value semantics stay green. | Existing positive, negative, and numeric vote tests passed after valid direct fixtures used real `User` objects. | Rejecting valid `AbstractUser` implementations, valid non-boolean integer values, parser-created votes, or manually created valid votes rejects this local completion claim. | Parser-created and manually created votes | `tests/unit/test_page_votes.py`, `tests/unit/test_page.py` |
| R4 | Existing adjacent page workflows remain green. | `tests/unit/test_page_votes.py` passed 39 tests, adjacent page workflow tests passed 706 tests, and full unit tests passed 1890 tests. | Regressing WhoRated parsing, parser diagnostics, lazy `Page.votes`, `PageVoteCollection.find(...)`, duplicate cached vote reuse, direct vote cache assignment, vote/cancel cache invalidation, page source/revision/file workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page vote and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `cbd4f55 fix(page_votes): validate vote user and value`.

- RED: `uv run pytest tests/unit/test_page_votes.py::TestPageVote::test_init_rejects_malformed_users tests/unit/test_page_votes.py::TestPageVote::test_init_rejects_malformed_values -q` failed 10 tests before the fix; every malformed `user` or `value` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 10 tests after `PageVote` user/value validation was added.
- `uv run pytest tests/unit/test_page_votes.py -q` passed 39 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 706 tests.
- `uv run pytest tests/unit -q` passed 1890 tests.
- `uv run ruff check src/wikidot/module/page_votes.py tests/unit/test_page_votes.py tests/unit/test_page.py` passed.
- `uv run ruff format src/wikidot/module/page_votes.py tests/unit/test_page_votes.py tests/unit/test_page.py` left 3 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/page_votes.py tests/unit/test_page_votes.py tests/unit/test_page.py` passed with no issues in 3 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/page_votes.py tests/unit/test_page_votes.py tests/unit/test_page.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed page/page-vote test files pass pyright together.

## Acceptance Criteria

- `PageVote(user=None)`, `True`, `"test-user"`, `{"id": 12345}`, and `object()` raise `ValueError("user must be an AbstractUser")`.
- `PageVote(value=None)`, `True`, `"1"`, `1.0`, and `[]` raise `ValueError("value must be an integer")`.
- Valid `AbstractUser` voters and valid non-boolean integer values remain valid, including existing `1`, `-1`, and `5` fixtures.
- Existing WhoRated parsing, parser-side user/value diagnostics, direct `PageVote.page` validation, `PageVoteCollection.find(...)`, collection initialization, direct `Page.votes` assignment validation, duplicate cached vote reuse, and vote/cancel cache invalidation remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVote.user` and `PageVote.value` are the core vote record fields behind WhoRated inventories, rating audits, duplicate vote cache reuse, moderation ledgers, and vote-cache invalidation checks. Parser paths already produce `AbstractUser` instances and integer vote values or contextual parser failures. Constructor validation keeps malformed local vote records out of fixtures, generated ledgers, migration comparisons, and downstream audit tooling while preserving parser and caller paths that construct valid votes.

## Local Evidence

- Local rollout evidence used browser-free vote acquisition, duplicate cached vote reuse, vote-cache invalidation, rating diagnostics, and tests that seed vote objects directly.
- Existing local drafts covered vote-list acquisition, duplicate request deduplication, cached duplicate vote reuse, parser user/value diagnostics, response-body diagnostics, public write-value validation, collection initialization validation, ID/name lookup validation, and direct parent-page validation, but did not cover direct `PageVote(user=..., value=...)` construction.
- The focused RED failures showed invalid constructor voter/value fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, dictionary, arbitrary object, numeric-string, float, and list values according to each field's expected type.
- This slice only validates page-vote user/value constructor input. It does not change WhoRated parsing, vote value conversion, collection lookup semantics, page vote mutation behavior, cache invalidation behavior, page source/revision/file behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, voter identities, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not require vote values to be `1` or `-1`, validate user IDs, verify site membership, coerce strings to integers, compare voter metadata against page metadata, or change live client authentication; those are separate parser, lookup, write-input, and workflow concerns.
