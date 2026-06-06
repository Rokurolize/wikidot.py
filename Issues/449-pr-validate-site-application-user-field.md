# PR Draft: Validate SiteApplication User Field

## Summary

`SiteApplication` records carry the applicant `AbstractUser` used by browser-free application-list reads, accept/decline actions, member-cache invalidation, generated membership ledgers, and downstream moderation or migration scripts. Earlier local slices validated application-list fetch retries, body parsing, response-body diagnostics, parsed applicant diagnostics, action-status diagnostics, accept cache invalidation, adjacent invitation user inputs, and `SiteApplication.user` immediately before accept/decline mutations, but the public `SiteApplication(...)` constructor still accepted malformed non-user values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `SiteApplication.user` at initialization. Malformed non-`AbstractUser` values now raise `ValueError("application.user must be an AbstractUser")`. Valid `User` and other `AbstractUser` subclasses remain valid constructor inputs, while the existing accept/decline preflight still validates action-specific `id` and `name` requirements before login checks or AMC requests.

## Outcome

Callers cannot silently construct site-application records whose stored `user` is not an `AbstractUser`, while parser-created application records, manually created valid records, application-list acquisition, accept/decline action validation, member-cache invalidation, and adjacent site/member/user workflows continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use site application moderation, `site.applications`, accept/decline automation, generated membership ledgers, site-access audits, local fixtures that construct `SiteApplication` directly, or scripts that carry parsed application rows between workflow stages.

## Current Evidence

Local rollout-backed drafts repeatedly identify site applications and membership administration as practical workflow surfaces. Existing drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), and [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md) establish application acquisition, parser diagnostics, response diagnostics, accept/decline behavior, applicant action preflight, adjacent invitation validation, and member-cache synchronization as active operational boundaries.

Those prior slices are not duplicates. Issue371 validates the already-stored `SiteApplication.user` immediately before accept/decline login checks, payload construction, AMC submission, or returned-status diagnostics. It intentionally protects a mutation workflow and still matters if `application.user` is mutated after construction. This slice validates the public dataclass constructor boundary so malformed non-user values cannot become stored `SiteApplication` state in the first place. Parser/fetch drafts cover creation from valid parsed users, while invitation and member drafts cover adjacent site-administration inputs rather than direct `SiteApplication(user=...)` construction.

## Related Issue

Builds directly on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), and the adjacent constructor field-validation pattern from [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), and [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteApplication.user` validation at dataclass initialization.
- Accept valid `AbstractUser` instances, including `User` and other subclasses.
- Reject malformed non-user constructor values with `ValueError("application.user must be an AbstractUser")`.
- Keep existing accept/decline validation for action-specific `application.user.id` and `application.user.name` requirements.
- Keep the existing accept/decline malformed-user regression by mutating the public dataclass field after valid construction.
- Replace parser test `MagicMock` user fixtures with real `User` objects so parser tests reflect the public `SiteApplication` contract.
- Preserve existing application-list parsing, retry behavior, response diagnostics, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site application state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication(user=None)`, `True`, `"TestUser"`, `{"id": 12345}`, and `object()` must raise `ValueError("application.user must be an AbstractUser")` when every other field is valid. |
| R2 | Valid `AbstractUser` values must remain valid constructor inputs, and application `text` storage must remain unchanged. |
| R3 | Existing accept/decline action preflight must still reject mutated non-user state and malformed action users before login checks or AMC requests. |
| R4 | Existing application-list parsing, retry behavior, response diagnostics, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private applicant data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, site-application tests, adjacent site/member/application/user tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor users fail at the public dataclass boundary. | `TestSiteApplicationDataclass.test_init_rejects_malformed_users` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting application rows with non-`AbstractUser` stored state rejects this local completion claim. | SiteApplication constructor | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Valid applicant-user and text-storage semantics stay green. | Existing dataclass tests and parser tests passed after parser fixtures returned real `User` instances. | Rejecting valid `User` objects, rejecting other `AbstractUser` subclasses by type, coercing user-like dictionaries, or changing stored text rejects this local completion claim. | Parser-created and manually created applications | `tests/unit/test_site_application.py` |
| R3 | Accept/decline action validation still protects mutable dataclass state before login or AMC work. | Existing action-user tests passed after the non-user case mutates `application.user` after valid construction; malformed `User(id=None)`, `User(id=True)`, and `User(name=None)` still reject before login or AMC requests. | Calling login, sending AMC requests, losing accept/decline ID/name validation, or leaking raw attribute errors rejects this local completion claim. | Site application mutation methods | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R4 | Existing adjacent site/application/member/user workflows remain green. | `tests/unit/test_site_application.py` passed 35 tests, adjacent site/site-member/site-application/user tests passed 364 tests, and full unit tests passed 1731 tests. | Regressing application-list acquisition, retry behavior, nested-body filtering, text spacing, response-body diagnostics, malformed applicant parser diagnostics, action-status diagnostics, accept member-cache invalidation, decline cache preservation, site member workflows, site read/write helpers, or user profile lookup rejects this local completion claim. | Site application and adjacent site workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private applicant names, application text, page source text, forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5d86f54 fix(site_application): validate application user`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_malformed_users -q` failed 5 tests before the fix; every malformed `user` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_malformed_users -q` passed 5 tests.
- `uv run pytest tests/unit/test_site_application.py -q` passed 35 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 364 tests.
- `uv run ruff check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed.
- `uv run pyright src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit -q` passed 1731 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 70 existing full-tree typing errors, including fixture `None` mismatches, intentional invalid-input test calls, invalid `test_search_pages_query` parameter calls, requestutil response narrowing issues, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `SiteApplication(user=None)`, `True`, `"TestUser"`, `{"id": 12345}`, and `object()` raise `ValueError("application.user must be an AbstractUser")`.
- Valid `User` instances remain valid as `SiteApplication.user`.
- Existing accept/decline methods still reject mutated non-user state and malformed `User` action fields before login or AMC requests.
- Existing application-list parsing, retry behavior, response-body diagnostics, malformed applicant diagnostics, text spacing, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private applicant data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteApplication.user` is the subject identity behind browser-free pending-application inventories, accept/decline moderation actions, cache invalidation, generated membership ledgers, and moderation or migration scripts. Constructor validation keeps malformed non-user state out of application rows while preserving parser-created and manually created records with real `AbstractUser` instances. The action-specific ID/name validation remains in the accept/decline path because read-side application rows may carry broader `AbstractUser` subclasses while mutation requests need a real integer user ID and string diagnostic name.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used application-list acquisition, accept/decline actions, member-cache invalidation, adjacent site invitation validation, site member workflows, and generated membership state as practical workflow surfaces.
- Existing local drafts covered site application fetch retry behavior, nested body markup filtering, text parse context, response-body diagnostics, malformed parsed applicants, action-status validation, accept cache invalidation, invitation-user validation, and action-user preflight, but did not cover direct `SiteApplication(user=...)` construction.
- The focused RED failures showed invalid constructor users were accepted as dataclass state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object values.
- This slice only validates the stored applicant-user object type at construction. It does not validate `site`, `text`, user ID, user name, application existence, accept/decline action status, parser selectors, live site behavior, or client authentication at `SiteApplication` construction time.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private applicant data, application text, page source text, forum content, private messages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `user` is an `AbstractUser` instance. It does not reject `AbstractUser` subclasses with `id=None` at construction; that stricter requirement belongs to accept/decline actions and is still enforced immediately before login checks and AMC requests.
