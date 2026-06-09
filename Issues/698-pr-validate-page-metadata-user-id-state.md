# PR Draft: Validate Page Metadata User ID State

## Summary

`Page(...)` records already validate site state, scalar fields, nullable metadata user shape, nullable timestamp shape, metadata user/client coherence, cached page ID state, source/revision/vote/file caches, and adjacent page workflows. One retained-state gap remained: a valid same-client `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `id` state and then stored as nullable `Page.created_by`, `Page.updated_by`, or `Page.commented_by` metadata.

This change validates retained page metadata user IDs after the existing `AbstractUser | None` type check and before metadata user/site client coherence. Malformed retained `created_by.id`, `updated_by.id`, or `commented_by.id` values now raise `ValueError("<field>.id must be an integer or None")`, negative retained IDs now raise `ValueError("<field>.id must be non-negative or None")`, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `Page(...)` rows cannot store malformed or negative retained creator, updater, or last-commenter user IDs. Valid missing metadata users, missing metadata user IDs, zero-ID compatibility, same-client metadata users, ListPages-derived page rows, page source/revision/vote/file workflows, cache ownership, and adjacent site/user behavior remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, ListPages metadata ledgers, migration comparison rows, publish-adjacent checks, source/revision/vote/file traversal, cached page records, local fixtures, or serialized and rehydrated page metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify page metadata, ListPages parsing, source/revision/vote/file traversal, page inventories, and user identity as practical workflow surfaces. Existing drafts [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [487-pr-validate-page-constructor-nullable-metadata.md](487-pr-validate-page-constructor-nullable-metadata.md), [616-pr-validate-page-metadata-user-clients.md](616-pr-validate-page-metadata-user-clients.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md), [696-pr-validate-forum-post-actor-user-id-state.md](696-pr-validate-forum-post-actor-user-id-state.md), and [697-pr-validate-forum-post-revision-creator-user-id-state.md](697-pr-validate-forum-post-revision-creator-user-id-state.md) establish page metadata, parser diagnostics, constructor validation, user/client coherence, direct user-ID validation, and downstream mutable user-state validation as practical workflow boundaries.

This slice is not a duplicate of those drafts. Issue 487 validates that `created_by`, `updated_by`, and `commented_by` are `AbstractUser | None`, plus timestamp shape; it does not validate retained metadata user ID state. Issue 616 validates metadata user/client coherence, not retained ID shape or range. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a `Page` record. Issue 306 validates parser-side malformed ListPages user markup before page construction. Issues 691 and 694 through 697 validate adjacent page-vote, page-revision, and forum retained user-ID boundaries, not nullable base page metadata.

## Related Issue / Non-Duplicate Analysis

Builds directly on [487-pr-validate-page-constructor-nullable-metadata.md](487-pr-validate-page-constructor-nullable-metadata.md), [616-pr-validate-page-metadata-user-clients.md](616-pr-validate-page-metadata-user-clients.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md), [696-pr-validate-forum-post-actor-user-id-state.md](696-pr-validate-forum-post-actor-user-id-state.md), and [697-pr-validate-forum-post-revision-creator-user-id-state.md](697-pr-validate-forum-post-revision-creator-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `created_by.id`, `updated_by.id`, and `commented_by.id` during `Page.__post_init__`.
- Reject retained constructor metadata user IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("<field>.id must be an integer or None")`.
- Reject retained constructor metadata user IDs `-1` and `-100` with `ValueError("<field>.id must be non-negative or None")`.
- Preserve retained constructor metadata user IDs `None` and `0`.
- Preserve existing nullable metadata user shape, timestamp shape, metadata user/client coherence, parser-created page rows, page source/revision/vote/file workflows, cache ownership, and adjacent site/user behavior.

## Type Of Change

