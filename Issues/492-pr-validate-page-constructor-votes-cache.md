# PR Draft: Validate Page Constructor Votes Cache

## Summary

`Page._votes` is the optional cached `PageVoteCollection` behind the public `Page.votes` property. It is used by lazy WhoRated reads, duplicate cached vote-list reuse, vote lookup, rating audit ledgers, vote and cancel-vote cache invalidation, local fixtures, and rehydrated page records. Public `Page.votes = ...` assignment already validates assigned values and entries, and `PageVoteCollection(...)` already validates constructor input and parent page state, but direct dataclass construction still accepted malformed `_votes` values such as booleans, strings, raw lists, dictionaries, arbitrary objects, and post-construction mutated collections.

This change validates the direct constructor's optional votes cache during `Page.__post_init__`. `_votes=None` remains valid for pages that have not acquired votes yet, real `PageVoteCollection` objects remain valid, and malformed non-null values now raise stable `ValueError` diagnostics before they can make `Page.votes` return malformed local cache state.

## Outcome

Directly constructed `Page` objects now fail early when optional cached vote state is malformed, while preserving lazy vote acquisition for `_votes=None` and preserving valid preloaded `PageVoteCollection` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, WhoRated ledgers, rating audit reports, moderation reports, cached page records, local fixtures, generated adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

[416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md) validates public `Page.votes = ...` assignment before mutating `_votes`. [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md) validates the public `PageVoteCollection(page, votes=...)` constructor's vote container and entries. [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md) validates the collection's parent page. [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md) and [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md) validate direct `PageVote` fields. Recent direct `Page` constructor slices validate identity, counts, rating, parent fullname, tags, site, nullable metadata, rating-percent, cached page-ID, cached source, and cached revisions fields.

Those prior slices are not duplicates. Issue 416 covers post-construction assignment through the public `Page.votes` setter, not direct dataclass initialization. Issue 418 covers constructing `PageVoteCollection` instances, not deciding whether a direct `Page(_votes=...)` value is a valid page cache. Issue 470 covers the collection parent field, not the `Page` object's optional cache slot. Issues 444 and 469 cover individual vote records. Issues 481 through 491 validate other direct `Page` constructor fields only. None validates direct `Page(_votes=...)` construction before malformed cached-vote state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), and the direct `Page` constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md).

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached votes validation for direct `Page(...)` construction.
- Preserve `_votes=None` for pages that should lazily acquire WhoRated data.
- Preserve valid `PageVoteCollection` objects without coercion.
- Reject booleans, strings, raw lists, dictionaries, arbitrary non-collection objects, and collections mutated with malformed entries using stable `ValueError` diagnostics.
- Add constructor tests for valid optional vote cache state, malformed direct `_votes` values, and malformed cached collection entries.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached vote state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_votes=...)` must accept `None` and real `PageVoteCollection` objects. |
| R2 | `Page(_votes=...)` must reject non-`None` non-`PageVoteCollection` values with `ValueError("page.votes must be PageVoteCollection or None")`. |
| R3 | `Page(_votes=...)` must reject `PageVoteCollection` objects containing non-`PageVote` entries with `ValueError("page.votes list entries must be PageVote")`. |
| R4 | Valid page construction, lazy vote acquisition, public `Page.votes` assignment validation, `PageVoteCollection` construction validation, parser-created pages, vote lookup, duplicate cached vote-list reuse, vote and cancel-vote cache invalidation, and page source/revision/file/vote workflows must remain unchanged. |
| R5 | This slice must not change public `Page.votes = ...` assignment behavior, WhoRated parsing, vote collection constructor semantics, page vote action behavior, cache invalidation, live request behavior, or unrelated constructor fields. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid `PageVoteCollection` cached vote values remain accepted. | `TestPageInit.test_init_accepts_valid_optional_votes` passed RED and GREEN, preserving `_votes=None` and returning a valid cached `PageVoteCollection` through `page.votes`. | Rejecting missing cached votes, triggering vote lookup during construction, or coercing valid collection objects rejects this local completion claim. | `Page` constructor cached-vote state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed optional cached vote values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_votes` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, raw lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor cached-vote state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Mutated vote collections with malformed entries fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_vote_entries` failed RED because a valid collection mutated with `object()` was accepted, then passed GREEN after entry validation was added. | Trusting a mutated collection, storing malformed entries, or deferring failure to `PageVoteCollection.find(...)`, duplicate cached vote reuse, or vote cache invalidation rejects this local completion claim. | `Page` constructor cached-vote entries | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R4 | Existing page and vote workflows remain green. | Constructor tests passed 130 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 724 tests; full unit tests passed 2112 tests. | Regressing lazy vote acquisition, `Page.votes` assignment validation, `PageVoteCollection` construction validation, parser-created pages, vote lookup, duplicate cached vote reuse, vote/cancel cache invalidation, or page source/revision/file/vote workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R5 | Broader vote semantics remain outside scope. | Existing WhoRated parser, public setter, collection constructor, vote action, cache invalidation, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing public assignment behavior, changing lazy acquisition, changing request construction, changing parser conversion, changing collection construction, or touching live request behavior rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d82da2f fix(page): validate constructor votes cache`.

