# PR Draft: Validate ForumPost Actor Clients

## Summary

`ForumPost` records carry the parent `ForumThread`, the post creator in `created_by`, and optional edit metadata in `edited_by`. Existing forum-post slices validate parser-side user extraction, direct `created_by` and `edited_by` types, direct timestamp fields, direct thread state, identity and text fields, source/revision caches, source acquisition, edit behavior, and adjacent forum workflows. One constructor coherence gap remained: direct `ForumPost(...)` construction could combine `thread=thread_from_site_a` with `created_by=User(client=site_b.client, ...)` or `edited_by=User(client=site_b.client, ...)`, producing a post ledger row whose actor users came from a different client context than the parent thread's site.

This change validates `ForumPost.created_by.client` and optional `ForumPost.edited_by.client` against `ForumPost.thread.site.client` during `ForumPost.__post_init__` after existing field-shape and cache checks. Mismatches raise `ValueError("created_by must belong to the site")` or `ValueError("edited_by must belong to the site")`. Valid parser-created post-list rows remain aligned because `_parse_post_list_user(...)` already calls `user_parser(thread.site.client, user_elem)` for both creator and editor metadata. Existing malformed field diagnostics, post-list parsing, source reads, revision reads, edit behavior, cache validation, and adjacent forum workflows remain unchanged.

## Outcome

Forum-post rows cannot store creator or editor users from a different client context than the parent thread's site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum post inventories, generated discussion migration ledgers, moderation exports, post source reads, edit-history traversals, local fixtures, or serialized and rehydrated post rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post-list reads, source reads, edit workflows, and revision traversal as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [411-pr-validate-forum-post-source-cache.md](411-pr-validate-forum-post-source-cache.md), [412-pr-validate-forum-post-revisions-cache.md](412-pr-validate-forum-post-revisions-cache.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), [578-pr-validate-forum-post-edit-thread.md](578-pr-validate-forum-post-edit-thread.md), [579-pr-validate-forum-post-edit-site.md](579-pr-validate-forum-post-edit-site.md), [594-pr-validate-forum-post-revisions-cache-ownership.md](594-pr-validate-forum-post-revisions-cache-ownership.md), and [607-pr-validate-forum-thread-creator-client.md](607-pr-validate-forum-thread-creator-client.md) establish post acquisition, parser diagnostics, direct record-state validation, cache validation, action/read preflights, and actor-client coherence as active operational boundaries.

The parser path already constructs both creator and editor users with the parent thread site's client: `_parse_post_list_user(...)` calls `user_parser(thread.site.client, user_elem)`. The new rule brings direct constructor behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 459. Issue 459 validates that `ForumPost.created_by` is an `AbstractUser` and `created_at` is a `datetime`; it does not validate the relationship between a valid creator object and the parent thread's site client.

This is not a duplicate of Issue 461. Issue 461 validates that non-null `ForumPost.edited_by` is an `AbstractUser` and `edited_at` is a `datetime`; it does not validate editor/client coherence.

This is not a duplicate of Issue 446. Issue 446 validates the direct parent `thread` field type; it does not validate actor users against the retained thread site's client.

