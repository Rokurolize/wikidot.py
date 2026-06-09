# PR Draft: Validate SiteMember Role-Change User ID Range

## Summary

`SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` already validate action type, site object state, stored member user object type, stored member user ID type, stored member user name type, member/site client coherence, returned action status, mapped role-change errors, and role-cache invalidation behavior. The shared role-change path still accepted a retained `member.user.id` that was an integer below zero after a valid `User` was mutated, fixture-loaded, or rehydrated. That invalid retained ID could reach login, `ManageSiteMembershipAction` request construction, mocked AMC handling, returned action-status diagnostics, or role-cache decisions instead of producing deterministic local member-user-ID validation.

This change validates the retained site-member action user ID range before login or AMC request work. Negative retained member user IDs now raise `ValueError("member.user.id must be non-negative")`, valid zero member user IDs remain accepted for role-change payloads, and successful role changes still use the existing `ManageSiteMembershipAction` payload, member/site client validation, action-status validation, mapped target errors, and role-cache behavior.

## Outcome

Site member role changes no longer authenticate, build `user_id` payloads, or diagnose returned action-status failures through impossible negative retained member user IDs. Valid moderator/admin promotions and removals, zero-ID compatibility, malformed member-user validation, member/site client validation, mapped target errors, action-status diagnostics, role-cache invalidation, and adjacent site/member/application/user/private-message workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free site administration, `site.members`, `site.admins`, `site.moderators`, generated membership ledgers, moderation workflows, migration checks, local fixtures, serialized member records, or rehydrated `SiteMember` objects before calling role-change helpers.

## Current Evidence

Site-member drafts [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [541-pr-validate-site-member-get-site.md](541-pr-validate-site-member-get-site.md), and [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md) establish member-list acquisition, role-change action-status diagnostics, action-user preflight, direct member row state, site validation, member/site coherence, and role-cache synchronization as practical mutation-boundary surfaces.

Related user-ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), [648-pr-validate-non-negative-site-member-lookup-user-ids.md](648-pr-validate-non-negative-site-member-lookup-user-ids.md), [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md), [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md), and [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md) establish direct user-ID range validation, QuickModule user-ID range validation, member lookup user-ID filter validation, private-message recipient ID range validation, site invitation target ID range validation, and site application applicant ID range validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 410 validates that the role-change user is an `AbstractUser`, that `member.user.id` is an integer and not a boolean, and that `member.user.name` is a string, but it still accepts negative integer member user IDs. Issue 605 validates that the member user belongs to the parent site client, not the retained ID range. Issue 647 validates direct `User` and `DeletedUser` construction, but explicitly leaves downstream mutable user-state action preflights for separate duplicate-checked slices. Issues 685, 686, and 687 validate the same retained user-ID range principle for private messages, site invitations, and site applications; they do not cover member role-change mutation payloads.

## Related Issue / Non-Duplicate Analysis

