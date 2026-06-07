# PR Draft: Validate PageVote User Client

## Summary

`PageVote` records carry the parent `Page`, the voting `user`, and the numeric vote value used by browser-free WhoRated inventories, rating audit ledgers, moderation reports, duplicate cached vote-list reuse, lazy `Page.votes`, vote/cancel cache invalidation checks, generated migration ledgers, and direct local fixtures. Existing page-vote slices validate WhoRated parser user/value extraction, public `Page.vote(value=...)` write values, `PageVoteCollection.find(user=...)` search inputs, `PageVoteCollection(...)` initialization, direct `Page.votes` assignment, direct parent `PageVote.page` construction, `PageVote.user` type, `PageVote.value` type, collection page ownership, and retained page-votes cache ownership. One constructor coherence gap remained: direct `PageVote(...)` construction could combine `page=page_from_site_a` with `user=User(client=site_b.client, ...)`, producing a page-vote row whose voter came from a different client context than the parent page's site.

This change validates `PageVote.user.client` against `PageVote.page.site.client` during `PageVote.__post_init__` after existing page and user type checks and before value validation. Mismatches raise `ValueError("user must belong to the site")`. Parser-created vote rows remain aligned because `PageCollection._acquire_page_votes(...)` parses WhoRated users with `user_parser(site.client, user_elem)` for the same site that owns the page batch. Existing malformed field diagnostics, valid numeric vote values, vote collection lookup, collection initialization, lazy vote acquisition, duplicate cached vote reuse, vote/cancel cache invalidation, and adjacent page workflows remain unchanged.

## Outcome

Page vote rows cannot store a voter user from a different client context than the parent page's site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free WhoRated inventories, rating audit ledgers, moderation reports, duplicate cached vote-list reuse, lazy `Page.votes`, vote/cancel cache invalidation checks, generated migration ledgers, local fixtures, or serialized and rehydrated page vote rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify page vote reads as practical workflow surfaces. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md), [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), and adjacent actor-client slices [604-pr-validate-site-change-actor-client.md](604-pr-validate-site-change-actor-client.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), [607-pr-validate-forum-thread-creator-client.md](607-pr-validate-forum-thread-creator-client.md), [608-pr-validate-forum-post-actor-clients.md](608-pr-validate-forum-post-actor-clients.md), [609-pr-validate-forum-post-revision-creator-client.md](609-pr-validate-forum-post-revision-creator-client.md), and [610-pr-validate-page-revision-creator-client.md](610-pr-validate-page-revision-creator-client.md) establish vote reads, parser diagnostics, response diagnostics, public write-value validation, lookup validation, cache invalidation, assignment validation, direct record-state validation, retained-owner validation, and actor/client coherence as active operational boundaries.

The parser path already constructs WhoRated voters with the batch site's client: `PageCollection._acquire_page_votes(...)` calls `user_parser(site.client, user_elem)` before constructing `PageVote(page, user, vote)`. The new rule brings direct constructor behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 469. Issue 469 validates that `PageVote.user` is an `AbstractUser` and `PageVote.value` is a non-boolean integer; it does not validate the relationship between a valid voter object and the parent page's site client.

This is not a duplicate of Issue 444. Issue 444 validates the direct parent `page` field type; it does not validate voter users against the retained page site's client.

This is not a duplicate of Issue 374. Issue 374 validates the caller-provided `PageVoteCollection.find(user=...)` search target before scanning existing votes; it does not validate stored vote-row coherence at `PageVote(...)` construction.

This is not a duplicate of Issues 588 or 598. Those slices validate page-vote collection and cached vote collection page ownership. This slice validates each `PageVote.user.client` against the retained `PageVote.page.site.client`.

No upstream issue was filed from this local workspace.

## Changes

