# PR Draft: Validate ForumPostRevision Constructor Creator User ID State

## Summary

`ForumPostRevision(...)` records already validate the parent post, revision ID shape and range, revision number shape and range, creator object type, creator/post-site client coherence, timestamp type, optional HTML cache shape, collection ownership, retained post/thread/revision IDs in acquisition paths, and adjacent forum post/thread/site workflows. One constructor retained-state gap remained: a valid same-client `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `id` state and then stored as `ForumPostRevision.created_by`.

This change validates retained constructor creator IDs after the existing `AbstractUser` type check and before creator/post-site client coherence checks. Malformed retained `created_by.id` values now raise `ValueError("created_by.id must be an integer or None")`, negative retained IDs now raise `ValueError("created_by.id must be non-negative or None")`, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `ForumPostRevision(...)` rows cannot store malformed or negative retained creator user IDs. Valid parser-created forum revision-list rows, same-client direct rows, optional missing creator IDs, zero-ID compatibility, revision-list collection behavior, lazy revision HTML reads, batched revision acquisition, HTML acquisition, cache validation, and adjacent forum/site/user workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision audit summaries, moderation exports, cached revision lists, duplicate revision reuse, lazy `ForumPost.revisions`, revision HTML capture, local fixtures, or serialized and rehydrated forum post revision records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revisions and user identity as practical workflow surfaces. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), [508-pr-validate-forum-post-revision-html-cache.md](508-pr-validate-forum-post-revision-html-cache.md), [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md), [582-pr-validate-forum-post-revision-html-target-post-thread.md](582-pr-validate-forum-post-revision-html-target-post-thread.md), [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md), [609-pr-validate-forum-post-revision-creator-client.md](609-pr-validate-forum-post-revision-creator-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [675-pr-validate-forum-post-revision-collection-retained-identity-state.md](675-pr-validate-forum-post-revision-collection-retained-identity-state.md), [678-pr-validate-forum-post-revision-html-acquisition-retained-id-state.md](678-pr-validate-forum-post-revision-html-acquisition-retained-id-state.md), [679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md](679-pr-validate-forum-post-revision-list-acquisition-retained-post-id-state.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md), and [696-pr-validate-forum-post-actor-user-id-state.md](696-pr-validate-forum-post-actor-user-id-state.md) establish forum revision acquisition, parser diagnostics, direct record construction, retained identity validation, direct user-ID validation, and downstream mutable user-state validation as practical workflow boundaries.

This slice is not a duplicate of those drafts. Issue 464 validates that `created_by` is an `AbstractUser` and `created_at` is a `datetime`; it does not validate retained creator ID state. Issue 609 validates creator/client coherence, not retained ID shape or range. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a `ForumPostRevision` record. Issues 675, 678, and 679 validate retained revision or parent post IDs during lookup/acquisition behavior, not retained creator identity. Issue 285 validates parser-side malformed revision-list user markup before `ForumPostRevision` construction; it does not validate direct constructor state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), [609-pr-validate-forum-post-revision-creator-client.md](609-pr-validate-forum-post-revision-creator-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md), and [696-pr-validate-forum-post-actor-user-id-state.md](696-pr-validate-forum-post-actor-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `created_by.id` during `ForumPostRevision.__post_init__`.
- Reject retained constructor creator IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("created_by.id must be an integer or None")`.
- Reject retained constructor creator IDs `-1` and `-100` with `ValueError("created_by.id must be non-negative or None")`.
- Preserve retained constructor creator IDs `None` and `0`.
- Preserve existing post, revision ID, revision number, creator object, creator/client coherence, timestamp, optional HTML cache, revision-list parsing, lazy HTML, acquisition, collection, and adjacent forum/site/user workflows.

## Type Of Change