Builds directly on [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md), [686-pr-validate-site-invite-user-id-range.md](686-pr-validate-site-invite-user-id-range.md), and [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `member.user.id` is non-negative inside the existing site-member action-user preflight.
- Reject retained member user IDs `-1` and `-100` with `ValueError("member.user.id must be non-negative")` before login or AMC request work.
- Preserve valid retained member user ID `0` for all four role-change helpers and submit it as `user_id: 0`.
- Preserve existing site validation, action validation, member user object validation, member user ID type validation, member user name validation, member/site client validation, action-status diagnostics, mapped target errors, role-cache invalidation, and successful role-change behavior.

## Type Of Change

- State validation
- Site member mutation-boundary hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` must reject retained `member.user.id=-1` and `member.user.id=-100` with `ValueError("member.user.id must be non-negative")` before login, AMC request construction, action-status parsing, mapped target errors, or role-cache mutation uses the value. |
| R2 | Valid retained member user ID `0` must remain accepted for all four role-change helpers and must produce a request payload with `user_id: 0`. |
| R3 | Existing malformed site validation, invalid action validation, non-`AbstractUser` member user validation, malformed member user ID type validation, malformed member user name validation, member/site client validation, action-status diagnostics, mapped target errors, role-cache invalidation, and adjacent site/member/application/user/private-message workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, site-member role-change tests, site-member tests, adjacent site/member/application/user/private-message tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative retained member user IDs fail before login, request construction, action-status parsing, mapped target errors, diagnostic formatting, or cache mutation. | `test_change_group_rejects_negative_user_id_before_login` failed RED for `-1` and `-100` across all four public role-change helpers, then passed GREEN after member user ID range validation was added. | Calling `login_check()`, sending `ManageSiteMembershipAction`, submitting negative `user_id`, mutating role caches, or raising post-request status errors rejects this local completion claim. | `SiteMember` role-change action-user preflight | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Valid zero member user IDs remain valid role-change payload values. | `test_change_group_accepts_zero_user_id` passed RED and GREEN for all four public role-change helpers, asserting each request payload uses `user_id == 0`. | Rejecting zero, converting it to `None`, stringifying it unexpectedly, or changing valid role-change payload shape rejects this local completion claim. | `SiteMember` role-change request payloads | `tests/unit/test_site_member.py` |
| R3 | Existing site-member behavior and adjacent workflows remain green. | `TestSiteMemberChangeGroup` passed 33 tests, `tests/unit/test_site_member.py` passed 76 tests, adjacent site/member/application/user/private-message coverage passed 730 tests, and full unit coverage passed 3399 tests. | Regressing site validation, action validation, member user type validation, integer/bool validation, member user name validation, member/site client validation, status diagnostics, mapped target errors, role-cache invalidation, site workflows, application workflows, user behavior, private-message behavior, or any unit test rejects this local completion claim. | Site member and adjacent workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic sites and users. | Using credentials, cookies, auth JSON, private member names, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, role-change/site-member/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `fa4a7e7 fix(site_member): validate action user id range`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup -k user_id -q` selected 12 role-change user-ID tests; 8 negative retained-member-ID cases failed before the fix by reaching mocked action-status handling and raising `WikidotStatusCodeException`, while 4 zero-ID compatibility guards passed.
- GREEN: the same focused command passed 12 tests after member user ID range validation was added.
- `uv run ruff format src/wikidot/module/site_member.py tests/unit/test_site_member.py` reformatted 1 file and left 1 file unchanged.
- `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup -q` passed 33 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 76 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py tests/unit/test_private_message.py -q` passed 730 tests.
- `uv run pytest tests/unit -q` passed 3399 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` raise `ValueError("member.user.id must be non-negative")` when the member user's retained `id` is `-1` or `-100`.
- Negative retained member user IDs fail before `site.client.login_check()`, `site.amc_request(...)`, returned action-status parsing, mapped target errors, user-based diagnostics, or role-cache mutation.
- Valid retained member user ID `0` still produces role-change request payloads with `user_id == 0`.
- Existing malformed site validation, invalid action validation, non-`AbstractUser` member user validation, malformed member user ID type validation, malformed member user name validation, member/site client ownership validation, valid moderator/admin promotions and removals, returned action-status validation, mapped target errors, role-cache invalidation, site invitation workflows, site application workflows, user behavior, and private-message behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated member rows with negative retained member user IDs now fail before role-change actions. Mitigation: negative user IDs are impossible identity state; deterministic local validation is safer than invalid membership mutation payloads.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID guard asserts `user_id == 0` for all four public role-change helpers.
- Risk: Validation precedence could regress earlier member diagnostics. Mitigation: the new range check runs after the existing integer/non-boolean member user ID type check and before member user name/client/login work; the existing role-change, site-member, adjacent, and full tests remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing site-member site validation, action validation, member user object validation, member user ID type validation, member user name validation, member/site client validation, action-status validation, mapped target errors, and role-cache invalidation remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered site-member role-change user-ID range boundary.

## Upstream-Safe Motivation

Site member role changes route Wikidot's `ManageSiteMembershipAction` mutation through the stored member user's retained ID. That ID should satisfy the same non-negative identity contract before it leaves local state, even if a valid `User` was later mutated or rehydrated. Validating stored member identity prevents corrupted fixtures or generated records from becoming invalid role-change payloads while preserving zero-ID compatibility, valid promotions/removals, member/site client checks, action-status diagnostics, mapped target errors, and role-cache behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site members as a practical workflow through member-list retry, parser diagnostics, response-body diagnostics, role-change action-status validation, action-user input validation, member/site client validation, and role-cache invalidation.
- Existing local drafts covered non-`AbstractUser` member users, malformed member user ID types, malformed member user names, member/site client mismatch, direct user constructor ID ranges, QuickModule user IDs, member lookup user-ID filters, private-message send recipient ID ranges, site invitation target ID ranges, and site application applicant ID ranges; they did not validate negative retained `User.id` values at the site-member role-change action boundary.
- The focused RED failure showed negative retained member user IDs reached mocked role-change handling and action-status diagnostics instead of deterministic member-user-ID diagnostics. The GREEN regressions cover negative rejection across all four role-change helpers, zero-ID compatibility across all four helpers, role-change behavior, adjacent site/member/application/user/private-message workflows, and full unit compatibility.
- This slice only validates retained member user IDs at the site-member role-change boundary. It does not change member-list parsing, site invitation actions, site application actions, member lookup filters, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private member data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally extends the existing `_validate_site_member_action_user(...)` helper instead of adding per-method validation. The helper already owns member user object, ID type, and name preflight for role-change payload construction and diagnostics, so the range check belongs next to those field contracts.