- Add `PageVote` voter-client coherence validation.
- Reject direct vote rows where `user.client is not page.site.client` with `ValueError("user must belong to the site")`.
- Keep valid page-vote fixtures aligned with their parent page's site client.
- Preserve existing validation order for malformed `page` and malformed `user` diagnostics before the coherence check.
- Preserve side-effect-free construction: the new check compares object identity only and does not perform login checks, HTTP requests, user lookups, coercion, remote membership checks, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page vote voter identity integrity
- Test addition
- Test fixture cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVote(page=page_a, user=User(client=site_b.client, ...), value=1)` must reject the mismatched voter client with `ValueError("user must belong to the site")` before contradictory vote record state can be used. |
| R2 | Valid direct `PageVote(...)` rows where `user.client is page.site.client` and parser-created WhoRated vote rows must remain valid. |
| R3 | Existing malformed `page`, malformed `user`, and malformed `value` diagnostics must remain unchanged. |
| R4 | Existing `PageVoteCollection.find(...)`, collection initialization, lazy vote acquisition, duplicate cached vote reuse, direct `Page.votes` assignment validation, vote/cancel cache invalidation, and adjacent page workflows must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor voter/client mismatches fail at the public dataclass boundary. | `TestPageVote.test_init_rejects_user_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `PageVote.__post_init__` called the voter-client preflight. | Accepting a valid `User` object from another client context, emitting a vote row whose page site and voter client disagree, or deferring the mismatch to lookup/cache code rejects this local completion claim. | `PageVote` constructor | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Existing valid direct and parser-created vote rows stay green. | `tests/unit/test_page_votes.py` passed 46 tests, including same-client direct fixture rows and collection workflows. Adjacent page workflow tests also passed. | Rejecting same-client users, replacing voter objects, coercing users, breaking parser-created rows, or requiring live authentication rejects this local completion claim. | Page vote constructor and parser-created rows | `tests/unit/test_page_votes.py`, `tests/unit/test_page.py` |
| R3 | Existing diagnostics stay stable. | Focused page-vote coverage passed existing malformed page, malformed user, malformed value, collection initialization, collection lookup, and ownership validation tests. | Changing existing `ValueError` diagnostics, validating coherence before malformed field checks, or accepting previously rejected malformed values rejects this local completion claim. | PageVote validation order | `tests/unit/test_page_votes.py` |
| R4 | Existing adjacent workflows remain green. | Adjacent page, page-constructor, page-revision, page-source, page-file, page-votes, and site coverage passed 1011 tests, and full unit coverage passed 2739 tests. | Regressing WhoRated parsing, lazy vote acquisition, duplicate vote propagation, duplicate cached vote reuse, cache assignment, vote/cancel cache invalidation, source/file/revision workflows, parser diagnostics, or adjacent site behavior rejects this local completion claim. | Page workflows | `tests/unit` |
| R5 | No live auth material or private site state is needed to prove the behavior. | The regression uses synthetic `Page` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, voter identities, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c4c9378 fix(page_votes): validate vote user client`.

- RED: `uv run pytest tests/unit/test_page_votes.py::TestPageVote::test_init_rejects_user_from_different_client -q` failed before the fix with `DID NOT RAISE`.
- GREEN regression: the same focused command passed 1 test.
- Page-vote coverage: `uv run pytest tests/unit/test_page_votes.py -q` passed 46 tests.
- Adjacent page/page-constructor/page-revision/page-source/page-file/page-votes/site coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1011 tests.
- `uv run pytest tests/unit -q` passed 2739 tests.
- `uv run ruff format src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed.
- `git diff --check` passed.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageVote(page=page_a, user=User(client=site_b.client, ...), value=1)` raises `ValueError("user must belong to the site")`.
- Valid direct rows where `user.client is page.site.client` remain valid.
- Existing malformed `user` values still raise `ValueError("user must be an AbstractUser")`.
- Existing malformed `page` and `value` diagnostics remain unchanged.
- Existing parser-created WhoRated vote rows still produce valid `PageVote` records.
- Existing collection initialization, `PageVoteCollection.find(...)`, lazy `Page.votes`, duplicate cached vote reuse, direct `Page.votes` assignment validation, vote/cancel cache invalidation, and adjacent page workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageVote` is the durable row shape behind browser-free WhoRated inventories, rating audit ledgers, duplicate cached vote-list reuse, moderation reports, lazy vote state, vote-cache invalidation checks, local fixtures, and rehydrated records. A vote row is page/site-scoped, and parser-created voter users already come from the owning page site's client. Constructor coherence validation keeps direct fixtures and serialized rows from mixing parent-page and voter client contexts while preserving normal WhoRated parsing, lookup, cache, and vote mutation paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `PageVote(page=page_a, user=User(client=site_b.client, ...), value=1)` construction silently accepted a contradictory row.
- Existing local drafts covered vote-list acquisition, duplicate request deduplication, cached duplicate vote reuse, parser user/value diagnostics, response-body diagnostics, public vote-value validation, collection lookup validation, collection initialization validation, direct page field validation, direct user/value type validation, collection page ownership, and page-votes cache ownership, but did not cover direct voter/client coherence at `PageVote(...)` construction.
- This slice only validates constructor-time vote user/client coherence. It does not change WhoRated request construction, parser selectors, user parser semantics, vote value parsing, collection lookup semantics, `Page.vote(...)`, `Page.cancel_vote()`, cache invalidation semantics, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page HTML, voter identities, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, page IDs, fullnames, site IDs, UNIX names, or authentication state. The parser path and retained object graph preserve client identity, and identity comparison avoids network lookups, login checks, remote membership checks, and ambiguous cross-client equivalence rules.
