# PR Draft: Validate SiteApplication User Client

## Summary

`SiteApplication` records carry both the parent `Site` and the applicant `user`. Existing site-application slices validate parser-side applicant extraction, direct `user` type, direct `site` type, direct `text` type, and accept/decline action-user ID/name requirements. One constructor and mutation coherence gap remained: direct `SiteApplication(...)` construction could combine `site=site_a` with `user=User(client=site_b.client, ...)`, and a later `application.user` mutation to another client context could reach accept/decline login, AMC request, and action-status handling.

This change validates `SiteApplication.user.client` against `SiteApplication.site.client` during `SiteApplication.__post_init__` after existing field-shape checks and again in the shared accept/decline path after existing site/user action checks but before login, AMC requests, action-status handling, or member-cache mutation. Mismatches raise `ValueError("application.user must belong to the site")`. Valid parser-created application rows, same-client direct rows, existing malformed field diagnostics, application-list parsing, accept/decline behavior, member-cache invalidation, and adjacent site/member/application/user workflows remain unchanged.

## Outcome

Site-application rows cannot store or act on an applicant user from a different client context than the parent site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free pending-application inventories, `site.applications`, accept/decline automation, generated membership ledgers, site-access audits, migration checks, local fixtures, or serialized and rehydrated application rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify site applications and membership administration as practical workflow surfaces. Existing drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), [450-pr-validate-site-application-text-field.md](450-pr-validate-site-application-text-field.md), and [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md) establish application acquisition, parser diagnostics, response diagnostics, accept/decline behavior, cache synchronization, action-user preflight, and direct application record state as active boundaries.

The parser path already constructs applicant users with the parent site's client by calling the shared user parser as `user_parser(site.client, user_element)`. The new rule brings direct constructor and action-time mutation behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 449. Issue 449 validates that `SiteApplication.user` is an `AbstractUser`; it explicitly does not validate `site`, `text`, user ID/name, application existence, or client authentication at construction time. This slice validates the relationship between a valid `Site` and a valid `AbstractUser`.

This is not a duplicate of Issue 371. Issue 371 validates action-specific applicant type, ID, and name before accept/decline side effects; it does not prevent a valid action user from belonging to another client context.

