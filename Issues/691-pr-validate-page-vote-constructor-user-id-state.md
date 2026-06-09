# PR Draft: Validate PageVote Constructor User ID State

## Summary

`PageVote(...)` records already validate the parent page, voter object type, voter/page client coherence, vote value type, lookup target user IDs, lookup target client coherence, and retained stored vote user IDs during `PageVoteCollection.find(...)`. One constructor gap remained: a valid same-client `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `user.id` state and then stored in a new `PageVote` row. That let booleans, numeric strings, floats, lists, or negative IDs become durable vote record state until a later lookup happened to validate the retained ID.

This change reuses the existing stored vote user-ID validator at the `PageVote(...)` constructor boundary. Malformed retained vote user IDs now raise `ValueError("vote.user.id must be an integer or None")`, negative retained vote user IDs now raise `ValueError("vote.user.id must be non-negative or None")`, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `PageVote(...)` rows cannot store malformed or negative retained voter IDs. Valid parser-created rows, same-client direct rows, optional missing IDs, zero-ID compatibility, vote value validation, collection initialization, lookup semantics, WhoRated parsing, duplicate cached vote reuse, vote/cache invalidation, and adjacent page/site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free WhoRated inventories, page rating ledgers, moderation exports, cached vote records, generated migration data, local fixtures, or serialized and rehydrated `PageVote` objects.

## Current Evidence

Local rollout-backed drafts [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md), [620-pr-validate-page-vote-search-user-client.md](620-pr-validate-page-vote-search-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), and [669-pr-validate-page-vote-lookup-retained-user-id-state.md](669-pr-validate-page-vote-lookup-retained-user-id-state.md) establish page-vote reads, cached vote reuse, lookup behavior, constructor field validation, ownership checks, direct user-ID range validation, and retained vote-user ID lookup validation as practical workflow surfaces.

This slice is not a duplicate of those drafts. Issue 469 validates that `PageVote.user` is an `AbstractUser` and `PageVote.value` is a non-boolean integer; it does not validate retained voter ID state. Issue 611 validates `PageVote.user.client` against the parent page site client, not the retained ID. Issue 669 validates retained vote-user IDs during `PageVoteCollection.find(...)`; it deliberately preserves stored `vote.user.id=None` as a skippable non-match and does not validate direct `PageVote(...)` construction. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a vote row.

## Related Issue / Non-Duplicate Analysis

Builds directly on [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md), [620-pr-validate-page-vote-search-user-client.md](620-pr-validate-page-vote-search-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), and [669-pr-validate-page-vote-lookup-retained-user-id-state.md](669-pr-validate-page-vote-lookup-retained-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `PageVote.user.id` during `PageVote.__post_init__` with the existing optional stored-vote ID helper.
- Reject retained constructor voter IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("vote.user.id must be an integer or None")`.
- Reject retained constructor voter ID `-1` with `ValueError("vote.user.id must be non-negative or None")`.
- Preserve retained constructor voter IDs `None` and `0`.
- Preserve existing page validation, user object validation, user/page client coherence, vote value validation, collection lookup behavior, WhoRated parsing, duplicate cached vote reuse, vote/cache invalidation, and adjacent page workflows.

## Type Of Change

- State validation
- Page vote constructor hardening
- Retained voter identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVote(page=page, user=user, value=...)` must reject retained `user.id=True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("vote.user.id must be an integer or None")` before storing the vote row. |
| R2 | `PageVote(page=page, user=user, value=...)` must reject retained `user.id=-1` with `ValueError("vote.user.id must be non-negative or None")` before storing the vote row. |
| R3 | Valid retained voter IDs `None` and `0` must remain accepted in direct `PageVote(...)` construction. |
| R4 | Existing malformed page validation, non-`AbstractUser` voter validation, voter/page client coherence, malformed vote-value validation, collection initialization, lookup target validation, retained lookup-time vote-user ID validation, WhoRated parsing, duplicate cached vote reuse, vote/cache invalidation, and adjacent page/site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private voter data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-vote tests, adjacent page/site tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained voter IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_user_ids` failed RED for five malformed values with `DID NOT RAISE`, then passed GREEN after `PageVote.__post_init__` called the retained-ID validator. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure only to `PageVoteCollection.find(...)` rejects this local completion claim. | `PageVote` constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Negative retained voter IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_user_id` failed RED with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained voter IDs, storing the row, or hiding the state behind an ordinary lookup miss rejects this local completion claim. | `PageVote` constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R3 | Optional missing and zero voter IDs remain compatible constructor state. | `test_init_accepts_optional_retained_user_ids` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `PageVote` constructor | `tests/unit/test_page_votes.py` |
| R4 | Existing page-vote behavior and adjacent workflows remain green. | `tests/unit/test_page_votes.py` passed 64 tests, adjacent page/site coverage passed 1235 tests, and full unit coverage passed 3413 tests. | Regressing parser-created votes, constructor page/user/value diagnostics, client coherence, collection lookup, stored-ID lookup validation, WhoRated parsing, duplicate cached vote reuse, page vote cache ownership, vote/cancel cache invalidation, page constructor/source/revision/file/site workflows, or any unit test rejects this local completion claim. | Page vote and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Page`, `Site`, `Client`, `User`, and `PageVote` objects only. | Using credentials, cookies, auth JSON, private voter names, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page-vote/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `608a773 fix(page_votes): validate constructor vote user ids`.