- RED: `uv run --extra test pytest -q tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_votes tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_votes tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_vote_entries` failed 6 malformed `_votes` cases before the fix with `DID NOT RAISE`, while the valid optional-votes case passed.
- GREEN: the same focused command passed 7 tests after optional cached votes validation was added.
- `uv run --extra test pytest -q tests/unit/test_page_constructor.py` passed 130 tests.
- `uv run --extra test pytest -q tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py` passed 724 tests.
- `uv run --extra test pytest -q tests/unit` passed 2112 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 44 existing full-tree test typing errors outside this slice, including intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test module pass pyright together.

## Acceptance Criteria

- `Page(_votes=None)` remains valid and lazy vote acquisition remains available.
- `Page(_votes=PageVoteCollection(...))` remains valid and `page.votes` returns the cached object without a lookup.
- `Page(_votes=True)`, `Page(_votes="cached votes")`, `Page(_votes=[])`, `Page(_votes={"votes": []})`, and `Page(_votes=object())` raise `ValueError("page.votes must be PageVoteCollection or None")` when every other constructor field is valid.
- `Page(_votes=collection_mutated_with_non_vote)` raises `ValueError("page.votes list entries must be PageVote")` when every other constructor field is valid.
- Existing parser-created pages, direct page fixtures, page collection behavior, lazy `Page.votes`, public `Page.votes` setter validation, `PageVoteCollection` construction validation, vote lookup, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not validate vote collection ownership, WhoRated parser contents, live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Cached votes are a shared state surface for WhoRated reads, duplicate cache reuse, vote lookup, rating audit ledgers, and vote/cancel invalidation. Direct construction is useful for fixtures and rehydrated records, but malformed cached vote values should fail at construction instead of making `Page.votes` return unusable state.

## Local Evidence

- Local rollout evidence used cached page vote state in browser-free page inventories, WhoRated ledgers, rating audit reports, moderation reports, cached page records, and generated audit records.
- Existing local drafts covered direct `Page.votes` assignment, `PageVoteCollection` construction, collection parent validation, individual `PageVote` fields, vote parser diagnostics, response diagnostics, cache invalidation, and duplicate cached vote reuse, but did not cover direct optional cached-votes construction on `Page`.
- Existing unit fixtures already relied on `_votes=None` being valid for lazy vote acquisition and `PageVoteCollection` being valid for preloaded vote records, so this change validates only malformed non-null values and mutated entries.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, source/revision/file/meta cache semantics, live Wikidot behavior, site client internals, vote action behavior, or unrelated constructor fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The validator deliberately does not change public `Page.votes = collection` assignment behavior. The direct `_votes` constructor field is the stored cache field and therefore accepts only the annotated cache object shape plus `None`, while the public setter keeps its existing non-optional collection diagnostic for post-construction assignments.
