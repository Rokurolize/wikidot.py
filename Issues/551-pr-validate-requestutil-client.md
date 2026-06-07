# PR Draft: Validate RequestUtil Client Input

## Summary

`RequestUtil.request(client, method, urls, return_exceptions=False)` is the shared direct URL GET/POST batch helper beneath profile lookup, direct page probes, and other retry-aware read paths. Earlier local slices validated empty URL batches, method and URL inputs, `return_exceptions`, numeric request controls, nested config-object state, and nested header-object state. One adjacent public request-input gap remained: non-empty direct calls such as `RequestUtil.request(None, "GET", ["https://example.com/test"])`, booleans, strings, dictionaries, or arbitrary objects reached `client.amc_client.config` and leaked raw `AttributeError`.

This change validates the caller-provided `client` object after method, return-exceptions, URL-shape validation, and the valid empty-URL shortcut, but before config/header access, semaphore setup, header preparation, async client construction, HTTP work, or retry loops. Malformed non-empty direct request clients now raise `ValueError("client must be a Client")` deterministically, while empty URL batches still return `[]` without requiring a client, and existing method/URL/return-exceptions/config/header/numeric validation precedence remains unchanged.

## Outcome

Non-empty direct URL request callers now get deterministic client validation before nested request state reads or HTTP setup instead of incidental attribute errors from malformed client-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using direct URL GET/POST batches, generated local fixtures, JSON/YAML adapters, archival workflows, profile lookup flows, page probing flows, or local CI fixtures where malformed non-empty RequestUtil clients should fail before network side effects.

## Current Evidence

