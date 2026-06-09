# PR Draft: Validate PageRevision Constructor Creator User ID State

## Summary

`PageRevision(...)` records already validate the parent page, revision ID shape and range, revision number shape and range, creator object type, creator/page-site client coherence, timestamp type, comments, source cache ownership, HTML cache shape, collection lookup state, and source/HTML acquisition retained revision IDs. One constructor retained-state gap remained: a valid same-client `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `id` state and then stored as `PageRevision.created_by`.

This change validates retained constructor creator IDs after the existing `AbstractUser` type check and before creator/page-site coherence checks. Malformed retained `created_by.id` values now raise `ValueError("created_by.id must be an integer or None")`, negative retained IDs now raise `ValueError("created_by.id must be non-negative or None")`, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `PageRevision(...)` rows cannot store malformed or negative retained creator user IDs. Valid parser-created page-history rows, same-client direct rows, optional missing creator IDs, zero-ID compatibility, page-revision collection behavior, source/HTML acquisition, source cache ownership, page workflows, and adjacent user workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use page revision history, direct `PageRevision(...)` construction in tests or local ledgers, page-history audit exports, migration checks, browser-free source/HTML comparison, generated revision reports, or serialized and rehydrated page revision records.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision history and user identity as practical workflow surfaces. Existing drafts [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [431-pr-validate-page-revision-source-assignment.md](431-pr-validate-page-revision-source-assignment.md), [465-pr-validate-page-revision-fields.md](465-pr-validate-page-revision-fields.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md), [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), [610-pr-validate-page-revision-creator-client.md](610-pr-validate-page-revision-creator-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [663-pr-validate-page-revision-source-cache-retained-page-id-state.md](663-pr-validate-page-revision-source-cache-retained-page-id-state.md), [676-pr-validate-page-revision-collection-retained-id-state.md](676-pr-validate-page-revision-collection-retained-id-state.md), [677-pr-validate-page-revision-acquisition-retained-id-state.md](677-pr-validate-page-revision-acquisition-retained-id-state.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), and [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md) establish page history parsing, parser diagnostics, direct revision construction, collection behavior, retained revision identity, direct user-ID validation, and downstream mutable user-state validation as practical workflow boundaries.

This slice is not a duplicate of those drafts. Issue 467 validates that `created_by` is an `AbstractUser`; it does not validate retained creator ID state. Issue 610 validates creator/client coherence, not retained ID shape or range. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a `PageRevision` record. Issues 676 and 677 validate retained `PageRevision.id` during lookup and source/HTML acquisition, not retained creator identity. Issue 303 validates parser-side malformed page-history user markup before `PageRevision` construction; it does not validate direct constructor state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), [610-pr-validate-page-revision-creator-client.md](610-pr-validate-page-revision-creator-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [676-pr-validate-page-revision-collection-retained-id-state.md](676-pr-validate-page-revision-collection-retained-id-state.md), [677-pr-validate-page-revision-acquisition-retained-id-state.md](677-pr-validate-page-revision-acquisition-retained-id-state.md), and [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `created_by.id` during `PageRevision.__post_init__`.
- Reject retained constructor creator IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("created_by.id must be an integer or None")`.
- Reject retained constructor creator IDs `-1` and `-100` with `ValueError("created_by.id must be non-negative or None")`.
- Preserve retained constructor creator IDs `None` and `0`.
- Preserve existing page, revision ID, revision number, creator object, creator/client coherence, timestamp, comment, source cache, HTML cache, collection lookup, source/HTML acquisition, page workflow, and adjacent user behavior.

## Type Of Change

