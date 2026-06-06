# PR Draft: Validate Page Vote Collection Initialization

## Summary

`PageVoteCollection` documents `votes` as `list[PageVote]`, but its constructor accepted arbitrary iterable containers and arbitrary list entries. A caller could construct `PageVoteCollection(page, "vote")`, `PageVoteCollection(page, ("vote",))`, or `PageVoteCollection(page, [None])`; the malformed collection then failed later in iteration, `find(...)`, direct `Page.votes` assignment, duplicate cached vote reuse, or vote-cache invalidation code with unstable attribute errors or silently poisoned local state.

This change validates constructor input before storing entries. Non-list `votes` now raises `ValueError("votes must be a list")`; list entries that are not `PageVote` now raise `ValueError("votes list entries must be PageVote")`. Valid empty collections, valid `PageVote` lists, iteration, `find(...)`, lazy `Page.votes` acquisition, direct `Page.votes` assignment validation, duplicate cached vote reuse, and successful vote/cancel cache invalidation remain unchanged.

## Outcome

Callers cannot silently create malformed `PageVoteCollection` instances through the public constructor, while the existing `Page.votes` setter still defends against later list mutation before cached vote state is replaced.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page vote reads, WhoRated audits, moderation ledgers, rating checks, duplicate cached vote reuse, generated reports, migration scripts, or local fixtures that construct vote collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page votes as a practical workflow surface. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), and [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md) establish vote acquisition, vote parsing, vote lookup, vote mutation, and vote cache state as active operational boundaries.

Those prior slices are not duplicates. Issues065 and 129 covered vote-list fetch deduplication and cached duplicate reuse; Issues093, 154, 202, 223, 241, 307, and 333 hardened WhoRated parsing and response diagnostics; Issues152 and 196 improved lazy vote failure context; Issue261 invalidated cached votes after successful vote mutations; Issue337 guarded rating action responses; Issue353 validated public vote values; Issue368 validated page collection entries before vote acquisition; Issue374 validated `PageVoteCollection.find(user=...)`; Issue416 validated direct `Page.votes = ...` assignment. None of them validates the `PageVoteCollection(page, votes=...)` constructor itself before malformed vote entries become stored list state.

## Related Issue

