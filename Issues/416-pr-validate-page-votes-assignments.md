# PR Draft: Validate Page Votes Assignments

## Summary

`Page.votes` is a public property that lazily acquires and caches a `PageVoteCollection`. The setter documented `value` as `PageVoteCollection`, but it accepted any object and stored it directly. A caller could assign `page.votes = None`, `page.votes = True`, `page.votes = "100"`, `page.votes = {"user": 100}`, or a raw list, causing later `Page.votes`, `PageVoteCollection.find(...)`, duplicate cached vote reuse, or vote-cache invalidation code to operate on malformed local state.

The setter also accepted already-built `PageVoteCollection` instances with malformed entries. This change validates direct `Page.votes` assignments before mutating `_votes`. Invalid assignment shapes now raise `ValueError("page.votes must be PageVoteCollection")`; invalid collection entries now raise `ValueError("page.votes list entries must be PageVote")`; previously cached valid votes are preserved when validation fails.

## Outcome

Manually constructed, fixture-created, duplicate-reused, or ledger-rehydrated `Page` objects can no longer silently corrupt their cached vote collection through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page vote reads, rating audits, moderation ledgers, publish-adjacent checks, cleanup tooling, generated reports, migration scripts, or local tests that construct `Page` objects directly.

## Current Evidence

Local rollout evidence repeatedly uses page vote state as a practical workflow boundary. Existing drafts [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), and [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md) establish page votes as an active operational surface.

Those prior slices are not duplicates. Issues093, 154, 202, 223, 241, 307, and 333 hardened WhoRated parsing and response boundaries; Issue129 reused cached duplicate page votes; Issues152 and 196 improved lazy vote failure context; Issue261 invalidated cached votes after successful vote mutations; Issue337 guarded malformed rating action responses before local state mutation; Issue353 validated `Page.vote(value=...)` inputs; Issue368 validated `PageCollection` entries before vote acquisition; Issue374 validated `PageVoteCollection.find(...)` search users; Issues413, 414, and 415 validated direct `Page.id`, `Page.source`, and `Page.revisions` assignment. None of them validates direct public `Page.votes = ...` assignments before cached state mutation.

## Related Issue

