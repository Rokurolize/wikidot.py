# PR Draft: Validate SiteApplication Constructor User ID Range

## Summary

`SiteApplication(...)` records already validate the parent site, applicant object type, applicant/site client coherence, application text type, accept/decline action-user ID type, action-user name type, action-user ID range, returned action status, `no_application` mappings, and accept-cache invalidation behavior. One constructor gap remained: a valid applicant `User` could be mutated, fixture-loaded, or rehydrated with a negative retained `user.id` and then stored in a new `SiteApplication` row. That corrupted row would not fail until a later accept/decline action, despite parser-created application rows and direct `User` construction already enforcing non-negative user IDs.

This change validates negative retained applicant IDs at the `SiteApplication(...)` constructor boundary. Negative retained applicant IDs now raise `ValueError("application.user.id must be non-negative")`, valid zero applicant IDs remain accepted in direct rows, and action-time validation still owns the stricter applicant ID type/name checks before membership mutation payloads are built.

## Outcome

Direct `SiteApplication(...)` rows cannot store impossible negative applicant user IDs. Valid parser-created rows, same-client direct rows, zero-ID compatibility, malformed site/user/text diagnostics, applicant/site client coherence, accept/decline action preflights, action-status diagnostics, `no_application` mapping, cache behavior, and adjacent site/member/user/private-message workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free pending-application inventories, generated membership ledgers, local fixtures, serialized application rows, migration checks, moderation workflows, or rehydrated `SiteApplication` objects before processing pending applications.

## Current Evidence

Site-application drafts [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [177-pr-site-application-fetch-failure-context.md](177-pr-site-application-fetch-failure-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), and [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md) establish application acquisition, parser diagnostics, constructor field validation, applicant/site coherence, accept/decline behavior, action-user preflight, and cache synchronization as practical workflow surfaces.

Related user-ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), [648-pr-validate-non-negative-site-member-lookup-user-ids.md](648-pr-validate-non-negative-site-member-lookup-user-ids.md), [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md), [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md), [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md), and [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md) establish direct user-ID range validation, QuickModule user-ID range validation, member lookup user-ID filter validation, private-message recipient ID range validation, site invitation target ID range validation, site application action-time applicant ID range validation, and site member role-change user ID range validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 449 validates that `SiteApplication.user` is an `AbstractUser`, but it does not validate retained applicant ID range. Issue 606 validates that the applicant belongs to the parent site client, not the retained ID range. Issue 687 validates negative retained `application.user.id` at the accept/decline action boundary, but a direct `SiteApplication(...)` row could still store the corrupted user until action time. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in an application row.

## Related Issue / Non-Duplicate Analysis