This is not a duplicate of Issue 500. Issue 500 validates that `SiteApplication.site` is a `Site` and revalidates mutated site state before accept/decline actions; it does not compare the valid site object with the valid user object.

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteApplication` user-client coherence validation.
- Reject direct rows where `user.client is not site.client` with `ValueError("application.user must belong to the site")`.
- Revalidate the same coherence in `_process(...)` before login checks, AMC requests, action-status handling, or member-cache mutation.
- Preserve existing validation order for invalid action strings, malformed site, malformed user type, malformed user ID/name, malformed text, and action-status diagnostics.
- Tighten unit fixtures so valid synthetic applications use the same client as their synthetic site.
- Preserve side-effect-free construction and preflight-only action validation: the new check compares object identity only and does not perform login checks, HTTP requests, user lookups, coercion, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site-application accept/decline preflight hardening
- Membership ledger identity integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication(site=site_a, user=User(client=site_b.client, ...), ...)` must reject the mismatched applicant client with `ValueError("application.user must belong to the site")` before storing record state. |
| R2 | Accept/decline methods must reject a later `application.user` mutation to another client context with the same `ValueError` before login checks, AMC requests, action-status handling, or member-cache mutation. |
| R3 | Valid direct `SiteApplication(...)` rows where `user.client is site.client` and parser-created application rows must remain valid. |
| R4 | Existing invalid-action, malformed `site`, malformed `user`, malformed `text`, malformed action-user ID/name, and action-status diagnostics must remain unchanged. |
| R5 | Existing application-list parsing, retry behavior, response diagnostics, malformed applicant diagnostics, text spacing, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor applicant/client mismatches fail at the public dataclass boundary. | `TestSiteApplicationDataclass.test_init_rejects_user_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `SiteApplication.__post_init__` called the coherence preflight. | Accepting a valid `User` object from another client context, emitting an application row whose site and user client disagree, or deferring the mismatch to later use rejects this local completion claim. | `SiteApplication` constructor | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Mutated applicant/client mismatches fail before accept/decline side effects. | `TestSiteApplicationProcess.test_accept_rejects_user_from_different_client_before_login` failed RED by reaching mocked action-status handling with `WikidotStatusCodeException`, then passed GREEN and asserts no login check, no AMC request, and no member-cache invalidation. | Calling `site.client.login_check()`, calling `site.amc_request(...)`, mutating `site._members`, or leaking returned-status diagnostics rejects this local completion claim. | Site application accept/decline methods | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R3 | Existing valid constructor, parser, and accept/decline rows stay green. | `tests/unit/test_site_application.py` passed 53 tests after valid fixtures and parser mocks used `site.client`. | Rejecting same-client direct users, replacing user objects, coercing users, breaking parser-created rows, or requiring live authentication rejects this local completion claim. | `SiteApplication` constructor, parser, and actions | `tests/unit/test_site_application.py` |
| R4 | Existing diagnostics stay stable. | Focused site-application coverage passed existing invalid-action, malformed site, malformed user, malformed text, malformed action-user ID/name, missing action status, non-ok action status, and `no_application` tests. | Changing existing `ValueError` diagnostics, validating coherence before malformed field/action checks, or accepting previously rejected malformed values rejects this local completion claim. | SiteApplication validation order | `tests/unit/test_site_application.py` |
| R5 | Existing adjacent workflows remain green. | Adjacent site/site-member/site-application/user coverage passed 463 tests, and full unit coverage passed 2733 tests. | Regressing application acquisition, retry behavior, nested-body filtering, text spacing, response-body diagnostics, malformed applicant parser diagnostics, action-status diagnostics, accept member-cache invalidation, decline cache preservation, site member workflows, site read/write helpers, or user profile workflows rejects this local completion claim. | Site application and adjacent workflows | `tests/unit` |
| R6 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic `Site` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw application-list HTML, private applicant names, application text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `623aa12 fix(site_application): validate application user client`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_user_from_different_client tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_user_from_different_client_before_login -q` failed before the fix. The constructor case reported `DID NOT RAISE`; the action-time case reached mocked action-status handling and raised `WikidotStatusCodeException` instead of the expected preflight `ValueError`.
- GREEN regression: the same focused command passed 2 tests.
- Site-application coverage: `uv run pytest tests/unit/test_site_application.py -q` passed 53 tests.
- Adjacent site/member/application/user coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 463 tests.
- `uv run pytest tests/unit -q` passed 2733 tests.
- `uv run ruff format src/wikidot/module/site_application.py tests/unit/test_site_application.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteApplication(site=site_a, user=User(client=site_b.client, ...), ...)` raises `ValueError("application.user must belong to the site")`.
- Accept/decline methods reject a mutated `application.user` from another client context before login checks, AMC requests, action-status handling, or member-cache mutation.
- Valid direct rows where `user.client is site.client` remain valid.
- Existing malformed `user` values still raise `ValueError("application.user must be an AbstractUser")`.
- Existing malformed `site`, malformed `text`, invalid action, malformed action-user ID/name, and action-status diagnostics remain unchanged.
- Existing parser-created application rows still produce valid `SiteApplication` records.
- Existing application-list parsing, retry behavior, response-body diagnostics, malformed applicant diagnostics, text spacing, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteApplication` is the durable row shape behind browser-free pending-application inventories, accept/decline actions, member-cache invalidation, membership ledgers, site-access audits, and migration checks. An application row is site-scoped, and parser-created users already come from the parent site's client. Constructor and action-time coherence validation keep direct fixtures, rehydrated rows, and mutated public fields from mixing site and applicant client contexts while preserving the normal parser and accept/decline paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed direct `SiteApplication(site=site_a, user=User(client=site_b.client, ...), ...)` construction silently accepted a contradictory row, and action-time mutation to another-client user reached accept action-status handling before validation.
- Existing local drafts covered application-list fetch retry, parser row scoping, response-body diagnostics, parser-side applicant extraction, direct user type validation, direct site type validation, direct text validation, action-user ID/name validation, accept/decline action-status diagnostics, and member-cache invalidation, but did not validate coherence between a valid applicant user object and a valid parent site.
- This slice only validates constructor-time and action-time applicant user/client coherence. It does not change application-list request construction, parser selectors, text extraction, user parser semantics, accept/decline payload fields, returned-status handling for valid rows, member-cache invalidation semantics, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw application-list HTML, private applicant names, application text, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, site IDs, UNIX names, or authentication state. The parser path and the rest of the object graph preserve client identity, and identity comparison avoids network lookups, login checks, and ambiguous cross-client equivalence rules.