- State validation
- Page-revision constructor hardening
- Retained creator identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(..., created_by=user, ...)` must reject retained creator IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("created_by.id must be an integer or None")` before storing the revision row. |
| R2 | `PageRevision(..., created_by=user, ...)` must reject retained creator IDs `-1` and `-100` with `ValueError("created_by.id must be non-negative or None")` before storing the revision row. |
| R3 | Valid retained creator IDs `None` and `0` must remain accepted in direct `PageRevision(...)` construction. |
| R4 | Existing malformed page, revision ID, revision number, comment, creator object, creator/client coherence, timestamp, source cache, HTML cache, collection lookup, source/HTML acquisition, page workflow, and adjacent user behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw page-history bodies, private revision source, rendered private revision HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-revision tests, adjacent page/page-source/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_created_by_ids` failed RED for five malformed `created_by.id` cases with `DID NOT RAISE`, then passed GREEN after `PageRevision.__post_init__` validated retained creator IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later source/HTML acquisition rejects this local completion claim. | `PageRevision` constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Negative retained creator IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_created_by_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained creator IDs, storing the row, or hiding the state behind later creator/client checks rejects this local completion claim. | `PageRevision` constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Optional missing and zero creator IDs remain compatible constructor state. | `test_init_accepts_optional_retained_created_by_ids` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `PageRevision` constructor | `tests/unit/test_page_revision.py` |
| R4 | Existing page-revision behavior and adjacent workflows remain green. | `tests/unit/test_page_revision.py` passed 173 tests, adjacent page/page-source/user coverage passed 666 tests, and full unit coverage passed 3447 tests. | Regressing parser-created revision rows, constructor validation order, creator/client coherence, source/HTML acquisition, source cache ownership, collection lookup, page workflows, or adjacent user behavior rejects this local completion claim. | Page revision and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Page`, `Client`, and `User` objects only. | Using credentials, cookies, auth JSON, raw page-history bodies, private revision source, rendered private revision HTML, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, page-revision/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4e4a3e0 fix(page_revision): validate creator user ids`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision -k retained_created_by_ids -q` selected 9 constructor retained-creator-ID tests; 7 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the two `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 9 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 173 tests.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py tests/unit/test_page_source.py tests/unit/test_user.py -q` passed 666 tests.
- `uv run pytest tests/unit -q` passed 3447 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageRevision(...)` raises `ValueError("created_by.id must be an integer or None")` when the retained creator ID is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- `PageRevision(...)` raises `ValueError("created_by.id must be non-negative or None")` when the retained creator ID is `-1` or `-100`.
- Malformed or negative retained creator IDs fail before the revision row is stored by direct construction.
- Valid retained creator IDs `None` and `0` remain accepted by direct construction.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing creator/client mismatches still raise `ValueError("created_by must belong to the site")`.
- Existing page, revision ID, revision number, timestamp, comment, source cache, HTML cache, collection lookup, source/HTML acquisition, page workflow, and adjacent user behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw page-history bodies, private revision source, rendered private revision HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed page-revision rows with corrupted retained creator IDs now fail during construction instead of later source/HTML or audit logic. Mitigation: those values are impossible creator identity state; failing before storage is deterministic and field-specific.
- Risk: Optional creator IDs could be rejected accidentally. Mitigation: the focused compatibility guard asserts that `None` and `0` remain accepted and preserved.
- Risk: Validation precedence could regress earlier `PageRevision` diagnostics. Mitigation: the retained-ID check runs after creator type validation and before creator/client coherence; page-revision, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing `PageRevision` page, revision ID, revision number, creator object, creator/client coherence, timestamp, comment, source cache, HTML cache, collection, and source/HTML acquisition behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `PageRevision` constructor retained creator user-ID boundary.

## Upstream-Safe Motivation

`PageRevision` is the durable row shape behind browser-free page-history reads, source/HTML comparisons, migration checks, generated revision reports, local fixtures, and audit ledgers. Parser-created users may legitimately have optional IDs, while direct `User` construction already rejects impossible negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated creator IDs out of stored page-revision rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, creator/client coherence, collection lookup, and source/HTML acquisition semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page revisions as a practical workflow through page-history acquisition, parser diagnostics, response diagnostics, source/HTML acquisition, source cache ownership, collection lookup, retained revision-ID validation, direct creator/time validation, and creator/client coherence.
- Existing local drafts covered non-`AbstractUser` creators, creator/client mismatch, direct user constructor ID ranges, retained revision IDs, PageVote constructor user IDs, PrivateMessage participant user IDs, and SiteChange actor user IDs; they did not validate corrupted retained `User.id` values at the direct `PageRevision(...)` constructor boundary.
- The focused RED failure showed malformed and negative retained creator IDs could be stored in direct page-revision rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, page-revision behavior, adjacent page/source/user workflows, and full unit compatibility.
- This slice only validates retained creator user IDs at the `PageRevision` constructor boundary. It does not change page-history request construction, parser selectors, revision ID semantics, revision-number semantics, source acquisition, HTML acquisition, source cache ownership, page source behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page-history bodies, private revision source, rendered private revision HTML, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained creator IDs instead of requiring concrete regular-user IDs. Page-history creators can be parsed as deleted, guest, anonymous, system, or otherwise unresolved users, and this constructor slice only rejects malformed or negative retained identity state.
