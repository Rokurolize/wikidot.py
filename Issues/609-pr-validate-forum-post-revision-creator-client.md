# PR Draft: Validate ForumPostRevision Creator Client

## Summary

`ForumPostRevision` records carry the parent `ForumPost` and the revision creator in `created_by`. Existing forum-post-revision slices validate parser-side user extraction, direct `created_by` type, direct `created_at` type, direct post state, identity fields, HTML cache state, collection ownership, retained parent state before revision reads, and adjacent forum workflows. One constructor coherence gap remained: direct `ForumPostRevision(...)` construction could combine `post=post_from_site_a` with `created_by=User(client=site_b.client, ...)`, producing an edit-history row whose creator came from a different client context than the parent post's site.

This change validates `ForumPostRevision.created_by.client` against `ForumPostRevision.post.thread.site.client` during `ForumPostRevision.__post_init__` after existing post, revision ID, revision number, and creator type checks. Mismatches raise `ValueError("created_by must belong to the site")`. Parser-created revision rows remain aligned because `ForumPostRevisionCollection._parse(...)` already calls `user_parser(post.thread.site.client, user_elem)` for revision creator metadata. Existing malformed field diagnostics, revision-list parsing, lazy revision HTML reads, batch revision HTML acquisition, collection ownership checks, retained-parent read preflights, and adjacent forum workflows remain unchanged.

## Outcome

Forum post revision rows cannot store a creator user from a different client context than the parent post's site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision audit summaries, moderation exports, local fixtures, or serialized and rehydrated forum revision rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision reads as practical workflow surfaces. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md), [582-pr-validate-forum-post-revision-html-target-post-thread.md](582-pr-validate-forum-post-revision-html-target-post-thread.md), and [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md) establish revision acquisition, parser diagnostics, response diagnostics, duplicate/cache behavior, direct record-state validation, collection ownership, and retained-parent safety as active operational boundaries.

The parser path already constructs revision creators with the parent post site's client: `ForumPostRevisionCollection._parse(...)` calls `user_parser(post.thread.site.client, user_elem)`. The new rule brings direct constructor behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 464. Issue 464 validates that `ForumPostRevision.created_by` is an `AbstractUser` and `created_at` is a `datetime`; it does not validate the relationship between a valid creator object and the parent post's site client.

This is not a duplicate of Issue 445. Issue 445 validates the direct parent `post` field type; it does not validate creator users against the retained post site's client.

This is not a duplicate of Issues 580 through 583. Those slices validate retained post/thread/site state before revision-list or revision-HTML request work and reject mixed-site revision batches. This slice validates constructor-time actor/client coherence for a valid `ForumPostRevision` record.

