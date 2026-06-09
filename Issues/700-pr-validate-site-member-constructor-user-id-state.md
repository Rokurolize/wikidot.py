# PR Draft: Validate SiteMember Constructor User ID State

## Summary

`SiteMember(...)` records already validate the parent site, member user object type, member/site client coherence, joined-at type, constructor negative member ID range, role-change action-user ID type, action-user name type, action-user ID range, returned action status, mapped target errors, and role-cache behavior. One constructor retained-state gap remained: a valid member `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `user.id` state and then stored in a new `SiteMember` row.

This change validates retained member user ID shape at the `SiteMember(...)` constructor boundary. Malformed non-`None` retained member IDs now raise `ValueError("member.user.id must be an integer or None")`, negative retained member IDs continue to raise `ValueError("member.user.id must be non-negative")`, and valid optional `None` plus zero-ID compatibility remain accepted at construction time.

## Outcome

Direct `SiteMember(...)` rows cannot store malformed retained member user IDs. Valid parser-created rows, same-client direct rows, missing member IDs, zero-ID compatibility, malformed site/user/joined-at diagnostics, member/site client coherence, role-change action preflights, action-status diagnostics, mapped target errors, role-cache behavior, and adjacent site/application/user/private-message workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free member inventories, generated membership ledgers, local fixtures, serialized member rows, migration checks, moderation workflows, site-access audits, or rehydrated `SiteMember` objects before role administration.

## Current Evidence

Site-member drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [499-pr-validate-site-member-joined-at-field.md](499-pr-validate-site-member-joined-at-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [541-pr-validate-site-member-get-site.md](541-pr-validate-site-member-get-site.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md), and [690-pr-validate-site-member-constructor-user-id-range.md](690-pr-validate-site-member-constructor-user-id-range.md) establish member acquisition, parser diagnostics, constructor field validation, member/site coherence, role-change behavior, action-user preflight, constructor range validation, and role-cache synchronization as practical workflow surfaces.

Related retained user-ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md), [696-pr-validate-forum-post-actor-user-id-state.md](696-pr-validate-forum-post-actor-user-id-state.md), [697-pr-validate-forum-post-revision-creator-user-id-state.md](697-pr-validate-forum-post-revision-creator-user-id-state.md), [698-pr-validate-page-metadata-user-id-state.md](698-pr-validate-page-metadata-user-id-state.md), and [699-pr-validate-site-application-constructor-user-id-state.md](699-pr-validate-site-application-constructor-user-id-state.md) establish direct user-ID validation and adjacent retained mutable user-state validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 448 validates that `SiteMember.user` is an `AbstractUser`, but it does not validate retained member ID shape. Issue 605 validates that the member belongs to the parent site client, not the retained ID shape or range. Issue 688 validates malformed and negative retained `member.user.id` at the role-change action boundary, but a direct `SiteMember(...)` row could still store corrupted member ID state until action time. Issue 690 validates negative retained member IDs at construction time, but it did not reject malformed non-`None` retained member IDs such as booleans, numeric strings, floats, or lists. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in a member row. Issue 699 validates the adjacent `SiteApplication` constructor boundary, not site members.

## Related Issue / Non-Duplicate Analysis

Builds directly on [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [688-pr-validate-site-member-action-user-id-range.md](688-pr-validate-site-member-action-user-id-range.md), [690-pr-validate-site-member-constructor-user-id-range.md](690-pr-validate-site-member-constructor-user-id-range.md), and [699-pr-validate-site-application-constructor-user-id-state.md](699-pr-validate-site-application-constructor-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `member.user.id` shape inside the existing `SiteMember` user object validator used by `__post_init__`.
- Reject retained constructor member IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("member.user.id must be an integer or None")`.
- Preserve retained constructor member IDs `None` and `0`.
- Preserve the existing negative retained member ID diagnostic `ValueError("member.user.id must be non-negative")`.
- Keep action-time malformed ID type and malformed name validation in the existing role-change helper.
- Preserve existing site validation, member object validation, member/site client validation, joined-at validation, action-status diagnostics, mapped target errors, role-cache behavior, and successful role-change behavior.

## Type Of Change

