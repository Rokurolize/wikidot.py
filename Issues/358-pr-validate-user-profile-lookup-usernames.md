# PR Draft: Validate User Profile Lookup Username Inputs

## Summary

`User.from_name(client, name)` and `UserCollection.from_names(client, names)` document username inputs as strings, but malformed caller-provided values were not rejected at the public API boundary. Non-string values could reach `StringUtil.to_unix(...)` during profile URL construction and leak raw Python errors such as `AttributeError: 'dict' object has no attribute 'translate'` instead of a stable user-facing validation failure.

This change validates single-user and bulk profile lookup inputs before profile GET URL construction or `RequestUtil.request(...)` calls. Invalid values now raise `ValueError("name must be a string")`, `ValueError("names must be a list")`, or `ValueError("names list entries must be strings")`. Valid profile lookup, not-found skipping/raising, profile-title spacing, ID extraction, avatar URL construction, collection ordering, request batching, and existing profile parser diagnostics remain unchanged.

## Outcome

Profile lookup callers now get deterministic Python-side preflight validation for malformed username inputs instead of raw string-normalization failures or accidental direct profile requests built from invalid data.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `client.user.get(...)`, `client.user.get_bulk(...)`, `User.from_name(...)`, or `UserCollection.from_names(...)` for identity lookup, membership checks, migration tooling, moderation workflows, audit ledgers, or browser-free user resolution.

## Current Evidence

Local rollout evidence repeatedly treats user/profile lookup as a practical read surface. Existing drafts [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), and QuickModule-related drafts [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), and [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md) establish user lookup and user identity parsing as practical surfaces.

