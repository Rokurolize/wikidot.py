# PR Draft: Validate SiteApplication Site Field

## Summary

`SiteApplication` records carry the parent `Site` used by browser-free pending-application reads, accept/decline moderation actions, returned-status diagnostics, member-cache invalidation, generated membership ledgers, and local fixtures. Earlier local slices validated application-list fetch retries, response-body diagnostics, parser-side applicant and text handling, accept/decline action status, direct `SiteApplication.user`, direct `SiteApplication.text`, adjacent site invitation inputs, and application action user preflight. One direct record-state gap remained: `SiteApplication(..., site=...)` still accepted arbitrary non-`Site` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `SiteApplication.site` at initialization and immediately before accept/decline action work. Malformed parent-site values now raise `ValueError("site must be a Site")` before invalid application state can be stored or a mutated public field can reach login checks, AMC request construction, or member-cache mutation. Valid `Site` parents, application-list parsing, text/user validation, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows remain unchanged.

## Outcome

Callers cannot silently construct site-application records with malformed parent-site state, and a later `application.site` mutation is rejected before login or AMC work. Parser-created applications and valid direct `SiteApplication(...)` construction keep the existing moderation behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use pending site-application inventories, `site.applications`, accept/decline automation, generated membership ledgers, site-access audits, local fixtures, or serialized and rehydrated application rows.

## Current Evidence

Site-application drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), and [450-pr-validate-site-application-text-field.md](450-pr-validate-site-application-text-field.md) establish application acquisition, parser diagnostics, response diagnostics, accept/decline behavior, cache synchronization, action-user preflight, and direct application record state as practical operational boundaries.

Adjacent constructor-hardening drafts [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), and [499-pr-validate-site-member-joined-at-field.md](499-pr-validate-site-member-joined-at-field.md) establish the local pattern for validating direct dataclass parent fields instead of relying only on parser boundaries or mocks.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 449. Issue 449 validates the direct `SiteApplication.user` field at construction and intentionally does not validate `site` or `text`. This slice validates the separate parent-site field that supplies the client, AMC action surface, site name diagnostics, and member-cache mutation target.

This is not a duplicate of Issue 450. Issue 450 validates the stored application text field and explicitly leaves `site` outside its scope. This slice validates the parent object while preserving text storage semantics.

