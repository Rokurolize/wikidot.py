# PR Draft: Validate Site Member User Field

## Summary

`SiteMember` records carry the member `AbstractUser` used by browser-free member-list reads, role-change actions, role-cache invalidation, member lookup workflows, generated membership ledgers, and downstream moderation or migration scripts. Earlier local slices validated member-list fetch retries, row scoping, pager scoping, response-body diagnostics, parsed member-user diagnostics, joined-at diagnostics, role-change action responses, role-cache invalidation, member lookup inputs, and `SiteMember.user` immediately before role-change mutations, but the public `SiteMember(...)` constructor still accepted malformed non-user values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `SiteMember.user` at initialization. Malformed non-`AbstractUser` values now raise `ValueError("member.user must be an AbstractUser")`. Valid `User` and other `AbstractUser` subclasses remain valid constructor inputs, while the existing role-change preflight still validates action-specific `id` and `name` requirements before login checks or AMC requests.

## Outcome

Callers cannot silently construct site-member records whose stored `user` is not an `AbstractUser`, while parser-created member records, manually created valid records, member-list acquisition, role-change action validation, and adjacent site/application/user workflows continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free member inventories, `site.members`, `site.moderators`, `site.admins`, member lookup, generated membership ledgers, role-change automation, site-access audits, local fixtures that construct `SiteMember` directly, or scripts that carry parsed membership rows between workflow stages.

## Current Evidence

Local rollout-backed drafts repeatedly identify site membership and role administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), and [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md) establish member acquisition, parser diagnostics, response diagnostics, member lookup, role-change response validation, action-user preflight, and role-cache synchronization as active operational boundaries.

Those prior slices are not duplicates. Issue410 validates the already-stored `SiteMember.user` immediately before role-change login checks, payload construction, AMC submission, or returned-status diagnostics. It intentionally protects a mutation workflow and still matters if `member.user` is mutated after construction. This slice validates the public dataclass constructor boundary so malformed non-user values cannot become stored `SiteMember` state in the first place. Parser/fetch drafts cover creation from valid parsed users, while lookup/input drafts cover `Site.member_lookup(...)` inputs rather than direct `SiteMember(user=...)` construction.

## Related Issue

Builds directly on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), and the adjacent constructor field-validation pattern from [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), and [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteMember.user` validation at dataclass initialization.
- Accept valid `AbstractUser` instances, including `User` and other subclasses.
- Reject malformed non-user constructor values with `ValueError("member.user must be an AbstractUser")`.
- Keep existing role-change validation for action-specific `member.user.id` and `member.user.name` requirements.
- Keep the existing role-change malformed-user regression by mutating the public dataclass field after valid construction.
- Replace parser test `MagicMock` user fixtures with real `User` objects so parser tests reflect the public `SiteMember` contract.
- Preserve existing member-list parsing, pagination, retry behavior, response diagnostics, role-change behavior, cache invalidation, site application behavior, site workflows, and user workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site member state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember(user=None)`, `True`, `"TestUser"`, `{"id": 12345}`, and `object()` must raise `ValueError("member.user must be an AbstractUser")` when every other field is valid. |
| R2 | Valid `AbstractUser` values must remain valid constructor inputs, and `joined_at=None` must remain valid. |
| R3 | Existing role-change action preflight must still reject mutated non-user state and malformed action users before login checks or AMC requests. |
| R4 | Existing member-list parsing, pagination, retry behavior, response diagnostics, role-cache invalidation, site application behavior, site workflows, and user workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, site-member tests, adjacent site/member/application/user tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor users fail at the public dataclass boundary. | `TestSiteMemberDataclass.test_init_rejects_malformed_users` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting member rows with non-`AbstractUser` stored state rejects this local completion claim. | SiteMember constructor | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Valid member-user and optional joined-at semantics stay green. | Existing dataclass tests and parser tests passed after parser fixtures returned real `User` instances. | Rejecting valid `User` objects, rejecting other `AbstractUser` subclasses by type, requiring `joined_at`, or changing stored valid member fields rejects this local completion claim. | Parser-created and manually created members | `tests/unit/test_site_member.py` |
| R3 | Role-change action validation still protects mutable dataclass state before login or AMC work. | Existing action-user tests passed after the non-user case mutates `member.user` after valid construction; malformed `User(id=None)`, `User(id=True)`, and `User(name=None)` still reject before login or AMC requests. | Calling login, sending AMC requests, losing role-change ID/name validation, or leaking raw attribute errors rejects this local completion claim. | Site member role-change methods | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R4 | Existing adjacent site/member/application/user workflows remain green. | `tests/unit/test_site_member.py` passed 47 tests, adjacent site/site-member/site-application/user tests passed 359 tests, and full unit tests passed 1726 tests. | Regressing member-list acquisition, pagination, retry behavior, response-body diagnostics, malformed user/timestamp parser diagnostics, member lookup, role-cache invalidation, site application processing, site read/write helpers, or user profile lookup rejects this local completion claim. | Site member and adjacent site workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private member names, application text, page source text, forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a45f229 fix(site_member): validate member user`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_malformed_users -q` failed 5 tests before the fix; every malformed `user` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_malformed_users -q` passed 5 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 47 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 359 tests.
- `uv run ruff check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed.
- `uv run pyright src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit -q` passed 1726 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 72 existing full-tree typing errors, including fixture `None` mismatches, intentional invalid-input test calls, invalid `test_search_pages_query` parameter calls, requestutil response narrowing issues, and site/application test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `SiteMember(user=None)`, `True`, `"TestUser"`, `{"id": 12345}`, and `object()` raise `ValueError("member.user must be an AbstractUser")`.
- Valid `User` instances remain valid as `SiteMember.user`.
- Existing role-change methods still reject mutated non-user state and malformed `User` action fields before login or AMC requests.
- Existing member-list parsing, pagination, retry behavior, response-body diagnostics, malformed member-user diagnostics, malformed joined-at diagnostics, role-cache invalidation, site application behavior, site workflows, and user workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private member data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteMember.user` is the subject identity behind browser-free member inventories, role-change actions, cache invalidation, member lookup follow-ups, generated membership ledgers, and moderation or migration scripts. Constructor validation keeps malformed non-user state out of member rows while preserving parser-created and manually created records with real `AbstractUser` instances. The action-specific ID/name validation remains in the role-change path because read-side member rows may carry broader `AbstractUser` subclasses while mutation requests need a real integer user ID and string diagnostic name.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used member-list acquisition, role-change actions, role-cache invalidation, direct member lookup, site application processing, and generated membership state as practical workflow surfaces.
- Existing local drafts covered site member fetch retry behavior, parser row scoping, response-body diagnostics, malformed parsed member users, malformed joined-at timestamps, action-status validation, role-cache invalidation, member lookup inputs, and action-user preflight, but did not cover direct `SiteMember(user=...)` construction.
- The focused RED failures showed invalid constructor users were accepted as dataclass state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object values.
- This slice only validates the stored member-user object type at construction. It does not validate `site`, `joined_at`, user ID, user name, role membership, lookup behavior, role-change action status, parser selectors, live site behavior, or client authentication at `SiteMember` construction time.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private member data, application text, page source text, forum content, private messages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `user` is an `AbstractUser` instance. It does not reject `AbstractUser` subclasses with `id=None` at construction; that stricter requirement belongs to role-change actions and is still enforced immediately before login checks and AMC requests.
