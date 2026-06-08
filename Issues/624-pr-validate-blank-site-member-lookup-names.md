# PR Draft: Validate Blank Site Member Lookup Names

## Summary

`Site.member_lookup(user_name, user_id=None)` already rejects non-string username queries, but empty strings and whitespace-only strings still passed validation and reached `QuickModule.member_lookup(...)`. A blank query is not a useful membership lookup target and can trigger avoidable remote QuickModule work from generated configs, CLI inputs, spreadsheets, or filtered lookup queues.

This change rejects blank site member lookup names before QuickModule request construction. Valid member lookups, non-string username diagnostics, optional `user_id` validation, empty result behavior, matching and mismatching user-ID filters, returned user-name trimming, QuickModule response diagnostics, retry behavior, and adjacent site member/application/user workflows remain unchanged.

## Outcome

Site membership lookup callers now get deterministic preflight failures for blank username queries instead of sending empty or whitespace-only lookup terms into QuickModule.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.member_lookup(...)` in site administration, access checks, membership audits, migration tooling, moderation helpers, invitation/application workflows, generated membership ledgers, or browser-free member resolution.

## Current Evidence

Local rollout-backed drafts repeatedly identify site membership and administration as practical workflow surfaces. Existing drafts [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md), [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [213-pr-site-member-list-response-body-context.md](213-pr-site-member-list-response-body-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), and QuickModule diagnostics [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), and [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md) establish member lookup and QuickModule parsing as active operational boundaries.

This is not a duplicate of Issue 357. Issue 357 validates that `user_name` is a string; it does not reject empty or whitespace-only strings.

This is not a duplicate of Issue 623. Issue 623 validates direct user profile lookup helpers. This slice covers the separate site membership lookup wrapper that delegates to QuickModule.

No upstream issue was filed from this local workspace.

## Changes

- Add a `Site.member_lookup(...)`-specific username validator that keeps the existing `ValueError("user_name must be a string")` type diagnostic.
- Reject `site.member_lookup("")` and whitespace-only variants with `ValueError("user_name must not be empty")` before `QuickModule.member_lookup(...)`.
- Preserve valid lookup behavior, empty QuickModule result behavior, optional user-ID matching, QuickModule request shape, QuickModule parser diagnostics, and adjacent member/application/user workflows.
- Avoid changing the shared `_validate_page_text_field(...)` helper because page/source/title/comment fields intentionally allow empty strings in other contexts.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Blank site member lookup names must raise `ValueError("user_name must not be empty")` before `QuickModule.member_lookup(...)` is called. |
| R2 | Non-string `user_name` values must continue to raise `ValueError("user_name must be a string")` before QuickModule calls. |
| R3 | Valid member lookup names, empty QuickModule results, and matching/mismatching `user_id` filter behavior must remain unchanged. |
| R4 | Existing QuickModule diagnostics, retry behavior, member-list parsing, site application workflows, invitation workflows, and user lookup workflows must remain unchanged. |
| R5 | Focused RED/GREEN, adjacent site/member/application/user/QuickModule tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Blank member lookup names fail before QuickModule work. | `test_member_lookup_rejects_blank_user_name_before_quickmodule` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after `_validate_member_lookup_user_name(...)` rejected blank strings. | Calling `QuickModule.member_lookup(...)`, accepting blank queries, stripping and continuing, or returning a lookup result rejects this local completion claim. | `Site.member_lookup(...)` | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Existing type diagnostics remain stable. | Existing non-string username validation passed in adjacent `TestSiteMemberLookup` coverage. | Changing `ValueError("user_name must be a string")` or checking blankness before type validation rejects this local completion claim. | Lookup preflight | `tests/unit/test_site.py` |
| R3 | Valid lookup semantics remain unchanged. | `TestSiteMemberLookup` passed 11 tests, including found, not-found, user-ID match/mismatch, non-string name rejection, blank name rejection, and malformed user-ID rejection. | Changing the QuickModule site ID/query, returned-name trimming, empty result behavior, or user-ID match rule rejects this local completion claim. | Site member lookup behavior | `tests/unit/test_site.py` |
| R4 | Adjacent workflows remain green. | Adjacent site member lookup, QuickModule, site member, site application, and user coverage passed 318 tests; full unit passed 2803 tests. | Regressing QuickModule retries, malformed JSON/response/key/field/row/user-ID diagnostics, member-list parsing, member role changes, application actions, invitation workflows, or user profile lookup rejects this local completion claim. | Site administration and QuickModule workflows | `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic `Site` state and a patched `QuickModule.member_lookup(...)` only; this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c963d11 fix(site): validate blank member lookup names`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteMemberLookup::test_member_lookup_rejects_blank_user_name_before_quickmodule -q` failed 2 cases with `DID NOT RAISE`.
- GREEN focused: the same command passed 2 tests after blank member lookup names were rejected before QuickModule calls.
- Adjacent coverage: `uv run pytest tests/unit/test_site.py::TestSiteMemberLookup tests/unit/test_quick_module.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 318 tests.
- `uv run pytest tests/unit -q` passed 2803 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `site.member_lookup("")` and `site.member_lookup("   ")` raise `ValueError("user_name must not be empty")` before `QuickModule.member_lookup(...)` is called.
- `site.member_lookup({"name": "test-user"})` still raises `ValueError("user_name must be a string")` before QuickModule calls.
- `site.member_lookup("test-user")` still calls `QuickModule.member_lookup(site.id, "test-user")`.
- Matching returned user names still return `True`.
- Empty QuickModule results still return `False`.
- Explicit matching and mismatching integer `user_id` filters keep the existing behavior.
- Existing QuickModule malformed JSON, missing response key, malformed response body, malformed result field, malformed row, missing row field, malformed returned user ID diagnostics, member-list workflows, site application workflows, invitation workflows, and user workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Site.member_lookup(...)` is a read-only helper, but it sits on practical membership administration surfaces and delegates directly to QuickModule. Runtime validation should reject blank username queries before request construction so generated configs, CLI payloads, spreadsheets, JSON/YAML inputs, or filtered queues do not trigger avoidable remote lookup work. The change is narrow and keeps valid lookup semantics and existing QuickModule diagnostics unchanged.

## Local Evidence, Not For Upstream Paste

- The focused RED run showed blank member lookup usernames crossing the public call boundary without a stable validation failure.
- Existing Issue 357 covered non-string `user_name` values, Issue 372 covered malformed `user_id` filters, and Issue 623 covered direct profile lookup blank names. None validates blank `Site.member_lookup(user_name=...)` inputs.
- This slice only validates blank site member lookup username inputs. It does not change member-list parsing, site application parsing, site invitation actions, member permission changes, QuickModule response parsing, QuickModule retry behavior, direct user profile lookup behavior, shared page text validation, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The new helper deliberately does not strip valid names before returning them. It only rejects strings whose stripped form is empty and leaves existing lookup comparison behavior unchanged.
