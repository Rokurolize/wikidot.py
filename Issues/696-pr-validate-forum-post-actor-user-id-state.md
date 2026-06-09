# PR Draft: Validate ForumPost Constructor Actor User ID State

## Summary

`ForumPost(...)` records already validate the parent thread, post ID shape and range, parent ID shape and range, source and revision caches, title, text, creator/editor object types, creator/editor site-client coherence, timestamps, retained post IDs during source/edit actions, and surrounding forum post collection/revision retained state. One constructor retained-state gap remained: valid same-client `User` objects could be mutated, fixture-loaded, or rehydrated with malformed retained `id` state and then stored as `ForumPost.created_by` or `ForumPost.edited_by`.

This change validates retained constructor actor IDs after the existing `AbstractUser` type checks and before actor/site client coherence checks. Malformed retained `created_by.id` and `edited_by.id` values now raise field-specific `ValueError(... "must be an integer or None")` diagnostics, negative retained IDs now raise field-specific `ValueError(... "must be non-negative or None")` diagnostics, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `ForumPost(...)` rows cannot store malformed or negative retained creator/editor user IDs. Valid parser-created post-list rows, same-client direct rows, unedited `edited_by=None` rows, optional missing actor IDs, zero-ID compatibility, source reads, edit behavior, revision reads, cache validation, and adjacent forum/site/user workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum post inventories, generated discussion or moderation ledgers, migration checks, cached thread post lists, lazy `ForumThread.posts`, post source capture, post edit workflows, forum revision capture, local fixtures, or serialized and rehydrated forum post records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post records and user identity as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md), [506-pr-validate-forum-post-source-cache.md](506-pr-validate-forum-post-source-cache.md), [507-pr-validate-forum-post-revisions-cache.md](507-pr-validate-forum-post-revisions-cache.md), [592-pr-validate-forum-post-collection-thread-ownership.md](592-pr-validate-forum-post-collection-thread-ownership.md), [608-pr-validate-forum-post-actor-clients.md](608-pr-validate-forum-post-actor-clients.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md), [679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md](679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md), [680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md](680-pr-validate-forum-post-list-acquisition-retained-thread-id-state.md), [682-pr-validate-forum-post-source-acquisition-retained-id-state.md](682-pr-validate-forum-post-source-acquisition-retained-id-state.md), [683-pr-validate-forum-post-edit-retained-id-state.md](683-pr-validate-forum-post-edit-retained-id-state.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), and [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md) establish forum-post acquisition, parser diagnostics, direct record construction, retained identity validation, direct user-ID validation, and downstream mutable user-state validation as practical workflow boundaries.

