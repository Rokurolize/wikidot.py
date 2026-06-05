# PR Draft: Validate Site Lookup UNIX Name Inputs

## Summary

`client.site.get(unix_name)` and `Site.from_unix_name(client, unix_name)` document the site UNIX name as a string, but malformed caller-provided runtime values were not rejected with a stable public error. Non-string values reached `StringUtil.validate_site_unix_name(...)` and leaked raw regex errors such as `TypeError: expected string or bytes-like object, got 'dict'` before the normal Wikidot site-name validation message could run.

This change validates the shared Wikidot site UNIX-name helper before regex matching. Non-string values now raise `ValueError("site_name must be a string")` before host interpolation, direct site lookup, redirect handling, or HTTP requests. Existing malformed-string validation, valid site lookup, not-found behavior, site ID/title/domain parsing, SSL redirect handling, client accessor delegation, and Ajax connector behavior remain unchanged.

## Outcome

Site lookup callers now get deterministic Python-side preflight validation for malformed site-name inputs instead of raw regex implementation errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `client.site.get(...)`, `Site.from_unix_name(...)`, or shared site-name configuration for migration tooling, audit ledgers, moderation scripts, browser-free page workflows, and generated JSON/YAML/CLI-driven site selection.

## Current Evidence

Local rollout evidence repeatedly treats site lookup and site identity as practical read surfaces. Existing drafts [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [176-pr-site-member-fetch-failure-context.md](176-pr-site-member-fetch-failure-context.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [203-pr-site-page-get-miss-site-context.md](203-pr-site-page-get-miss-site-context.md), [310-pr-site-id-context.md](310-pr-site-id-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), and [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md) establish site identity, site lookup, and site-scoped workflows as practical surfaces.

Those prior slices are not duplicates. They covered member-list parsing, site-scoped diagnostics, malformed generated site IDs, site identity in result ledgers, and site member lookup username validation. They did not validate caller-provided site UNIX-name values before regex matching and direct site host construction. This slice follows the input-boundary pattern from [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), and [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), but applies it to public site lookup names.

## Related Issue

Builds directly on [103-pr-ignore-site-member-row-pager-markup.md](103-pr-ignore-site-member-row-pager-markup.md), [310-pr-site-id-context.md](310-pr-site-id-context.md), [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), and [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `StringUtil.validate_site_unix_name(site_name=...)` input type before regex matching.
- Ensure `Site.from_unix_name(...)` rejects non-string `unix_name` values before any direct site request is recorded.
- Ensure `client.site.get(...)` reaches the same validation boundary through the real `Site.from_unix_name(...)` path.
- Preserve malformed-string rejection, successful direct site lookup, not-found handling, SSL redirect detection, generated site metadata parsing, and client accessor delegation.

## Type Of Change

- Input validation
- Public API behavior hardening
- Site lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `StringUtil.validate_site_unix_name(...)` must reject non-string values with `ValueError("site_name must be a string")` before regex matching. |
| R2 | `Site.from_unix_name(..., unix_name=...)` must reject non-string values with `ValueError("site_name must be a string")` before host construction or direct HTTP requests. |
| R3 | `client.site.get(...)` must reach the same validation boundary through the real site lookup path. |
| R4 | Existing malformed-string site UNIX-name validation must remain unchanged. |
| R5 | Valid site lookup, not-found behavior, SSL redirect handling, site ID/title/domain parsing, Ajax connector site-name validation, and client accessor delegation must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent site/client/Ajax/stringutil tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-string helper inputs fail with stable `ValueError` before the regex engine receives them. | `TestStringUtilValidateSiteUnixName.test_non_string_site_names` failed RED before the fix with raw `TypeError`, then passed GREEN after validation was added. | Leaking regex `TypeError`, coercing dictionaries/lists/numbers to strings, or preserving a regex-dependent error rejects this local completion claim. | Site UNIX-name helper | `src/wikidot/util/stringutil.py`, `tests/unit/test_stringutil.py` |
| R2 | Non-string direct site lookup inputs fail before any HTTPX request is recorded. | `TestSiteFromUnixName.test_from_unix_name_non_string_name_rejected_before_request` failed RED before the fix with raw `TypeError`, then passed GREEN and asserts `httpx_mock.get_requests() == []`. | Building `http://<value>.wikidot.com`, following redirects, recording an HTTPX request, or leaking regex errors rejects this local completion claim. | Direct site lookup preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Client accessor lookup uses the same validation path. | `TestClientSiteAccessor.test_get_site_rejects_non_string_unix_name` failed RED before the fix with raw `TypeError`, then passed GREEN without mocking `Site.from_unix_name(...)`. | Mock-only coverage, bypassing `Site.from_unix_name(...)`, coercing malformed values, or leaking raw regex errors rejects this local completion claim. | Client site accessor | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R4 | Invalid string site names still fail with the existing invalid-name message before request work. | Existing invalid-string tests in `tests/unit/test_stringutil.py`, `tests/unit/test_site.py`, and `tests/unit/test_amc_client.py` passed in the adjacent run. | Accepting uppercase, blank, path, query, fragment, or host-breaking site names rejects this local completion claim. | Site-name syntax validation | stringutil/site/Ajax tests |
| R5 | Valid and adjacent site workflows remain green. | The adjacent 52-test run passed `TestStringUtilValidateSiteUnixName`, `TestSiteFromUnixName`, `TestClientSiteAccessor`, `TestAjaxModuleConnectorClientInit`, and `TestAjaxModuleConnectorClientRequest`; the full unit suite passed 973 tests. | Regressing valid site lookup, SSL redirect handling, not-found handling, generated site metadata parsing, Ajax connector construction, request override validation, or client accessor delegation rejects this local completion claim. | Site and Ajax workflows | adjacent tests and full unit |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic malformed values. | Using real site names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw site HTML, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0f976b6 fix(site): validate site lookup unix names`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_stringutil.py::TestStringUtilValidateSiteUnixName::test_non_string_site_names tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_non_string_name_rejected_before_request tests/unit/test_client.py::TestClientSiteAccessor::test_get_site_rejects_non_string_unix_name` failed before the fix with raw regex `TypeError` for `None`, `int`, and `dict` values.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_stringutil.py::TestStringUtilValidateSiteUnixName::test_non_string_site_names tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_non_string_name_rejected_before_request tests/unit/test_client.py::TestClientSiteAccessor::test_get_site_rejects_non_string_unix_name` passed 5 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_stringutil.py::TestStringUtilValidateSiteUnixName tests/unit/test_site.py::TestSiteFromUnixName tests/unit/test_client.py::TestClientSiteAccessor tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientInit tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest` passed 52 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 973 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `StringUtil.validate_site_unix_name({"site": "www"})` raises `ValueError("site_name must be a string")` instead of a regex `TypeError`.
- `Site.from_unix_name(client, {"site": "test-site"})` raises `ValueError("site_name must be a string")` before any HTTPX request is recorded.
- `client.site.get({"site": "scp-wiki"})` raises `ValueError("site_name must be a string")` through the real `Site.from_unix_name(...)` path.
- Existing invalid string values such as `"127.0.0.1:8000#"` still raise `ValueError("Invalid Wikidot site UNIX name: ...")` before any request.
- Valid site lookup, not-found behavior, SSL redirect handling, site ID/title/domain parsing, Ajax connector construction, Ajax request override validation, and client accessor delegation remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Site lookup is a small read-only helper, but it sits underneath page discovery, page publishing helpers, site-scoped audit ledgers, membership workflows, and generated automation. Runtime validation should reject malformed site selector values before direct host construction so JSON/YAML/CLI payload mistakes or generated structures do not trigger raw regex errors. The change is narrow: it keeps valid site lookup semantics and existing malformed-string rejection unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established site lookup, site identity, site-scoped diagnostics, and client accessors as practical surfaces.
- The focused RED failures showed malformed site lookup values crossing the public call boundary and leaking raw `TypeError` from regex matching.
- Existing site-related drafts covered member parsing, page lookup diagnostics, generated site ID parsing, result-ledger site fields, and site member username validation, but not malformed public site UNIX-name input preflight.
- This slice only validates site UNIX-name input type before regex matching. It does not change direct site GET request construction, redirect handling, generated metadata parsing, site dataclass fields, Ajax request payloads, client authentication, live Wikidot behavior, or parser diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw site HTML, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load site names from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to strings before calling wikidot.py site lookup helpers.
