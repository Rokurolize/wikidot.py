# PR Draft: Validate QuickModule Request Arguments

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` accept caller-provided `site_id` and `query` values before constructing a `quickmodule.php` GET request. Earlier local slices already retry transient QuickModule failures and report malformed JSON, response bodies, top-level result fields, row objects, missing row fields, malformed returned `user_id` values, and malformed result text fields. One request-boundary gap remained: direct public `QuickModule` calls could accept malformed `site_id` or `query` values and URL-encode them into an avoidable HTTP request.

This change validates direct QuickModule request arguments before request construction. `site_id` must be a non-boolean integer and `query` must be a string. Invalid direct inputs now raise deterministic `ValueError` messages before `httpx.get(...)` can be reached through the retry helper, while valid lookup request construction, URL encoding, retry behavior, site-not-found mapping, and response parsing remain unchanged.

## Outcome

Direct public QuickModule lookups now reject malformed request arguments locally instead of issuing remote lookup attempts with caller configuration mistakes serialized into the URL.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free QuickModule lookup directly for site member resolution, user resolution, page selection, generated moderation tools, migration ledgers, local fixtures, or CLI/config-driven automation.

## Current Evidence

QuickModule-related drafts [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md), and [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md) establish QuickModule lookup as a practical read surface and cover adjacent retry and response-parser boundaries.

Site member lookup drafts [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md) and [372-pr-validate-site-member-lookup-user-id.md](372-pr-validate-site-member-lookup-user-id.md) cover the higher-level `Site.member_lookup(...)` wrapper. They do not cover direct public `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, or `QuickModule.page_lookup(...)` calls.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of the prior QuickModule response-shape work. Those slices classify data returned by Wikidot after a request succeeds. This slice validates caller-provided request arguments before the request URL is built.

