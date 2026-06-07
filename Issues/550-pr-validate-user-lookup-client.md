# PR Draft: Validate User Lookup Client Input

## Summary

`User.from_name(client, name, raise_when_not_found=False)` and `UserCollection.from_names(client, names, raise_when_not_found=False)` are direct user-profile lookup helpers behind the client user accessor. Earlier local slices validated user lookup names, the not-found flag, collection constructor contents, user scalar fields, and client accessor parent state. One adjacent public user-input gap remained: direct calls such as `User.from_name(None, "test-user")` or `UserCollection.from_names(None, ["test-user"])`, booleans, strings, dictionaries, or arbitrary objects reached `client.amc_client.config` in `RequestUtil.request(...)` and leaked raw `AttributeError`.

This change validates the caller-provided `client` object after user-name and `raise_when_not_found` validation, but before profile URL request setup, config/header access, HTTP work, or profile parsing. Malformed direct user lookup clients now raise `ValueError("client must be a Client")` deterministically, while existing name validation precedence, not-found flag validation precedence, valid lookup behavior, not-found behavior, parser diagnostics, and adjacent client/request workflows remain unchanged.

## Outcome

Direct user lookup callers now get deterministic client validation before nested request state reads or profile fetch work instead of incidental attribute errors from malformed client-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call user lookup helpers directly, construct clients from generated configuration, run browser-free profile lookup workflows, or use local fixtures where malformed lookup clients should fail before network side effects.

## Current Evidence

