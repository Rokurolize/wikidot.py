# PR Draft: Validate Page Vote Lookup Retained User ID State

## Summary

`PageVoteCollection.find(user)` validates the lookup target shape and site client before scanning stored votes, but the scan compared each retained `vote.user.id` directly against the lookup user's ID. After local fixture, serialized, or rehydrated vote state has been mutated incorrectly, booleans and floats can satisfy Python equality against integer user IDs, while strings, lists, and negative IDs are reported as generic "has not voted" misses instead of corrupted retained vote-user ID state. A negative retained lookup user ID could also reach the scan and return the same generic miss.

This change validates the lookup user's retained ID as a non-negative integer before scanning and validates each stored vote user's retained ID as an optional non-negative integer before comparison. Malformed stored vote user IDs now raise `ValueError("vote.user.id must be an integer or None")`, negative stored vote user IDs now raise `ValueError("vote.user.id must be non-negative or None")`, negative lookup user IDs now raise `ValueError("user.id must be non-negative")`, valid zero-ID vote lookup remains accepted, stored `vote.user.id=None` remains a non-match that can be skipped, and no WhoRated fetching or live Wikidot behavior changes.

## Outcome

`PageVoteCollection.find(user)` can no longer return a vote by Python's loose numeric equality or hide corrupted retained vote-user IDs behind an ordinary lookup miss.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free WhoRated inventories, rating audit ledgers, moderation exports, cached page vote records, generated migration data, local fixtures, or serialized and rehydrated `PageVoteCollection` objects.

## Current Evidence

Local rollout-backed drafts already established page vote lookup and caches as practical boundaries. [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md), and [620-pr-validate-page-vote-search-user-client.md](620-pr-validate-page-vote-search-user-client.md) cover scoped vote parsing, cached duplicate vote reuse, cache invalidation, lookup target validation, assignment validation, collection construction, vote fields, collection parent state, vote ownership, cache ownership, stored vote user client coherence, and lookup target client coherence.

This slice is not a duplicate of those drafts. Issue 374 validates caller-provided `PageVoteCollection.find(user=...)` search targets with missing, boolean, and non-integer IDs, but it does not validate stored vote-row `vote.user.id` values before comparison and did not reject a retained negative lookup user ID. Issue 620 validates the lookup target's client coherence. Issue 611 validates `PageVote(...)` construction-time user/client coherence. Issues 469, 588, and 598 validate vote record fields and page ownership boundaries. Direct `User` constructor ID validation cannot cover a valid user object whose retained ID is corrupted after construction and then reused in a vote collection.

## Related Issue / Non-Duplicate Analysis

