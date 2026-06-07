# PR Draft: Validate RequestUtil URL String Values

## Summary

`RequestUtil.request(client, method, urls, return_exceptions=False)` already validates the HTTP method, URL container shape, URL entry types, `return_exceptions`, empty URL batches, parent client type, nested config/header state, and numeric request controls. One adjacent URL-boundary gap remained: malformed string values such as `""`, `"not-a-url"`, `"/relative/path"`, `"ftp://example.com/test"`, and `"https://"` passed URL preflight because they were strings.

This change validates each URL string as an absolute HTTP(S) URL with a hostname before client validation, config/header access, semaphore setup, async client construction, HTTP work, or retry loops. Malformed URL strings now raise `ValueError("urls must be absolute HTTP(S) URLs")` deterministically while empty URL batches still return `[]`, non-string URL entries still raise `ValueError("urls must be a list of strings")`, and valid `http://` / `https://` request behavior remains unchanged.

## Outcome

Malformed direct URL string values now fail at the RequestUtil URL boundary instead of falling through to client/config validation or lower-level request diagnostics.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using direct URL GET/POST batches, generated local fixtures, JSON/YAML adapters, archival workflows, profile lookup flows, page probing flows, or local CI fixtures where malformed URL strings should fail before client validation and network setup.

## Current Evidence

Local rollout-backed drafts repeatedly identify `RequestUtil.request(...)` as practical shared infrastructure. Existing drafts [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), [517-pr-validate-requestutil-method-urls.md](517-pr-validate-requestutil-method-urls.md), [523-pr-validate-requestutil-config-object.md](523-pr-validate-requestutil-config-object.md), [528-pr-validate-requestutil-header-object.md](528-pr-validate-requestutil-header-object.md), and [551-pr-validate-requestutil-client.md](551-pr-validate-requestutil-client.md) establish RequestUtil public-boundary validation as an active operational surface.

This is not a duplicate of Issue 137. Issue 137 covers empty URL batches; this slice preserves that fast path.

This is not a duplicate of Issue 517. Issue 517 validates the URL container and entry type; this slice validates string URL values.

This is not a duplicate of Issue 551. Issue 551 validates the parent client for non-empty batches after URL preflight; this slice validates malformed URL strings before parent-client validation.

No upstream issue was filed from this local workspace.

## Changes

- Add focused regressions for malformed RequestUtil URL strings.
- Extend `_validate_request_urls(...)` to require absolute `http` or `https` URLs with a hostname.
- Preserve existing empty URL no-op behavior, URL entry type validation, parent client validation, config/header/numeric validation, header forwarding, retry behavior, and adjacent workflows.

## Type Of Change

