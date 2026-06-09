# PR Draft: Validate Site.invite_user User ID Range

## Summary

`Site.invite_user(user, text)` already validates invitation text, invitation target object type, invitation target ID type, invitation target name type, target/client coherence, returned action status, direct user record IDs at construction, and site member lookup user-ID filters. The invitation path still accepted a retained `user.id` that was an integer below zero after a valid `User` was mutated, fixture-loaded, or rehydrated. That invalid retained ID could reach login, `ManageSiteMembershipAction` request construction, mocked AMC handling, or returned invitation action-status diagnostics instead of producing deterministic local target-ID validation.

This change validates the retained site invitation target ID range before login or AMC request work. Negative retained invitation target IDs now raise `ValueError("user.id must be non-negative")`, valid zero target IDs remain accepted, and successful invitations still use the existing `ManageSiteMembershipAction` payload, target client validation, text validation, returned action-status validation, duplicate-invitation mappings, and no-return successful behavior.

## Outcome

Site invitations no longer authenticate, build `user_id` payloads, or diagnose invitation action-status failures through impossible negative retained user IDs. Valid invitations, zero-ID compatibility, malformed target validation, target client validation, text validation, duplicate-invitation mappings, action-status diagnostics, and adjacent site/member/application/user/private-message workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free site invitations, generated onboarding jobs, moderation tooling, migration notifications, audit-driven membership operations, local fixtures, serialized user records, or rehydrated `User` objects before calling `Site.invite_user(...)`.

## Current Evidence

Site invitation drafts [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), and [619-pr-validate-site-invite-user-client.md](619-pr-validate-site-invite-user-client.md) establish `Site.invite_user(...)`, invitation payloads, text input validation, target user validation, target client coherence, duplicate-invitation mappings, and returned action-status diagnostics as practical mutation-boundary surfaces.

Related user-ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), [648-pr-validate-non-negative-site-member-lookup-user-ids.md](648-pr-validate-non-negative-site-member-lookup-user-ids.md), and [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md) establish direct user-ID range validation, QuickModule user-ID range validation, member lookup user-ID filter validation, and private-message send recipient ID range validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 370 validates the invitation target is a `User`, that `user.id` is an integer and not a boolean, and that `user.name` is a string, but it still accepts negative integer target IDs. Issue 619 validates that the target user belongs to the inviting site client, not the retained ID range. Issue 647 validates direct `User` and `DeletedUser` construction, but explicitly leaves downstream mutable user-state action preflights for separate duplicate-checked slices. Issue 648 validates a read-only `Site.member_lookup(..., user_id=...)` filter, not the invitation mutation target. Issue 685 validates the same retained user-ID range principle for private messages, not site invitations.

## Related Issue / Non-Duplicate Analysis