This slice is not a duplicate of those drafts. Issue 459 validates that `created_by` is an `AbstractUser` and `created_at` is a `datetime`; it does not validate retained creator ID state. Issue 461 validates optional edit metadata object/time shape; it does not validate retained editor ID state. Issue 608 validates actor/client coherence, not retained actor ID shape or range. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a `ForumPost` record. Issues 682 and 683 validate retained post/thread IDs during source and edit actions, not retained actor identities. Parser-side user diagnostics in Issues 295 and 297 validate malformed markup before parser-created rows, not direct constructor state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), [608-pr-validate-forum-post-actor-clients.md](608-pr-validate-forum-post-actor-clients.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), and [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `created_by.id` during `ForumPost.__post_init__`.
- Validate retained non-null `edited_by.id` during `ForumPost.__post_init__`.
- Reject retained constructor actor IDs `True`, `False`, numeric strings, floats, and lists with field-specific `ValueError("<field>.id must be an integer or None")`.
- Reject retained constructor actor IDs `-1` and `-100` with field-specific `ValueError("<field>.id must be non-negative or None")`.
- Preserve retained constructor actor IDs `None` and `0`.
- Preserve unedited `edited_by=None` post rows.
- Preserve existing thread, post ID, parent ID, source cache, revision cache, title, text, actor object type, actor/client coherence, timestamp, parser, source, edit, revision, cache, and adjacent forum/site/user workflows.

## Type Of Change

- State validation
- Forum-post constructor hardening
- Retained actor identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(..., created_by=user, ...)` must reject retained creator IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("created_by.id must be an integer or None")` before storing the post row. |
| R2 | `ForumPost(..., created_by=user, ...)` must reject retained creator IDs `-1` and `-100` with `ValueError("created_by.id must be non-negative or None")` before storing the post row. |
| R3 | Valid retained creator IDs `None` and `0` must remain accepted in direct `ForumPost(...)` construction. |
| R4 | `ForumPost(..., edited_by=user, ...)` must reject retained editor IDs `True`, `False`, `"54322"`, `54322.0`, and `[]` with `ValueError("edited_by.id must be an integer or None")` before storing the post row. |
| R5 | `ForumPost(..., edited_by=user, ...)` must reject retained editor IDs `-1` and `-100` with `ValueError("edited_by.id must be non-negative or None")` before storing the post row. |
| R6 | Valid retained editor IDs `None` and `0` must remain accepted in direct `ForumPost(...)` construction, and `edited_by=None` must remain valid for unedited posts. |
| R7 | Existing malformed thread, post ID, parent ID, source cache, revision cache, title, text, actor object, actor/client coherence, timestamp, parser, source, edit, revision, cache, and adjacent forum behavior must remain unchanged. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, forum-post tests, adjacent forum/site/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_created_by_ids` failed RED for five malformed `created_by.id` cases with `DID NOT RAISE`, then passed GREEN after `ForumPost.__post_init__` validated retained creator IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later source, edit, or revision behavior rejects this local completion claim. | `ForumPost` constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Negative retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_created_by_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained creator IDs, storing the row, or hiding the state behind later creator/client checks rejects this local completion claim. | `ForumPost` constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Optional missing and zero creator IDs remain compatible constructor state. | `test_init_accepts_optional_retained_created_by_ids` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `ForumPost` constructor | `tests/unit/test_forum_post.py` |
| R4 | Malformed retained editor IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_edited_by_ids` failed RED for five malformed `edited_by.id` cases with `DID NOT RAISE`, then passed GREEN after `ForumPost.__post_init__` validated retained editor IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later source, edit, or revision behavior rejects this local completion claim. | `ForumPost` constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R5 | Negative retained editor IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_edited_by_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained editor IDs, storing the row, or hiding the state behind later editor/client checks rejects this local completion claim. | `ForumPost` constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R6 | Optional missing and zero editor IDs remain compatible constructor state, while unedited rows remain valid. | `test_init_accepts_optional_retained_edited_by_ids` passed RED and GREEN for `None` and `0`, asserting the stored editor value is preserved; existing fixture and tests preserve `edited_by=None`. | Rejecting `None`, rejecting `0`, coercing either value, requiring concrete regular-user IDs, or rejecting unedited post rows rejects this local completion claim. | `ForumPost` constructor | `tests/unit/test_forum_post.py` |
| R7 | Existing forum-post behavior and adjacent workflows remain green. | `tests/unit/test_forum_post.py` passed 289 tests, adjacent forum/site/user coverage passed 1321 tests, and full unit coverage passed 3474 tests. | Regressing parser-created post rows, constructor validation order, actor/client coherence, post-list parsing, source reads, edit behavior, revision reads, cache validation, or adjacent forum/site/user behavior rejects this local completion claim. | Forum post and adjacent workflows | `tests/unit` |
| R8 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Site`, `Client`, `ForumThread`, `ForumPost`, and `User` objects only. | Using credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-post/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7a82c42 fix(forum_post): validate actor user ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic -k "retained_created_by_ids or retained_edited_by_ids" -q` selected 18 constructor retained-actor-ID tests; 14 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the four `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 18 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left both files unchanged.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 289 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py tests/unit/test_user.py -q` passed 1321 tests.
- `uv run pytest tests/unit -q` passed 3474 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPost(...)` raises `ValueError("created_by.id must be an integer or None")` when the retained creator ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `ForumPost(...)` raises `ValueError("created_by.id must be non-negative or None")` when the retained creator ID is `-1` or `-100`.
- `ForumPost(...)` raises `ValueError("edited_by.id must be an integer or None")` when the retained editor ID is `True`, `False`, `"54322"`, `54322.0`, or `[]`.
- `ForumPost(...)` raises `ValueError("edited_by.id must be non-negative or None")` when the retained editor ID is `-1` or `-100`.
- Malformed or negative retained actor IDs fail before the post row is stored by direct construction.
- Valid retained actor IDs `None` and `0` remain accepted by direct construction.
- Unedited post rows with `edited_by=None` remain accepted.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing malformed non-null `edited_by` values still raise `ValueError("edited_by must be an AbstractUser or None")`.
- Existing actor/client mismatches still raise `ValueError("created_by must belong to the site")` or `ValueError("edited_by must belong to the site")`.
- Existing thread, post ID, parent ID, source cache, revision cache, title, text, timestamp, parser, source, edit, revision, cache, and adjacent forum/site/user behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed forum-post rows with corrupted retained actor IDs now fail during construction instead of later source, edit, revision, or audit logic. Mitigation: those values are impossible actor identity state; failing before storage is deterministic and field-specific.
- Risk: Optional actor IDs could be rejected accidentally. Mitigation: the focused compatibility guards assert that `None` and `0` remain accepted and preserved for both creator and editor.
- Risk: Unedited rows could be forced to carry an editor. Mitigation: validation only inspects non-null `edited_by`, and existing `edited_by=None` fixture coverage remains green.
- Risk: Validation precedence could regress earlier `ForumPost` diagnostics. Mitigation: the retained-ID checks run after actor type validation and before actor/client coherence; forum-post, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing `ForumPost` thread, post ID, parent ID, source cache, revision cache, title, text, actor object type, actor/client coherence, timestamp, parser, source, edit, revision, cache, and adjacent behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `ForumPost` constructor retained actor user-ID boundary.

## Upstream-Safe Motivation

`ForumPost` is the durable row shape behind browser-free forum post inventories, generated discussion or moderation ledgers, migration checks, cached thread post lists, lazy source capture, edit workflows, and downstream forum revision traversal. Parser-created users may legitimately have optional IDs, while direct `User` construction already rejects impossible negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated creator/editor IDs out of stored forum-post rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, actor/client coherence, source reads, edit behavior, and revision semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum posts as a practical workflow through retry-aware post-list acquisition, parser diagnostics, response diagnostics, direct record construction, creator/time validation, edit metadata validation, actor/client coherence, retained source/edit IDs, revision traversal, and adjacent forum workflows.
- Existing local drafts covered non-`AbstractUser` creators/editors, actor/client mismatch, direct user constructor ID ranges, retained forum post/thread IDs, retained revision IDs, PageVote constructor user IDs, PrivateMessage participant user IDs, SiteChange actor user IDs, PageRevision creator user IDs, and ForumThread creator user IDs; they did not validate corrupted retained `User.id` values at the direct `ForumPost(...)` constructor boundary.
- The focused RED failure showed malformed and negative retained creator/editor IDs could be stored in direct forum-post rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, forum-post behavior, adjacent forum/site/user workflows, and full unit compatibility.
- This slice only validates retained actor user IDs at the `ForumPost` constructor boundary. It does not change forum post-list acquisition, parser selectors, user parser semantics, timestamp parsing, source acquisition, edit request payloads, revision acquisition, cache invalidation semantics, live site behavior, authentication semantics, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, private forum content, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained actor IDs instead of requiring concrete regular-user IDs. Forum post actors can be parsed as deleted, guest, anonymous, system, or otherwise unresolved users, and this constructor slice only rejects malformed or negative retained identity state.
