# PR Draft: Validate ForumThread Constructor Creator User ID State

## Summary

`ForumThread(...)` records already validate the parent site, thread ID shape and range, title, description, creator object type, creator/site client coherence, timestamp type, post count shape and range, parent category, posts cache ownership, lookup IDs, reply-time retained IDs, and category-thread-list acquisition retained category IDs. One constructor retained-state gap remained: a valid same-client `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `id` state and then stored as `ForumThread.created_by`.

This change validates retained constructor creator IDs after the existing `AbstractUser` type check and before creator/site client coherence checks. Malformed retained `created_by.id` values now raise `ValueError("created_by.id must be an integer or None")`, negative retained IDs now raise `ValueError("created_by.id must be non-negative or None")`, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `ForumThread(...)` rows cannot store malformed or negative retained creator user IDs. Valid parser-created category thread-list rows, direct thread-detail rows, same-client direct rows, optional missing creator IDs, zero-ID compatibility, lazy post access, reply behavior, cache validation, and adjacent forum/site/user workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, category thread lists, direct thread-detail reads, generated forum ledgers, moderation exports, migration checks, cached category scans, duplicate direct-thread reads, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, `ForumThread.posts`, forum replies, local fixtures, or serialized and rehydrated thread records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-thread records and user identity as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), [607-pr-validate-forum-thread-creator-client.md](607-pr-validate-forum-thread-creator-client.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md](680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), [684-pr-validate-forum-thread-reply-retained-id-state.md](684-pr-validate-forum-thread-reply-retained-id-state.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md), and [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md) establish forum-thread acquisition, parser diagnostics, direct record construction, retained thread/category identity, direct user-ID validation, and downstream mutable user-state validation as practical workflow boundaries.

This slice is not a duplicate of those drafts. Issue 458 validates that `created_by` is an `AbstractUser`; it does not validate retained creator ID state. Issue 607 validates creator/client coherence, not retained ID shape or range. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a `ForumThread` record. Issues 680, 681, and 684 validate retained forum/thread/category IDs during acquisition or reply behavior, not retained creator identity. Issue 293 validates parser-side malformed direct thread-detail user markup before `ForumThread` construction; it does not validate direct constructor state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [607-pr-validate-forum-thread-creator-client.md](607-pr-validate-forum-thread-creator-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md), and [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `created_by.id` during `ForumThread.__post_init__`.
- Reject retained constructor creator IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("created_by.id must be an integer or None")`.
- Reject retained constructor creator IDs `-1` and `-100` with `ValueError("created_by.id must be non-negative or None")`.
- Preserve retained constructor creator IDs `None` and `0`.
- Preserve existing site, thread ID, title, description, creator object, creator/client coherence, timestamp, post count, category, posts cache, category thread-list parsing, direct thread-detail parsing, lazy post access, reply behavior, and adjacent forum/site/user workflows.

## Type Of Change

