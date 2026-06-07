# PR Draft: Validate Site Application Acquire Site

## Summary

`SiteApplication(site=...)` already validates constructor sites, and application accept/decline already revalidates mutated application sites before login checks. One adjacent direct list-acquire boundary still used the generic `login_required` decorator diagnostic: direct `SiteApplication.acquire_all(site)` calls with malformed sites such as `None`, booleans, strings, dictionaries, or arbitrary objects raised `ValueError("Client is not found")` instead of the explicit site-application site diagnostic used by the surrounding public helpers.

This change validates the caller-provided `site` at the start of `SiteApplication.acquire_all(...)`, then runs the same valid-site `site.client.login_check()` before fetching the application list. Malformed direct acquire sites now raise `ValueError("site must be a Site")` before login checks, AMC list fetches, response parsing, or user parsing. Valid application-list acquisition, not-logged-in behavior, retry behavior, response-body diagnostics, parser diagnostics, and application action behavior remain unchanged.

## Outcome

Direct site-application list acquisition now reports the same explicit site preflight as constructor and action-time site validation.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `SiteApplication.acquire_all(site)` directly, use `site.applications`, or load site-like inputs from generated fixtures where malformed site objects should fail before login or request work.

## Current Evidence

Existing drafts [500-pr-validate-site-application-state.md](500-pr-validate-site-application-state.md), [541-pr-validate-site-member-get-site.md](541-pr-validate-site-member-get-site.md), [542-pr-validate-forum-category-acquire-site.md](542-pr-validate-forum-category-acquire-site.md), and [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md) establish constructor/action state and direct list-acquire site arguments as active boundaries. This slice covers direct `SiteApplication.acquire_all(site)`, not `SiteApplication(site=...)`, application accept/decline, member lists, forum categories, or forum threads.

No upstream issue was filed from this local workspace.

## Changes

- Validate `site` in `SiteApplication.acquire_all(...)` before login checks.
- Replace the generic decorator preflight on this static method with explicit valid-site `site.client.login_check()` after site validation.
- Add direct acquire regressions for malformed `site` inputs.
- Preserve valid application-list acquisition, logged-out errors for valid sites, retry behavior, response-body diagnostics, parser diagnostics, and application accept/decline behavior.

## Type Of Change

- Input validation
- Public read-boundary diagnostic hardening
- Site-application list acquisition hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication.acquire_all(None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` before login checks or application-list fetch work. |
| R2 | Valid `SiteApplication.acquire_all(site)` and `site.applications` acquisition must remain unchanged. |
| R3 | Valid-site logged-out behavior must still raise `LoginRequiredException`. |
| R4 | Existing site-application parser diagnostics, retry behavior, response-body diagnostics, constructor validation, and accept/decline validation must remain unchanged. |
| R5 | Site-application module tests, adjacent site/site-member/client tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct acquire sites fail with the explicit site diagnostic before login or fetch work. | `TestSiteApplicationAcquireAll.test_acquire_all_rejects_malformed_site_before_login` failed RED for 5 malformed cases with `ValueError("Client is not found")`, then passed GREEN after the direct site preflight was added. | Relying on the generic decorator diagnostic, accepting site-like dictionaries, reaching login checks, reaching `amc_request_with_retry`, or leaking lower-level attribute errors rejects this local completion claim. | `SiteApplication.acquire_all(...)` | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Valid direct and accessor acquisition remains stable. | Existing `test_acquire_all_success` and `test_site_applications_retries_transient_fetch_failures` passed in the focused GREEN run and the 51-test site-application module run. | Changing request shape, retry behavior, `site.applications` delegation, parsed users, or parsed application text rejects this local completion claim. | Site application list acquisition | `tests/unit/test_site_application.py` |
| R3 | Valid-site logged-out behavior remains stable. | `test_acquire_all_not_logged_in` passed in the focused GREEN run and the 51-test site-application module run. | Returning a generic site error for a valid logged-out site, bypassing login checks, or performing list fetch work while logged out rejects this local completion claim. | Login preflight for valid sites | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R4 | Existing site-application and adjacent workflows remain stable. | Site-application module tests passed 51 tests, adjacent site-application/site/site-member/client tests passed 436 tests, and full unit passed 2651 tests. | Regressing parser context, response-body diagnostics, forbidden handling, retry exhaustion, constructor validation, accept/decline status handling, member/site/client behavior, or adjacent direct site validation rejects this local completion claim. | Site-application and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | All regressions use synthetic malformed sites and unit-level mocked valid sites; this draft contains no credentials, cookies, auth JSON, raw application bodies, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `a7f4508 fix(site_application): validate acquire site`.

- RED direct acquire site validation: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_rejects_malformed_site_before_login -q` failed 5 tests before the fix because malformed sites raised the generic `ValueError("Client is not found")`.
- GREEN focused: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_rejects_malformed_site_before_login tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_not_logged_in tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_success -q` passed 7 tests.
- `uv run pytest tests/unit/test_site_application.py -q` passed 51 tests.
- `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_client.py -q` passed 436 tests.
- `uv run pytest tests/unit -q` passed 2651 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteApplication.acquire_all(...)` rejects malformed direct site arguments with `ValueError("site must be a Site")` before login checks, application-list fetches, response parsing, or user parsing.
- Valid `SiteApplication.acquire_all(site)` and `site.applications` acquisition remain unchanged.
- Valid logged-out sites still raise `LoginRequiredException`.
- Constructor site validation and accept/decline action-time validation remain intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This could be mistaken for constructor validation. Mitigation: Issue 500 still covers `SiteApplication(site=...)`; this slice covers direct application-list acquisition.
- Risk: This could be mistaken for member or forum list acquisition validation. Mitigation: Issues 541, 542, and 543 cover those adjacent surfaces; this slice covers `SiteApplication.acquire_all(...)`.
- Risk: Replacing the generic decorator with explicit login checking could accidentally change valid logged-out behavior. Mitigation: the focused logged-out test, full site-application module, adjacent suite, and full unit suite remain green.

## Dependencies

- Existing `Site` constructor validation remains responsible for valid `Site` object construction.
- Existing site-application response parsing remains responsible for application list body validation and parser diagnostics.
- Existing application action validation remains responsible for accept/decline state revalidation.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`SiteApplication.acquire_all(...)` is a practical browser-free site-administration entry point. Validating the direct site argument before login discovery gives generated callers, fixtures, and config adapters deterministic errors for malformed values without changing valid login checks, request shape, retries, parsing, or application action workflows.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct acquire sites reaching the generic login decorator and raising `Client is not found` instead of the site-application site diagnostic.
- This slice only validates the direct `SiteApplication.acquire_all(site)` argument. It does not change application list parsing, response-body diagnostics, nested body markup handling, retry controls, application constructor validation, accept/decline action behavior, member lists, forum lists, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, and live Wikidot account details out of upstream discussion.
