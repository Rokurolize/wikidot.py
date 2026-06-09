# PR Draft: Skip Empty User Profile Lookups

## Summary

`UserCollection.from_names(client, names, raise_when_not_found=False)` is the direct bulk user-profile lookup helper behind `client.user.get_bulk(...)`. Empty `names` already produced an empty URL list for `RequestUtil.request(...)`, and `RequestUtil` already has an empty-URL fast path, but `UserCollection.from_names(...)` validated the caller-provided `client` before the empty lookup could return. That made `UserCollection.from_names(object(), [])` fail with `ValueError("client must be a Client")` even though no profile URL, client request state, or returned user row could be used.

This change validates `names` and `raise_when_not_found`, then returns an empty `UserCollection` immediately when the validated name list is empty. Non-empty bulk profile lookups still validate `client`, build profile URLs, use `RequestUtil.request(...)`, apply not-found behavior, parse profile pages, and return users exactly as before.

## Outcome

Generated or filtered user lookup batches can treat empty work as a typed no-op without requiring a configured `Client`, while malformed names and malformed boolean controls still fail deterministically before the empty fast path.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free user profile lookups, generated lookup queues, optional member/user resolution, migration or audit ledgers, and bulk user workflows where filtering can naturally produce an empty username list.

## Current Evidence

