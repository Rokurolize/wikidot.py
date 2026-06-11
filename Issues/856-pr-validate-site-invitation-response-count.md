# PR: Validate site invitation response count

## Problem Statement

`Site.invite_user(...)` sends one direct `ManageSiteMembershipAction` AMC request and then immediately indexed the first returned response. Before this change, a connector, mock, or adapter that returned zero responses leaked Python's raw `IndexError("tuple index out of range")` before wikidot.py could explain which site, invite target, and action broke the direct action batch contract.

This was a low-context failure at a browser-free membership invitation mutation boundary. It also bypassed the existing invitation action diagnostics that already attach site, user, event, status-field, and malformed-payload context.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free site invitations as practical infrastructure for membership onboarding, moderation workflows, migration notifications, generated membership ledgers, local fixtures, and site administration tooling. Existing local slices hardened site invitations around invitation text, retained site/client state, invite-target shape, invite-target client ownership, invite-target ID range, missing action status, malformed action status type, explicit non-ok status mapping, and non-mapping action payloads. They did not validate the direct `ManageSiteMembershipAction` response count before selecting the single returned response.

The local fix is committed as `1bd370a`.

## Affected Workflows

- Browser-free site invitations through `Site.invite_user(...)`.
- Generated membership onboarding, migration, notification, or moderation scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct invitation responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small site invitation action response-count guard. Validate that the direct invitation response sequence has exactly one entry before indexing and parsing it. Raise `UnexpectedException` with site, invite-target user, event, expected count, and actual count on mismatch.

## Implementation Notes

The change adds `_require_site_invitation_action_response_count(...)` next to the existing site invitation action-status helper. `Site.invite_user(...)` now stores the raw `self.amc_request(...)` result, validates the count, then parses `responses[0].json()` through the existing `_require_site_invitation_action_status(...)` helper.

The guard intentionally stays local to site invitation action handling instead of adding a generic `Site.amc_request(...)` response-count policy. Direct action callers already have domain-specific diagnostics, and a broad site-level guard could preempt more useful page, forum, member, application, or invitation context.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_site.py::TestSiteInviteUser::test_invite_user_rejects_response_count_mismatch_before_parsing -q
uv run pytest tests/unit/test_site.py::TestSiteInviteUser -q
uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

The focused RED run failed before the fix because an empty direct invitation response tuple leaked raw `IndexError("tuple index out of range")`. The focused GREEN run passed after adding the count guard. `TestSiteInviteUser` passed 19 tests, adjacent site/member/application/user coverage passed 682 tests, full unit verification passed 3977 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid invitation calls still send the same `ManageSiteMembershipAction` request body and parse action status before treating the invitation as successful.
- Existing invitation text, retained site/client, invite-target shape, invite-target client ownership, invite-target ID range, malformed payload, missing action status, malformed status type, explicit non-ok status, `already_invited`, and `already_member` behavior remain unchanged.
- Mismatched response-count failures occur before response JSON parsing or duplicate-invitation status mapping.
- The diagnostic does not include raw generated module bodies, raw response JSON, invitation text, credentials, cookies, auth JSON, local rollout paths, account material, or private member data.

## Rationale For Upstream Suitability

Direct site invitations rely on positional correspondence between the submitted action and returned response. When that correspondence is broken, wikidot.py should report the site invitation action response-count failure directly instead of leaking a raw Python indexing error.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, request construction, target-user validation, action status parsing, duplicate-invitation mapping, live Wikidot behavior, or upstream filing state.
