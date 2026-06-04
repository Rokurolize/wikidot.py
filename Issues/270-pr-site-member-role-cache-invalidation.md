# PR Draft: Invalidate Site Role Caches After Member Permission Changes

## Summary

`Site.members`, `Site.moderators`, and `Site.admins` cache generated member-list reads on the `Site` object. `SiteMember.to_moderator()`, `remove_moderator()`, `to_admin()`, and `remove_admin()` successfully mutate the role membership views through `ManageSiteMembershipAction`, but before this slice they did not invalidate the cached role lists. Browser-free administration workflows could therefore promote or demote a user and then keep reading stale `site.moderators` or `site.admins` data from the pre-mutation cache.

This follow-up clears only the affected role cache after a confirmed successful role change. Moderator mutations clear `site._moderators`; admin mutations clear `site._admins`. The general `site._members` cache is preserved because the user remains a site member and `SiteMember` does not model role flags in the member object.

## Related Issue

Builds on [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), and [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md). Those drafts established retry-aware member-list reads, site invitation status validation, and role-change action-status validation as practical local site-administration surfaces.

No upstream issue was filed from this local workspace.

## Changes

- Clear `Site._moderators` after successful `toModerators` and `removeModerator` actions.
- Clear `Site._admins` after successful `toAdmins` and `removeAdmin` actions.
- Preserve the general `Site._members` cache across role changes.
- Preserve the unaffected role cache for the other role family.
- Add focused regressions for all four role-change public methods with seeded site caches.
- Extend the malformed role-change status regression to assert cached role lists are preserved on failure.

## Type Of Change

- Site member role local-state consistency
- Site role-list cache invalidation
- Browser-free site administration ergonomics
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Successful moderator role changes invalidate the cached moderator list. | `TestSiteMemberChangeGroup.test_change_group_success_invalidates_affected_role_cache` covers `to_moderator()` and `remove_moderator()` with seeded `_moderators` and asserts `_moderators is None`. | Reusing a cached `site.moderators` list after a successful moderator mutation rejects this local completion claim. |
| Successful admin role changes invalidate the cached admin list. | The same parameterized regression covers `to_admin()` and `remove_admin()` with seeded `_admins` and asserts `_admins is None`. | Reusing a cached `site.admins` list after a successful admin mutation rejects this local completion claim. |
| Role changes do not unnecessarily drop unrelated caches. | The focused regression asserts `_members` remains the same object and the unaffected role cache remains the same object after each mutation. | Clearing all member caches without need, or clearing the wrong role cache, rejects this local completion claim. |
| Failed role-change responses do not mutate cached role lists. | `TestSiteMemberChangeGroup.test_change_group_missing_action_status_includes_site_user_event_and_field_context` now seeds `_moderators` and `_admins` and asserts both survive a malformed action response. | Clearing role caches before status validation rejects this local completion claim. |
| Existing member-list acquisition, role-change, invitation, and lookup behavior remains intact. | `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup tests/unit/test_site_member.py::TestSiteMemberGet tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site.py::TestSiteMemberLookup -q` passed 38 tests. | Regressions in member reads, role-change payloads, invitations, or member lookup reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run --extra test pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `0c53f7c fix(site_member): invalidate role caches on change`.

- RED: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_success_invalidates_affected_role_cache -q` failed in all four parameterized cases because `_moderators` or `_admins` still referenced the stale cached list after successful role changes.
- GREEN: `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_success_invalidates_affected_role_cache tests/unit/test_site_member.py::TestSiteMemberChangeGroup::test_change_group_missing_action_status_includes_site_user_event_and_field_context -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_site_member.py::TestSiteMemberChangeGroup tests/unit/test_site_member.py::TestSiteMemberGet tests/unit/test_site.py::TestSiteInviteUser tests/unit/test_site.py::TestSiteMemberLookup -q` passed 38 tests.
- `uv run --extra test pytest tests/unit -q` passed 826 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Successful moderator promotions and removals clear `site._moderators`.
- Successful admin promotions and removals clear `site._admins`.
- Unaffected role caches and the general member cache are preserved.
- Missing or non-`ok` permission-change action statuses still prevent role-cache mutation.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Site administration scripts often read the current moderators or admins, perform a permission change, and then inspect the same role list again to verify or continue routing work. Cached role lists are useful for read-heavy workflows, but a successful role mutation makes the corresponding cached list stale. Invalidating the affected role cache after confirmed success keeps browser-free admin state coherent without changing request payloads, retry policy, member-list parsing, or failed-action behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts made member-list reads retry-aware and validated role-change action responses before accepting success. This slice connects those behaviors by invalidating the read cache after a successful role write.
- This slice intentionally targets only the cached moderator/admin role lists on the owning `Site`. It does not infer or mutate role flags on `SiteMember` objects, change member lookup, or force refetching the general member list.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, saved member names, private site membership data, page names from real sites, and site contents out of upstream discussion.

## Additional Notes

This is a local-state consistency fix. It does not alter member-list acquisition, parser behavior, invitation handling, application processing, role-change request construction, action-status parsing, or explicit status-code mappings; it only invalidates the affected cached role list after a confirmed successful permission change.
