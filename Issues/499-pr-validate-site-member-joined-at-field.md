# PR Draft: Validate SiteMember Joined-At Field

## Summary

`SiteMember` records carry browser-free member-list rows for `Site.members`, `Site.admins`, `Site.moderators`, direct `SiteMember.get(site, group)` calls, role-change follow-ups, generated membership ledgers, and local fixtures. Earlier local slices validated member-list fetch retries, row scoping, response-body diagnostics, parsed member-user diagnostics, parsed joined-at diagnostics, role-change action responses, role-cache invalidation, member lookup inputs, action-user preflight, and the direct `SiteMember.user` constructor field. One direct record-state gap remained: `SiteMember(..., joined_at=...)` still accepted arbitrary non-`datetime` values such as booleans, epoch integers, date strings, and lists.

This change validates `SiteMember.joined_at` at initialization. The field remains optional: `datetime` values and `None` are accepted. Other values now raise `ValueError("joined_at must be a datetime or None")` before malformed local state can be stored, while valid member-list parsing, rows without joined-at timestamps, role-change behavior, member lookup behavior, site application behavior, site workflows, and user workflows remain unchanged.

## Outcome

Callers cannot silently construct site-member records with malformed joined-date state, while parser-created members and valid direct `SiteMember(...)` construction keep the existing optional timestamp semantics.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free member inventories, `site.members`, `site.moderators`, `site.admins`, direct `SiteMember.get(site, group)` calls, generated membership ledgers, role-change automation, site-access audits, local fixtures, or serialized and rehydrated member rows.

## Current Evidence

Site-member drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [270-pr-site-member-role-cache-invalidation.md](270-pr-site-member-role-cache-invalidation.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), and [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md) establish member acquisition, parser diagnostics, response diagnostics, role-change response validation, role-cache synchronization, lookup validation, action-user preflight, and direct member-user state as practical operational boundaries.

Adjacent constructor-hardening drafts [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), [487-pr-validate-page-constructor-nullable-metadata.md](487-pr-validate-page-constructor-nullable-metadata.md), and [498-pr-validate-private-message-record-fields.md](498-pr-validate-private-message-record-fields.md) establish the local pattern for validating direct dataclass timestamp state instead of relying only on parser boundaries.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 290. Issue 290 catches malformed generated member-list `span.odate` metadata at the parser boundary and converts it into contextual `NoElementException`. This slice validates direct `SiteMember(joined_at=...)` construction used by fixtures, generated ledgers, rehydrated records, and downstream local state after parser output has already become a field value.

This is not a duplicate of Issue 448. Issue 448 validates only `SiteMember.user` at construction and explicitly left `joined_at` outside its scope. This slice validates the separate optional timestamp field while preserving the same valid user semantics and role-change action preflight.

This is not a duplicate of Issues 410, 357, or 372. Those slices validate role-change user state and member lookup inputs. This slice validates stored member-row timestamp state and does not change mutation request construction or lookup request construction.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_site_member_joined_at(...)` for optional stored member join timestamps.
- Update `SiteMember.__post_init__` to validate `joined_at` after the existing user validation.
- Preserve valid `datetime` timestamps and `joined_at=None`.
- Reject malformed direct constructor values with `ValueError("joined_at must be a datetime or None")`.
- Add focused constructor regressions for boolean, epoch integer, date-string, and list values.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site-member record state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteMember(joined_at=True)`, `1700000000`, `"2024-01-01"`, and `[]` must raise `ValueError("joined_at must be a datetime or None")` when every other constructor field is valid. |
| R2 | Valid `datetime` values and `joined_at=None` must remain valid constructor inputs and preserve stored values. |
| R3 | Existing member-list parsing, rows without joined-at timestamps, parser-side joined-at diagnostics, pagination, retry behavior, group selection, response diagnostics, role-change behavior, role-cache invalidation, site application behavior, site workflows, and user workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private membership data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, site-member tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor joined-at values fail at the public dataclass boundary. | `TestSiteMemberDataclass.test_init_rejects_malformed_joined_at` failed RED for 4 malformed values, then passed GREEN after validation was added. | Accepting booleans, epoch integers, date strings, lists, arbitrary objects, or emitting member rows with non-datetime joined-at state rejects this local completion claim. | SiteMember constructor | `src/wikidot/module/site_member.py`, `tests/unit/test_site_member.py` |
| R2 | Optional valid joined-at semantics stay green. | Existing dataclass tests for valid `datetime` and `None` passed with the new validator. | Rejecting `None`, coercing strings or epoch integers, changing stored datetime values, or requiring timezone normalization rejects this local completion claim. | Parser-created and manually created members | `tests/unit/test_site_member.py` |
| R3 | Existing site-member and adjacent workflows remain green. | `tests/unit/test_site_member.py` passed 51 tests and the full unit suite passed 2207 tests. | Regressing member-list acquisition, optional missing timestamps, malformed generated timestamp diagnostics, response-body validation, pagination, retry behavior, group validation, role changes, role-cache invalidation, site application processing, site read/write helpers, or user profile workflows rejects this local completion claim. | Site member and adjacent workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw member-list HTML, private member names, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, pyright, unit, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `db6f97e fix(site_member): validate joined_at field`.