- Input validation
- Public direct URL request-boundary hardening
- Request preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Malformed string URL values `""`, `"not-a-url"`, `"/relative/path"`, `"ftp://example.com/test"`, and `"https://"` must raise `ValueError("urls must be absolute HTTP(S) URLs")` before client validation, config/header access, or HTTP requests. |
| R2 | Existing non-string URL entry validation must remain earlier and continue to raise `ValueError("urls must be a list of strings")`. |
| R3 | Valid empty URL batches must still return `[]` without requiring client config, parent-client validation, or URL syntax work. |
| R4 | Valid absolute `http://` and `https://` URLs must keep existing GET/POST behavior, Wikidot header forwarding, non-Wikidot header suppression, retry behavior, and return-exceptions behavior. |
| R5 | RequestUtil, adjacent workflow, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed URL strings fail at the RequestUtil URL boundary. | `TestRequestUtilUrlValidation.test_rejects_malformed_url_strings_before_client_validation` failed RED for all 5 values because they reached later client validation, then passed GREEN after URL syntax validation was added. | Reaching parent-client validation, config/header reads, async client creation, HTTP requests, or lower-level URL diagnostics rejects this local completion claim. | `RequestUtil.request(...)` URL preflight | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R2 | Non-string URL entries keep the existing list-of-strings error. | Existing URL entry type tests passed inside the 129-test RequestUtil suite. | Treating non-string entries as malformed URL strings or shifting them into client validation rejects this local completion claim. | Direct request URL entry validation | `tests/unit/test_requestutil.py` |
| R3 | Empty URL batches remain cheap no-ops. | Existing empty GET/POST tests passed inside the 129-test RequestUtil suite. | Requiring `Client`, reading config/header state, creating semaphores, or raising for `[]` rejects this local completion claim. | Empty direct URL batches | `tests/unit/test_requestutil.py` |
| R4 | Existing direct URL and adjacent workflows remain stable. | RequestUtil passed 129 tests, adjacent RequestUtil/user/page/client/site/auth/AMC tests passed 1028 tests, and full unit passed 2628 tests. | Regressing valid GET/POST behavior, Wikidot-only header forwarding, non-Wikidot header suppression, retryable 5xx behavior, non-retryable 4xx behavior, timeout retry, return-exceptions behavior, user lookup, page probing, client construction, site lookup, raw AMC, or auth behavior rejects this local completion claim. | Direct URL and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full unit tests passed 2628 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c569130 fix(requestutil): validate URL strings`.

- RED URL strings: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilUrlValidation::test_rejects_malformed_url_strings_before_client_validation -q` failed 5 tests before the fix because malformed strings passed URL validation and reached `ValueError("client must be a Client")`.
- GREEN focused: the same focused command passed 5 tests.
- `uv run pytest tests/unit/test_requestutil.py -q` passed 129 tests.
- `uv run pytest tests/unit/test_requestutil.py tests/unit/test_user.py tests/unit/test_page.py tests/unit/test_client.py tests/unit/test_site.py tests/unit/test_auth.py tests/unit/test_amc_client.py -q` passed 1028 tests.
- `uv run pytest tests/unit -q` passed 2628 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct RequestUtil URL strings raise `ValueError("urls must be absolute HTTP(S) URLs")`.
- Non-string URL entries continue to raise `ValueError("urls must be a list of strings")`.
- Empty URL batches still return `[]` without requiring a configured or typed client.
- Existing parent-client, config-object, header-object, numeric-control, valid GET/POST, retry, header forwarding, and adjacent workflow behavior remains unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: URL syntax validation could accidentally break the empty URL no-op contract. Mitigation: the syntax loop is a no-op for `[]`, and empty GET/POST tests remain green.
- Risk: This could change non-string URL entry precedence. Mitigation: list and entry type checks still run before parsing string values, and existing tests remain green.
- Risk: This could reject relative URLs or non-HTTP(S) schemes that lower-level clients might otherwise reject later. Mitigation: `RequestUtil.request(...)` is a direct HTTP(S) URL helper, and deterministic preflight avoids client/config/network setup for malformed values.
- Risk: This could be confused with client validation. Mitigation: Issue 551 covers the parent `Client` object after URL preflight; this slice covers URL string syntax before client validation.

## Dependencies

- Existing `urlparse` import remains available in `wikidot.util.requestutil`.
- Existing method, URL container, URL entry type, return-exceptions, client, config, header, and numeric validators remain responsible for their inputs in the current order.
- Existing empty URL no-op behavior remains a separate fast path.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`RequestUtil.request(...)` is the direct URL executor beneath multiple browser-free workflows. Validating URL string values before client validation and request setup gives generated callers and tests deterministic errors for malformed direct URL batches without changing empty-batch behavior, URL type validation, request configuration validation, header forwarding, retry behavior, or live Wikidot semantics for valid absolute HTTP(S) URLs.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct URL strings crossing the URL boundary and reaching parent-client validation.
- This slice only validates string URL syntax in `RequestUtil.request(...)`. It does not change method validation, URL container validation, URL entry type validation, return-exceptions validation, parent-client validation, config/header/numeric validation, retry policy, response parsing, header forwarding, raw AMC behavior, auth behavior, live site behavior, or direct URL semantics for valid URLs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, and live Wikidot account details out of upstream discussion.