Local rollout-backed drafts repeatedly identify `RequestUtil.request(...)` as practical shared infrastructure. Existing drafts [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [388-pr-validate-requestutil-return-exceptions-flag.md](388-pr-validate-requestutil-return-exceptions-flag.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), [517-pr-validate-requestutil-method-urls.md](517-pr-validate-requestutil-method-urls.md), [523-pr-validate-requestutil-config-object.md](523-pr-validate-requestutil-config-object.md), [528-pr-validate-requestutil-header-object.md](528-pr-validate-requestutil-header-object.md), [549-pr-validate-auth-client.md](549-pr-validate-auth-client.md), and [550-pr-validate-user-lookup-client.md](550-pr-validate-user-lookup-client.md) establish direct URL request validation, nested request-state validation, and caller-provided client validation as active operational boundaries.

This is not a duplicate of Issue 137. Issue 137 intentionally lets empty direct URL batches return `[]` without reading client state. This slice preserves that shortcut and validates the parent client object only for non-empty URL batches.

This is not a duplicate of Issue 517 or Issue 388. Those slices validate method, URL, and `return_exceptions` inputs before client validation. This slice preserves their precedence.

This is not a duplicate of Issue 523 or Issue 528. Those slices validate nested config/header state after a usable client reaches request setup. This slice validates the parent client object before `amc_client`, `config`, or `header` is read.

No upstream issue was filed from this local workspace.

## Changes

- Add focused regressions for malformed direct non-empty `RequestUtil.request(client=...)` inputs.
- Add `_validate_request_client(...)` and call it after the empty URL shortcut but before nested AMC state access.
- Update RequestUtil test fixtures to use an uninitialized real `Client` with synthetic AMC state so valid RequestUtil tests exercise the stricter public boundary without constructor/login side effects.
- Preserve empty URL no-op behavior, method/URL/return-exceptions validation precedence, config/header/numeric validation, header forwarding, retry behavior, and adjacent workflows.

## Type Of Change

- Input validation
- Public direct URL request-boundary hardening
- Request preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Non-empty `RequestUtil.request(None, "GET", ["https://example.com/test"])`, `True`, `"test-client"`, `{"username": "test-user"}`, and `object()` must raise `ValueError("client must be a Client")` before config/header access or HTTP requests. |
| R2 | Valid empty URL batches must still return `[]` without requiring client config or parent-client validation. |
| R3 | Existing malformed method, URL, and `return_exceptions` validation must remain earlier than client validation and request work. |
| R4 | Existing config-object, header-object, and numeric request-control validation must remain separate valid-client preflights. |
| R5 | Valid GET/POST success, header forwarding/suppression, retry behavior, return-exceptions behavior, and adjacent caller workflows must remain unchanged. |
| R6 | RequestUtil, adjacent workflow, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed non-empty direct request clients fail at the RequestUtil boundary. | `TestRequestUtilConfigValidation.test_rejects_malformed_client_before_config` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `client.amc_client.config`, accepting client-like dictionaries, preparing headers, creating async clients, issuing HTTP requests, or leaking raw attribute errors rejects this local completion claim. | `RequestUtil.request(...)` | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R2 | Empty URL batches remain cheap no-ops. | Existing empty GET/POST tests passed inside the 124-test RequestUtil suite. | Requiring `Client`, reading config/header state, creating semaphores, or raising for `[]` rejects this local completion claim. | Empty direct URL batches | `tests/unit/test_requestutil.py` |
| R3 | Existing direct request input validation remains first. | Existing malformed method, URL, and return-exceptions tests passed inside the RequestUtil suite. | Shifting malformed method/URL/flag inputs into client validation, config reads, or HTTP work rejects this local completion claim. | Direct request public inputs | `tests/unit/test_requestutil.py` |
| R4 | Nested config/header/numeric validation remains separate after valid client validation. | Existing invalid config-object, invalid header-object, and numeric config tests passed inside the RequestUtil suite. | Treating malformed nested state as malformed parent clients, reading numeric fields before object validation, or issuing requests rejects this local completion claim. | RequestUtil nested state | `src/wikidot/util/requestutil.py`, `tests/unit/test_requestutil.py` |
| R5 | Existing direct URL and adjacent workflows remain stable. | RequestUtil passed 124 tests, adjacent RequestUtil/user/page/client/site/auth/AMC tests passed 1023 tests, and full unit passed 2623 tests. | Regressing GET/POST success, Wikidot-only header forwarding, non-Wikidot header suppression, retryable 5xx behavior, non-retryable 4xx behavior, timeout retry, return-exceptions behavior, user lookup, page probing, client construction, site lookup, raw AMC, or auth behavior rejects this local completion claim. | Direct URL and adjacent workflows | `tests/unit` |
| R6 | Existing repository quality gates remain green. | Full unit tests passed 2623 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `bfec3ae fix(requestutil): validate request client`.

- RED client: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilConfigValidation::test_rejects_malformed_client_before_config -q` failed 5 tests before the fix because malformed clients reached `client.amc_client.config` and leaked raw `AttributeError`.
- GREEN focused: the same focused command passed 5 tests.
- `uv run pytest tests/unit/test_requestutil.py -q` passed 124 tests.
- `uv run pytest tests/unit/test_requestutil.py tests/unit/test_user.py tests/unit/test_page.py tests/unit/test_client.py tests/unit/test_site.py tests/unit/test_auth.py tests/unit/test_amc_client.py -q` passed 1023 tests.
- `uv run pytest tests/unit -q` passed 2623 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed non-empty direct `RequestUtil.request(client=...)` inputs raise `ValueError("client must be a Client")`.
- Empty URL batches still return `[]` without requiring a configured or typed client.
- Existing malformed method, URL, `return_exceptions`, config-object, header-object, and numeric-control validation remains separate and stable.
- Valid direct GET/POST behavior, retry behavior, header forwarding, and adjacent workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Client validation could accidentally break the empty URL no-op contract. Mitigation: validation runs after the existing empty-list return, and empty GET/POST tests remain green.
- Risk: This could change method/URL/flag validation precedence. Mitigation: validation runs after existing method, `return_exceptions`, and URL validation, and those tests remain green.
- Risk: This could be confused with config/header validation. Mitigation: Issues 523 and 528 cover nested state after a valid client exists; this draft covers the parent client object before `amc_client` is read.
- Risk: RequestUtil tests need a stricter client-shaped fixture. Mitigation: the test helper uses `object.__new__(Client)` with synthetic AMC state to pass the public type boundary without running constructor/login side effects.

## Dependencies

- Existing `Client` remains the canonical parent type for non-empty direct RequestUtil batches.
- Existing method, URL, return-exceptions, config, header, and numeric validators remain responsible for their inputs in the current order.
- Existing empty URL no-op behavior remains a separate fast path before client validation.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`RequestUtil.request(...)` is the direct URL executor beneath multiple browser-free workflows. Validating the supplied client object before nested state reads and request work gives generated callers and tests deterministic errors for malformed non-empty batches without changing empty-batch behavior, method/URL validation, request configuration validation, header forwarding, retry behavior, or live Wikidot semantics for valid clients.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct non-empty `client` arguments crossing the RequestUtil boundary and leaking `AttributeError` from `client.amc_client.config`.
- This slice only validates the `RequestUtil.request(...)` caller-provided parent client after empty URL batches have already returned. It does not change method validation, URL validation, return-exceptions validation, config/header/numeric validation, retry policy, response parsing, header forwarding, raw AMC behavior, auth behavior, live site behavior, or direct URL semantics for valid clients.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, and live Wikidot account details out of upstream discussion.