This is not a duplicate of Issue 607. Issue 607 validates `ForumThread.created_by.client` against the thread's parent site. This slice validates `ForumPost` creator and editor users against the post's retained thread site.

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPost` creator-client coherence validation.
- Add `ForumPost` optional editor-client coherence validation.
- Reject direct rows where `created_by.client is not thread.site.client` with `ValueError("created_by must belong to the site")`.
- Reject direct rows where non-null `edited_by.client is not thread.site.client` with `ValueError("edited_by must belong to the site")`.
- Preserve existing validation order for malformed thread, post ID, parent ID, source cache, revision cache, title, text, actor type, and timestamp diagnostics.
- Preserve side-effect-free construction: the new checks compare object identity only and do not perform login checks, HTTP requests, user lookups, coercion, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum post ledger identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(thread=thread_a, created_by=User(client=site_b.client, ...), ...)` must reject the mismatched creator client with `ValueError("created_by must belong to the site")` before contradictory post record state can be used. |
| R2 | `ForumPost(thread=thread_a, edited_by=User(client=site_b.client, ...), ...)` must reject the mismatched editor client with `ValueError("edited_by must belong to the site")` before contradictory edit metadata can be used. |
| R3 | Valid direct `ForumPost(...)` rows where actor users share `thread.site.client`, parser-created post-list rows, and unedited rows with `edited_by=None` must remain valid. |
| R4 | Existing malformed `thread`, `id`, `parent_id`, source cache, revision cache, `title`, `text`, actor type, actor timestamp, and cache-ownership diagnostics must remain unchanged. |
| R5 | Existing post-list parsing, source acquisition, revision acquisition, edit behavior, cache validation, and adjacent forum category/thread/post/revision workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor creator/client mismatches fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_created_by_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumPost.__post_init__` called the creator-client preflight. | Accepting a valid `User` object from another client context, emitting a post row whose thread site and creator client disagree, or deferring the mismatch to later use rejects this local completion claim. | `ForumPost` constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Constructor editor/client mismatches fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_edited_by_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumPost.__post_init__` called the editor-client preflight. | Accepting a valid edited-by user from another client context, emitting post edit metadata whose thread site and editor client disagree, or deferring the mismatch to later source/edit/revision paths rejects this local completion claim. | `ForumPost` constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Existing valid direct, parser-created, and unedited rows stay green. | `tests/unit/test_forum_post.py` passed 164 tests, including parser-created post rows and existing unedited-row behavior. | Rejecting same-client users, rejecting `edited_by=None`, replacing actor objects, coercing users, breaking parser-created rows, or requiring live authentication rejects this local completion claim. | Forum post constructor and parser | `tests/unit/test_forum_post.py` |
| R4 | Existing diagnostics stay stable. | Focused forum-post coverage passed existing malformed thread, ID, parent ID, title, text, creator type, edit metadata type, source cache, revision cache, and cache-ownership validation tests. | Changing existing `ValueError` diagnostics, validating coherence before malformed field checks, or accepting previously rejected malformed values rejects this local completion claim. | ForumPost validation order | `tests/unit/test_forum_post.py` |
| R5 | Existing adjacent workflows remain green. | Adjacent forum category/thread/post/revision coverage passed 545 tests, and full unit coverage passed 2736 tests. | Regressing category/thread parsing, thread post-list acquisition, post source reads, revision reads, edit workflows, lazy caches, duplicate reuse, parser diagnostics, or adjacent forum behavior rejects this local completion claim. | Forum workflows | `tests/unit` |
| R6 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic `ForumThread` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, private usernames, forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `e9dc630 fix(forum_post): validate actor clients`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_created_by_from_different_client tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_edited_by_from_different_client -q` failed before the fix with two `DID NOT RAISE` failures.
- GREEN regression: the same focused command passed 2 tests.
- Forum-post coverage: `uv run pytest tests/unit/test_forum_post.py -q` passed 164 tests.
- Adjacent forum category/thread/post/revision coverage: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 545 tests.
- `uv run pytest tests/unit -q` passed 2736 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPost(thread=thread_a, created_by=User(client=site_b.client, ...), ...)` raises `ValueError("created_by must belong to the site")`.
- `ForumPost(thread=thread_a, edited_by=User(client=site_b.client, ...), ...)` raises `ValueError("edited_by must belong to the site")`.
- Valid direct rows where actor users share `thread.site.client` remain valid.
- Unedited rows with `edited_by=None` remain valid.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing malformed `edited_by` values still raise `ValueError("edited_by must be an AbstractUser or None")`.
- Existing malformed thread, post ID, parent ID, title, text, timestamp, source-cache, revisions-cache, and cache-ownership diagnostics remain unchanged.
- Existing parser-created post-list rows still produce valid `ForumPost` records.
- Existing source reads, revision reads, edit behavior, cache validation, and adjacent forum workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost` is the durable row shape behind browser-free forum post inventories, generated discussion migration ledgers, moderation exports, post source reads, edit-history traversal, local fixtures, and rehydrated records. A post row is thread/site-scoped, and parser-created actor users already come from the parent thread site's client. Constructor coherence validation keeps direct fixtures and serialized rows from mixing parent-thread and actor-user client contexts while preserving normal parser, source, edit, and revision paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `ForumPost(thread=thread_a, created_by=User(client=site_b.client, ...), ...)` construction silently accepted a contradictory row.
- The focused RED failure also showed direct `ForumPost(thread=thread_a, edited_by=User(client=site_b.client, ...), ...)` construction silently accepted contradictory edit metadata.
- Existing local drafts covered post-list fetch retry behavior, parser scoping, response-body diagnostics, parser-side creator/editor extraction, direct actor type validation, direct timestamp validation, direct thread/scalar validation, source and revision cache validation, source acquisition, edit action-time parent validation, and adjacent forum workflows, but did not validate coherence between valid actor user objects and a valid parent thread site.
- This slice only validates constructor-time post actor/client coherence. It does not change post-list request construction, parser selectors, user parser semantics, timestamp parsing, post ID parsing, source form fetching, edit save payloads, revision acquisition, cache invalidation semantics, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, private forum content, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, thread IDs, site IDs, UNIX names, or authentication state. The parser path and retained object graph preserve client identity, and identity comparison avoids network lookups, login checks, and ambiguous cross-client equivalence rules.
