# PR Draft: Validate SiteChange Constructor Actor User ID State

## Summary

`SiteChange(...)` records already validate flags, revision number shape and range, page identity, text fields, optional comments, actor object type, timestamp type, parent site type, and actor/client coherence. One constructor retained-state gap remained: a valid same-client `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `id` state and then stored as `SiteChange.changed_by`.

This change validates retained constructor actor IDs after the existing `AbstractUser` type check and before timestamp, site, and actor/client coherence checks. Malformed retained `changed_by.id` values now raise `ValueError("changed_by.id must be an integer or None")`, negative retained IDs now raise `ValueError("changed_by.id must be non-negative or None")`, and valid optional `None` plus zero-ID compatibility remain accepted.

## Outcome

Direct `SiteChange(...)` rows cannot store malformed or negative retained actor user IDs. Valid parser-created recent-change rows, same-client direct rows, optional missing actor IDs, zero-ID compatibility, recent-change fetching, parser diagnostics, pagination, limit handling, and adjacent site/page/member/application/user workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, browser-free change monitoring, generated multi-site reports, or serialized and rehydrated recent-change records.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent-change records and user identity as practical workflow surfaces. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md), [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [604-pr-validate-site-change-actor-client.md](604-pr-validate-site-change-actor-client.md), [631-pr-validate-blank-site-change-page-fullnames.md](631-pr-validate-blank-site-change-page-fullnames.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [657-pr-validate-non-negative-site-change-revision-numbers.md](657-pr-validate-non-negative-site-change-revision-numbers.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), and [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md) establish recent-change fetching, parser diagnostics, direct record construction, user-ID validation, and downstream mutable user-state validation as practical workflow boundaries.

This slice is not a duplicate of those drafts. Issue 438 validates that `changed_by` is an `AbstractUser`; it does not validate retained actor ID state. Issue 604 validates actor/client coherence, not retained ID shape or range. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a `SiteChange` record. Issues 436 and 657 validate `SiteChange.revision_no`, not actor identity. Issue 299 validates parser-side malformed recent-change user markup before `SiteChange` construction; it does not validate direct constructor state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md), [604-pr-validate-site-change-actor-client.md](604-pr-validate-site-change-actor-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), and [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `changed_by.id` during `SiteChange.__post_init__`.
- Reject retained constructor actor IDs `True`, `False`, `"1"`, `1.0`, and `[]` with `ValueError("changed_by.id must be an integer or None")`.
- Reject retained constructor actor IDs `-1` and `-100` with `ValueError("changed_by.id must be non-negative or None")`.
- Preserve retained constructor actor IDs `None` and `0`.
- Preserve existing flags, revision number, page fullname, page title, comment, actor object, timestamp, site, actor/client coherence, recent-change parser, pagination, limit handling, and adjacent site/page/member/application/user workflows.

## Type Of Change

- State validation
- Recent-change constructor hardening
- Retained actor identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(..., changed_by=user, ...)` must reject retained actor IDs `True`, `False`, `"1"`, `1.0`, and `[]` with `ValueError("changed_by.id must be an integer or None")` before storing the recent-change row. |
| R2 | `SiteChange(..., changed_by=user, ...)` must reject retained actor IDs `-1` and `-100` with `ValueError("changed_by.id must be non-negative or None")` before storing the recent-change row. |
| R3 | Valid retained actor IDs `None` and `0` must remain accepted in direct `SiteChange(...)` construction. |
| R4 | Existing malformed flags, revision numbers, page text fields, comments, actor objects, timestamps, sites, actor/client coherence, recent-change parser workflows, pagination, limit validation, and adjacent site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw recent-change bodies, private edit comments, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, recent-change constructor/parser tests, site tests, adjacent site/page/member/application/user tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained actor IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_changed_by_ids` failed RED for five malformed `changed_by.id` cases with `DID NOT RAISE`, then passed GREEN after `SiteChange.__post_init__` validated retained actor IDs. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure to later recent-change handling rejects this local completion claim. | `SiteChange` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Negative retained actor IDs fail at the direct constructor boundary. | `test_init_rejects_negative_retained_changed_by_ids` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor retained-ID validation was added. | Accepting negative retained actor IDs, storing the row, or hiding the state behind later actor/client checks rejects this local completion claim. | `SiteChange` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Optional missing and zero actor IDs remain compatible constructor state. | `test_init_accepts_optional_retained_changed_by_ids` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring concrete regular-user IDs rejects this local completion claim. | `SiteChange` constructor | `tests/unit/test_site.py` |
| R4 | Existing recent-change behavior and adjacent workflows remain green. | `TestSiteChangeDataclass` plus `TestSiteGetRecentChanges` passed 91 tests, `tests/unit/test_site.py` passed 342 tests, adjacent site/page/member/application/user coverage passed 969 tests, and full unit coverage passed 3438 tests. | Regressing parser-created recent-change rows, constructor validation order, actor/client coherence, flags, revisions, page identity, timestamps, pagination, limit validation, response diagnostics, or adjacent site workflows rejects this local completion claim. | Recent changes and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `Site`, `Client`, and `User` objects only. | Using credentials, cookies, auth JSON, raw recent-change bodies, private edit comments, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, constructor/parser/site/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8a6fcbd fix(site): validate site change actor user ids`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass -k retained_changed_by_ids -q` selected 9 constructor retained-actor-ID tests; 7 malformed or negative retained-ID cases failed before the fix with `DID NOT RAISE`, while the two `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 9 tests after constructor retained-ID validation was added.
- Focused recent-change constructor and parser coverage: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 91 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_site.py -q` passed 342 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 969 tests.
- `uv run pytest tests/unit -q` passed 3438 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `SiteChange(...)` raises `ValueError("changed_by.id must be an integer or None")` when the retained actor ID is `True`, `False`, `"1"`, `1.0`, or `[]`.
- `SiteChange(...)` raises `ValueError("changed_by.id must be non-negative or None")` when the retained actor ID is `-1` or `-100`.
- Malformed or negative retained actor IDs fail before the recent-change row is stored by direct construction.
- Valid retained actor IDs `None` and `0` remain accepted by direct construction.
- Existing malformed `changed_by` values still raise `ValueError("changed_by must be an AbstractUser")`.
- Existing actor/client mismatches still raise `ValueError("changed_by must belong to the site")`.
- Existing flags, revision number, page fullname, page title, comment, timestamp, site, recent-change parser, pagination, limit validation, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw recent-change bodies, private edit comments, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed recent-change rows with corrupted retained actor IDs now fail during construction instead of later consumer logic. Mitigation: those values are impossible actor identity state; failing before storage is deterministic and field-specific.
- Risk: Optional actor IDs could be rejected accidentally. Mitigation: the focused compatibility guard asserts that `None` and `0` remain accepted and preserved.
- Risk: Validation precedence could regress earlier `SiteChange` diagnostics. Mitigation: the retained-ID check runs after actor type validation and before actor/client coherence; recent-change constructor, parser, site, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing `SiteChange` flags, revision number, page fullname, page title, comment, actor object, timestamp, site, actor/client coherence, and parser behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `SiteChange` constructor retained actor user-ID boundary.

## Upstream-Safe Motivation

`SiteChange` is the durable row shape behind browser-free recent-change monitoring, moderation dashboards, audit exports, migration checks, and generated multi-site reports. Parser-created users may legitimately have optional IDs, while direct `User` construction already rejects impossible negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated actor IDs out of stored recent-change rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, actor/client coherence, and recent-change fetch semantics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established recent changes as a practical workflow through retry-aware fetching, pagination, parser diagnostics, response diagnostics, title/page/revision/timestamp/user extraction, direct `SiteChange` constructor validation, actor/client coherence, and adjacent site workflows.
- Existing local drafts covered non-`AbstractUser` actors, actor/client mismatch, direct user constructor ID ranges, page vote constructor user IDs, and private-message participant user IDs; they did not validate corrupted retained `User.id` values at the direct `SiteChange(...)` constructor boundary.
- The focused RED failure showed malformed and negative retained actor IDs could be stored in direct recent-change rows. The GREEN regressions cover constructor malformed/negative rejection, optional-ID and zero-ID constructor compatibility, recent-change parser compatibility, adjacent site workflows, and full unit compatibility.
- This slice only validates retained actor user IDs at the `SiteChange` constructor boundary. It does not change recent-change request construction, parser selectors, flag-code semantics, page fullname parsing, title extraction, comment extraction, revision extraction, timestamp extraction, user parser semantics, response-body validation, `limit` validation, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw recent-change bodies, private edit comments, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained actor IDs instead of requiring concrete regular-user IDs. Recent-change actors can be parsed as deleted, guest, anonymous, system, or otherwise unresolved users, and this constructor slice only rejects malformed or negative retained identity state.
