# PR Draft: Validate SiteApplication Applicant User ID Range

## Summary

`SiteApplication.accept()` and `SiteApplication.decline()` already validate action type, site object state, applicant object type, applicant ID type, applicant name type, applicant/site client coherence, returned action status, `no_application` mappings, direct user record IDs at construction, and accept-cache invalidation behavior. The shared application action path still accepted a retained `application.user.id` that was an integer below zero after a valid `User` was mutated, fixture-loaded, or rehydrated. That invalid retained ID could reach login, `ManageSiteMembershipAction` request construction, mocked AMC handling, returned action-status diagnostics, or member-cache decisions instead of producing deterministic local applicant-ID validation.

This change validates the retained site-application applicant ID range before login or AMC request work. Negative retained applicant IDs now raise `ValueError("application.user.id must be non-negative")`, valid zero applicant IDs remain accepted for accept payloads, and successful accept/decline actions still use the existing `ManageSiteMembershipAction` payload, applicant client validation, action-status validation, `no_application` handling, and cache behavior.

## Outcome

Site application accept/decline actions no longer authenticate, build `user_id` payloads, or diagnose returned action-status failures through impossible negative retained applicant IDs. Valid application actions, zero-ID accept compatibility, malformed applicant validation, applicant client validation, `no_application` mapping, action-status diagnostics, accept cache invalidation, decline cache preservation, and adjacent site/member/application/user/private-message workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free pending-application inventories, accept/decline automation, generated membership ledgers, moderation workflows, migration checks, local fixtures, serialized application records, or rehydrated `SiteApplication` objects before calling `accept()` or `decline()`.

## Current Evidence

Site-application drafts [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [177-pr-site-application-fetch-failure-context.md](177-pr-site-application-fetch-failure-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), and [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md) establish application acquisition, parser diagnostics, response diagnostics, accept/decline behavior, applicant preflight, applicant/site coherence, and cache synchronization as practical mutation-boundary surfaces.

Related user-ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), [648-pr-validate-non-negative-site-member-lookup-user-ids.md](648-pr-validate-non-negative-site-member-lookup-user-ids.md), [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md), and [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md) establish direct user-ID range validation, QuickModule user-ID range validation, member lookup user-ID filter validation, private-message recipient ID range validation, and site invitation target ID range validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 371 validates that the action applicant is an `AbstractUser`, that `application.user.id` is an integer and not a boolean, and that `application.user.name` is a string, but it still accepts negative integer applicant IDs. Issue 606 validates that the applicant belongs to the parent site client, not the retained ID range. Issue 647 validates direct `User` and `DeletedUser` construction, but explicitly leaves downstream mutable user-state action preflights for separate duplicate-checked slices. Issue 685 validates the same retained user-ID range principle for private-message sends, and Issue 686 validates it for site invitations; neither covers pending-application accept/decline mutation payloads.

## Related Issue / Non-Duplicate Analysis