- State validation
- Site member constructor hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember(site=site, user=user, joined_at=...)` must reject retained member `user.id` values `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("member.user.id must be an integer or None")` before storing the member row. |
| R2 | Valid retained member IDs `None` and `0` must remain accepted in direct `SiteMember(...)` construction. |
| R3 | Existing constructor negative-ID validation must continue to reject retained member IDs `-1` and `-100` with `ValueError("member.user.id must be non-negative")`. |
| R4 | Existing action-time malformed-ID, missing-ID, malformed-name, and post-construction mutation preflights must continue to reject before login or AMC request work. |
| R5 | Existing malformed site validation, non-`AbstractUser` member validation, member/site client validation, joined-at validation, action-status diagnostics, mapped target errors, role-cache behavior, and adjacent site/member/application/user/private-message workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, site-member tests, adjacent site/member/application/user/private-message tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained member IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_user_id` failed RED for five malformed retained-ID cases with `DID NOT RAISE`, then passed GREEN after constructor user-ID state validation was added. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure only to role-change helpers rejects this local completion claim. | `SiteMember` constructor | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Optional missing and zero member IDs remain compatible constructor state. | `test_init_accepts_optional_retained_user_id` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring a concrete regular-user ID rejects this local completion claim. | `SiteMember` constructor | `tests/unit/test_site_member.py` |
| R3 | Negative retained member IDs still fail at the direct constructor boundary. | Existing `test_init_rejects_negative_user_id` passed after the new validator preserved the prior negative-ID diagnostic and behavior. | Accepting negative retained member IDs, storing the row, or changing the existing negative diagnostic rejects this local completion claim. | `SiteMember` constructor | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R4 | Action-time preflights still defend post-construction mutation before side effects. | `test_change_group_rejects_malformed_user_before_login` now constructs a valid row, mutates the retained user state, and passes by rejecting before `login_check()` or AMC request work. Existing negative-ID action-time tests also remain green. | Losing action-time mutation coverage, calling `login_check()`, sending `ManageSiteMembershipAction`, mutating role caches, or raising returned-status diagnostics rejects this local completion claim. | `SiteMember` role-change helpers | `tests/unit/test_site_member.py` |
| R5 | Existing site-member behavior and adjacent workflows remain green. | `tests/unit/test_site_member.py` passed 86 tests, adjacent site/member/application/user/private-message coverage passed 775 tests, and full unit coverage passed 3524 tests. | Regressing parser-created members, constructor site/user/joined-at diagnostics, client coherence, action preflights, action-status handling, mapped target errors, role-cache behavior, site/application/user/private-message workflows, or any unit test rejects this local completion claim. | Site member and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic sites and members. | Using credentials, cookies, auth JSON, private member names, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site-member/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `93e401d fix(site_member): validate constructor user id state`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass -k retained_user_id -q` selected 7 constructor retained-user-ID tests; 5 malformed retained-ID cases failed before the fix with `DID NOT RAISE`, while the 2 `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 7 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/site_member.py tests/unit/test_site_member.py` left both files unchanged.
- `uv run pytest tests/unit/test_site_member.py -q` passed 86 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py tests/unit/test_private_message.py -q` passed 775 tests.
- `uv run pytest tests/unit -q` passed 3524 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `SiteMember(...)` raises `ValueError("member.user.id must be an integer or None")` when the member user's retained `id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- Malformed non-`None` retained member IDs fail before the member row is stored by direct construction.
- Valid retained member IDs `None` and `0` remain accepted by direct construction.
- Existing negative retained member IDs still raise `ValueError("member.user.id must be non-negative")` by direct construction.
- Existing action-time role-change malformed-ID, missing-ID, malformed-name, and negative-ID tests still prove post-construction mutation fails before `site.client.login_check()`, `site.amc_request(...)`, returned action-status parsing, mapped target errors, or role-cache mutation.
- Existing malformed site validation, non-`AbstractUser` member validation, member/site client ownership validation, joined-at validation, valid moderator/admin role changes, returned action-status validation, mapped target errors, role-cache invalidation, site application workflows, user behavior, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed member rows with corrupted retained member IDs now fail during construction instead of later role-change work. Mitigation: those values are impossible user identity state; failing before storage is deterministic and keeps member rows coherent.
- Risk: Optional member IDs could be rejected accidentally. Mitigation: focused compatibility guards assert that `None` and `0` remain accepted and preserved at construction time.
- Risk: The constructor fix could erase action-time mutation coverage. Mitigation: the role-change malformed-user test now constructs a valid row first and mutates the retained user afterward, proving the action helper still rejects before login and AMC request work.
- Risk: Validation precedence could regress earlier member diagnostics. Mitigation: the retained-ID check runs after the existing `AbstractUser` check; stricter action payload name and concrete-ID requirements remain in the existing action helper; site-member, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing site-member site validation, member object validation, member/site client validation, joined-at validation, action-user concrete ID validation, action-user name validation, action-status validation, mapped target errors, and role-cache behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `SiteMember` constructor retained user-ID state boundary.

## Upstream-Safe Motivation

`SiteMember` is the durable row shape behind member inventories, membership ledgers, site-access audits, moderation workflows, and role-change automation. Parser-created member users can legitimately have optional IDs, while direct `User` construction already rejects malformed and negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated member identity out of stored member rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, client coherence, joined-at validation, and action-time mutation preflights.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site members as a practical workflow through member-list retry, parser diagnostics, response-body diagnostics, member field validation, member/site client validation, role-change action-status validation, member action-time ID range validation, constructor negative member ID validation, and role-cache invalidation.
- Existing local drafts covered non-`AbstractUser` members, malformed action-time member ID types, missing action-time member IDs, malformed action-time member names, member client mismatch, direct user constructor ID ranges, site-member constructor negative member IDs, site-application constructor applicant ID state, and adjacent retained user-ID state; they did not validate corrupted malformed non-`None` `User.id` values at the direct `SiteMember(...)` constructor boundary.
- The focused RED failure showed malformed retained member IDs could be stored in direct member rows. The GREEN regressions cover constructor malformed rejection, optional-ID and zero-ID constructor compatibility, existing negative constructor rejection, action-time post-construction mutation coverage, site-member behavior, adjacent site/member/application/user/private-message workflows, and full unit compatibility.
- This slice only validates retained member user ID state at the `SiteMember` constructor boundary. It does not change member-list parsing, site invitation actions, site application actions, member lookup filters, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private member data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained constructor member IDs instead of requiring a concrete regular-user ID. The role-change path still owns the stricter action-payload requirement for concrete integer IDs and member names before membership mutation requests are built.