Builds directly on [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), and [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate negative retained applicant IDs inside the existing `SiteApplication` user object validator used by `__post_init__`.
- Reject retained constructor applicant IDs `-1` and `-100` with `ValueError("application.user.id must be non-negative")`.
- Preserve valid retained applicant ID `0` for direct `SiteApplication(...)` construction.
- Keep action-time malformed ID type and malformed name validation in the existing accept/decline helper.
- Preserve existing site validation, applicant object validation, applicant/site client validation, text validation, action-status diagnostics, `no_application` handling, cache behavior, and successful application behavior.

## Type Of Change

- State validation
- Site application constructor hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication(site=site, user=user, text=...)` must reject retained `user.id=-1` and `user.id=-100` with `ValueError("application.user.id must be non-negative")` before storing the application row. |
| R2 | Valid retained applicant ID `0` must remain accepted in direct `SiteApplication(...)` construction. |
| R3 | Existing action-time negative-ID regressions must continue to prove post-construction mutation is rejected before login or AMC request work. |
| R4 | Existing malformed site validation, non-`AbstractUser` applicant validation, applicant/site client validation, text validation, malformed action-user ID/name validation, action-status diagnostics, `no_application` mapping, cache behavior, and adjacent site/member/application/user/private-message workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private applicant data, private application text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, site-application tests, adjacent site/member/application/user/private-message tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative retained applicant IDs fail at the direct constructor boundary. | `test_init_rejects_negative_user_id` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after constructor user-ID range validation was added. | Accepting a negative retained applicant ID, storing the row, or deferring the failure only to `accept()` / `decline()` rejects this local completion claim. | `SiteApplication` constructor | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Valid zero applicant IDs remain valid direct constructor state. | `test_init_accepts_zero_user_id` passed RED and GREEN, asserting the stored applicant ID remains `0`. | Rejecting zero, converting it to `None`, or changing valid row construction rejects this local completion claim. | `SiteApplication` constructor | `tests/unit/test_site_application.py` |
| R3 | Post-construction mutation remains covered at action time. | Existing accept/decline negative-ID tests now construct a valid row, mutate `app.user.id`, and pass by rejecting before login and AMC request work. | Losing action-time mutation coverage, calling `login_check()`, sending `ManageSiteMembershipAction`, or raising returned-status diagnostics rejects this local completion claim. | `SiteApplication.accept()` / `decline()` | `tests/unit/test_site_application.py` |
| R4 | Existing site-application behavior and adjacent workflows remain green. | `tests/unit/test_site_application.py` passed 61 tests, adjacent site/member/application/user/private-message coverage passed 733 tests, and full unit coverage passed 3402 tests. | Regressing parser-created applications, constructor site/user/text diagnostics, client coherence, action preflights, action-status handling, cache behavior, site/member/user/private-message workflows, or any unit test rejects this local completion claim. | Site application and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic sites, applicants, and safe application text. | Using credentials, cookies, auth JSON, private applicant names, private application text, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site-application/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `cf27a37 fix(site_application): validate constructor user id range`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass -k user_id -q` selected 3 constructor user-ID tests; 2 negative retained-applicant-ID cases failed before the fix with `DID NOT RAISE`, while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 3 tests after constructor user-ID range validation was added.
- `uv run ruff format src/wikidot/module/site_application.py tests/unit/test_site_application.py` left both files unchanged.
- `uv run pytest tests/unit/test_site_application.py -q` passed 61 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py tests/unit/test_private_message.py -q` passed 733 tests.
- `uv run pytest tests/unit -q` passed 3402 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `SiteApplication(...)` raises `ValueError("application.user.id must be non-negative")` when the applicant user's retained `id` is `-1` or `-100`.
- Negative retained applicant IDs fail before the application row is stored by direct construction.
- Valid retained applicant ID `0` remains accepted by direct construction.
- Existing action-time accept/decline negative-ID tests still prove post-construction mutation fails before `site.client.login_check()`, `site.amc_request(...)`, returned action-status parsing, `no_application` mapping, or member-cache mutation.
- Existing malformed site validation, non-`AbstractUser` applicant validation, applicant/site client ownership validation, text validation, action-user ID type validation, action-user name validation, valid accept/decline actions, returned application action-status validation, `no_application` mapping, accept cache invalidation, decline cache preservation, site member workflows, site invitation workflows, user behavior, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private applicant data, private application text, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated application rows with negative retained applicant IDs now fail during construction instead of later accept/decline work. Mitigation: negative user IDs are impossible identity state; failing before storing corrupted application rows is more deterministic.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID constructor guard asserts `app.user.id == 0`.
- Risk: Action-time mutation coverage could be lost after constructor hardening. Mitigation: the accept/decline negative-ID tests now construct a valid row first and mutate `app.user.id` afterward.
- Risk: Validation precedence could regress earlier application diagnostics. Mitigation: the constructor range check still runs after the existing `AbstractUser` check, while stricter ID type/name checks remain in the existing action helper; the site-application, adjacent, and full tests remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing site-application site validation, applicant object validation, applicant/site client validation, text validation, action-user ID type validation, action-user name validation, action-status validation, `no_application` handling, and cache behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `SiteApplication` constructor user-ID range boundary.

## Upstream-Safe Motivation

`SiteApplication` is the durable row shape behind pending-application inventories, membership ledgers, moderation workflows, and accept/decline automation. Parser-created application users come from structured printuser parsing and direct `User` construction already rejects negative IDs. Constructor-side range validation keeps corrupted fixture-loaded or rehydrated applicant identity out of stored application rows while preserving zero-ID compatibility, valid parser-created rows, client coherence, text validation, and action-time mutation preflights.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site applications as a practical workflow through application-list retry, parser diagnostics, response-body diagnostics, applicant field validation, applicant/site client validation, accept/decline action-status validation, applicant action-time ID range validation, and accept member-cache invalidation.
- Existing local drafts covered non-`AbstractUser` applicants, malformed action-time applicant ID types, malformed action-time applicant names, applicant client mismatch, direct user constructor ID ranges, QuickModule user IDs, member lookup user-ID filters, private-message send recipient ID ranges, site invitation target ID ranges, and site-application action-time applicant ID ranges; they did not validate negative retained `User.id` values at the direct `SiteApplication(...)` constructor boundary.
- The focused RED failure showed negative retained applicant IDs could be stored in direct application rows. The GREEN regressions cover constructor negative rejection, zero-ID constructor compatibility, action-time post-construction mutation coverage, site-application behavior, adjacent site/member/application/user/private-message workflows, and full unit compatibility.
- This slice only validates negative retained applicant IDs at the `SiteApplication` constructor boundary. It does not change application-list parsing, site invitation actions, site member role changes, member lookup filters, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private application text, private applicant data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally extends `_validate_site_application_user_object(...)` instead of calling the full action helper from `__post_init__`. The constructor now rejects impossible negative IDs while the accept/decline path continues to own stricter payload-specific ID type and applicant-name requirements.
