# PR Draft: Validate Site.member_lookup User ID Filter

## Summary

`Site.member_lookup(user_name, user_id=None)` documents `user_id` as `int | None`, but malformed caller-provided filter values were not rejected at the public API boundary. Values such as `True`, `"12345"`, `12345.0`, or `{"id": 12345}` could still call `QuickModule.member_lookup(...)` and then silently participate in membership-result comparison instead of failing deterministically before remote lookup work.

This change validates the optional `user_id` filter before QuickModule lookup calls. Invalid values now raise `ValueError("user_id must be an integer")`. Valid lookups, omitted `user_id`, matching and mismatching integer filters, returned user-name trimming, QuickModule request construction, QuickModule retry behavior, and QuickModule parser diagnostics remain unchanged.

## Outcome

Site membership lookup callers now get deterministic Python-side preflight validation for malformed optional user-ID filters instead of avoidable QuickModule lookup work or silent false/true decisions based on invalid comparison values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.member_lookup(...)` in site administration, access checks, membership audits, migration tooling, moderation helpers, invitation/application workflows, or generated membership ledgers.

## Current Evidence

Local rollout evidence repeatedly treats site membership and administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [255-pr-site-member-change-group-action-status-context.md](255-pr-site-member-change-group-action-status-context.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), and [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md) establish site member reads, direct member lookup, QuickModule lookup parsing, and adjacent membership mutation identity validation as practical surfaces.

Those prior slices are not duplicates. Issue 357 validated the public `user_name` argument and explicitly preserved optional `user_id` match/mismatch behavior, but it did not validate malformed `user_id` filter values before QuickModule lookup calls. QuickModule drafts validated returned row `user_id` values, not caller-provided filter values. Invitation and application drafts validated mutation target/applicant identities, not the read-only member lookup filter.

## Related Issue

Builds directly on [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), and [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `Site.member_lookup(user_id=...)` accepts only `None` or a non-boolean integer before calling `QuickModule.member_lookup(...)`.
- Preserve `user_name` validation from Issue 357.
- Preserve successful lookup behavior, empty result behavior, omitted `user_id`, matching integer `user_id`, mismatching integer `user_id`, returned user-name trimming, QuickModule request construction, QuickModule retry behavior, and QuickModule parser diagnostics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Site membership lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.member_lookup(user_id=...)` must reject non-integer and boolean values with `ValueError("user_id must be an integer")` before QuickModule lookup calls. |
| R2 | `Site.member_lookup(user_id=None)` and omitted `user_id` must keep existing behavior. |
| R3 | Valid integer `user_id` match/mismatch behavior must remain unchanged. |
| R4 | Existing `user_name` validation, QuickModule response diagnostics, retry behavior, and adjacent site member/application/user workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent site/member/application/user/QuickModule tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed user-ID filters fail before QuickModule lookup calls. | `TestSiteMemberLookup.test_member_lookup_rejects_non_integer_user_id_before_quickmodule` failed RED before the fix for `True`, `"12345"`, `12345.0`, and a dict because no `ValueError` was raised, then passed GREEN after validation was added. | Calling `QuickModule.member_lookup(...)`, accepting bool as integer ID 1, coercing strings/floats/dicts, or returning a lookup result rejects this local completion claim. | Site member lookup preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Omitted and `None` user-ID filters keep existing behavior. | Existing `TestSiteMemberLookup.test_member_lookup_found` and not-found tests passed. | Requiring a user ID, rejecting omitted/`None`, changing return type, or changing empty-result behavior rejects this local completion claim. | Site member lookup behavior | `tests/unit/test_site.py` |
| R3 | Integer user-ID filter semantics remain unchanged. | Existing `test_member_lookup_with_user_id_match` and `test_member_lookup_with_user_id_mismatch` passed in the focused member-lookup group and adjacent run. | Ignoring explicit mismatching IDs, requiring exact match when omitted, losing returned name trimming, or changing matching integer behavior rejects this local completion claim. | Site member lookup behavior | `tests/unit/test_site.py` |
| R4 | QuickModule parser and adjacent site administration workflows remain green. | `tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_quick_module.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py` passed 126 tests, and the full unit suite passed 1054 tests. | Regressing QuickModule retries, malformed JSON/response/key/field/row/user-ID diagnostics, member-list parsing, member role changes, application actions, invitation workflows, or user profile lookup rejects this local completion claim. | Site administration and QuickModule workflows | affected site/member/application/user/QuickModule tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw QuickModule responses, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1fcb183 fix(site): validate member lookup user id`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_rejects_non_integer_user_id_before_quickmodule` failed before the fix with 4 failures because malformed `user_id` values did not raise `ValueError`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_rejects_non_integer_user_id_before_quickmodule` passed 4 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteMemberLookup` passed 9 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_quick_module.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py` passed 126 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1054 tests.
- `.venv/bin/ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.member_lookup("test-user", user_id=True)` raises `ValueError("user_id must be an integer")` before calling `QuickModule.member_lookup(...)`.
- `site.member_lookup("test-user", user_id="12345")`, `user_id=12345.0`, and `user_id={"id": 12345}` raise the same `ValueError` before QuickModule lookup work.
- `site.member_lookup("test-user")` still calls `QuickModule.member_lookup(site.id, "test-user")`.
- `site.member_lookup("test-user", user_id=12345)` still returns `True` when the returned member has ID 12345.
- `site.member_lookup("test-user", user_id=99999)` still returns `False` when the returned member has a different ID.
- Existing username validation, QuickModule malformed JSON, missing response key, malformed response body, malformed result field, malformed row, missing row field, malformed returned user ID diagnostics, member-list workflows, site application workflows, invitation workflows, and user workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Site.member_lookup(...)` is often fed by generated configs, ledgers, CLI payloads, spreadsheets, JSON/YAML inputs, and prior crawler output. The optional user-ID filter is part of the public lookup contract, so malformed values should fail deterministically before remote QuickModule work. The change is narrow: it rejects malformed values instead of coercing them and leaves valid lookup semantics and existing QuickModule diagnostics unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established site member reads, site applications, member invitations, role changes, direct member lookup, and QuickModule parser diagnostics as practical surfaces.
- The focused RED failure showed malformed member lookup `user_id` filters crossing the public call boundary without a stable validation failure.
- Existing Issue 357 covered malformed `user_name`, while QuickModule drafts covered returned response and row shape. Neither validated caller-provided `Site.member_lookup(user_id=...)` inputs.
- This slice only validates the optional site member lookup user-ID filter. It does not change member-list parsing, site application parsing, site invitation actions, member permission changes, QuickModule response parsing, QuickModule retry behavior, username validation, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load lookup user IDs from text sources should parse and validate them as integers before calling `Site.member_lookup(...)`.