Builds directly on [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md), and [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `application.user.id` is non-negative inside the existing site-application applicant preflight.
- Reject retained applicant IDs `-1` and `-100` with `ValueError("application.user.id must be non-negative")` before login or AMC request work.
- Preserve valid retained applicant ID `0` for accept actions and submit it as `user_id: 0`.
- Preserve existing site validation, action validation, applicant object validation, applicant ID type validation, applicant name validation, applicant client validation, action-status diagnostics, `no_application` mapping, accept cache invalidation, decline cache preservation, and successful application action behavior.

## Type Of Change

- State validation
- Site application mutation-boundary hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication.accept()` and `SiteApplication.decline()` must reject retained `application.user.id=-1` and `application.user.id=-100` with `ValueError("application.user.id must be non-negative")` before login, AMC request construction, action-status parsing, `no_application` mapping, or member-cache mutation uses the value. |
| R2 | Valid retained applicant ID `0` must remain accepted for accept actions and must produce a request payload with `user_id: 0`. |
| R3 | Existing malformed site validation, invalid action validation, non-`AbstractUser` applicant validation, malformed applicant ID type validation, malformed applicant name validation, applicant client validation, action-status diagnostics, `no_application` mapping, accept cache invalidation, decline cache preservation, and adjacent site/member/application/user/private-message workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private applicant data, private application text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, site-application tests, adjacent site/member/application/user/private-message tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative retained applicant IDs fail before login, request construction, action-status parsing, `no_application` mapping, diagnostic formatting, or cache mutation. | `test_accept_rejects_negative_user_id_before_login` failed RED for `-1` and `-100`, then passed GREEN after applicant ID range validation was added. `test_decline_rejects_negative_user_id_before_login` also passes for `-1` and `-100` against the shared preflight. | Calling `login_check()`, sending `ManageSiteMembershipAction`, submitting negative `user_id`, mutating member cache, or raising post-request status errors rejects this local completion claim. | `SiteApplication.accept()` / `SiteApplication.decline()` applicant preflight | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Valid zero applicant IDs remain valid accept payload values. | `test_accept_accepts_zero_user_id` passed RED and GREEN, asserting the request payload uses `user_id == 0`. | Rejecting zero, converting it to `None`, stringifying it unexpectedly, or changing valid accept payload shape rejects this local completion claim. | `SiteApplication.accept()` request payload | `tests/unit/test_site_application.py` |
| R3 | Existing application behavior and adjacent workflows remain green. | `tests/unit/test_site_application.py` passed 58 tests, adjacent site/member/application/user/private-message coverage passed 718 tests, and full unit coverage passed 3387 tests. | Regressing site validation, action validation, applicant type validation, integer/bool validation, applicant name validation, applicant client validation, application status diagnostics, `no_application` mapping, accept cache invalidation, decline cache preservation, site workflows, member workflows, user behavior, private-message send behavior, or any unit test rejects this local completion claim. | Site application and adjacent workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic sites, applicants, and safe application text. | Using credentials, cookies, auth JSON, private applicant names, private application text, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site-application/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c060a78 fix(site_application): validate application user id range`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess -k user_id -q` selected the original 3 accept-path user-ID tests; 2 negative retained-applicant-ID cases failed before the fix by reaching mocked application action-status handling and raising `WikidotStatusCodeException`, while 1 zero-ID compatibility guard passed.
- GREEN: after applicant ID range validation and decline-path regression coverage were added, the focused command selected 5 tests and passed.
- `uv run ruff format src/wikidot/module/site_application.py tests/unit/test_site_application.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_site_application.py -q` passed 58 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py tests/unit/test_private_message.py -q` passed 718 tests.
- `uv run pytest tests/unit -q` passed 3387 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `SiteApplication.accept()` and `SiteApplication.decline()` raise `ValueError("application.user.id must be non-negative")` when the applicant user's retained `id` is `-1` or `-100`.
- Negative retained applicant IDs fail before `site.client.login_check()`, `site.amc_request(...)`, returned action-status parsing, `no_application` mapping, applicant-based diagnostics, or member-cache mutation.
- Valid retained applicant ID `0` still produces an accept request payload with `user_id == 0`.
- Existing malformed site validation, invalid action validation, non-`AbstractUser` applicant validation, malformed applicant ID type validation, malformed applicant name validation, applicant client ownership validation, valid accept/decline actions, returned application action-status validation, `no_application` mapping, accept cache invalidation, decline cache preservation, site member workflows, site invitation workflows, user behavior, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private applicant data, private application text, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated application rows with negative retained applicant IDs now fail before accept/decline actions. Mitigation: negative user IDs are impossible identity state; deterministic local validation is safer than invalid membership mutation payloads.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID guard asserts `user_id == 0`.
- Risk: Validation precedence could regress earlier application diagnostics. Mitigation: the new range check runs after the existing integer/non-boolean applicant ID type check and before applicant name/client/login work; the existing application, adjacent, and full tests remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing site-application site validation, action validation, applicant object validation, applicant ID type validation, applicant name validation, applicant client validation, action-status validation, `no_application` handling, accept cache invalidation, and decline cache preservation remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered site-application applicant-ID range boundary.

## Upstream-Safe Motivation

Pending application actions route Wikidot's `ManageSiteMembershipAction` mutation through the applicant user's retained ID. That ID should satisfy the same non-negative identity contract before it leaves local state, even if a valid `User` was later mutated or rehydrated. Validating stored applicant identity prevents corrupted fixtures or generated records from becoming invalid application action payloads while preserving zero-ID compatibility, valid accept/decline actions, applicant client checks, action-status diagnostics, `no_application` mapping, and member-cache behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site applications as a practical workflow through application list retry, parser diagnostics, response-body diagnostics, accept/decline action-status validation, applicant input validation, applicant client validation, and accept member-cache invalidation.
- Existing local drafts covered non-`AbstractUser` applicants, malformed applicant ID types, malformed applicant names, applicant client mismatch, direct user constructor ID ranges, QuickModule user IDs, member lookup user-ID filters, private-message send recipient ID ranges, and site invitation target ID ranges; they did not validate negative retained `User.id` values at the site-application action boundary.
- The focused RED failure showed negative retained applicant IDs reached mocked application handling and action-status diagnostics instead of deterministic applicant-ID diagnostics. The final GREEN regressions cover negative accept/decline rejection, zero-ID accept compatibility, application behavior, adjacent site/member/application/user/private-message workflows, and full unit compatibility.
- This slice only validates retained applicant IDs at the site-application accept/decline boundary. It does not change application-list parsing, site invitation actions, member permission changes, site member lookup filters, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private application text, private applicant data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally extends the existing `_validate_site_application_user(...)` helper instead of adding an accept-only or decline-only validation path. The helper already owns applicant object, ID type, and name preflight for application payload construction and diagnostics, so the range check belongs next to those field contracts.