- State validation
- Page constructor hardening
- Retained nullable metadata identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(..., created_by=user, ...)`, `Page(..., updated_by=user, ...)`, and `Page(..., commented_by=user, ...)` must reject retained metadata user IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("<field>.id must be an integer or None")` before storing the page row. |
| R2 | Those same metadata fields must reject retained metadata user IDs `-1` and `-100` with `ValueError("<field>.id must be non-negative or None")` before storing the page row. |
| R3 | Valid retained metadata user IDs `None` and `0` must remain accepted in direct `Page(...)` construction. |
| R4 | Existing malformed metadata user, metadata timestamp, metadata user/client, parser-created page, source/revision/vote/file, cache ownership, and adjacent site/user behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw page/forum/private content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-constructor tests, adjacent page/site/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained page metadata user IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_user_metadata_ids` failed RED for fifteen malformed field/value cases with `DID NOT RAISE`, then passed GREEN after `Page.__post_init__` validated retained metadata user IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later page reads rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Negative retained page metadata user IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_user_metadata_ids` failed RED for six negative field/value cases with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained metadata user IDs, storing the row, or hiding the state behind later metadata user/client checks rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Optional missing and zero metadata user IDs remain compatible constructor state. | `test_init_accepts_optional_retained_user_metadata_ids` passed RED and GREEN for `None` and `0` across all three metadata fields, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `Page` constructor | `tests/unit/test_page_constructor.py` |
| R4 | Existing page behavior and adjacent workflows remain green. | `tests/unit/test_page_constructor.py` passed 217 tests, adjacent page/site/user coverage passed 1289 tests, and full unit coverage passed 3510 tests. | Regressing nullable metadata shape diagnostics, timestamp diagnostics, metadata user/client coherence, ListPages parsing, source/revision/vote/file workflows, cache ownership, or adjacent site/user behavior rejects this local completion claim. | Page and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Site`, `Client`, `Page`, and `User` objects only. | Using credentials, cookies, auth JSON, raw page/forum/private content, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page-constructor/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1b32dc3 fix(page): validate metadata user ids`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit -k "retained_user_metadata_ids" -q` selected 27 constructor retained-metadata-user-ID tests; 21 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the six `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 27 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left both files unchanged.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 217 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py tests/unit/test_user.py -q` passed 1289 tests.
- `uv run pytest tests/unit -q` passed 3510 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `Page(...)` raises `ValueError("created_by.id must be an integer or None")`, `ValueError("updated_by.id must be an integer or None")`, or `ValueError("commented_by.id must be an integer or None")` when the retained metadata user ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `Page(...)` raises `ValueError("created_by.id must be non-negative or None")`, `ValueError("updated_by.id must be non-negative or None")`, or `ValueError("commented_by.id must be non-negative or None")` when the retained metadata user ID is `-1` or `-100`.
- Malformed or negative retained metadata user IDs fail before the page row is stored by direct construction.
- Valid retained metadata user IDs `None` and `0` remain accepted by direct construction.
- Existing malformed metadata user values still raise `ValueError("<field> must be an AbstractUser or None")`.
- Existing metadata user/client mismatches still raise `ValueError("<field> must belong to the site")`.
- Existing nullable timestamps, parser-created page rows, page source/revision/vote/file workflows, cache ownership, and adjacent site/user behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw page/forum/private content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed page rows with corrupted retained metadata user IDs now fail during construction instead of later page inventory, display, or ledger code. Mitigation: those values are impossible user identity state; failing before storage is deterministic and field-specific.
- Risk: Optional metadata user IDs could be rejected accidentally. Mitigation: focused compatibility guards assert that `None` and `0` remain accepted and preserved across `created_by`, `updated_by`, and `commented_by`.
- Risk: Validation precedence could regress earlier `Page` diagnostics. Mitigation: the retained-ID check runs after nullable metadata user type validation and before metadata user/client coherence; page-constructor, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing `Page` site, scalar, nullable metadata user, nullable timestamp, metadata user/client, parser, source/revision/vote/file, cache ownership, and adjacent site/user behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable state preflights, or complexity candidates outside this now-covered `Page` constructor retained metadata user-ID boundary.

## Upstream-Safe Motivation

`Page` metadata users are durable actor fields behind browser-free page inventories, ListPages metadata ledgers, source/revision/vote/file traversal, publish-adjacent checks, migration comparison rows, and local rehydrated page records. Parser-created users may legitimately have optional IDs, while direct `User` construction already rejects impossible negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated metadata user IDs out of stored page rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, metadata user/client coherence, cache ownership, and page workflow semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page metadata users as practical workflow state through ListPages parsing, page inventory ledgers, source/revision/vote/file traversal, publish-adjacent checks, and adjacent page record validation.
- Existing local drafts covered nullable metadata user type validation, nullable timestamp validation, metadata user/client mismatch, direct user constructor ID ranges, page vote user IDs, page revision creator user IDs, and adjacent forum retained user IDs; they did not validate corrupted retained `User.id` values at the direct nullable `Page(...)` metadata boundary.
- The focused RED failure showed malformed and negative retained metadata user IDs could be stored in direct page rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, page-constructor behavior, adjacent page/site/user workflows, and full unit compatibility.
- This slice only validates retained metadata user IDs at the `Page` constructor boundary. It does not change ListPages selectors, parser diagnostics, user parser semantics, timestamp parsing, page source/revision/vote/file acquisition, page write behavior, cache invalidation semantics, live site behavior, authentication semantics, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page/forum/private content, rendered page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained metadata user IDs instead of requiring concrete regular-user IDs. Page metadata can be omitted by ListPages output or represented by deleted, guest, anonymous, system, or otherwise unresolved users, and this constructor slice only rejects malformed or negative retained identity state.