This is not a duplicate of Issues 607 or 608. Issue 607 validates `ForumThread.created_by.client` against a thread site, and Issue 608 validates `ForumPost` creator/editor users against a post thread site. This slice validates `ForumPostRevision.created_by.client` against the revision's retained post site.

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPostRevision` creator-client coherence validation.
- Reject direct revision rows where `created_by.client is not post.thread.site.client` with `ValueError("created_by must belong to the site")`.
- Preserve existing validation order for malformed `post`, `id`, `rev_no`, `created_by`, `created_at`, and `_html` diagnostics.
- Keep valid test revision fixtures aligned with their parent post's site client.
- Preserve side-effect-free construction: the new check compares object identity only and does not perform login checks, HTTP requests, user lookups, coercion, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum edit-history actor identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevision(post=post_a, created_by=User(client=site_b.client, ...), ...)` must reject the mismatched creator client with `ValueError("created_by must belong to the site")` before contradictory revision record state can be used. |
| R2 | Valid direct `ForumPostRevision(...)` rows where `created_by.client is post.thread.site.client` and parser-created revision rows must remain valid. |
| R3 | Existing malformed `post`, `id`, `rev_no`, `created_by`, `created_at`, and `_html` diagnostics must remain unchanged. |
| R4 | Existing revision-list acquisition, lazy revision HTML reads, batch revision HTML acquisition, collection ownership checks, retained-parent read preflights, and adjacent forum category/thread/post/revision workflows must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor creator/client mismatches fail at the public dataclass boundary. | `TestForumPostRevisionBasic.test_init_rejects_created_by_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumPostRevision.__post_init__` called the creator-client preflight. | Accepting a valid `User` object from another client context, emitting a revision row whose post site and creator client disagree, or deferring the mismatch to later revision-list or revision-HTML paths rejects this local completion claim. | `ForumPostRevision` constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Existing valid direct and parser-created revision rows stay green. | `tests/unit/test_forum_post_revision.py` passed 130 tests, including parser-created revision rows and same-client direct fixture rows. | Rejecting same-client users, replacing creator objects, coercing users, breaking parser-created rows, or requiring live authentication rejects this local completion claim. | Forum post revision constructor and parser | `tests/unit/test_forum_post_revision.py` |
| R3 | Existing diagnostics stay stable. | Focused forum-post-revision coverage passed existing malformed post, ID, revision number, creator type, timestamp, HTML cache, collection, search-key, with-HTML flag, and ownership validation tests. | Changing existing `ValueError` diagnostics, validating coherence before malformed field checks, or accepting previously rejected malformed values rejects this local completion claim. | ForumPostRevision validation order | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing adjacent workflows remain green. | Adjacent forum category/thread/post/revision coverage passed 546 tests, and full unit coverage passed 2737 tests. | Regressing category/thread parsing, post-list acquisition, post source reads, revision reads, lazy caches, duplicate reuse, parser diagnostics, retained-parent request preflights, or adjacent forum behavior rejects this local completion claim. | Forum workflows | `tests/unit` |
| R5 | No live auth material or private site state is needed to prove the behavior. | The regression uses synthetic `ForumPost` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, private usernames, forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `6a71e42 fix(forum_post_revision): validate creator client`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_created_by_from_different_client -q` failed before the fix with `DID NOT RAISE`.
- GREEN regression: the same focused command passed 1 test.
- Forum-post-revision coverage: `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 130 tests.
- Adjacent forum category/thread/post/revision coverage: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 546 tests.
- `uv run pytest tests/unit -q` passed 2737 tests.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `git diff --check` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPostRevision(post=post_a, created_by=User(client=site_b.client, ...), ...)` raises `ValueError("created_by must belong to the site")`.
- Valid direct rows where `created_by.client is post.thread.site.client` remain valid.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing malformed `post`, `id`, `rev_no`, `created_at`, and `_html` diagnostics remain unchanged.
- Existing parser-created revision rows still produce valid `ForumPostRevision` records.
- Existing revision-list acquisition, lazy revision HTML reads, batch revision HTML acquisition, collection ownership checks, retained-parent read preflights, and adjacent forum workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevision` is the durable row shape behind browser-free forum edit-history reads, generated discussion migration ledgers, revision audit summaries, moderation exports, local fixtures, and rehydrated records. A revision row is post/site-scoped, and parser-created creator users already come from the parent post site's client. Constructor coherence validation keeps direct fixtures and serialized rows from mixing parent-post and revision-creator client contexts while preserving normal revision-list, revision-HTML, cache, and parser paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `ForumPostRevision(post=post_a, created_by=User(client=site_b.client, ...), ...)` construction silently accepted a contradictory row.
- Existing local drafts covered forum post revision fetch retry behavior, duplicate revision and revision-HTML reduction, parse reuse, response diagnostics, parser ID/user/timestamp diagnostics, cached direct acquisition, acquisition post input validation, collection initialization validation, loaded-collection mutation validation, search-key validation, optional HTML flag validation, HTML assignment validation, direct parent-post validation, direct identity-field validation, direct creator/time type validation, collection post ownership, retained-parent request preflights, and mixed-site batch rejection, but did not cover direct creator/client coherence at `ForumPostRevision(...)` construction.
- This slice only validates constructor-time revision creator/client coherence. It does not change revision-list request construction, parser selectors, user parser semantics, timestamp parsing, revision ID parsing, revision-number parsing, revision HTML request payloads, cache invalidation semantics, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, private forum content, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, post IDs, thread IDs, site IDs, UNIX names, or authentication state. The parser path and retained object graph preserve client identity, and identity comparison avoids network lookups, login checks, and ambiguous cross-client equivalence rules.
