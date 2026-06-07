# PR Draft: Validate ForumThread Creator Client

## Summary

`ForumThread` records carry the parent `Site` and the thread creator in `created_by`. Existing forum-thread slices validate parser-side creator extraction, direct `created_by` type, direct `created_at` type, direct site and scalar fields, category state, cached posts ownership, URL-time site state, reply action-time site state, and adjacent forum workflows. One constructor coherence gap remained: direct `ForumThread(...)` construction could combine `site=site_a` with `created_by=User(client=site_b.client, ...)`, producing a thread ledger row whose creator came from a different client context than the parent site.

This change validates `ForumThread.created_by.client` against `ForumThread.site.client` during `ForumThread.__post_init__` after existing field-shape and cache checks. Mismatches raise `ValueError("created_by must belong to the site")`. Valid parser-created category thread-list rows, direct thread-detail rows, same-client direct rows, existing malformed field diagnostics, URL generation, lazy posts, reply behavior, cache validation, and adjacent forum workflows remain unchanged.

## Outcome

Forum-thread rows cannot store a creator user from a different client context than the parent site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexes, category thread lists, direct thread detail fetches, generated forum ledgers, moderation exports, migration checks, local fixtures, or serialized and rehydrated thread rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum thread lists and thread detail reads as practical workflow surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md), and [544-pr-validate-forum-thread-category-input.md](544-pr-validate-forum-thread-category-input.md) establish thread acquisition, parser diagnostics, direct record-state validation, collection validation, direct acquisition input validation, and action/read preflights as active boundaries.

Both parser paths already construct thread creators with the parent site's client: category thread-list parsing calls `user_parser(site.client, user_elem)`, and direct thread-detail parsing does the same. The new rule brings direct constructor behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 458. Issue 458 validates that `ForumThread.created_by` is an `AbstractUser` and `created_at` is a `datetime`; it does not validate the relationship between a valid creator object and the valid parent site.

This is not a duplicate of Issue 447. Issue 447 validates the optional parent category type; it does not validate creator/client coherence.

This is not a duplicate of Issues 543 or 544. Those validate caller-provided parent sites for direct thread-detail and category thread-list acquisition; they do not validate manually constructed or rehydrated `ForumThread` rows after parsing.

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumThread` creator-client coherence validation.
- Reject direct rows where `created_by.client is not site.client` with `ValueError("created_by must belong to the site")`.
- Preserve existing validation order for malformed site, thread ID, title, description, creator type, creation time, post count, category, and cached posts diagnostics.
- Preserve side-effect-free construction: the new check compares object identity only and does not perform login checks, HTTP requests, user lookups, coercion, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum thread ledger identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(site=site_a, created_by=User(client=site_b.client, ...), ...)` must reject the mismatched creator client with `ValueError("created_by must belong to the site")` before contradictory thread record state can be used. |
| R2 | Valid direct `ForumThread(...)` rows where `created_by.client is site.client` and parser-created thread rows must remain valid. |
| R3 | Existing malformed `site`, `thread_id`, `title`, `description`, `created_by`, `created_at`, `post_count`, `category`, and cached posts diagnostics must remain unchanged. |
| R4 | Existing category thread-list parsing, direct thread-detail parsing, URL generation, lazy posts, reply behavior, cache validation, and adjacent forum category/post/revision workflows must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor creator/client mismatches fail at the public dataclass boundary. | `TestForumThreadBasic.test_init_rejects_created_by_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumThread.__post_init__` called the coherence preflight. | Accepting a valid `User` object from another client context, emitting a thread row whose site and creator client disagree, or deferring the mismatch to later use rejects this local completion claim. | `ForumThread` constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Existing valid constructor and parser rows stay green. | `tests/unit/test_forum_thread.py` passed 150 tests, including category thread-list and direct thread-detail parser coverage. | Rejecting same-client direct creators, replacing creator objects, coercing users, breaking parser-created rows, or requiring live authentication rejects this local completion claim. | `ForumThread` constructor and parsers | `tests/unit/test_forum_thread.py` |
| R3 | Existing diagnostics stay stable. | Focused forum-thread coverage passed existing malformed site, ID, text, creator type, timestamp, count, category, and posts-cache validation tests. | Changing existing `ValueError` diagnostics, validating coherence before malformed field checks, or accepting previously rejected malformed values rejects this local completion claim. | ForumThread validation order | `tests/unit/test_forum_thread.py` |
| R4 | Existing adjacent workflows remain green. | Adjacent forum category/thread/post/revision coverage passed 543 tests, and full unit coverage passed 2734 tests. | Regressing category-thread acquisition, direct thread detail acquisition, thread URL generation, lazy posts, reply behavior, post-list reads, post source/revision workflows, category cache behavior, or parser diagnostics rejects this local completion claim. | Forum workflows | `tests/unit` |
| R5 | No live auth material or private site state is needed to prove the behavior. | The regression uses synthetic `Site` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, private usernames, forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `197436a fix(forum_thread): validate creator client`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_created_by_from_different_client -q` failed before the fix with `DID NOT RAISE`.
- GREEN regression: the same focused command passed 1 test.
- Forum-thread coverage: `uv run pytest tests/unit/test_forum_thread.py -q` passed 150 tests.
- Adjacent forum category/thread/post/revision coverage: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 543 tests.
- `uv run pytest tests/unit -q` passed 2734 tests.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(site=site_a, created_by=User(client=site_b.client, ...), ...)` raises `ValueError("created_by must belong to the site")`.
- Valid direct rows where `created_by.client is site.client` remain valid.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing malformed site, thread ID, title, description, created_at, post_count, category, and posts-cache diagnostics remain unchanged.
- Existing parser-created category thread-list and direct thread-detail rows still produce valid `ForumThread` records.
- Existing URL generation, lazy posts, reply behavior, cache validation, and adjacent forum workflows remain green.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread` is the durable row shape behind browser-free forum indexes, category thread lists, direct thread detail fetches, generated forum ledgers, moderation exports, migration checks, and rehydrated records. A thread row is site-scoped, and parser-created creator users already come from the parent site's client. Constructor coherence validation keeps direct fixtures and serialized rows from mixing parent-site and creator-user client contexts while preserving the normal parser, read, and reply paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `ForumThread(site=site_a, created_by=User(client=site_b.client, ...), ...)` construction silently accepted a contradictory row.
- Existing local drafts covered category thread-list and direct thread-detail fetch retry behavior, parser scoping, response-body diagnostics, parser-side creator extraction, direct creator type validation, direct created_at validation, direct site/category/scalar validation, URL-time site validation, reply-time site validation, and posts-cache ownership, but did not validate coherence between a valid creator user object and a valid parent site.
- This slice only validates constructor-time creator/client coherence. It does not change thread-list request construction, direct thread-detail request construction, parser selectors, user parser semantics, timestamp parsing, post-count parsing, URL formatting, lazy posts, reply payload fields, cache invalidation semantics, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, private forum content, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, site IDs, thread IDs, UNIX names, or authentication state. The parser path and the rest of the object graph preserve client identity, and identity comparison avoids network lookups, login checks, and ambiguous cross-client equivalence rules.