Local rollout-backed drafts already establish empty read batches and direct profile lookup as practical workflow surfaces. [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md) and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md) remove unnecessary work from empty direct read batches. [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md) specifically notes `UserCollection.from_names(...)` as a caller that reaches `RequestUtil.request(...)` for profile-page batches. [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [426-pr-validate-user-collection-initialization.md](426-pr-validate-user-collection-initialization.md), and [550-pr-validate-user-lookup-client.md](550-pr-validate-user-lookup-client.md) cover profile lookup input validation, boolean controls, collection construction, and non-empty lookup client validation.

This slice is not a duplicate of those drafts. Issue 137 makes the shared direct URL helper skip empty URL batches; it does not stop `UserCollection.from_names(...)` from validating a client before it can call the helper. Issue 550 validates malformed clients for real user lookups; this slice preserves that behavior for non-empty lookups and only skips client validation once the validated `names` list is empty. Issues 358 and 384 validate the name list and not-found flag, and this slice deliberately keeps those validations before the empty return.

No upstream issue was filed from this local workspace.

## Changes

- Return `UserCollection([])` from `UserCollection.from_names(...)` when the validated `names` list is empty.
- Keep `names` validation before the empty return so malformed containers, non-string entries, and blank entries still fail.
- Keep `raise_when_not_found` validation before the empty return so malformed boolean controls still fail.
- Preserve client validation, URL construction, request behavior, not-found handling, parser diagnostics, and output ordering for non-empty lookups.
- Add a focused public-interface regression proving an empty bulk user lookup does not require client validation or HTTP work.

## Type Of Change

- Performance improvement
- Empty-input fast path
- User lookup ergonomics
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `UserCollection.from_names(object(), [])` must return an empty `UserCollection` without validating client state or issuing HTTP requests. |
| R2 | Malformed `names` input must still fail before the empty fast path. |
| R3 | Malformed `raise_when_not_found` input must still fail before the empty fast path. |
| R4 | Non-empty `UserCollection.from_names(...)`, `User.from_name(...)`, and `client.user.get_bulk(...)` behavior must remain unchanged. |
| R5 | Focused RED/GREEN, user lookup tests, adjacent request/client/QuickModule tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private user data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Empty bulk profile lookup returns a typed empty collection without client setup. | `test_from_names_empty_input_skips_client_validation_and_request` failed RED with `ValueError("client must be a Client")`, then passed GREEN after the empty fast path was added. | Requiring a `Client`, reaching `client.amc_client`, building URLs, issuing HTTP requests, returning a plain list, or returning `None` rejects this local completion claim. | `UserCollection.from_names(...)` | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Malformed name containers and entries still fail before any request work. | Existing malformed `names` tests remained green in `tests/unit/test_user.py`. | Accepting non-list names, non-string entries, blank entries, coercing malformed names, or shifting those failures into client/request code rejects this local completion claim. | Bulk user lookup names | `tests/unit/test_user.py` |
| R3 | Malformed `raise_when_not_found` values still fail before any request work. | Existing malformed not-found-flag tests remained green in `tests/unit/test_user.py`. | Accepting truthy/falsy non-bools, coercing strings or integers, or hiding flag errors behind the empty return rejects this local completion claim. | User lookup boolean control | `tests/unit/test_user.py` |
| R4 | Existing profile lookup behavior remains compatible. | `tests/unit/test_user.py` passed 113 tests; adjacent user/request/client/QuickModule coverage passed 403 tests. | Regressing successful profile lookups, not-found skip/raise behavior, profile ID parsing, profile title spacing, malformed client diagnostics for non-empty lookups, client accessors, RequestUtil, or QuickModule behavior rejects this local completion claim. | User lookup and adjacent workflows | `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit passed 3544 tests, full ruff check passed, full ruff format check passed, full mypy passed with no issues in 87 source files, pyright passed with 0 errors, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use unit-level synthetic state and `pytest_httpx`; the draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `28d642c perf(user): skip empty profile lookups`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_empty_input_skips_client_validation_and_request -q` failed before the fix with `ValueError("client must be a Client")`.
- GREEN focused: the same focused command passed after the empty fast path was added.
- `uv run pytest tests/unit/test_user.py -q` passed 113 tests.
- `uv run pytest tests/unit/test_user.py tests/unit/test_requestutil.py tests/unit/test_client.py tests/unit/test_quick_module.py -q` passed 403 tests.
- `uv run pytest tests/unit -q` passed 3544 tests.
- `uv run ruff check src/wikidot/module/user.py tests/unit/test_user.py` passed.
- `uv run ruff format --check src/wikidot/module/user.py tests/unit/test_user.py` passed with 2 files already formatted.
- `git diff --check` passed.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `UserCollection.from_names(object(), [])` returns an empty `UserCollection`.
- Empty bulk lookup does not inspect `client.amc_client`, call `RequestUtil.request(...)`, or issue HTTP requests.
- Malformed `names` values still raise their existing `ValueError` diagnostics before request work.
- Malformed `raise_when_not_found` values still raise `ValueError("raise_when_not_found must be a boolean")`.
- Non-empty `UserCollection.from_names(...)` still validates `client`, still rejects malformed clients with `ValueError("client must be a Client")`, and still preserves successful lookup, not-found handling, parser diagnostics, and ordering.
- `User.from_name(...)` remains unchanged because a single lookup cannot be empty.
- The new tests use synthetic local state only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Some callers may have expected malformed clients to fail even for empty bulk lookups. Mitigation: `UserCollection` stores no parent client, no profile request is needed for an empty list, and shared `RequestUtil` already treats empty URL batches as dependency-light no-ops; malformed clients still fail for non-empty lookups.
- Risk: Empty fast paths can accidentally hide malformed controls. Mitigation: the fast path runs after `_validate_user_names(...)` and `_validate_raise_when_not_found(...)`, preserving those diagnostics and test coverage.
- Risk: Returning a new `UserCollection([])` could differ from the normal constructor path. Mitigation: it uses the existing constructor and preserves the public collection type.

## Out Of Scope

Changing `User.from_name(...)`, changing non-empty lookup client validation, changing user profile selectors, changing not-found behavior, changing `RequestUtil.request(...)`, changing QuickModule user lookup behavior, changing live Wikidot behavior, pushing changes, opening upstream Issues, and opening upstream PRs are outside this slice.

## Why This Matters

Bulk user lookup inputs often come from filtered member lists, optional lookup queues, migration ledgers, and generated audit jobs. When that filtering leaves no names, requiring a configured client adds avoidable setup and makes empty work harder to compose. Returning a typed empty collection keeps the public API useful while preserving all validation that can still affect empty input.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly improved profile lookup, direct request helpers, empty read batches, user parsing diagnostics, and client validation because generated workflows often build lookup batches from filtered data.
- Existing local drafts covered empty shared URL batches, empty private-message and thread reads, username validation, not-found flag validation, collection construction, and non-empty client validation; they did not let empty bulk profile lookup return before client validation.
- The focused RED failure showed an empty username list still required a real `Client`. The GREEN regressions cover typed empty return, no request work, existing name/control validation, non-empty lookup compatibility, adjacent request/client/QuickModule behavior, full unit compatibility, lint, format, type, pyright, and whitespace gates.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
