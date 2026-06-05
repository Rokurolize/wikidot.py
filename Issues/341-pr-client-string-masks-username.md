# PR Draft: Mask Client Username In String Output

## Summary

`Client.__str__()` exposed the raw `username` value whenever a logged-in client was interpolated into a log line, assertion failure, debug report, or operator-facing status string. Local rollout evidence repeatedly treats Wikidot account names, credentials, cookies, and sandbox details as material that must not appear in upstream-facing summaries or reusable diagnostics. The client object already exposes `client.username` for deliberate programmatic access, so the implicit string form does not need to disclose the account name.

This change makes `str(client)` report whether a username is set without printing the username itself: `Client(username_set=True, is_logged_in=True)` for an authenticated client and `Client(username_set=False, is_logged_in=False)` for a fresh unauthenticated client.

## Outcome

Client string output remains useful for status checks while avoiding accidental account-name disclosure in diagnostics.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Client(...)` in scripts, tests, reports, notebook output, or logging around authenticated Wikidot workflows.

## Current Evidence

Local rollout evidence repeatedly uses wikidot.py around authenticated sandbox, SPECA, FTML, and report-generation workflows where account details must be kept out of upstream discussion. The existing client string test only checked that the output contained the client type and login state; it did not cover a logged-in client or reject raw username exposure.

## Related Issue

Builds on local privacy and authentication-boundary drafts such as [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), and [340-pr-login-session-cookie-validation.md](340-pr-login-session-cookie-validation.md). Those drafts covered sensitive request/header/cookie handling; this slice covers the client object's implicit human-readable string output.

No upstream issue was filed from this local workspace.

## Changes

- Change `Client.__str__()` from printing `username=<value>` to printing `username_set=<bool>`.
- Preserve `is_logged_in=<bool>` in the string output.
- Preserve `client.username`, login state, logout clearing, context-manager cleanup, and accessor initialization behavior.
- Add a focused unit regression proving a logged-in client's string output does not contain the username while still reporting `username_set=True` and `is_logged_in=True`.

## Type Of Change

- Diagnostic privacy hardening
- Public string-representation behavior fix
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `str(Client())` must keep identifying the object as a client and must report `username_set=False` and `is_logged_in=False`. |
| R2 | `str(Client(username=..., password=...))` must not include the username value and must report `username_set=True` and `is_logged_in=True` after mocked successful login. |
| R3 | The explicit `client.username` attribute must remain unchanged for callers that deliberately need programmatic access. |
| R4 | The change must not alter login, logout, context-manager cleanup, accessor initialization, `client.me`, or AMC client behavior. |
| R5 | Diagnostics, docs, and tests must not require real account names, passwords, cookies, auth JSON, raw rollout paths, or live Wikidot actions. |
| R6 | Focused, client, adjacent connector/auth, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A fresh unauthenticated client string contains `Client(`, `username_set=False`, and `is_logged_in=False`. | Updated `TestClient.test_str_representation` stayed green. | Reintroducing raw `username=None` as the primary status field rejects this local completion claim. | Client string output | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R2 | A mocked logged-in client string omits the username value and includes the expected boolean state fields. | New `TestClient.test_str_representation_masks_logged_in_username` failed RED before the fix and passed GREEN after it. | Printing the raw username, replacing it with a reversible partial value, or dropping login-state visibility rejects this local completion claim. | Client diagnostic privacy | `src/wikidot/module/client.py`, `tests/unit/test_client.py` |
| R3 | Programmatic username access still returns the supplied username after login. | Existing `test_init_with_credentials` stayed green. | Removing, masking, or rewriting `client.username` itself rejects this local completion claim. | Client identity state | `tests/unit/test_client.py` |
| R4 | Existing client lifecycle behavior is unchanged. | Full `tests/unit/test_client.py` passed 20 tests; adjacent auth/client/ajax/AMC suite passed 74 tests. | Breaking logout cleanup, context-manager cleanup, accessors, login checks, or AMC setup rejects this local completion claim. | Client lifecycle and adjacent auth/connector surface | `tests/unit/test_client.py`, `tests/unit/test_auth.py`, `tests/unit/test_ajax.py`, `tests/unit/test_amc_client.py` |
| R5 | No real account material or live Wikidot state is needed to prove the behavior. | The regression uses mocked login and a synthetic username; no network call or credential material is required. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | `tests/unit/test_client.py`, this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, client passed 20 tests, adjacent connector/auth passed 74 tests, full unit passed 916 tests, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3de2eb0 fix(client): mask username in string form`.

- RED: `uv run --extra test pytest tests/unit/test_client.py::TestClient::test_str_representation_masks_logged_in_username -q` failed before the fix because the username appeared in `str(client)`.
- GREEN: `uv run --extra test pytest tests/unit/test_client.py::TestClient::test_str_representation_masks_logged_in_username -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_client.py::TestClient::test_str_representation -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_client.py -q` passed 20 tests.
- `uv run --extra test pytest tests/unit/test_auth.py tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_amc_client.py -q` passed 74 tests.
- `uv run --extra test pytest tests/unit -q` passed 916 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- Unauthenticated client string output reports `username_set=False` and `is_logged_in=False`.
- Authenticated client string output reports `username_set=True` and `is_logged_in=True` without including the username value.
- `client.username` remains available and unchanged for explicit programmatic use.
- Login, logout, context-manager cleanup, `client.me`, accessors, and AMC setup remain unchanged.
- The new test uses mocked login only and does not require live Wikidot, real account names, credentials, cookies, auth JSON, private site data, or raw rollout paths.
- No live Wikidot action, upstream Issue, upstream PR, push, real login response body, credentials, cookies, auth JSON, or account material is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`str(client)` is likely to appear in human-facing logs and assertion output, where accidental account-name disclosure is harder to control than explicit attribute access. Reporting boolean username presence keeps the string useful for diagnosing whether a client was constructed with credentials while making the safer behavior the default.

## Local Evidence, Not For Upstream Paste

- Local sandbox and oracle workflows repeatedly require account material to stay out of upstream-facing reports and drafts.
- The focused RED failure showed the current string form embedding the username for a logged-in client.
- This slice only changes implicit string output; it does not mask the explicit `client.username` attribute, change authentication, perform a live login, alter cookies, change logging sinks, or add broader secret scanning.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, and private site data out of upstream discussion.

## Additional Notes

This is a deliberate public string-representation change. Code that needs the username should use `client.username` explicitly instead of parsing `str(client)`.