- RED: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_malformed_joined_at -q` failed 4 tests before the fix; every malformed `joined_at` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site_member.py::TestSiteMemberDataclass::test_init_rejects_malformed_joined_at -q` passed 4 tests.
- `uv run pytest tests/unit/test_site_member.py -q` passed 51 tests.
- `uv run ruff check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed.
- `uv run ruff format --check src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/site_member.py tests/unit/test_site_member.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2207 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteMember(joined_at=True)`, `1700000000`, `"2024-01-01"`, and `[]` raise `ValueError("joined_at must be a datetime or None")`.
- Valid `datetime` values remain valid as `joined_at`.
- `joined_at=None` remains valid for member rows where Wikidot does not expose a join date.
- Existing member-list parsing, optional missing timestamps, malformed parser-side joined-at diagnostics, response-body diagnostics, pagination, retry behavior, group validation, role-change behavior, role-cache invalidation, site application behavior, site workflows, and user workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private membership data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with parser diagnostics. Mitigation: parser-boundary malformed `span.odate` diagnostics remain covered separately by Issue 290 and unchanged by this slice.
- Risk: Rejecting date strings could surprise callers loading JSON or spreadsheets. Mitigation: `SiteMember.joined_at` is typed as `datetime | None`; callers should normalize external serialized values before constructing records rather than relying on implicit coercion.
- Risk: Timezone policy could accidentally expand scope. Mitigation: this change validates type only and does not normalize timezone, parse epoch values, or require aware datetimes.

## Dependencies

- Valid member-list parser output continues to produce `datetime` values through the shared `odate_parser(...)` utility or `None` when no timestamp is present.
- `SiteMember` remains the stored row shape for member, admin, and moderator list reads.
- Existing role-change preflight remains responsible for action-specific user ID and user name validation.

## Open Questions

None for this local slice. A future separate change can evaluate whether `SiteMember.site` should be validated at construction, but that would require its own duplicate analysis and circular-import-safe implementation.

## Upstream-Safe Motivation

`SiteMember.joined_at` is the optional join-date state behind browser-free membership inventories, role-administration ledgers, site-access audits, and rehydrated member rows. Parser paths already return `datetime` or `None` and report malformed generated timestamp metadata with site/group/page/row context. Constructor validation keeps malformed local timestamp state out of manually constructed records without changing member-list acquisition, parser diagnostics, role changes, cache behavior, or live Wikidot interactions.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used browser-free member-list acquisition, generated membership state, role-change actions, role-cache invalidation, direct member lookup, site application processing, and tests that construct `SiteMember` records directly.
- Existing local drafts covered member-list fetch retry behavior, parser row scoping, response-body diagnostics, malformed parsed member users, malformed parsed joined-at timestamps, action-status validation, role-cache invalidation, member lookup inputs, action-user preflight, and direct member-user validation, but did not cover direct `SiteMember(joined_at=...)` construction.
- The focused RED failures showed invalid constructor joined-at values were accepted as dataclass state. The GREEN regression covers boolean, epoch integer, date-string, and list values.
- This slice only validates stored site-member joined-at type at construction. It does not change member-list acquisition, parser selectors, joined-at parsing, missing joined-at behavior, response-body diagnostics, member lookup, role-change action status, role-cache invalidation, site application behavior, live site behavior, or timestamp timezone policy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw member-list HTML, private member names, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load member records from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize optional join-date values into `datetime` or `None` before constructing `SiteMember` objects.