This is not a duplicate of Issue 371. Issue 371 validates the action applicant before accept/decline login checks and AMC request construction. This slice validates the action parent site before those same side-effect surfaces and also validates the constructor boundary so malformed parent objects cannot become stored application state.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_site_application_site(...)` with a circular-import-safe local `Site` import.
- Update `SiteApplication.__post_init__` to reject non-`Site` parent objects.
- Revalidate `self.site` inside `_process(...)` before user validation, login checks, AMC requests, and cache mutation.
- Use the validated `site` local for login, AMC request, and accept-cache invalidation.
- Tighten site-application unit fixtures so valid application tests use real `Site` instances with request methods stubbed.
- Add focused regressions for malformed constructor sites and mutated action-time sites.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site application mutation preflight hardening
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` when every other constructor field is valid. |
| R2 | Valid `Site` parents must remain valid constructor inputs, and parser-created `SiteApplication` rows must retain the original parent site. |
| R3 | `SiteApplication.accept()` must reject a mutated non-`Site` `application.site` with `ValueError("site must be a Site")` before login checks, AMC requests, or member-cache changes. |
| R4 | Existing application-list parsing, retry behavior, response diagnostics, malformed applicant diagnostics, text validation, user validation, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private application data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, site-application tests, adjacent site/member/application/user tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor site values fail at the public dataclass boundary. | `TestSiteApplicationDataclass.test_init_rejects_malformed_sites` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, site names, dictionaries, arbitrary objects, or emitting application rows with non-`Site` parent state rejects this local completion claim. | SiteApplication constructor | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Valid parent-site semantics stay green. | Existing constructor tests and application-list parser tests passed after valid fixtures used real `Site` objects with stubbed request methods. | Rejecting valid `Site` objects, losing the parent site during `SiteApplication.acquire_all(...)`, or changing stored user/text fields rejects this local completion claim. | Parser-created and manually created applications | `tests/unit/test_site_application.py` |
| R3 | Mutated non-site parent state fails before side-effect surfaces. | `TestSiteApplicationProcess.test_accept_rejects_malformed_site_before_login` passed and asserts no login check, no AMC request, and no cache invalidation after mutating `app.site` to a mock. | Calling `client.login_check()`, calling `amc_request(...)`, invalidating `_members`, or leaking raw attribute errors rejects this local completion claim. | Site application mutation methods | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R4 | Existing adjacent workflows remain green. | `tests/unit/test_site_application.py` passed 46 tests, adjacent site/site-member/site-application/user tests passed 392 tests, and the full unit suite passed 2213 tests. | Regressing application acquisition, retry behavior, nested body filtering, text spacing, response-body diagnostics, malformed applicant parser diagnostics, action-status diagnostics, applicant-user validation, text validation, accept cache invalidation, decline cache preservation, site member workflows, site read/write helpers, or user profile workflows rejects this local completion claim. | Site application and adjacent workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw application-list HTML, private applicant names, application text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, pyright, unit, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `6ac88e2 fix(site_application): validate application site`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_malformed_sites -q` failed 5 tests before the fix; every malformed `site` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_malformed_sites -q` passed 5 tests.
- `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_malformed_sites tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_malformed_site_before_login -q` passed 6 tests.
- `uv run pytest tests/unit/test_site_application.py -q` passed 46 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 392 tests.
- `uv run ruff check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed.
- `uv run ruff format --check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed with no issues in 2 source files.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2213 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteApplication(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- Valid `Site` instances remain valid as `SiteApplication.site`.
- Parser-created rows from `SiteApplication.acquire_all(site)` retain the original valid `Site` parent.
- `accept()` rejects a mutated non-`Site` parent before login checks, AMC requests, or member-cache invalidation.
- Existing application-list parsing, response-body diagnostics, malformed applicant diagnostics, text spacing, user/text validation, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private application data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Tests could keep using permissive mocks that no longer reflect the public contract. Mitigation: valid site-application fixtures now construct real `Site` objects and only stub network-facing request methods.
- Risk: Constructor validation could be confused with live-site validation. Mitigation: this change only checks the local parent object type and does not contact Wikidot, validate permissions, or change authentication behavior.
- Risk: Action-time validation could accidentally change invalid-action ordering. Mitigation: `_process(...)` still rejects invalid action strings before checking the parent site, preserving the existing invalid-action behavior.

## Dependencies

- Valid application-list parser output continues to be created from a real `Site` object supplied to `SiteApplication.acquire_all(site)`.
- Existing `Site` constructor validation remains responsible for site scalar fields such as `id`, `title`, `unix_name`, `domain`, and `ssl_supported`.
- Existing action-user preflight remains responsible for applicant `id` and `name` validation before mutation requests.

## Open Questions

None for this local slice. A future separate change can evaluate the analogous `SiteMember.site` constructor boundary, but that requires its own duplicate analysis and fixture tightening.

## Upstream-Safe Motivation

`SiteApplication.site` is the parent object behind browser-free pending-application reads, moderation actions, action diagnostics, and accepted-member cache invalidation. Parser paths already pass a real `Site` object into created application rows. Constructor and action-time validation keep malformed local parent state out of manually constructed or mutated records without changing application acquisition, parser selectors, action payloads, returned-status handling, cache behavior, or live Wikidot interactions.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used browser-free application-list acquisition, accept/decline actions, member-cache invalidation, generated membership state, site invitations, member workflows, and tests that construct `SiteApplication` records directly.
- Existing local drafts covered site application fetch retry behavior, response-body handling, nested body markup filtering, application text spacing, malformed parser diagnostics, accept/decline action-status validation, applicant action preflight, direct user validation, and direct text validation, but did not cover direct `SiteApplication(site=...)` construction or action-time parent-site mutation.
- The focused RED failures showed invalid constructor site values were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, dictionary, and arbitrary object values plus a mutated action-time mock site.
- This slice only validates stored site-application parent type at construction and before mutation actions. It does not change application-list acquisition, parser selectors, response-body diagnostics, applicant parsing, text extraction, accept/decline payload construction, returned-status handling, member-cache invalidation semantics for valid sites, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw application-list HTML, private applicant names, application text, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed parent objects instead of accepting site-like mocks or dictionaries. Tests and downstream callers should construct a real `Site` object and stub network-facing request methods when unit-level isolation is needed.