- State validation
- Forum-post-revision constructor hardening
- Retained creator identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevision(..., created_by=user, ...)` must reject retained creator IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("created_by.id must be an integer or None")` before storing the revision row. |
| R2 | `ForumPostRevision(..., created_by=user, ...)` must reject retained creator IDs `-1` and `-100` with `ValueError("created_by.id must be non-negative or None")` before storing the revision row. |
| R3 | Valid retained creator IDs `None` and `0` must remain accepted in direct `ForumPostRevision(...)` construction. |
| R4 | Existing malformed post, revision ID, revision number, creator object, creator/client coherence, timestamp, optional HTML cache, parser, lazy HTML, acquisition, collection, and adjacent forum behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post-revision tests, adjacent forum/site/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_created_by_ids` failed RED for five malformed `created_by.id` cases with `DID NOT RAISE`, then passed GREEN after `ForumPostRevision.__post_init__` validated retained creator IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later revision-list or HTML acquisition behavior rejects this local completion claim. | `ForumPostRevision` constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Negative retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_created_by_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained creator IDs, storing the row, or hiding the state behind later creator/client checks rejects this local completion claim. | `ForumPostRevision` constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Optional missing and zero creator IDs remain compatible constructor state. | `test_init_accepts_optional_retained_created_by_ids` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `ForumPostRevision` constructor | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing forum-post-revision behavior and adjacent workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 228 tests, adjacent forum/site/user coverage passed 1330 tests, and full unit coverage passed 3483 tests. | Regressing parser-created revision rows, constructor validation order, creator/client coherence, revision-list parsing, lazy HTML, batch acquisition, collection behavior, cache validation, or adjacent forum/site/user behavior rejects this local completion claim. | Forum post revision and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Site`, `Client`, `ForumPost`, `ForumThread`, `ForumPostRevision`, and `User` objects only. | Using credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-post-revision/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b958308 fix(forum_post_revision): validate creator user ids`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic -k retained_created_by_ids -q` selected 9 constructor retained-creator-ID tests; 7 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the two `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 9 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left both files unchanged.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 228 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_site.py tests/unit/test_user.py -q` passed 1330 tests.
- `uv run pytest tests/unit -q` passed 3483 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `ForumPostRevision(...)` raises `ValueError("created_by.id must be an integer or None")` when the retained creator ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `ForumPostRevision(...)` raises `ValueError("created_by.id must be non-negative or None")` when the retained creator ID is `-1` or `-100`.
- Malformed or negative retained creator IDs fail before the revision row is stored by direct construction.
- Valid retained creator IDs `None` and `0` remain accepted by direct construction.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing creator/client mismatches still raise `ValueError("created_by must belong to the site")`.
- Existing post, revision ID, revision number, timestamp, optional HTML cache, parser, lazy HTML, acquisition, collection, and adjacent forum/site/user behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw forum HTML, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed forum-post-revision rows with corrupted retained creator IDs now fail during construction instead of later revision-list, HTML acquisition, or audit logic. Mitigation: those values are impossible creator identity state; failing before storage is deterministic and field-specific.
- Risk: Optional creator IDs could be rejected accidentally. Mitigation: the focused compatibility guard asserts that `None` and `0` remain accepted and preserved.
- Risk: Validation precedence could regress earlier `ForumPostRevision` diagnostics. Mitigation: the retained-ID check runs after creator type validation and before creator/client coherence; forum-post-revision, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing `ForumPostRevision` post, revision ID, revision number, creator object, creator/client coherence, timestamp, optional HTML cache, parser, lazy HTML, acquisition, collection, and adjacent behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `ForumPostRevision` constructor retained creator user-ID boundary.

## Upstream-Safe Motivation

`ForumPostRevision` is the durable row shape behind browser-free forum edit-history reads, generated discussion migration ledgers, revision audit summaries, moderation exports, cached revision lists, duplicate revision reuse, lazy revision reads, revision HTML capture, and downstream forum analysis. Parser-created users may legitimately have optional IDs, while direct `User` construction already rejects impossible negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated creator IDs out of stored forum-post-revision rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, creator/client coherence, collection behavior, and HTML acquisition semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post revisions as a practical workflow through retry-aware revision-list acquisition, parser diagnostics, response diagnostics, direct record construction, creator/time validation, creator/client coherence, retained parent post/thread/revision IDs, HTML acquisition, and adjacent forum workflows.
- Existing local drafts covered non-`AbstractUser` creators, creator/client mismatch, direct user constructor ID ranges, retained revision IDs, retained parent post/thread IDs, PageRevision creator user IDs, ForumThread creator user IDs, and ForumPost actor user IDs; they did not validate corrupted retained `User.id` values at the direct `ForumPostRevision(...)` constructor boundary.
- The focused RED failure showed malformed and negative retained creator IDs could be stored in direct forum-post-revision rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, forum-post-revision behavior, adjacent forum/site/user workflows, and full unit compatibility.
- This slice only validates retained creator user IDs at the `ForumPostRevision` constructor boundary. It does not change revision-list acquisition, parser selectors, user parser semantics, revision ID semantics, revision-number semantics, HTML acquisition, cache invalidation semantics, live site behavior, authentication semantics, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, private forum content, rendered revision HTML, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained creator IDs instead of requiring concrete regular-user IDs. Forum post revision creators can be parsed as deleted, guest, anonymous, system, or otherwise unresolved users, and this constructor slice only rejects malformed or negative retained identity state.
