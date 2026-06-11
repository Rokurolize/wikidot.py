# PR: Validate site member action response counts

## Problem Statement

`SiteMember.to_moderator()`, `SiteMember.remove_moderator()`, `SiteMember.to_admin()`, and `SiteMember.remove_admin()` share `_change_group(...)`, which sends one direct `ManageSiteMembershipAction` AMC request and then immediately indexes the first returned response. Before this change, a connector, mock, or adapter that returned zero responses leaked Python's raw `IndexError("list index out of range")` before wikidot.py could explain which site, member, and role-change action broke the direct action batch contract.

This was a low-context failure at a membership role mutation boundary. It also bypassed the existing action diagnostics that preserve moderator/admin caches until the returned action status is confirmed.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free membership role administration as practical infrastructure for site access audits, moderation workflows, generated membership ledgers, migration checks, local tests, and role maintenance automation. Existing local slices hardened site members around member-list reads, retained site/client state, action user validation, user ID ranges, role cache invalidation, action payload shape, missing action status, malformed action status type, and explicit non-ok status mapping. They did not validate the direct `ManageSiteMembershipAction` response count before indexing the returned response sequence.

The local fix is committed as `404a5c9`.

## Affected Workflows

- Browser-free moderator promotion through `SiteMember.to_moderator()`.
- Browser-free moderator removal through `SiteMember.remove_moderator()`.
- Browser-free administrator promotion through `SiteMember.to_admin()`.
- Browser-free administrator removal through `SiteMember.remove_admin()`.
- Generated access-audit, migration, or moderation scripts that wrap or mock `site.amc_request(...)`.
- Fixture-backed tests where a malformed adapter returns the wrong number of direct action responses.
- Debugging malformed connector behavior where response count, not payload shape, is the first broken contract.

## Proposed Fix

Add a small site member action response-count guard. Validate that the direct role-change response sequence has exactly one entry before indexing and parsing it. Raise `UnexpectedException` with site/member/event context and expected/actual counts on mismatch.

## Implementation Notes

The change adds `_require_site_member_action_response_count(...)` next to the existing site member action-status helper. `_change_group(...)` now stores the raw `site.amc_request(...)` result, validates the count, then parses `responses[0].json()` through the existing `_require_site_member_action_status(...)` helper.

The guard intentionally stays local to site member action handling instead of adding a generic `Site.amc_request(...)` response-count policy. Direct action callers already have domain-specific diagnostics, and a broad site-level guard could preempt more useful page/forum/member/application context.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_rejects_action_response_count_mismatch_before_parsing -q --tb=short
uv run pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup -q --tb=short
uv run pytest tests/unit/test_site_member.py -q --tb=short
uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_user.py -q --tb=short
uv run pytest tests/unit -q --tb=short
uv run ruff check
uv run ruff format --check
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix because the new regression leaked raw `IndexError` from indexing the empty response list. The focused GREEN run passed after adding the count guard. Full unit verification passed 3967 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Compatibility And Risk Notes

- Valid role changes still send the same `ManageSiteMembershipAction` request body and parse action status before treating the mutation as successful.
- Existing member user validation, user ID range, malformed payload, missing action status, malformed status type, explicit non-ok status, and cache-invalidation diagnostics remain unchanged.
- Mismatched response-count failures preserve the site moderators and admins caches before role-specific invalidation can run.
- The diagnostic does not include raw generated module bodies, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Rationale For Upstream Suitability

Direct site member role changes rely on positional correspondence between the submitted action and returned response. When that correspondence is broken, wikidot.py should report the site member action response-count failure directly instead of leaking a raw Python indexing error.

## Scope

This slice does not change retry policy, direct `site.amc_request(...)` behavior, request construction, member validation, action status parsing, role cache invalidation on valid success, live Wikidot behavior, or upstream filing state.