Those prior slices are not duplicates. They covered profile-title text fidelity, empty request batches, request client reuse, profile parser context, malformed profile ID hrefs, QuickModule retries, and decoded QuickModule response diagnostics. They did not validate caller-provided profile lookup username inputs before `StringUtil.to_unix(...)` and direct profile GET URL construction. This slice follows the input-boundary pattern from [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [356-pr-validate-site-invite-text-input.md](356-pr-validate-site-invite-text-input.md), and [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md), but applies it to profile-page user lookup.

## Related Issue

Builds directly on [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), and [357-pr-validate-site-member-lookup-username.md](357-pr-validate-site-member-lookup-username.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `User.from_name(name=...)` before delegating to `UserCollection.from_names(...)`.
- Validate `UserCollection.from_names(names=...)` before profile GET URL construction.
- Reject non-list bulk input and non-string bulk entries with stable `ValueError` messages.
- Preserve successful profile lookup behavior, empty bulk lookup behavior, not-found skip/raise behavior, parser diagnostics, collection ordering, request batching, and client accessor delegation.

## Type Of Change

- Input validation
- Public API behavior hardening
- Profile lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `User.from_name(..., name=...)` must reject non-string username values with `ValueError("name must be a string")` before profile GET URL construction or direct HTTP requests. |
| R2 | `UserCollection.from_names(..., names=...)` must reject non-list bulk inputs with `ValueError("names must be a list")` before profile GET URL construction or direct HTTP requests. |
| R3 | `UserCollection.from_names(..., names=[...])` must reject non-string username entries with `ValueError("names list entries must be strings")` before profile GET URL construction or direct HTTP requests. |
| R4 | Valid profile lookup, skipped/raised not-found behavior, profile-title spacing, ID extraction, avatar URL construction, collection ordering, and client accessor delegation must remain unchanged. |
| R5 | Existing user parser, request helper, and QuickModule diagnostics must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent user/client/request/parser/QuickModule tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-string single username inputs fail before any profile request. | `TestUserFromName.test_from_name_rejects_non_string_name_before_request` failed RED before the fix with raw `AttributeError`, then passed GREEN after validation was added. | Calling `RequestUtil.request(...)`, recording an HTTPX request, coercing dictionaries/lists/numbers to strings, or leaking `StringUtil.to_unix(...)` errors rejects this local completion claim. | User profile lookup preflight | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Non-list bulk username inputs fail before any profile request. | `TestUserCollection.test_from_names_rejects_non_list_names_before_request` passed after the bulk validator was added and asserts no HTTPX requests were made. | Treating dictionaries/tuples/scalars as username collections, entering URL construction, or recording an HTTPX request rejects this local completion claim. | Bulk user profile lookup preflight | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Non-string bulk username entries fail before any profile request. | `TestUserCollection.test_from_names_rejects_non_string_name_before_request` failed RED before the fix with raw `AttributeError`, then passed GREEN after validation was added. | Partially requesting earlier valid entries, coercing malformed entries, leaking raw string-normalization errors, or recording any HTTPX request rejects this local completion claim. | Bulk user profile lookup preflight | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R4 | Valid user lookup behavior remains unchanged. | `tests/unit/test_user.py` passed 19 tests, including single lookup, not-found skip/raise, multi-user lookup, ID extraction, title spacing, parser diagnostics, and iteration. `tests/unit/test_client.py` passed 20 tests. | Regressing profile URLs, not-found handling, profile-title spacing, ID extraction, avatar URLs, collection ordering, `User.from_name(...)`, `client.user.get(...)`, or `client.user.get_bulk(...)` rejects this local completion claim. | User and client accessors | `tests/unit/test_user.py`, `tests/unit/test_client.py` |
| R5 | Adjacent parser/request/QuickModule behavior remains green. | `tests/unit/test_requestutil.py`, `tests/unit/parsers/test_user_parser.py`, and `tests/unit/test_quick_module.py` passed in the adjacent 106-test run; the full unit suite passed 968 tests. | Regressing empty request batches, async client reuse, user parser variants, QuickModule response diagnostics, or profile request behavior rejects this local completion claim. | Request and parser workflows | adjacent tests and full unit |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic malformed values. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw profile HTML, private member data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent user/client/request/parser/QuickModule tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `531acbe fix(user): validate profile lookup usernames`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_user.py::TestUserFromName::test_from_name_rejects_non_string_name_before_request` failed before the fix with raw `AttributeError: 'dict' object has no attribute 'translate'`.
- RED: `.venv/bin/python -m pytest -q tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_non_string_name_before_request` failed before the fix with raw `AttributeError: 'dict' object has no attribute 'translate'`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_user.py::TestUserFromName::test_from_name_rejects_non_string_name_before_request tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_non_list_names_before_request tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_non_string_name_before_request` passed 3 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_user.py tests/unit/test_client.py tests/unit/test_requestutil.py tests/unit/parsers/test_user_parser.py tests/unit/test_quick_module.py` passed 106 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 968 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `User.from_name(client, {"name": "test-user"})` raises `ValueError("name must be a string")` before any profile GET request is recorded.
- `UserCollection.from_names(client, {"name": "bad-user"})` raises `ValueError("names must be a list")` before any profile GET request is recorded.
- `UserCollection.from_names(client, ["ok-user", {"name": "bad-user"}])` raises `ValueError("names list entries must be strings")` before any profile GET request is recorded.
- `client.user.get("test-user")` still delegates to `User.from_name(client, "test-user", False)`.
- `client.user.get_bulk(["user1", "user2"])` still delegates to `UserCollection.from_names(client, ["user1", "user2"], False)`.
- Valid profile lookup, not-found skip/raise behavior, profile-title spacing, ID extraction from message and karma links, avatar URL construction, collection ordering, and iteration remain unchanged.
- Existing user parser, request helper, and QuickModule response diagnostics remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Profile lookup is a read-only helper, but it sits underneath identity resolution, client user accessors, membership workflows, and migration tooling. Runtime validation should reject malformed username inputs before direct profile URL construction so generated configs, CLI payloads, JSON/YAML values, spreadsheets, or caller mistakes do not trigger raw string-normalization errors or accidental network work. The change is narrow: it keeps valid profile lookup semantics and existing parser diagnostics unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established profile lookup, request batching, user parser fidelity, and QuickModule identity diagnostics as practical surfaces.
- The focused RED failures showed malformed profile lookup usernames crossing the public call boundary and leaking raw `AttributeError` from `StringUtil.to_unix(...)`.
- Existing profile lookup drafts covered title spacing, profile parser context, malformed profile ID hrefs, empty request batches, and request client reuse, but not malformed public username input preflight.
- This slice only validates profile lookup username inputs. It does not change profile-page parsing, profile not-found behavior, request batching, QuickModule response parsing, client authentication, live Wikidot behavior, or user dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw profile HTML, private member data, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load profile lookup usernames from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to strings before calling wikidot.py user lookup helpers.
