# PR Draft: Validate Page Vote Search User Client

## Summary

`PageVoteCollection.find(user)` already validates that the lookup target is an `AbstractUser` with a non-boolean integer `id`. One adjacent coherence gap remained: a well-formed `User` from a different `Client` context could be passed to a collection and, if it shared the same numeric ID as a stored same-site voter, `find(...)` returned that page vote.

This change validates the search target/client relationship after existing user-shape and ID checks but before scanning stored votes. Mismatched lookup targets now raise `ValueError("user must belong to the site")`. Valid same-client lookups, malformed target precedence, nonexistent-vote errors, stored vote-row validation, collection ownership validation, lazy `Page.votes`, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows remain unchanged.

## Outcome

Page vote lookup can no longer return a stored vote for a different-client search user that happens to reuse the same numeric user ID.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free WhoRated inventories, page rating audit ledgers, moderation reports, generated migration records, cached duplicate page-vote reuse, lazy `Page.votes`, or local fixtures that use `PageVoteCollection.find(user=...)`.

## Current Evidence

Local rollout-backed drafts repeatedly identify page vote reads as practical workflow surfaces. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), and [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md) establish vote reads, parser diagnostics, response diagnostics, public write-value validation, lookup validation, cache invalidation, assignment validation, direct record validation, retained-owner validation, and actor/client coherence as active operational boundaries.

This is not a duplicate of Issue 374. Issue 374 validates malformed `PageVoteCollection.find(user=...)` search targets: non-user values and malformed `user.id`. This slice validates a well-formed `User` whose retained `user.client` differs from `collection.page.site.client`.

This is not a duplicate of Issue 611. Issue 611 validates stored `PageVote.user` coherence at `PageVote(...)` construction. This slice validates the caller-provided lookup user before `find(...)` compares numeric IDs against already-valid stored vote rows.

This is not a duplicate of Issues 588 or 598. Those protect collection target-page ownership and page vote-cache ownership. This slice protects the public lookup argument used to search an otherwise valid collection.

No upstream issue was filed from this local workspace.

## Changes

- Reuse the existing `_validate_vote_user_site(...)` helper in `PageVoteCollection.find(...)`.
- Reject `collection.find(User(client=other_client, id=<same-id>))` with `ValueError("user must belong to the site")`.
- Preserve existing validation precedence by checking `AbstractUser` type and integer `user.id` before checking client coherence.
- Add a focused RED/GREEN regression proving a different-client lookup target with the same numeric ID is rejected instead of returning a stored vote.
- Preserve valid lookups, missing-vote errors, stored vote-row validation, collection ownership validation, cached page-vote behavior, and adjacent page workflows.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVoteCollection(page, [PageVote(page, same_site_user, 1)]).find(User(client=other_client, id=same_site_user.id, ...))` must raise `ValueError("user must belong to the site")`. |
| R2 | The client-coherence check must run after existing `AbstractUser` and integer `user.id` validation, preserving malformed input diagnostics. |
| R3 | Valid same-client lookups must continue to return the matching stored vote by numeric user ID. |
| R4 | Existing nonexistent-vote lookups must continue to raise the existing `"has not voted"` diagnostic. |
| R5 | Stored `PageVote` construction, `PageVoteCollection` initialization, `Page.votes`, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows must remain green. |
| R6 | Full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Different-client vote lookup targets fail at the public lookup boundary. | `TestPageVoteCollection.test_find_rejects_user_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `PageVoteCollection.find(...)` called the user/client coherence preflight. | Returning the stored vote, accepting the different-client search target, or relying on numeric ID alone rejects this local completion claim. | `PageVoteCollection.find(...)` | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Existing malformed input precedence remains stable. | `tests/unit/test_page_votes.py` passed 47 tests, including non-user lookup targets and malformed `user.id` values. | Changing `ValueError("user must be an AbstractUser")` or `ValueError("user.id must be an integer")` rejects this local completion claim. | Search input validation | `tests/unit/test_page_votes.py` |
| R3 | Valid lookup behavior remains unchanged. | `TestPageVoteCollection.test_find_existing_vote` passed in the 47-test page-votes module run. | Rejecting same-client lookup users, changing ID matching, or requiring object identity instead of numeric user ID rejects this local completion claim. | Vote lookup semantics | `tests/unit/test_page_votes.py` |
| R4 | Missing-vote behavior remains unchanged. | `TestPageVoteCollection.test_find_nonexistent_vote_raises` passed in the 47-test page-votes module run. | Returning a fabricated vote, changing the existing missing-vote diagnostic, or bypassing the miss path rejects this local completion claim. | Vote lookup miss path | `tests/unit/test_page_votes.py` |
| R5 | Adjacent page vote/cache workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_page_constructor.py -q` passed 517 tests. | Regressing WhoRated parsing, direct `Page.votes` validation, cached vote ownership, lazy vote acquisition, duplicate cached vote reuse, or page constructor caches rejects this local completion claim. | Page vote and adjacent page workflows | `tests/unit` |
| R6 | Repository quality gates remain green. | Full unit coverage passed 2779 tests; full ruff check, full format check, mypy, pyright, and `git diff --check` passed. | Any unreported test, lint, format, type, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic `Page`, `Site`, `Client`, `User`, `PageVote`, and `PageVoteCollection` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `423fa15 fix(page_votes): validate search user client`.

- RED: `uv run pytest tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_user_from_different_client -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: the same command passed after the lookup user/client preflight was added.
- Page-votes module coverage: `uv run pytest tests/unit/test_page_votes.py -q` passed 47 tests.
- Adjacent page vote/cache coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_page_constructor.py -q` passed 517 tests.
- `uv run pytest tests/unit -q` passed 2779 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageVoteCollection.find(User(client=other_client, id=<same numeric id>))` raises `ValueError("user must belong to the site")` before scanning stored vote IDs.
- `PageVoteCollection.find(User(client=collection.page.site.client, id=<matching id>))` still returns the matching stored vote.
- Non-user lookup targets still raise `ValueError("user must be an AbstractUser")`.
- Lookup targets with missing, boolean, or non-integer IDs still raise `ValueError("user.id must be an integer")`.
- Same-client users with no matching vote still raise the existing `"has not voted"` error.
- Stored `PageVote` construction, `PageVoteCollection` initialization, `Page.votes`, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows remain green.
- The new tests use unit-level synthetic state only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVoteCollection.find(user)` is used as a convenience lookup over page-owned vote records. Existing validation now keeps stored rows coherent with the page's site client; the lookup argument should satisfy the same client relationship before its numeric ID is compared to those rows. That prevents mixed-client scripts, generated fixtures, cached user objects, or rehydrated records from reading another user's vote by ID collision while preserving valid same-client lookup semantics.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid `User` from another `Client` object could be accepted by `PageVoteCollection.find(...)` and match an existing stored vote by numeric ID.
- Existing local drafts covered malformed vote lookup targets, direct page-vote user-client coherence, collection page ownership, page vote-cache ownership, WhoRated parser diagnostics, response diagnostics, vote mutation cache invalidation, and duplicate cached vote reuse, but did not cover direct lookup target/client coherence.
- This slice only validates `PageVoteCollection.find(...)` search target/client coherence. It does not change WhoRated parsing, vote value conversion, stored vote construction for valid users, collection initialization, page vote mutation behavior, cache invalidation behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw WhoRated response bodies, voter identities, private page content, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares retained client object identity. This matches the existing `PageVote(...)` record coherence rule and keeps `find(...)` as numeric-ID lookup within one site/client context rather than a cross-client global user resolver.