Builds directly on [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), [619-pr-validate-site-invite-user-client.md](619-pr-validate-site-invite-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), and [685-pr-validate-private-message-send-recipient-id-range.md](685-pr-validate-private-message-send-recipient-id-range.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `user.id` is non-negative inside the existing site invitation target preflight.
- Reject retained invitation target IDs `-1` and `-100` with `ValueError("user.id must be non-negative")` before login or AMC request work.
- Preserve valid retained target ID `0` and submit it as `user_id: 0`.
- Preserve existing target object validation, target ID type validation, target name validation, target client validation, invitation text validation, action-status diagnostics, duplicate-invitation mappings, other-error reraising, and successful invitation behavior.

## Type Of Change

- State validation
- Site invitation mutation-boundary hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.invite_user(...)` must reject retained `user.id=-1` and `user.id=-100` with `ValueError("user.id must be non-negative")` before login, AMC request construction, action-status parsing, duplicate-invitation mappings, or invitation diagnostics use the value. |
| R2 | Valid retained target ID `0` must remain accepted and must produce a request payload with `user_id: 0`. |
| R3 | Existing non-`User` target validation, malformed target ID type validation, malformed target name validation, target client validation, invitation text validation, action-status diagnostics, duplicate mappings, other-error reraising, and adjacent site/member/application/user/private-message workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, private invitation text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, site invitation tests, site tests, adjacent site/member/application/user/private-message tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative retained invitation target IDs fail before login, request construction, action-status parsing, or diagnostic formatting. | `test_invite_user_rejects_negative_user_id_before_login` failed RED for `-1` and `-100`, then passed GREEN after invitation target ID range validation was added. | Calling `login_check()`, sending `ManageSiteMembershipAction`, submitting negative `user_id`, or raising post-request status errors rejects this local completion claim. | `Site.invite_user(...)` target preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid zero invitation target IDs remain valid payload values. | `test_invite_user_accepts_zero_user_id` passed RED and GREEN, asserting the request payload uses `user_id == 0`. | Rejecting zero, converting it to `None`, stringifying it unexpectedly, or changing valid invitation payload shape rejects this local completion claim. | `Site.invite_user(...)` request payload | `tests/unit/test_site.py` |
| R3 | Existing invitation behavior and adjacent workflows remain green. | `TestSiteInviteUser` passed 15 tests, `tests/unit/test_site.py` passed 333 tests, adjacent site/member/application/user/private-message coverage passed 713 tests, and full unit coverage passed 3382 tests. | Regressing text validation, target type validation, integer/bool validation, target name validation, target client validation, invitation status diagnostics, duplicate mappings, site member/application workflows, user behavior, private-message send behavior, or any unit test rejects this local completion claim. | Site invitation and adjacent workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic users, sites, and safe invitation text. | Using credentials, cookies, auth JSON, private member data, private invitation text, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, invitation/site/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ba33ae4 fix(site): validate invite user id range`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser -k user_id -q` selected 3 tests; 2 negative retained-target-ID cases failed before the fix by reaching mocked invitation action-status handling and raising `WikidotStatusCodeException`, while 1 zero-ID compatibility guard passed.
- GREEN: the same focused command passed 3 tests after invitation target ID range validation was added.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_site.py::TestSiteInviteUser -q` passed 15 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 333 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py tests/unit/test_private_message.py -q` passed 713 tests.
- `uv run pytest tests/unit -q` passed 3382 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `Site.invite_user(...)` raises `ValueError("user.id must be non-negative")` when the target user's retained `id` is `-1` or `-100`.
- Negative retained target IDs fail before `site.client.login_check()`, `site.amc_request(...)`, `site.client.amc_client.request(...)`, returned action-status parsing, duplicate-invitation mappings, or target-based invitation diagnostics.
- Valid retained target ID `0` still produces a request payload with `user_id == 0`.
- Existing non-`User` target validation, malformed target ID type validation, malformed target name validation, target client ownership validation, text validation, valid invitations, returned invitation action-status validation, duplicate-invitation mappings, other-error reraising, site member workflows, site application workflows, user behavior, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, private invitation text, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rehydrated users with negative retained IDs now fail before site invitations. Mitigation: negative user IDs are impossible identity state; deterministic local validation is safer than invalid membership mutation payloads.
- Risk: Valid zero IDs could be accidentally rejected if validation were changed to positive-only. Mitigation: the focused zero-ID guard asserts `user_id == 0`.
- Risk: Validation precedence could regress earlier invitation diagnostics. Mitigation: the new range check runs after the existing integer/non-boolean ID type check and before target name/client/login work; the existing invitation, site, adjacent, and full tests remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing site invitation text validation, target object validation, target ID type validation, target name validation, target client validation, action-status validation, duplicate-invitation mappings, and other-error reraising remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered site invitation target-ID range boundary.

## Upstream-Safe Motivation

Site invitations route Wikidot's `ManageSiteMembershipAction` mutation through the target user's retained ID. That ID should satisfy the same non-negative identity contract before it leaves local state, even if a valid `User` was later mutated or rehydrated. Validating stored target identity prevents corrupted fixtures or generated records from becoming invalid membership mutation payloads while preserving zero-ID compatibility, valid invitations, target client checks, text validation, duplicate mappings, and returned action-status diagnostics.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site invitations as a practical workflow through invitation action-status validation, invitation text validation, target input validation, target client validation, duplicate-invitation mappings, and adjacent site member/application hardening.
- Existing local drafts covered non-`User` targets, malformed target ID types, malformed target names, target client mismatch, direct user constructor ID ranges, QuickModule user IDs, member lookup user-ID filters, and private-message send recipient ID ranges; they did not validate negative retained `User.id` values at the invitation action boundary.
- The focused RED failure showed negative retained invitation target IDs reached mocked invitation handling and action-status diagnostics instead of deterministic target-ID diagnostics. The GREEN regressions cover negative rejection, zero-ID compatibility, invitation behavior, adjacent site/member/application/user/private-message workflows, and full unit compatibility.
- This slice only validates retained target IDs at the site invitation boundary. It does not change member-list parsing, site application parsing, application accept/decline actions, member permission changes, site member lookup filters, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private invitation text, private member data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally extends the existing `_validate_site_invitation_user(...)` helper instead of adding a second invite-only validation path. The helper already owns target object, ID type, and name preflight for invitation payload construction and diagnostics, so the range check belongs next to those field contracts.
