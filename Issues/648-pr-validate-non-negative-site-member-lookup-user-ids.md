# PR Draft: Validate Non-Negative Site Member Lookup User IDs

## Summary

`Site.member_lookup(user_name, user_id=None)` accepts an optional caller-provided Wikidot user ID filter and compares it against `QuickModule.member_lookup(...)` results. Existing local drafts validate malformed filter types, blank member-lookup names, returned QuickModule user IDs, and direct `User`/`DeletedUser` IDs, but this higher-level caller filter still accepted negative integers such as `-1`.

This change validates the optional `Site.member_lookup(...)` `user_id` filter as a non-negative integer before calling QuickModule. It deliberately preserves omitted and `None` filters, preserves integer match/mismatch behavior, and preserves `0` as a non-negative filter value.

## Outcome

Negative member-lookup user-ID filters now fail locally before any QuickModule request is attempted, while valid omitted, `None`, zero, matching, and mismatching filters keep their existing behavior. Existing malformed type diagnostics, blank user-name validation, QuickModule user result validation, site membership workflows, site application workflows, and direct user-record validation remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.member_lookup(...)` to check membership by display name and optional numeric user identity in browser-free membership tooling, generated member ledgers, site administration helpers, adapters, fixtures, or local automation.

## Current Evidence

Membership and user-identity drafts [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [624-pr-validate-blank-member-lookup-names.md](624-pr-validate-blank-member-lookup-names.md), [645-pr-validate-non-negative-site-ids.md](645-pr-validate-non-negative-site-ids.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), and [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md) establish member lookup, site identity, QuickModule user results, and user IDs as practical local automation surfaces.

This slice is not a duplicate of Issues 372, 624, 645, 646, or 647. Issue 372 validates malformed `user_id` filter types and preserves `ValueError("user_id must be an integer")`. Issue 624 validates blank `user_name` values. Issue 645 validates direct `Site.id` and QuickModule site IDs. Issue 646 validates `QMCUser` records and returned QuickModule row IDs. Issue 647 validates direct `User` and `DeletedUser` record IDs. None of those drafts reject a negative caller-provided `Site.member_lookup(..., user_id=-1)` filter before QuickModule.

## Related Issue / Non-Duplicate Analysis

Builds directly on [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [624-pr-validate-blank-member-lookup-names.md](624-pr-validate-blank-member-lookup-names.md), [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md), and [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject `Site.member_lookup("test-user", user_id=-1)` and `user_id=-100` with `ValueError("user_id must be non-negative")`.
- Reject negative `user_id` filters before `QuickModule.member_lookup(...)` is called.
- Preserve `ValueError("user_id must be an integer")` for non-integer and boolean filters.
- Preserve `Site.member_lookup("test-user", user_id=0)` as a valid non-negative filter.
- Preserve omitted, `None`, integer match, and integer mismatch behavior.
- Leave QuickModule parsing, returned QuickModule user ID validation, direct `User`/`DeletedUser` constructors, Site identity validation, live Wikidot behavior, pushes, upstream Issues, and upstream PRs unchanged.

## Type Of Change

- Input validation
- Public method argument hardening
- Membership lookup identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.member_lookup(..., user_id=-1)` and `user_id=-100` must raise `ValueError("user_id must be non-negative")` before QuickModule is called. |
| R2 | Existing malformed filter type diagnostics must remain `ValueError("user_id must be an integer")`. |
| R3 | Omitted, `None`, matching integer, mismatching integer, and zero `user_id` filters must remain valid for covered tests. |
| R4 | Existing blank `user_name`, QuickModule user result validation, SiteMember, SiteApplication, and User workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user/member/site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, member-lookup tests, adjacent membership/user tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative caller-provided member-lookup user-ID filters cannot reach QuickModule. | `test_member_lookup_rejects_negative_user_id_before_quickmodule` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_optional_user_id(...)` rejected values below zero. | Accepting negative filters, calling QuickModule before rejecting them, or silently converting them rejects this local completion claim. | `Site.member_lookup` argument validation | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Existing malformed filter type diagnostics remain stable. | `test_member_lookup_rejects_non_integer_user_id_before_quickmodule` passed in the focused RED and GREEN commands. | Changing the type diagnostic, accepting booleans, or moving malformed values into QuickModule rejects this local completion claim. | `Site.member_lookup` argument validation | `tests/unit/test_site.py` |
| R3 | Valid optional and non-negative filter behavior remains stable. | `test_member_lookup_with_user_id_match`, `test_member_lookup_with_user_id_mismatch`, and `test_member_lookup_with_zero_user_id_match` passed in the focused RED and GREEN commands, and the full member-lookup class passed 14 tests. | Rejecting `None`, omitted filters, zero, normal matches, or normal mismatches rejects this local completion claim. | Membership lookup compatibility | `tests/unit/test_site.py` |
| R4 | Adjacent membership and user workflows remain green. | Adjacent `Site.member_lookup`/QuickModule/SiteMember/SiteApplication/User coverage passed 357 tests, and the full unit suite passed 2940 tests. | Regressing blank-name validation, returned QuickModule user ID validation, member list behavior, applications, direct user records, or site workflows rejects this local completion claim. | Membership and user consumers | `tests/unit/test_site.py`, `tests/unit/test_quick_module.py`, `tests/unit/test_site_member.py`, `tests/unit/test_site_application.py`, `tests/unit/test_user.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw member markup from real sites, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, member-lookup tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bafba51 fix(site): validate non-negative member lookup user ids`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_rejects_non_integer_user_id_before_quickmodule tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_rejects_negative_user_id_before_quickmodule tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_with_zero_user_id_match -q` failed 2 negative member-lookup user-ID filter cases before the fix; 5 malformed-input and zero-compatibility guards stayed green.
- GREEN: the same focused command passed 7 tests after optional filter range validation was added.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left both files unchanged.
- Re-running the same focused command after formatting passed 7 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteMemberLookup -q` passed 14 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_quick_module.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 357 tests.
- `uv run pytest tests/unit -q` passed 2940 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Site.member_lookup("test-user", user_id=-1)` raises `ValueError("user_id must be non-negative")`.
- `Site.member_lookup("test-user", user_id=-100)` raises the same `ValueError`.
- Negative filters are rejected before `QuickModule.member_lookup(...)` is called.
- `Site.member_lookup("test-user", user_id=0)` remains accepted and can match a `QMCUser(id=0, ...)` result.
- Omitted and `None` filters continue to match by user name only.
- Existing positive integer match and mismatch behavior remains unchanged.
- Direct `Site.member_lookup(..., user_id=True)`, `user_id="12345"`, `user_id=12345.0`, and other malformed filter types continue to raise `ValueError("user_id must be an integer")`.
- Existing blank user-name validation, QuickModule result validation, direct user-record validation, site identity validation, adjacent workflows, live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Site.member_lookup(...)` is a small but public membership lookup boundary. A negative `user_id` filter is impossible Wikidot identity state, but it is still an integer and previously flowed into QuickModule lookup before silently failing to match. Rejecting the filter locally makes invalid caller state explicit while preserving all valid optional and non-negative lookup modes.

## Local Evidence

- Local rollout-backed drafts repeatedly use member lookup, QuickModule users, direct users, site membership, applications, generated ledgers, fixtures, and browser-free membership automation.
- Existing local drafts covered malformed member-lookup filter types, blank member-lookup names, returned QuickModule user IDs, and direct user-record IDs, but did not cover negative caller-provided `Site.member_lookup` filters.
- The focused RED failures showed negative member-lookup user-ID filters were accepted before this slice.
- This slice only validates non-negative optional `Site.member_lookup` filter IDs. It does not change QuickModule request construction for valid filters, result parsing, name comparison, direct user constructors, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw member markup from real sites, private member data, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates only the caller-provided `Site.member_lookup` filter. QuickModule returned user rows and direct user records are covered by separate local drafts so each PR-sized slice remains independently reviewable.
