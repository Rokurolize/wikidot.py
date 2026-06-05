# PR Draft: Validate Site.member_lookup Username Before QuickModule Lookup

## Summary

`Site.member_lookup(user_name, user_id=None)` documents `user_name` as a string lookup query, but malformed non-string values were not rejected at the public API boundary. Those values could flow directly into `QuickModule.member_lookup(...)`, making caller configuration mistakes look like downstream QuickModule request or parser behavior.

This change validates `user_name` before QuickModule request construction or membership-result comparison. Invalid values now raise `ValueError("user_name must be a string")`. Valid member lookups, empty results, user ID matching, QuickModule response diagnostics, retry behavior, and request payload construction remain unchanged.

## Outcome

Site membership lookup callers now get deterministic Python-side preflight validation for malformed username queries instead of a remote QuickModule lookup attempt or confusing downstream behavior.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.member_lookup(...)` in site administration, access checks, membership audits, migration tooling, moderation helpers, or invitation/application workflows.

## Current Evidence

Local rollout evidence repeatedly treats site membership and administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [253-pr-site-invite-action-status-context.md](253-pr-site-invite-action-status-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), and [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md) establish site member reads, direct member lookup, and QuickModule lookup parsing as practical surfaces.

Those prior slices are not duplicates. They covered member-list fetches, member-list parser diagnostics, membership mutation action-status validation, QuickModule retry behavior, decoded QuickModule response diagnostics, row-shape diagnostics, and malformed returned user IDs. They did not validate the public `Site.member_lookup(user_name=...)` input before calling QuickModule. This slice follows the input-boundary pattern from [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), and [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), but applies it to a read-only site membership lookup.

## Related Issue

Builds directly on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), and [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `Site.member_lookup(user_name=...)` before calling `QuickModule.member_lookup(...)`.
- Reuse the existing text-field validator already used by page and site public text inputs.
- Preserve successful lookup behavior, empty result behavior, optional `user_id` matching, returned user-name trimming, QuickModule request construction, QuickModule retry behavior, and QuickModule parser diagnostics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Site membership lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.member_lookup(user_name=...)` must reject non-string username values with `ValueError("user_name must be a string")` before QuickModule lookup calls. |
| R2 | Valid member lookups must keep the existing QuickModule call shape and successful match behavior. |
| R3 | Empty results and optional `user_id` match/mismatch behavior must remain unchanged. |
| R4 | Existing QuickModule response diagnostics, retry behavior, and adjacent site member/application workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent site/member/application/QuickModule tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-string username queries fail before QuickModule lookup calls. | `TestSiteMemberLookup.test_member_lookup_rejects_non_string_user_name_before_quickmodule` failed RED before the fix because invalid `user_name` did not raise `ValueError`, then passed GREEN after validation was added. | Calling `QuickModule.member_lookup(...)`, accepting the malformed query, coercing dictionaries/lists/numbers to strings, or leaking QuickModule/parser/request errors rejects this local completion claim. | Site member lookup preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid lookup behavior remains unchanged. | Existing `TestSiteMemberLookup.test_member_lookup_found` passed in the adjacent run and still asserts `QuickModule.member_lookup(123456, "test-user")`. | Changing the QuickModule module, site ID, query string, return type, or successful match rule rejects this local completion claim. | Site member lookup behavior | `tests/unit/test_site.py` |
| R3 | Empty and user ID filter behavior remains unchanged. | Existing `TestSiteMemberLookup` tests for not-found, matching `user_id`, and mismatching `user_id` passed in the adjacent run. | Returning true for empty lookup results, ignoring explicit mismatching user IDs, requiring user IDs when omitted, or removing returned name trimming rejects this local completion claim. | Site member lookup behavior | `tests/unit/test_site.py` |
| R4 | QuickModule parser and site administration workflows remain green. | `tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_quick_module.py tests/unit/test_site_member.py tests/unit/test_site_application.py` passed 99 tests; the full unit suite passed 965 tests. | Regressing QuickModule retries, QuickModule malformed JSON/response/key/field/row/user-ID diagnostics, member-list parsing, member role changes, application actions, or invitation workflows rejects this local completion claim. | Site administration and QuickModule workflows | affected site/member/application/QuickModule tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw QuickModule responses, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent site/member/application/QuickModule tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1691646 fix(site): validate member lookup username`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_rejects_non_string_user_name_before_quickmodule` failed before the fix because invalid `user_name` did not raise `ValueError`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_rejects_non_string_user_name_before_quickmodule` passed 1 test.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_quick_module.py tests/unit/test_site_member.py tests/unit/test_site_application.py` passed 99 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 965 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.member_lookup({"name": "test-user"})` raises `ValueError("user_name must be a string")` before calling `QuickModule.member_lookup(...)`.
- `site.member_lookup("test-user")` still calls `QuickModule.member_lookup(site.id, "test-user")`.
- Matching returned user names still return `True`.
- Empty QuickModule user results still return `False`.
- Explicit matching `user_id` values still return `True`.
- Explicit mismatching `user_id` values still return `False`.
- Existing QuickModule malformed JSON, missing response key, malformed response body, malformed result field, malformed row, missing row field, and malformed returned user ID diagnostics remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Site.member_lookup(...)` is a small read-only helper, but it sits on a real membership workflow surface and delegates directly to a remote QuickModule lookup. Runtime validation should reject malformed username queries before request construction so generated configs, CLI payloads, spreadsheets, JSON/YAML inputs, or caller mistakes do not trigger avoidable remote lookup work or confusing downstream parser behavior. The change is narrow: it keeps valid lookup semantics and existing QuickModule diagnostics unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established site member reads, site applications, member invitations, role changes, direct member lookup, and QuickModule parser diagnostics as practical surfaces.
- The focused RED failure showed malformed member lookup usernames crossing the public call boundary without a stable validation failure.
- Existing QuickModule drafts covered returned response and row shape, but not malformed public `Site.member_lookup(user_name=...)` inputs.
- This slice only validates site member lookup username inputs. It does not change member-list parsing, site application parsing, site invitation actions, member permission changes, QuickModule response parsing, QuickModule retry behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load lookup usernames from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to strings before calling `Site.member_lookup(...)`.
