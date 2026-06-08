# PR Draft: Validate QuickModule Blank User Lookup Queries

## Summary

`QuickModule.member_lookup(...)` and `QuickModule.user_lookup(...)` already reject malformed non-string query values, but empty strings and whitespace-only strings still passed validation and were serialized into `quickmodule.php` URLs as `q=` or `q=+++`. These direct public helpers can bypass the higher-level `Site.member_lookup(...)` wrapper, so generated configs, CLI inputs, spreadsheets, JSON/YAML payloads, or filtered lookup queues could still trigger avoidable remote member/user lookup work with a blank identity query.

This change rejects blank direct QuickModule member/user queries before request construction while leaving `QuickModule.page_lookup(...)` blank-query behavior unchanged. Valid member/user lookups, non-string query diagnostics, site-ID validation, page lookup request behavior, URL encoding, retry behavior, site-not-found mapping, empty-result handling, and QuickModule response parser diagnostics remain unchanged.

## Outcome

Direct QuickModule member and user lookup callers now get deterministic preflight failures for blank identity queries instead of issuing remote lookup attempts with empty query text.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `QuickModule.member_lookup(...)` or `QuickModule.user_lookup(...)` directly for browser-free member resolution, user resolution, site administration, generated moderation helpers, migration ledgers, local fixtures, or CLI/config-driven automation.

## Current Evidence

QuickModule-related drafts [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), and [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md) establish QuickModule lookup as a practical read surface and cover adjacent retry, response-parser, and request-argument boundaries.

Issue [497-pr-validate-quickmodule-request-arguments.md](497-pr-validate-quickmodule-request-arguments.md) explicitly scoped request-argument validation to scalar type checks and left empty-string query semantics as future work. This slice resolves that open question only for member/user identity lookup queries. It deliberately does not reject blank page lookup queries because page search semantics are broader than identity resolution.

Higher-level wrapper drafts [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md), [623-pr-validate-blank-user-profile-lookup-names.md](623-pr-validate-blank-user-profile-lookup-names.md), and [624-pr-validate-blank-site-member-lookup-names.md](624-pr-validate-blank-site-member-lookup-names.md) cover separate public lookup boundaries. They do not cover direct public `QuickModule.member_lookup(...)` or `QuickModule.user_lookup(...)` calls.

No upstream issue was filed from this local workspace.

## Changes

