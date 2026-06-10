# PR Draft: Validate Site Administration Action Clients

## Summary

`Site.invite_user(...)`, `SiteApplication.acquire_all(...)`, `SiteApplication.accept()` / `decline()`, and `SiteMember` role-change helpers now validate retained `site.client` state before authentication. After Issues 800, 801, and 802 covered page and forum retained-client action paths, these were the remaining direct site-administration paths still calling `site.client.login_check()` or `self.client.login_check()` without first checking that the retained client was still a `Client`.

This change adds narrow retained-client validators at those action boundaries. Valid invitation, application-list, application accept/decline, and member role-change behavior, input validation precedence, request payloads, response diagnostics, and cache invalidation behavior remain unchanged.

## Problem Statement

Site-administration helpers should not authenticate, fetch lists, issue AMC requests, parse generated responses, or mutate local caches through corrupted retained parent-client state. Before this slice, a valid `Site` could have its public `client` field replaced after construction. The affected helpers then authenticated through that malformed object and could continue toward list response parsing, action-status parsing, or later AMC request-state validation instead of reporting the established `ValueError("client must be a Client")` before login.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free site administration as a practical workflow surface: invitations, member inventories, application queues, application accept/decline, role changes, cache invalidation, and generated membership tooling. Directly related drafts include [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), [619-pr-validate-site-invite-user-client.md](619-pr-validate-site-invite-user-client.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [556-pr-validate-site-application-acquire-site.md](556-pr-validate-site-application-acquire-site.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [605-pr-validate-site-member-user-client.md](605-pr-validate-site-member-user-client.md), [800-pr-validate-page-save-site-clients.md](800-pr-validate-page-save-site-clients.md), [801-pr-validate-page-action-site-clients.md](801-pr-validate-page-action-site-clients.md), and [802-pr-validate-forum-action-site-clients.md](802-pr-validate-forum-action-site-clients.md).

This slice is not a duplicate of [701-pr-validate-site-constructor-client.md](701-pr-validate-site-constructor-client.md), which rejects malformed `Site(client=...)` constructor input. It cannot cover a valid `Site` whose public `client` field is replaced later.

This slice is not a duplicate of [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md), which validates retained `Site` request state at `Site.amc_request(...)` and `Site.amc_request_with_retry(...)`. These site-administration helpers authenticate through `site.client.login_check()` before reaching those request wrappers.

This slice is not a duplicate of Issues 619, 605, or 606. Those drafts validate whether target users, members, and applications belong to the same client context as the site; this draft validates that the retained site client itself is still a `Client` before authentication.

This slice is not a duplicate of Issues 800, 801, or 802. Those drafts cover page save/action and forum action entry points; this draft covers the remaining site invitation, application, and member-administration entry points.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free site invitations through `Site.invite_user(...)`.
- Pending application list acquisition through `SiteApplication.acquire_all(...)` and `site.applications`.
- Pending application acceptance and decline through `SiteApplication.accept()` and `SiteApplication.decline()`.
- Member role promotion and demotion through `SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()`.
- Generated membership jobs, moderation scripts, migration tooling, serialized administration records, and local tests that may rehydrate or mutate retained `Site` state before action work.

## Proposed Fix

- Reuse `_validate_site_client(self.client)` in `Site.invite_user(...)` after existing text, user-shape, and user/site coherence validation and before `login_check()`.
- Add module-local retained-site-client validators to `site_application.py` and `site_member.py` that lazily import `Client` and raise `ValueError("client must be a Client")`.
- Use the validators after existing site/user/coherence preflights and before `login_check()`.
- Authenticate through the validated client object.
- Leave request construction, response parsing, local mutation, and cache invalidation behavior unchanged for valid `Site` and `Client` parents.

## Implementation Notes

Implemented locally in commit `7aa3752 fix(site): validate admin action clients`.

The implementation intentionally keeps client validation local to each module. `site.py` already owns `_validate_site_client(...)`; `site_application.py` and `site_member.py` use small module-local helpers to preserve import direction and avoid coupling those modules back to the site module for a single retained-state guard.

The focused RED failures demonstrated the shared boundary gap:

- `Site.invite_user(...)` called the malformed retained client's `login_check()` before failing later.
- `SiteApplication.acquire_all(...)` reached application-list response-body diagnostics with a malformed retained client.
- `SiteApplication.accept()` reached application action-status diagnostics with a malformed retained client.
- `SiteMember.to_moderator()` reached member action-status diagnostics with a malformed retained client.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Site.invite_user(...)` rejects mutated retained `site.client` before login or invitation request work. | `TestSiteInviteUser.test_invite_user_rejects_mutated_site_client_before_login` failed RED because malformed `login_check()` was called, then passed GREEN. | Calling malformed `login_check()`, calling the malformed AMC client, or leaking later invitation diagnostics rejects this claim. |
| `SiteApplication.acquire_all(...)` rejects mutated retained `site.client` before login, retry work, response-body parsing, or applicant parsing. | `TestSiteApplicationAcquireAll.test_acquire_all_rejects_mutated_site_client_before_login` failed RED with application-list response-body diagnostics, then passed GREEN. | Calling malformed `login_check()`, calling `site.amc_request_with_retry(...)`, or leaking response-body diagnostics rejects this claim. |
| `SiteApplication.accept()` / `decline()` reject mutated retained `application.site.client` before login, AMC requests, action-status parsing, or member-cache mutation. | `TestSiteApplicationProcess.test_accept_rejects_mutated_site_client_before_login` failed RED with action-status diagnostics, then passed GREEN. | Calling malformed `login_check()`, calling `site.amc_request(...)`, mutating `site._members`, or leaking action-status diagnostics rejects this claim. |
| `SiteMember` role changes reject mutated retained `member.site.client` before login, AMC requests, action-status parsing, or role-cache mutation. | `TestSiteMemberChangeGroup.test_change_group_rejects_mutated_site_client_before_login` failed RED with action-status diagnostics, then passed GREEN. | Calling malformed `login_check()`, calling `site.amc_request(...)`, clearing `_moderators`, clearing `_admins`, or leaking action-status diagnostics rejects this claim. |
| Existing validation precedence and valid site-administration behavior remain stable. | Affected invite/application/member action classes passed 95 tests; full touched modules passed 536 tests; full unit passed 3892 tests. | Moving retained-client validation before malformed explicit inputs or regressing valid administration calls rejects this claim. |
| Repository quality gates remain green. | Ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `7aa3752 fix(site): validate admin action clients`.

- RED vertical cases:
  - `uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_mutated_site_client_before_login -q --tb=short` failed before the fix because malformed `login_check()` was called.
  - `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_rejects_mutated_site_client_before_login -q --tb=short` failed before the fix with malformed application-list response-body diagnostics.
  - `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_mutated_site_client_before_login -q --tb=short` failed before the fix with malformed application action-status diagnostics.
  - `uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_mutated_site_client_before_login -q --tb=short` failed before the fix with malformed member action-status diagnostics.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_mutated_site_client_before_login tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_rejects_mutated_site_client_before_login tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_rejects_mutated_site_client_before_login tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_mutated_site_client_before_login -q --tb=short` passed 4 tests.
- Affected action classes: `uv run pytest tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site_application.py::TestSiteApplicationAcquireAll tests/unit/test_site_application.py::TestSiteApplicationProcess tests/unit/test_site_member.py::TestSiteMemberChangeGroup -q --tb=short` passed 95 tests.
- Full touched modules: `uv run pytest tests/unit/test_site.py tests/unit/test_site_application.py tests/unit/test_site_member.py -q --tb=short` passed 536 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3892 tests.
- `uv run ruff check .` passed after correcting one import-order issue.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Source scan after the change found no remaining direct `site.client.login_check()` or `self.client.login_check()` calls in the touched site/page/forum action modules.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Site.invite_user(...)` with a valid `Site` whose retained `client` has been replaced by a non-`Client` object raises `ValueError("client must be a Client")` before login, invitation request construction, returned-status parsing, or duplicate-invitation mapping.
- `SiteApplication.acquire_all(...)` with a mutated non-`Client` retained `site.client` raises `ValueError("client must be a Client")` before login, retry work, response-body parsing, forbidden-page checks, applicant parsing, or application construction.
- `SiteApplication.accept()` and `SiteApplication.decline()` with a mutated non-`Client` retained `application.site.client` raise `ValueError("client must be a Client")` before login, AMC request work, action-status parsing, `no_application` mapping, or member-cache invalidation.
- `SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` with a mutated non-`Client` retained `member.site.client` raise `ValueError("client must be a Client")` before login, AMC request work, action-status parsing, target-error mapping, or role-cache invalidation.
- Existing explicit input validation, retained site validation, retained user validation, target/user client-coherence validation, action-status parsing, retry behavior, successful local mutation, and cache invalidation behavior remain unchanged for valid `Client` parents.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: Earlier client validation could change precedence for calls that pass both malformed retained client state and malformed explicit action inputs. Mitigation: client validation is placed after existing explicit input, retained-site, retained-user, and user/site coherence validators.
- Risk: This could be confused with user/client coherence validation. Mitigation: Issues 619, 605, and 606 cover whether target users belong to the site; this draft covers whether the site's retained client is a `Client`.
- Risk: Adding module-local helpers duplicates a small client check. Mitigation: the duplication is narrow, preserves import direction, and keeps the established diagnostic without introducing a broader abstraction.
- Risk: A broad site-admin slice could hide method-specific behavior changes. Mitigation: each method has a focused RED/GREEN regression plus affected class, touched module, and full unit verification.

## Dependencies

- Existing `Client` class identity remains the parent-client contract.
- Existing invitation text/user validators define public input validation precedence.
- Existing `SiteApplication` site/user/text validators and user/site coherence validators define application action precedence.
- Existing `SiteMember` site/user/joined-at validators and user/site coherence validators define role-change precedence.
- Existing response validators continue to define malformed remote response diagnostics after valid authentication and request work.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, result ergonomics, cache ownership checks, cross-owner batch checks, or complexity candidates outside this now-covered site-administration retained-client boundary.

## Rationale for Upstream Suitability

The change makes documented site-administration helpers fail locally and deterministically when their retained parent client is corrupted, using the same client diagnostic already enforced by constructor, AMC request-state, page save/action, and forum action validators. It prevents authentication and administration-side work from starting with malformed parent-client state while preserving valid browser-free invitations, application-list acquisition, application processing, role changes, response handling, local mutation, and cache invalidation.

## Local Evidence

- Local browser-free maintenance drafts repeatedly use invitations, application queues, application processing, member lists, and role changes to administer sites without browser automation.
- Existing local drafts covered invitation target validation, site-application site/user/text validation, site-member site/user/joined-at validation, target/user client coherence, response diagnostics, retry behavior, and cache invalidation ordering. They did not cover post-construction retained `Site.client` mutation before these site-administration authentication calls.
- This slice only validates retained client state for site-administration entry points. It does not change live Wikidot behavior, member-list parsers, application-list parsers, request payload shapes, response parsing, action response parsing, cache invalidation timing, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw application text, raw member lists, private site data, and private membership metadata out of upstream discussion.

## Additional Notes

Callers that mutate or rehydrate site-administration records should keep `site.client`, `application.site.client`, and `member.site.client` as real `Client` instances before invoking invitation, application, or role-change APIs.