Builds directly on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), and [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageVoteCollection.__init__(..., votes=...)` validation.
- Reject non-list `votes` with `ValueError("votes must be a list")`.
- Reject non-`PageVote` list entries with `ValueError("votes list entries must be PageVote")`.
- Update the direct `Page.votes` setter regression fixture to mutate a valid collection after construction, so the setter guard still proves later list mutation is rejected.
- Preserve valid empty collections, valid `PageVote` entries, iteration, `find(...)`, lazy vote acquisition, direct valid `Page.votes` assignment, duplicate cached vote reuse, and vote/cancel cache invalidation behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Page vote collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVoteCollection(page, None)`, `PageVoteCollection(page, True)`, `PageVoteCollection(page, "vote")`, and `PageVoteCollection(page, ("vote",))` must raise `ValueError("votes must be a list")` before storing collection entries. |
| R2 | `PageVoteCollection(page, [None])`, `PageVoteCollection(page, [True])`, `PageVoteCollection(page, ["vote"])`, and `PageVoteCollection(page, [{"user": 1}])` must raise `ValueError("votes list entries must be PageVote")` before storing collection entries. |
| R3 | `PageVoteCollection(page, [])` and `PageVoteCollection(page, [valid_vote])` must remain valid. |
| R4 | A valid `PageVoteCollection` that is later mutated to contain malformed entries must still be rejected by direct `Page.votes` assignment before replacing cached vote state. |
| R5 | Existing iteration, `PageVoteCollection.find(...)`, lazy vote acquisition, duplicate cached vote reuse, successful vote/cancel cache invalidation, page source/revision/file workflows, and site/page workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent page/vote tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary. | `TestPageVoteCollection.test_init_rejects_non_list_votes` failed RED for `None` and `True` with incidental `TypeError`, and for `"vote"` and `("vote",)` with no `ValueError`; it passed GREEN after constructor validation was added. | Treating strings as character entries, accepting tuples, storing booleans, or deferring failure to iteration rejects this local completion claim. | PageVoteCollection constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Non-`PageVote` constructor list entries fail at the public constructor boundary. | `TestPageVoteCollection.test_init_rejects_non_vote_entries` failed RED for `None`, `True`, `"vote"`, and `{"user": 1}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized vote records, or fixture stand-ins as stored votes rejects this local completion claim. | PageVoteCollection constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R3 | Valid constructor inputs remain green. | Existing initialization, empty-list, iteration, `find(...)`, and `PageVote` tests passed in the 24-test page-votes module run. | Rejecting empty valid lists, valid `PageVote` lists, normal iteration, or normal user lookup rejects this local completion claim. | PageVoteCollection constructor and methods | `tests/unit/test_page_votes.py` |
| R4 | The direct `Page.votes` setter still rejects malformed entries introduced after construction. | `TestPageProperties.test_votes_setter_rejects_invalid_collection_entries` now creates a valid collection, mutates its list entry, and passes in the 182-test adjacent page/vote run. | Removing setter entry validation, allowing mutated vote collections to replace cached votes, or corrupting an existing valid vote cache rejects this local completion claim. | Direct page votes setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R5 | Existing page and vote workflows remain green. | Page/vote/property/write tests passed 182 tests, page/page-file/page-revision/page-votes/site tests passed 524 tests, and full unit tests passed 1502 tests. | Regressing lazy WhoRated lookup, `find(...)`, duplicate cached vote reuse, vote mutation cache invalidation, page source/revision/file reads, publish/create/edit, or site/page workflows rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/vote/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e75310c fix(page_votes): validate vote collection initialization`.

- RED: `uv run --extra test pytest tests/unit/test_page_votes.py::TestPageVoteCollection::test_init_rejects_non_list_votes tests/unit/test_page_votes.py::TestPageVoteCollection::test_init_rejects_non_vote_entries -q` failed 8 tests before the fix; malformed constructor input either raised incidental `TypeError`, was accepted without `ValueError`, or stored malformed entries.
- GREEN: the same focused command passed 8 tests after adding constructor validation.
- `uv run ruff format src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` left 2 files unchanged.
- Initial adjacent regression check exposed that `TestPageProperties.test_votes_setter_rejects_invalid_collection_entries` was constructing an invalid `PageVoteCollection` directly; the fixture was updated to mutate a valid collection after construction so it still proves the setter guard.
- `uv run ruff format tests/unit/test_page.py tests/unit/test_page_votes.py src/wikidot/module/page_votes.py && uv run --extra test pytest tests/unit/test_page_votes.py tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageWriteMethods -q` passed 182 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 524 tests.
- `uv run --extra test pytest tests/unit -q` passed 1502 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PageVoteCollection(page, None)`, `PageVoteCollection(page, True)`, `PageVoteCollection(page, "vote")`, and `PageVoteCollection(page, ("vote",))` raise `ValueError("votes must be a list")`.
- `PageVoteCollection(page, [None])`, `PageVoteCollection(page, [True])`, `PageVoteCollection(page, ["vote"])`, and `PageVoteCollection(page, [{"user": 1}])` raise `ValueError("votes list entries must be PageVote")`.
- `PageVoteCollection(page, [])` and `PageVoteCollection(page, [valid_vote])` continue to work.
- A valid collection that is later mutated with a malformed entry still causes direct `page.votes = mutated_collection` to raise `ValueError("page.votes list entries must be PageVote")` without changing an existing cached valid vote collection.
- Existing `PageVoteCollection.find(...)`, lazy `Page.votes` acquisition, WhoRated parsing, duplicate cached vote reuse, vote mutation cache invalidation, page source/revision/file reads, create/edit, publish, and site/page behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVoteCollection` is the stored object shape behind browser-free WhoRated reads, cached duplicate vote reuse, vote lookup, rating audit ledgers, and successful vote/cancel cache invalidation. Constructor validation keeps malformed local state out of the collection while preserving the existing direct-assignment guard against post-construction list mutation.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free vote acquisition, duplicate cached vote reuse, vote mutation cache invalidation, rating diagnostics, and tests that seed vote collections directly.
- Existing local drafts covered vote-list fetch deduplication, duplicate vote-list reuse, lazy vote failure context, WhoRated parser scoping and diagnostics, rating action validation, public vote-value validation, page collection entry validation, `PageVoteCollection.find(...)` search-user validation, and direct `Page.votes` assignment, but did not cover the `PageVoteCollection(page, votes=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, and the existing setter guard after explicit post-construction mutation.
- This slice only validates vote collection constructor input and updates test fixtures to use real `PageVote` objects or explicit post-construction mutation. It does not change lazy vote acquisition, WhoRated parsing, `PageVoteCollection.find(...)`, vote mutation behavior, duplicate source/revision/file behavior, publish behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, voter identities, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed vote-like objects and test mocks in `PageVoteCollection`. Callers should construct real `PageVote` entries before storing them in a vote collection; tests that only need mutation-safety coverage should mutate a valid collection after construction.