This is also not a duplicate of `Site.member_lookup(...)` input validation. The `QuickModule` class exposes direct member, user, and page lookup helpers, and direct use can bypass the `Site.member_lookup(...)` wrapper entirely.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_quickmodule_site_id(...)` for non-boolean integer site IDs.
- Add `_validate_quickmodule_query(...)` for string lookup queries.
- Validate `site_id` and `query` in `QuickModule._request(...)` after module-name validation and before `urlencode(...)`.
- Add focused regression tests proving malformed direct member/user/page lookup arguments fail before an HTTP request is attempted.

## Type Of Change

- Input validation
- QuickModule request-boundary hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` calls must reject non-integer `site_id` values, including booleans, before request construction. |
| R2 | Direct `QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` calls must reject non-string `query` values before request construction. |
| R3 | Valid lookup request construction, URL encoding, retry behavior, invalid-module handling, site-not-found mapping, empty-result handling, and response parser diagnostics must remain unchanged. |
| R4 | Existing adjacent Site/User workflows that depend on QuickModule lookup must remain green. |
| R5 | Focused RED/GREEN, QuickModule tests, adjacent workflow tests, full unit tests, lint, format, mypy, full pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct member, user, and page lookups raise `ValueError("site_id must be an integer")` for `None`, `True`, `"123456"`, `123456.0`, and `object()`. | `TestQuickModuleRequest.test_lookup_rejects_malformed_site_ids_before_request` failed RED because the mocked HTTP request was reached, then passed GREEN after validation was added. | URL-encoding malformed site IDs, accepting booleans as integers, or reaching `httpx.get(...)` rejects this local completion claim. | QuickModule request boundary | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R2 | Direct member, user, and page lookups raise `ValueError("query must be a string")` for `None`, `True`, `12345`, `[]`, and `object()`. | `TestQuickModuleRequest.test_lookup_rejects_malformed_queries_before_request` failed RED because the mocked HTTP request was reached, then passed GREEN after validation was added. | URL-encoding malformed queries, coercing query values to strings, or reaching `httpx.get(...)` rejects this local completion claim. | QuickModule request boundary | `src/wikidot/util/quick_module.py`, `tests/unit/test_quick_module.py` |
| R3 | Valid request behavior and existing QuickModule parser behavior remain unchanged. | `tests/unit/test_quick_module.py` passed 84 tests. | Regressing valid query serialization, transient retry, invalid module checks, final 500 site-not-found mapping, empty results, or Issues 313-320/339/494 diagnostics rejects this local completion claim. | QuickModule request and parser behavior | `tests/unit/test_quick_module.py` |
| R4 | Adjacent Site/User workflows remain compatible with the new request validators. | `tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py` passed 426 tests. | Breaking `Site.member_lookup(...)`, user lookup, site member workflows, or user record behavior rejects this local completion claim. | QuickModule consumers | `tests/unit/test_site.py`, `tests/unit/test_site_member.py`, `tests/unit/test_user.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, pyright, unit, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d8b8dc3 fix(quick_module): validate request arguments`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_quick_module.py::TestQuickModuleRequest::test_lookup_rejects_malformed_site_ids_before_request tests/unit/test_quick_module.py::TestQuickModuleRequest::test_lookup_rejects_malformed_queries_before_request` failed 30 malformed direct-lookup cases before the fix because the mocked HTTP request was reached.
- GREEN: the same focused command passed 30 tests after request-argument validation was added.
- `.venv/bin/python -m pytest -q tests/unit/test_quick_module.py` passed 84 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_user.py` passed 426 tests.
- `uv run ruff check src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` passed.
- `uv run ruff format --check src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` passed with 2 files already formatted after formatting the touched tests.
- `uv run mypy src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/util/quick_module.py tests/unit/test_quick_module.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `.venv/bin/python -m pytest -q tests/unit` passed 2186 tests.
- `git diff --check` passed.

## Acceptance Criteria

- `QuickModule.member_lookup(123456, "test-user")`, `QuickModule.user_lookup(123456, "test-user")`, and `QuickModule.page_lookup(123456, "test-page")` retain the existing request and response behavior.
- Direct QuickModule lookups reject malformed `site_id` values before `httpx.get(...)`.
- Direct QuickModule lookups reject malformed `query` values before `httpx.get(...)`.
- `bool` is not accepted as a valid site ID even though Python treats it as an `int` subclass.
- Existing QuickModule retry behavior, final 500 site-not-found mapping, invalid-module handling, empty-result handling, response parser diagnostics, adjacent Site/User workflows, live Wikidot semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, raw queries, and raw response bodies remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting booleans could surprise callers that accidentally passed `True` as `1`. Mitigation: booleans are configuration mistakes at this boundary and should not be serialized into remote site IDs.
- Risk: Request validation could change response-parser diagnostics. Mitigation: validators run only on caller-provided request arguments, while existing response-parser tests remain green.
- Risk: Higher-level wrapper validation could be mistaken as sufficient. Mitigation: direct `QuickModule` helpers remain public and are now covered explicitly.

## Dependencies

- Valid Wikidot site IDs are represented as integers in this library.
- QuickModule lookup queries are string values.
- Existing retry helper behavior remains responsible for transport failures and final status handling after validated request construction.

## Open Questions

None for this local slice. Future work can separately evaluate whether empty string queries should be rejected, but that would be a broader semantic choice than this scalar type guard.

## Upstream-Safe Motivation

QuickModule lookup is a browser-free read path used for member, user, and page selection. Direct request helpers should reject malformed caller data before building remote URLs, especially when inputs can come from generated configs, CLI payloads, spreadsheets, JSON/YAML data, or local fixtures. This keeps request logs and retry behavior focused on real remote lookup failures rather than avoidable caller-shape mistakes.

## Local Evidence

- Rollout-backed local drafts repeatedly use QuickModule lookup for site membership, user lookup, and page lookup workflows.
- Existing local drafts covered QuickModule request retry behavior and response parsing, but not direct public request argument validation.
- The focused RED failures showed malformed direct `site_id` and `query` values reached the mocked HTTP request path before this slice.
- This slice does not change valid URL encoding, module selection, retry policy, site-not-found mapping, QuickModule response parsing, live Wikidot behavior, site workflows, or private payload handling.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, real QuickModule response bodies, raw lookup query text, usernames, passwords, session cookies, credentials, auth JSON, and private user/member/page data out of upstream discussion.

## Additional Notes

The request validators intentionally run after the module-name allowlist. That preserves the existing invalid-module diagnostic while still rejecting malformed direct request arguments before URL construction.
