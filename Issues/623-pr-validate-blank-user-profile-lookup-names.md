# PR Draft: Validate Blank User Profile Lookup Names

## Summary

`User.from_name(...)` and `UserCollection.from_names(...)` already reject non-string lookup names, but empty strings and whitespace-only strings still passed validation. Those values normalize to an empty user slug and can issue malformed profile requests such as `https://www.wikidot.com/user:info/`; in bulk lookup, an earlier valid entry can also be requested before the blank entry fails.

This change rejects blank single-user and bulk profile lookup names before URL construction or `RequestUtil.request(...)`. Valid profile lookup, non-string input diagnostics, empty bulk lookup behavior, not-found skip/raise behavior, profile-title spacing, ID extraction, avatar URL construction, request batching, parser diagnostics, and client accessor delegation remain unchanged.

## Outcome

Profile lookup callers now get deterministic preflight failures for blank requested usernames instead of accidental profile GETs against an empty slug.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `client.user.get(...)`, `client.user.get_bulk(...)`, `User.from_name(...)`, or `UserCollection.from_names(...)` for identity lookup, membership checks, moderation workflows, migration tooling, audit ledgers, generated fixtures, or browser-free user resolution.

## Current Evidence

Local rollout-backed drafts repeatedly identify user/profile lookup as a practical read surface. Existing drafts [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), and [550-pr-validate-user-lookup-client.md](550-pr-validate-user-lookup-client.md) establish profile lookup, parser diagnostics, username type validation, not-found controls, and lookup client validation as active operational boundaries.

This is not a duplicate of Issue 358. Issue 358 validates that single and bulk profile lookup names are strings; it does not reject empty or whitespace-only strings that normalize to an empty URL slug.

This is not a duplicate of Issue 137. Issue 137 makes explicitly empty URL batches return without setup work; this slice prevents non-empty lookup inputs from generating empty profile URL slugs.

No upstream issue was filed from this local workspace.

## Changes

- Reject `User.from_name(client, "")` and whitespace-only variants with `ValueError("name must not be empty")` before profile GET construction.
- Reject `UserCollection.from_names(client, ["ok-user", ""])` and whitespace-only variants with `ValueError("names list entries must not be empty")` before any profile GET requests.
- Preserve non-string diagnostics: `ValueError("name must be a string")`, `ValueError("names must be a list")`, and `ValueError("names list entries must be strings")`.
- Preserve valid profile lookup behavior, client accessor delegation, empty bulk lookup behavior, not-found skip/raise behavior, parser diagnostics, collection ordering, and request batching.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Blank single-user lookup names must raise `ValueError("name must not be empty")` before URL construction or HTTP requests. |
| R2 | Blank bulk lookup entries must raise `ValueError("names list entries must not be empty")` before URL construction or HTTP requests, including requests for earlier valid entries in the same batch. |
| R3 | Existing malformed type diagnostics and validation precedence must remain unchanged. |
| R4 | Valid lookup names, empty bulk input, not-found skip/raise behavior, profile parser diagnostics, client accessor delegation, request helper behavior, and QuickModule adjacency must remain unchanged. |
| R5 | Focused RED/GREEN, adjacent user/client/request/parser/QuickModule tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Blank single lookup names fail before request work. | `test_from_name_rejects_blank_name_before_request` failed RED for `""` and `"   "` by issuing unexpected `GET https://www.wikidot.com/user:info/`, then passed GREEN after `_validate_user_name(...)` rejected blank strings. | Constructing a profile URL, recording any HTTPX request, coercing whitespace, or leaking an HTTPX timeout rejects this local completion claim. | `User.from_name(...)` | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Blank bulk entries fail before any batch request. | `test_from_names_rejects_blank_name_before_request` failed RED for `""` and `"   "` by issuing unexpected `GET .../ok-user` and `GET .../user:info/`, then passed GREEN after `_validate_user_names(...)` rejected blank entries before request setup. | Requesting earlier valid names in a batch, constructing an empty profile URL, partially processing entries, or leaking HTTPX timeout diagnostics rejects this local completion claim. | `UserCollection.from_names(...)` | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Existing type diagnostics remain stable. | Adjacent user coverage passed existing non-string name, non-list names, non-string bulk entry, malformed client, and malformed not-found flag tests. | Changing existing `ValueError` messages or checking blankness before type validation rejects this local completion claim. | Lookup preflight | `tests/unit/test_user.py` |
| R4 | Existing valid and adjacent workflows remain green. | Adjacent user/client/request/parser/QuickModule coverage passed 378 tests; full unit passed 2801 tests. | Regressing valid profile URLs, empty bulk lookups, not-found behavior, profile-title spacing, ID extraction, avatar URLs, collection ordering, request utility behavior, user parser variants, QuickModule diagnostics, or client accessor delegation rejects this local completion claim. | User lookup and adjacent workflows | `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic client state and `pytest_httpx` request recording only; this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `5bc07e9 fix(user): validate blank profile lookup names`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserFromName::test_from_name_rejects_blank_name_before_request tests/unit/test_user.py::TestUserCollection::test_from_names_rejects_blank_name_before_request -q` failed 4 cases and raised 4 teardown errors because blank names recorded unexpected profile GET requests.
- GREEN focused: the same command passed 4 tests after blank single and bulk lookup names were rejected at preflight.
- Adjacent lookup coverage: `uv run pytest tests/unit/test_user.py tests/unit/test_client.py tests/unit/test_requestutil.py tests/unit/parsers/test_user_parser.py tests/unit/test_quick_module.py -q` passed 378 tests.
- `uv run pytest tests/unit -q` passed 2801 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `User.from_name(client, "")` and `User.from_name(client, "   ")` raise `ValueError("name must not be empty")` before any profile GET request is recorded.
- `UserCollection.from_names(client, ["ok-user", ""])` and whitespace-only variants raise `ValueError("names list entries must not be empty")` before any profile GET request is recorded.
- Non-string lookup names still raise the existing string-type diagnostics.
- `UserCollection.from_names(client, [])` still returns an empty collection without client/request setup.
- Valid profile lookups, not-found skip/raise behavior, profile-title spacing, ID extraction, avatar URL construction, collection ordering, iteration, request helper behavior, user parser variants, QuickModule diagnostics, and client accessor delegation remain green.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Profile lookup is a browser-free identity resolution helper. Rejecting blank names at the public API boundary prevents accidental empty-slug profile requests from generated configs, CLI inputs, spreadsheets, filtered rollout queues, or other caller-provided data while preserving all valid lookup and parser behavior.

## Local Evidence, Not For Upstream Paste

- The focused RED run showed blank single-user lookup names reaching `https://www.wikidot.com/user:info/`.
- The focused RED run also showed a blank bulk entry allowing `https://www.wikidot.com/user:info/ok-user` to be requested before the invalid entry was handled.
- Existing local drafts covered profile title fidelity, parser context, request empty batches, username type validation, not-found flags, and lookup client validation, but not blank string semantics.
- This slice only validates blank public profile lookup names. It does not change `StringUtil.to_unix(...)`, valid profile lookup names with spaces, profile-page parsing, not-found handling, request batching, request retry behavior, QuickModule response parsing, client authentication, live Wikidot behavior, or user dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw profile HTML, private member data, private messages, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The validator deliberately does not strip valid names before returning them. It only rejects strings whose stripped form is empty, leaving existing `StringUtil.to_unix(...)` normalization responsible for valid display-name inputs.