Builds directly on [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [620-pr-validate-page-vote-search-user-client.md](620-pr-validate-page-vote-search-user-client.md), [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), and [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageVoteCollection.find(...)` lookup user IDs as non-boolean, non-negative integers.
- Validate stored `vote.user.id` values during `find(...)` as `None` or non-boolean, non-negative integers before comparing them with the lookup ID.
- Reject retained stored vote IDs such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("vote.user.id must be an integer or None")`.
- Reject retained stored vote IDs such as `-1` with `ValueError("vote.user.id must be non-negative or None")`.
- Preserve valid zero-ID lookup, stored `None` vote-user IDs as skipped non-matches, existing malformed lookup-user diagnostics, lookup target client validation, not-voted misses, WhoRated parsing, duplicate cached vote reuse, page vote cache ownership, vote/cancel cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Retained page-vote user-ID hardening
- Page vote lookup integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVoteCollection.find(user)` must reject a retained negative lookup `user.id` with `ValueError("user.id must be non-negative")` before scanning stored votes. |
| R2 | `PageVoteCollection.find(user)` must reject malformed retained stored `vote.user.id` values such as `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("vote.user.id must be an integer or None")` before comparison. |
| R3 | `PageVoteCollection.find(user)` must reject retained negative stored `vote.user.id` values such as `-1` with `ValueError("vote.user.id must be non-negative or None")` before comparison. |
| R4 | Valid vote lookup where the stored and lookup user IDs are `0` must remain accepted. |
| R5 | Stored `vote.user.id=None` must remain a skipped non-match so a later valid vote in the same collection can still be found. |
| R6 | Existing lookup target type diagnostics, missing-ID diagnostics, different-client diagnostics, not-voted misses, WhoRated parsing, duplicate cached vote reuse, page vote cache behavior, and adjacent page workflows must remain green. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, page-vote module coverage, adjacent page/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative retained lookup user IDs fail before scanning stored votes. | `test_find_rejects_negative_retained_search_user_id` failed RED with a generic `has not voted` miss, then passed GREEN after lookup user ID range validation. | Treating negative lookup IDs as ordinary misses, matching them to stored votes, coercing them, or deferring to stored scan behavior rejects this local completion claim. | `PageVoteCollection.find(...)` lookup target | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Malformed retained stored vote user IDs fail before comparison. | `test_find_rejects_vote_with_malformed_retained_user_ids` failed RED for five malformed values: booleans and `12345.0` were accepted through Python equality, while `"12345"` and `[]` produced generic not-voted misses. The test passed GREEN after stored vote user ID validation. | Accepting booleans/floats, returning generic misses for strings/lists, coercing malformed values, or returning a vote from corrupted stored ID state rejects this local completion claim. | Stored `PageVote.user.id` during lookup | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R3 | Negative retained stored vote user IDs fail before comparison. | `test_find_rejects_vote_with_negative_retained_user_id` failed RED with a generic not-voted miss, then passed GREEN after stored vote user ID range validation. | Treating negative stored IDs as ordinary misses, matching them, accepting them, or coercing them rejects this local completion claim. | Stored `PageVote.user.id` during lookup | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R4 | Zero remains a valid retained user ID for lookup. | `test_find_accepts_vote_with_zero_retained_user_id` passed RED and GREEN. | Rejecting `0`, treating it as missing, coercing it to false, or changing returned vote identity rejects this local completion claim. | Page vote lookup semantics | `tests/unit/test_page_votes.py` |
| R5 | Stored `None` user IDs remain skippable non-matches. | `test_find_skips_vote_with_missing_retained_user_id` passed RED and GREEN, proving a later matching vote can still be returned after a stored `None` ID entry. | Raising on stored `None`, treating it as a match, stopping the scan, or losing a later valid vote rejects this local completion claim. | Page vote lookup compatibility | `tests/unit/test_page_votes.py` |
| R6 | Existing compatible behavior remains compatible. | Focused GREEN coverage passed 9 tests, `tests/unit/test_page_votes.py` passed 56 tests, adjacent page/site coverage passed 1192 tests, and full unit passed 3173 tests. | Regressing lookup target type checks, missing-ID checks, different-client checks, valid not-voted misses, WhoRated parsing, duplicate cached vote reuse, page vote cache ownership, vote/cancel cache invalidation, page constructor behavior, page source/revision/file workflows, site workflows, or any unit test rejects this local completion claim. | Page vote and adjacent page workflows | `tests/unit/test_page_votes.py`, `tests/unit/test_page.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic `Page`, `Site`, `Client`, `User`, `PageVote`, and `PageVoteCollection` objects only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, voter identities, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b835612 fix(page_votes): validate retained vote user ids`.

- RED: `uv run pytest tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_accepts_vote_with_zero_retained_user_id tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_skips_vote_with_missing_retained_user_id tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_negative_retained_search_user_id tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_vote_with_malformed_retained_user_ids tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_vote_with_negative_retained_user_id -q` collected 9 tests: 7 retained lookup/stored ID cases failed before the fix, and the zero-ID plus stored-`None` compatibility guards passed.
- GREEN: the same focused command passed 9 tests after validating lookup and stored retained user IDs before comparison.
- `uv run ruff format src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_page_votes.py -q` passed 56 tests.
- `uv run pytest tests/unit/test_page_votes.py tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py -q` passed 1192 tests.
- `uv run pytest tests/unit -q` passed 3173 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageVoteCollection.find(search_user)` raises `ValueError("user.id must be non-negative")` when `search_user.id` has been retained or mutated to `-1`.
- `PageVoteCollection.find(search_user)` raises `ValueError("vote.user.id must be an integer or None")` when a stored vote's retained `vote.user.id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `PageVoteCollection.find(search_user)` raises `ValueError("vote.user.id must be non-negative or None")` when a stored vote's retained `vote.user.id` is `-1`.
- `PageVoteCollection.find(search_user)` still returns the matching vote when the stored vote user ID and lookup user ID are both `0`.
- `PageVoteCollection.find(search_user)` still skips a stored vote whose user ID is `None` and can return a later valid matching vote.
- Existing lookup target non-user rejection, lookup target missing/bool/string ID rejection, different-client rejection, not-voted miss behavior, valid vote lookup, WhoRated parsing, duplicate cached vote reuse, direct page vote cache assignment validation, cache ownership validation, vote/cancel cache invalidation, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVoteCollection.find(user)` is a convenience lookup over browser-free WhoRated results, cached duplicate vote lists, moderation exports, rating audit ledgers, and generated migration data. The lookup target already has to be a same-client `AbstractUser` with a usable integer ID; stored vote rows used during that comparison should satisfy an equally explicit retained-ID contract. Validating those retained IDs keeps corrupted local state from being matched by Python's loose numeric equality or hidden as an ordinary "has not voted" miss, while preserving valid zero IDs, stored `None` as a non-match, and all network/parsing behavior.

## Local Evidence

- Existing local drafts covered vote-list fetching, duplicate cached vote reuse, lazy vote failure context, WhoRated parser scoping and diagnostics, rating action validation, public vote-value validation, page collection entry validation, `PageVoteCollection.find(...)` search-user validation, search-user client validation, direct `PageVote` field validation, direct `Page.votes` assignment validation, page vote collection construction, page-vote ownership, and page vote cache ownership.
- None of those drafts covered malformed retained stored `vote.user.id` values inside `PageVoteCollection.find(...)` because the scan still compared `vote.user.id == user.id` directly.
- The focused RED failure showed booleans and floats could be accepted as stored vote user IDs when they compared equal to lookup integers, while strings, lists, and negative IDs could be misreported as ordinary lookup misses.
- This slice only validates retained user IDs at the page-vote lookup comparison boundary. It does not change WhoRated parsing, page vote acquisition, vote value conversion, direct vote construction for valid users, collection initialization, page vote mutation behavior, cache invalidation behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, voter identities, and private site data out of upstream discussion.

## Additional Notes

Stored `vote.user.id=None` remains accepted as a non-match because `AbstractUser` records can carry optional IDs in direct local state. Lookup targets still require a concrete non-negative integer ID before scanning.