Local rollout-backed drafts repeatedly identify direct lookup helpers, client accessors, request utility state, and user profile parsing as practical workflow surfaces. Existing drafts [358-pr-validate-user-lookup-names.md](358-pr-validate-user-lookup-names.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [426-pr-validate-user-collection-constructor.md](426-pr-validate-user-collection-constructor.md), [479-pr-validate-client-accessor-parent.md](479-pr-validate-client-accessor-parent.md), [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md), [548-pr-validate-site-lookup-client.md](548-pr-validate-site-lookup-client.md), and [549-pr-validate-auth-client.md](549-pr-validate-auth-client.md) establish input validation, direct client validation, and nested request-state access as active operational boundaries.

This is not a duplicate of Issue 358. Issue 358 validates `name` and `names` inputs. This slice preserves that precedence and validates the separate caller-provided `client` object only after user names are known valid.

This is not a duplicate of Issue 384. Issue 384 validates `raise_when_not_found`. This slice preserves that precedence and validates the parent client object only after the flag is known valid.

This is not a duplicate of Issue 479. Issue 479 validates client accessor parent construction. This slice covers direct static user lookup helper calls.

This is not a duplicate of Issue 548 or Issue 549. Those slices validate site lookup and authentication helper clients. This slice covers user profile lookup clients before `RequestUtil.request(...)` reads nested AMC state.

No upstream issue was filed from this local workspace.

## Changes

- Add focused regressions for malformed direct `User.from_name(client=...)` and `UserCollection.from_names(client=...)` inputs.
- Add `_validate_user_lookup_client(...)` and call it before user lookup request setup.
- Update user lookup tests to use an uninitialized real `Client` with synthetic AMC state so lookup tests exercise the stricter public boundary without constructor/login side effects.
- Preserve user-name validation, `raise_when_not_found` validation, valid lookup behavior, not-found handling, parser diagnostics, and adjacent request/client workflows.

## Type Of Change

- Input validation
- Public user lookup-boundary hardening
- Profile lookup preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `User.from_name(None, "test-user")`, `True`, `"test-client"`, `{"username": "test-user"}`, and `object()` must raise `ValueError("client must be a Client")` before config/header access or HTTP requests. |
| R2 | `UserCollection.from_names(...)` must reject the same malformed clients before profile request setup or parsing. |
| R3 | Existing malformed `name` and `names` validation must remain earlier than client validation and request work. |
| R4 | Existing `raise_when_not_found` validation must remain earlier than client validation and request work. |
| R5 | Valid lookup, not-found handling, parser diagnostics, and adjacent client/RequestUtil workflows must remain unchanged. |
| R6 | User, adjacent workflow, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct single-user lookup clients fail at the public user boundary. | `TestUserFromName.test_from_name_rejects_malformed_client_before_request` passed after validation was added. | Reaching `client.amc_client.config`, issuing profile requests, parsing HTML, accepting client-like dictionaries, or leaking raw attribute errors rejects this local completion claim. | `User.from_name(...)` | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Malformed direct bulk user lookup clients fail before request setup. | `TestUserCollection.test_from_names_rejects_malformed_client_before_request` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `client.amc_client.config`, issuing profile requests, parsing HTML, accepting client-like dictionaries, or leaking raw attribute errors rejects this local completion claim. | `UserCollection.from_names(...)` | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Existing name validation remains the first user lookup preflight. | Focused GREEN included malformed `name` and `names` tests before request work. | Shifting malformed names into client validation, config reads, HTTP GET, or parser work rejects this local completion claim. | User lookup names | `tests/unit/test_user.py` |
| R4 | Existing not-found flag validation remains before client validation. | Focused GREEN included malformed `raise_when_not_found` tests for single and bulk lookup before request work. | Shifting malformed flags into client validation, config reads, HTTP GET, or parser work rejects this local completion claim. | User lookup flags | `tests/unit/test_user.py` |
| R5 | Existing user lookup behavior remains stable. | `uv run pytest tests/unit/test_user.py -q` passed 59 tests, and adjacent client/RequestUtil tests passed 152 tests. | Regressing successful lookup, missing-user handling, user ID extraction, profile title spacing, parser exceptions, client tests, or RequestUtil behavior rejects this local completion claim. | User lookup and adjacent workflows | `tests/unit` |
| R6 | Existing repository quality gates remain green. | Full unit tests passed 2618 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `3653528 fix(user): validate lookup client`.

- RED bulk client: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_malformed_client_before_request -q` failed 5 tests before the fix because malformed clients reached `client.amc_client.config` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_malformed_client_before_request -q` passed 5 tests.
- `uv run pytest tests/unit/test_user.py -q` passed 59 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_requestutil.py -q` passed 152 tests.
- `uv run pytest tests/unit -q` passed 2618 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct `User.from_name(client=...)` inputs raise `ValueError("client must be a Client")`.
- Malformed direct `UserCollection.from_names(client=...)` inputs raise `ValueError("client must be a Client")`.
- Existing malformed `name`, `names`, and `raise_when_not_found` validation remains earlier than client validation.
- Valid lookup, missing-user handling, profile parsing diagnostics, and adjacent workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Client validation could accidentally change user-name or flag validation precedence. Mitigation: lookup client validation runs after existing name and not-found flag validation, and focused GREEN includes those malformed-input tests.
- Risk: This could be confused with request config/header validation. Mitigation: existing RequestUtil validations cover nested state after request setup; this draft covers the parent client object before `amc_client` is read.
- Risk: User lookup tests need a stricter client-shaped fixture. Mitigation: the test helper uses `object.__new__(Client)` with synthetic AMC state to pass the public type boundary without running constructor/login side effects.

## Dependencies

- Existing `Client` remains the canonical parent type for direct user lookup helpers.
- Existing user-name and `raise_when_not_found` validators remain responsible for lookup inputs before client validation.
- Existing RequestUtil validators remain responsible for nested request state after a valid client is supplied.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`User.from_name(...)` and `UserCollection.from_names(...)` are direct profile lookup entry points for browser-free workflows. Validating the supplied client object before nested state reads and request work gives generated callers and tests deterministic errors for malformed inputs without changing name validation, not-found behavior, parser diagnostics, request behavior, or live Wikidot semantics for valid clients.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `client` arguments crossing the public static bulk user lookup boundary and leaking `AttributeError` from `client.amc_client.config`.
- This slice only validates the `User.from_name(...)` and `UserCollection.from_names(...)` caller-provided parent client. It does not change name policy, not-found policy, retry policy, HTTP helper behavior, header serialization, profile parser semantics, client construction, live site behavior, or lookup semantics for valid clients.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, and live Wikidot account details out of upstream discussion.