- State validation
- Forum-thread constructor hardening
- Retained creator identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(..., created_by=user, ...)` must reject retained creator IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("created_by.id must be an integer or None")` before storing the thread row. |
| R2 | `ForumThread(..., created_by=user, ...)` must reject retained creator IDs `-1` and `-100` with `ValueError("created_by.id must be non-negative or None")` before storing the thread row. |
| R3 | Valid retained creator IDs `None` and `0` must remain accepted in direct `ForumThread(...)` construction. |
| R4 | Existing malformed site, thread ID, title, description, creator object, creator/client coherence, timestamp, post count, category, posts cache, parser, lazy posts, reply, and adjacent forum behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-thread tests, adjacent forum/site/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_created_by_ids` failed RED for five malformed `created_by.id` cases with `DID NOT RAISE`, then passed GREEN after `ForumThread.__post_init__` validated retained creator IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later post acquisition or reply behavior rejects this local completion claim. | `ForumThread` constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Negative retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_created_by_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained creator IDs, storing the row, or hiding the state behind later creator/client checks rejects this local completion claim. | `ForumThread` constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Optional missing and zero creator IDs remain compatible constructor state. | `test_init_accepts_optional_retained_created_by_ids` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `ForumThread` constructor | `tests/unit/test_forum_thread.py` |
| R4 | Existing forum-thread behavior and adjacent workflows remain green. | `tests/unit/test_forum_thread.py` passed 221 tests, adjacent forum/site/user coverage passed 1303 tests, and full unit coverage passed 3456 tests. | Regressing parser-created thread rows, constructor validation order, creator/client coherence, category thread-list parsing, direct thread-detail parsing, lazy posts, reply behavior, cache validation, or adjacent forum/site/user behavior rejects this local completion claim. | Forum thread and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Site`, `Client`, and `User` objects only. | Using credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-thread/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4e3d1d0 fix(forum_thread): validate creator user ids`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic -k retained_created_by_ids -q` selected 9 constructor retained-creator-ID tests; 7 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the two `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 9 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left both files unchanged.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 221 tests.
- `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py tests/unit/test_user.py -q` passed 1303 tests.
- `uv run pytest tests/unit -q` passed 3456 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumThread(...)` raises `ValueError("created_by.id must be an integer or None")` when the retained creator ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `ForumThread(...)` raises `ValueError("created_by.id must be non-negative or None")` when the retained creator ID is `-1` or `-100`.
- Malformed or negative retained creator IDs fail before the thread row is stored by direct construction.
- Valid retained creator IDs `None` and `0` remain accepted by direct construction.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing creator/client mismatches still raise `ValueError("created_by must belong to the site")`.
- Existing site, thread ID, title, description, timestamp, post count, category, posts cache, parser, lazy post, reply, and adjacent forum/site/user behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed forum-thread rows with corrupted retained creator IDs now fail during construction instead of later post acquisition, reply, or audit logic. Mitigation: those values are impossible creator identity state; failing before storage is deterministic and field-specific.
- Risk: Optional creator IDs could be rejected accidentally. Mitigation: the focused compatibility guard asserts that `None` and `0` remain accepted and preserved.
- Risk: Validation precedence could regress earlier `ForumThread` diagnostics. Mitigation: the retained-ID check runs after creator type validation and before creator/client coherence; forum-thread, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing `ForumThread` site, thread ID, title, description, creator object, creator/client coherence, timestamp, post count, category, posts cache, parser, lazy posts, and reply behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `ForumThread` constructor retained creator user-ID boundary.

## Upstream-Safe Motivation

`ForumThread` is the durable row shape behind browser-free forum indexing, category thread lists, direct thread-detail reads, generated forum ledgers, moderation exports, migration checks, cached category scans, duplicate direct-thread reads, lazy post-list reads, replies, and downstream forum post/revision traversal. Parser-created users may legitimately have optional IDs, while direct `User` construction already rejects impossible negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated creator IDs out of stored forum-thread rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, creator/client coherence, lazy posts, and reply semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum threads as a practical workflow through retry-aware category thread-list and direct thread-detail acquisition, parser diagnostics, response diagnostics, direct record construction, creator/time validation, creator/client coherence, retained thread/category identity validation, lazy posts, reply behavior, and adjacent forum workflows.
- Existing local drafts covered non-`AbstractUser` creators, creator/client mismatch, direct user constructor ID ranges, retained forum thread IDs, PageVote constructor user IDs, PrivateMessage participant user IDs, SiteChange actor user IDs, and PageRevision creator user IDs; they did not validate corrupted retained `User.id` values at the direct `ForumThread(...)` constructor boundary.
- The focused RED failure showed malformed and negative retained creator IDs could be stored in direct forum-thread rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, forum-thread behavior, adjacent forum/site/user workflows, and full unit compatibility.
- This slice only validates retained creator user IDs at the `ForumThread` constructor boundary. It does not change category thread-list acquisition, direct thread-detail acquisition, parser selectors, user parser semantics, timestamp parsing, post-count parsing, URL formatting, lazy posts, reply payload fields, cache invalidation semantics, live site behavior, authentication semantics, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, private forum content, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained creator IDs instead of requiring concrete regular-user IDs. Forum-thread creators can be parsed as deleted, guest, anonymous, system, or otherwise unresolved users, and this constructor slice only rejects malformed or negative retained identity state.
