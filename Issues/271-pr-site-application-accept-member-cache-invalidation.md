# PR Draft: Invalidate Member Cache After Accepting Site Applications

## Summary

`Site.applications` fetches pending join applications each time, but `Site.members` caches the site member list on `site._members`. `SiteApplication.accept()` successfully adds the applicant as a site member through `ManageSiteMembershipAction`, yet before this slice it left any cached `site._members` list untouched. Browser-free administration workflows could accept an application and then read a stale member list that still omitted the accepted user.

This follow-up clears `site._members` after a confirmed successful application acceptance. Declines preserve the member cache because declining an application does not add a member. Moderator and admin role-list caches are also preserved because accepting a basic application does not grant those roles.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), and [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md). Those drafts established pending-application reads, application action-status validation, and membership cache invalidation as practical local site-administration surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Clear `Site._members` after successful `SiteApplication.accept()`.
- Preserve `Site._members` after successful `SiteApplication.decline()`.
- Preserve `Site._moderators` and `Site._admins` when accepting an application.
- Preserve `Site._members` when accept action-status validation fails.
- Add focused regressions for successful accept, successful decline, and malformed accept behavior.

## Type Of Change

- Site application local-state consistency
- Site member-list cache invalidation
- Browser-free site administration ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful application acceptance invalidates the general member-list cache. | `TestSiteApplicationProcess.test_accept_success_invalidates_members_cache` seeds `_members`, accepts an application, and asserts `_members is None`. | Reusing a cached `site.members` list after a successful application accept rejects this local completion claim. |
| Successful application decline preserves the member-list cache. | `TestSiteApplicationProcess.test_decline_success_preserves_members_cache` seeds `_members`, declines an application, and asserts the cache object is unchanged. | Clearing the member cache after decline rejects this local completion claim. |
| Application acceptance does not clear unrelated role-list caches. | The accept-cache regression seeds `_moderators` and `_admins` and asserts both are preserved. | Clearing moderator/admin caches for a basic application accept rejects this local completion claim. |
| Failed accept responses do not mutate member-list cache state. | `TestSiteApplicationProcess.test_accept_missing_action_status_includes_site_user_event_type_and_field_context` now seeds `_members` and asserts it survives a malformed accept action response. | Clearing `_members` before action-status validation rejects this local completion claim. |
| Existing application acquisition, application processing, member-list, role-change, and invitation behavior remains intact. | `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess tests/unit/test_site_application.py::TestSiteApplicationAcquireAll tests/unit/test_site_member.py::TestSiteMemberGet tests/unit/test_site_member.py::TestSiteMemberChangeGroup tests/unit/test_site.py::TestSiteInviteUser -q` passed 56 tests. | Regressions in application reads/actions, member reads, role changes, or invitations reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `40722ab fix(site_application): invalidate members cache on accept`.

- RED: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_success_invalidates_members_cache -q` failed before the fix because `site._members` still referenced the stale cached list after successful accept.
- GREEN: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_success_invalidates_members_cache tests/unit/test_site_application.py::TestSiteApplicationProcess::test_decline_success_preserves_members_cache tests/unit/test_site_application.py::TestSiteApplicationProcess::test_accept_missing_action_status_includes_site_user_event_type_and_field_context -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess tests/unit/test_site_application.py::TestSiteApplicationAcquireAll tests/unit/test_site_member.py::TestSiteMemberGet tests/unit/test_site_member.py::TestSiteMemberChangeGroup tests/unit/test_site.py::TestSiteInviteUser -q` passed 56 tests.
- `uv run --extra test pytest tests/unit -q` passed 828 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful `SiteApplication.accept()` clears `site._members`.
- Successful `SiteApplication.decline()` preserves `site._members`.
- Successful application acceptance preserves `site._moderators` and `site._admins`.
- Missing or non-`ok` accept action statuses still prevent member-cache mutation.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Application handling scripts often inspect applications, accept one, and then inspect members to verify or route follow-up work. A cached member list is useful for reads, but accepting an application changes the membership set. Invalidating the general member cache after confirmed acceptance keeps browser-free site administration state coherent without changing application request payloads, action-status validation, retry policy, member-list parsing, or decline behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts made application reads retry-aware, validated application action responses before accepting success, and invalidated site role-list caches after role changes. This slice applies the same write/read cache rule to the application acceptance path that actually adds a new member.
- This slice intentionally targets only the owning site's general member-list cache. It does not cache application lists, update role caches, infer role flags, change invitations, or alter member lookup.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved applicant names/text, private site membership data, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a local-state consistency fix. It does not alter application acquisition, parser behavior, accept/decline request construction, decline notification text, action-status parsing, explicit status-code mappings, site invitations, or role-change behavior; it only invalidates the general member-list cache after a confirmed successful application acceptance.