Builds directly on [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), and [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a direct `Page.votes` assignment validator.
- Reject non-`PageVoteCollection` values with `ValueError("page.votes must be PageVoteCollection")`.
- Reject malformed entries in assigned `PageVoteCollection` objects with `ValueError("page.votes list entries must be PageVote")`.
- Validate before assigning `_votes`, so invalid assignments preserve any previously cached valid vote collection.
- Preserve valid `PageVoteCollection` assignment, lazy vote acquisition, `PageVoteCollection.find(...)`, duplicate cached vote reuse, vote-cache invalidation after successful vote mutations, and adjacent site/page workflows.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `page.votes = None`, `page.votes = True`, `page.votes = "100"`, `page.votes = {"user": 100}`, and `page.votes = []` must raise `ValueError("page.votes must be PageVoteCollection")` before mutating `_votes`. |
| R2 | `page.votes = PageVoteCollection(page, [bad_entry])` must raise `ValueError("page.votes list entries must be PageVote")` for `None`, `True`, `"100"`, and `{"user": 100}` entries before mutating `_votes`. |
| R3 | Invalid assignments after an already-cached valid `PageVoteCollection` must preserve that previous collection. |
| R4 | Valid `PageVoteCollection` assignments must remain allowed. |
| R5 | Lazy vote acquisition, `PageVoteCollection.find(...)`, duplicate cached vote reuse, successful vote/cancel cache invalidation, page source/revision/file workflows, and site/page workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent page/vote tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-`PageVoteCollection` assignments fail before local vote cache mutation. | `TestPageProperties.test_votes_setter_rejects_invalid_collections` failed RED for `None`, `True`, `"100"`, `{"user": 100}`, and `[]` because the setter did not raise, then passed GREEN after assignment-shape validation was added. | Accepting missing values, booleans, strings, dictionaries, or raw lists as vote collections, clearing `_votes`, or surfacing later iteration/cache failures rejects this local completion claim. | Direct page votes setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Assigned `PageVoteCollection` objects with malformed entries fail before local vote cache mutation. | `TestPageProperties.test_votes_setter_rejects_invalid_collection_entries` failed RED for `None`, `True`, `"100"`, and `{"user": 100}` entries, then passed GREEN after collection-entry validation was added. | Trusting a prebuilt malformed collection, storing it as `_votes`, or deferring failure to vote lookup, cached duplicate reuse, or mutation invalidation rejects this local completion claim. | Direct page votes setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Invalid assignments preserve the previous valid cached votes. | Each focused GREEN regression asserts the cached vote value remains `1` after a rejected assignment. | Mutating `_votes` before raising, clearing cached votes, or triggering lazy lookup to recover the value rejects this local completion claim. | Local page vote cache | `tests/unit/test_page.py` |
| R4 | Valid vote assignment behavior remains green. | Valid `PageVoteCollection` assignment is used as the setup path in the focused tests, property/acquisition/vote tests passed 129 tests, and adjacent page/site tests passed 511 tests. | Rejecting valid vote collections or breaking page-owned collection behavior rejects this local completion claim. | Page fixtures and cache setup | `tests/unit/test_page.py`, `tests/unit/test_page_votes.py` |
| R5 | Existing page and vote workflows remain green. | Page property plus acquisition plus vote tests passed 129 tests, page/page-file/page-revision/page-votes/site tests passed 511 tests, and full unit tests passed 1489 tests. | Regressing lazy vote lookup, WhoRated parsing, duplicate cached vote reuse, vote mutation cache invalidation, page source/revision/file reads, publish/create/edit, or site/page workflows rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/vote/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b52b4c5 fix(page): validate page votes assignments`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_invalid_collections -q` failed 5 tests before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`; bad values were accepted by the setter and assigned into `_votes`.
- GREEN: the same focused command passed 5 tests after adding assignment-shape validation.
- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_invalid_collection_entries -q` failed 4 tests before the entry fix with `Failed: DID NOT RAISE <class 'ValueError'>`; bad collection entries were accepted and assigned into `_votes`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_invalid_collections tests/unit/test_page.py::TestPageProperties::test_votes_setter_rejects_invalid_collection_entries -q` passed 9 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` reformatted one file and left one file unchanged.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_votes.py -q` passed 129 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 511 tests.
- `uv run --extra test pytest tests/unit -q` passed 1489 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `page.votes = None`, `page.votes = True`, `page.votes = "100"`, `page.votes = {"user": 100}`, and `page.votes = []` raise `ValueError("page.votes must be PageVoteCollection")` without changing an existing cached valid vote collection.
- `page.votes = PageVoteCollection(page, [None])`, `[True]`, `["100"]`, and `[{"user": 100}]` raise `ValueError("page.votes list entries must be PageVote")` without changing an existing cached valid vote collection.
- `page.votes = PageVoteCollection(page, [valid_vote])` remains valid.
- Existing lazy `Page.votes` acquisition still runs when `_votes` is missing and still reports site/page context if acquisition leaves `_votes` unset.
- Existing `PageVoteCollection.find(...)`, WhoRated acquisition, duplicate cached vote reuse, vote mutation cache invalidation, page source/revision/file reads, create/edit, publish, and site/page behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.votes` is shared by lazy WhoRated reads, duplicate cached vote reuse, vote lookup, rating audit ledgers, and successful vote/cancel cache invalidation. Direct assignment is useful for tests, caller-created page objects, and data rehydrated from external ledgers, but malformed vote collections should fail at the property boundary instead of silently poisoning later vote scans or cache behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free vote acquisition, duplicate cached vote reuse, vote mutation cache invalidation, rating diagnostics, and tests that seed vote caches directly.
- Existing local drafts covered lazy vote failure context, WhoRated parser scoping and diagnostics, duplicate vote-list reuse, vote mutation cache invalidation, rating action validation, public vote-value validation, page collection entry validation, and `PageVoteCollection.find(...)` search-user validation, but did not cover direct `Page.votes` setter mutation.
- The focused RED failures showed invalid assignments were accepted by the property setter. The GREEN regressions cover malformed assignment shapes, malformed prebuilt collection entries, and previous-cache preservation.
- This slice only validates direct page votes assignment shape and entry shape; it does not change lazy vote acquisition, WhoRated parsing, `PageVoteCollection.find(...)`, vote mutation behavior, duplicate source/revision/file behavior, publish behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, voter identities, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed vote cache objects instead of coercing or duck-typing them. Callers that load vote records from files, generated structures, JSON, YAML, CLI flags, or ledgers should resolve them to `PageVoteCollection` objects containing `PageVote` entries before assigning them to `Page.votes`.