- RED: `uv run pytest tests/unit/test_page_votes.py::TestPageVote -k retained_user_id -q` selected 8 constructor retained-user-ID tests; 6 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 8 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` left both files unchanged.
- `uv run pytest tests/unit/test_page_votes.py -q` passed 64 tests.
- `uv run pytest tests/unit/test_page_votes.py tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py -q` passed 1235 tests.
- `uv run pytest tests/unit -q` passed 3413 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageVote(...)` raises `ValueError("vote.user.id must be an integer or None")` when the retained voter ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `PageVote(...)` raises `ValueError("vote.user.id must be non-negative or None")` when the retained voter ID is `-1`.
- Malformed or negative retained voter IDs fail before the vote row is stored by direct construction.
- Valid retained voter IDs `None` and `0` remain accepted by direct construction.
- Existing malformed page validation, non-`AbstractUser` voter validation, voter/page client coherence validation, vote-value validation, collection initialization, lookup target validation, stored vote-user ID validation during lookup, valid not-voted misses, valid vote lookup, WhoRated parsing, duplicate cached vote reuse, direct page vote cache assignment validation, cache ownership validation, vote/cancel cache invalidation, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private voter data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed vote rows with corrupted retained voter IDs now fail during construction instead of later lookup. Mitigation: those values are impossible vote identity state; failing before storage is deterministic and uses the existing lookup-time stored-ID contract.
- Risk: Optional IDs could be rejected accidentally. Mitigation: the focused compatibility guard asserts that `None` and `0` remain accepted and preserved.
- Risk: Validation precedence could regress earlier page-vote diagnostics. Mitigation: the retained-ID check runs after page/user/client checks and before vote-value validation; the full page-vote and adjacent suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing page-vote page validation, user object validation, user/page client validation, vote value validation, collection lookup validation, retained lookup-time ID validation, and cache behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `PageVote` constructor retained user-ID boundary.

## Upstream-Safe Motivation

`PageVote` is the durable row shape behind WhoRated inventories, rating audit ledgers, moderation exports, cached vote records, and local fixtures. Parser-created voters come from the page site's client, direct `User` construction already rejects impossible negative IDs, and lookup-time retained-ID validation already defines the stored vote-user ID contract. Constructor-side validation keeps corrupted fixture-loaded or rehydrated voter IDs out of stored vote rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, client coherence, and lookup semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page votes as a practical workflow through WhoRated parsing, duplicate cached vote reuse, cache invalidation, constructor field validation, collection lookup validation, collection/cache ownership, client coherence, and retained lookup-time user-ID validation.
- Existing local drafts covered non-`AbstractUser` voters, malformed vote values, voter/page client mismatch, lookup target ID shape/range, lookup target client mismatch, stored vote-user ID validation during lookup, direct user constructor ID ranges, and page vote cache state; they did not validate corrupted retained `User.id` values at the direct `PageVote(...)` constructor boundary.
- The focused RED failure showed malformed and negative retained voter IDs could be stored in direct vote rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, page-vote behavior, adjacent page/site workflows, and full unit compatibility.
- This slice only validates retained voter IDs at the `PageVote` constructor boundary. It does not change WhoRated parsing, page vote acquisition, vote value conversion, collection initialization, lookup behavior for valid rows, page vote mutation behavior, cache invalidation behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private voter data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally reuses `_validate_stored_vote_user_id(...)` instead of adding a stricter action-style user requirement. Stored vote rows may legitimately carry `user.id=None` as an optional local state, and lookup-time behavior already treats that state as a skipped non-match.