- Add a member/user-specific QuickModule query validator that preserves the existing `ValueError("query must be a string")` diagnostic for non-string values.
- Reject `QuickModule.member_lookup(site_id, "")`, whitespace-only variants, `QuickModule.user_lookup(site_id, "")`, and whitespace-only variants with `ValueError("query must not be empty")` before `httpx.get(...)`.
- Preserve `QuickModule.page_lookup(site_id, "")` request behavior and response parsing.
- Preserve valid member/user lookup behavior, site-ID validation, URL encoding, retry behavior, site-not-found mapping, empty-result handling, and existing response parser diagnostics.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `QuickModule.member_lookup(...)` and `QuickModule.user_lookup(...)` calls must reject blank and whitespace-only query strings with `ValueError("query must not be empty")` before request construction. |
| R2 | Non-string query values for direct member, user, and page lookups must continue to raise `ValueError("query must be a string")` before request construction. |
| R3 | Direct `QuickModule.page_lookup(...)` blank-query request behavior must remain unchanged. |
| R4 | Valid member, user, and page lookup request construction, URL encoding, retry behavior, site-not-found mapping, empty-result handling, and response parser diagnostics must remain unchanged. |
| R5 | Adjacent `Site.member_lookup(...)`, user lookup, site member, and QuickModule consumer workflows must remain green. |
| R6 | Focused RED/GREEN, QuickModule tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct blank member/user queries fail before HTTP. | `test_user_lookups_reject_blank_queries_before_request` failed RED for `""` and `"   "` across member and user lookups because the patched HTTP layer was reached, then passed GREEN after `_validate_quickmodule_user_query(...)` rejected blank strings. | Reaching `httpx.get(...)`, URL-encoding `q=` or whitespace-only `q=+++`, accepting blank queries, stripping and continuing, or returning lookup rows rejects this local completion claim. | Direct QuickModule member/user lookup | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R2 | Existing type diagnostics remain stable. | Existing `test_lookup_rejects_malformed_queries_before_request` coverage passed for member, user, and page lookups. | Changing `ValueError("query must be a string")`, checking blankness before type validation, accepting bools/numbers/containers, or reaching HTTP for malformed queries rejects this local completion claim. | Direct QuickModule request boundary | `tests/unit/test_quick_module.py` |
| R3 | Page blank-query behavior remains unchanged. | `test_page_lookup_allows_blank_query` passed in the focused RED and GREEN runs and asserted `PageLookupQModule`, `s=123456`, and `q=` were still sent through the existing request path. | Rejecting blank page queries, changing the module, omitting `q=`, or bypassing existing page response parsing rejects this local completion claim. | Direct QuickModule page lookup | `tests/unit/test_quick_module.py` |
| R4 | Valid request and parser behavior remains unchanged. | `tests/unit/test_quick_module.py` passed 89 tests. | Regressing valid query serialization, transient retry, invalid module checks, final 500 site-not-found mapping, empty results, malformed JSON/response/key/field/row diagnostics, malformed user IDs, or result text validation rejects this local completion claim. | QuickModule request and parser behavior | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R5 | Adjacent workflows remain green. | `tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py` passed 549 tests. | Breaking `Site.member_lookup(...)`, direct user/profile lookup, site member workflows, QuickModule consumers, or wrapper-level blank lookup validation rejects this local completion claim. | QuickModule consumers | `tests/unit/test_site.py`, `tests/unit/test_site_member.py`, `tests/unit/test_user.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit passed 2808 tests; full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | The regressions use patched unit-level HTTP responses only; this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private member data, private user data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `bad2bf9 fix(quickmodule): validate blank user lookup queries`.

- RED: `uv run pytest tests/unit/test_quick_module.py::TestQuickModuleRequest::test_user_lookups_reject_blank_queries_before_request tests/unit/test_quick_module.py::TestQuickModuleRequest::test_page_lookup_allows_blank_query -q` failed 4 member/user blank-query cases because `httpx.get(...)` was reached with `q=` or whitespace-encoded `q=+++`; the page blank-query preservation case passed.
- GREEN focused: the same command passed 5 tests after blank member/user queries were rejected before request construction and page lookup remained on the existing request path.
- QuickModule coverage: `uv run pytest tests/unit/test_quick_module.py -q` passed 89 tests.
- Adjacent coverage: `uv run pytest tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py -q` passed 549 tests.
- `uv run pytest tests/unit -q` passed 2808 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `QuickModule.member_lookup(123456, "")`, `QuickModule.member_lookup(123456, "   ")`, `QuickModule.user_lookup(123456, "")`, and `QuickModule.user_lookup(123456, "   ")` raise `ValueError("query must not be empty")` before `httpx.get(...)`.
- `QuickModule.member_lookup(123456, None)`, `QuickModule.user_lookup(123456, True)`, and malformed page lookup query values still raise `ValueError("query must be a string")`.
- `QuickModule.page_lookup(123456, "")` still constructs a `PageLookupQModule` request with `q=` and parses the response normally.
- `QuickModule.member_lookup(123456, "test-user")`, `QuickModule.user_lookup(123456, "test-user")`, and `QuickModule.page_lookup(123456, "test-page")` retain existing request and response behavior.
- Existing QuickModule retry behavior, final 500 site-not-found mapping, invalid-module handling, empty-result handling, response parser diagnostics, wrapper-level `Site.member_lookup(...)` validation, direct profile lookup behavior, live Wikidot semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, raw queries, and raw response bodies remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

QuickModule member and user lookup are browser-free identity resolution paths. Direct request helpers should reject blank identity queries before building remote URLs, especially when inputs can come from generated configs, CLI payloads, spreadsheets, JSON/YAML data, local fixtures, or filtered rollout queues. The change is deliberately narrower than global QuickModule query validation because page lookup can have broader search semantics and should not be changed without separate evidence.

## Local Evidence, Not For Upstream Paste

- The focused RED run showed blank direct member/user queries reaching the mocked HTTP request path as `q=` and whitespace-only queries as `q=+++`.
- Issue 497 covered non-string QuickModule query validation and explicitly left empty-string query semantics as future work.
- Issues 623 and 624 cover blank higher-level profile and site member lookup inputs, but direct public `QuickModule.member_lookup(...)` and `QuickModule.user_lookup(...)` can bypass those wrappers.
- This slice only validates blank direct member/user QuickModule queries. It does not change page lookup blank-query behavior, general query syntax, URL encoding for valid strings, site-ID validation, retry behavior, QuickModule response parsing, wrapper-level site member lookup behavior, direct profile lookup behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw QuickModule response bodies, private member data, private user data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The new helper deliberately does not strip valid queries before returning them. It only rejects strings whose stripped form is empty and leaves existing URL encoding and valid query semantics unchanged.
