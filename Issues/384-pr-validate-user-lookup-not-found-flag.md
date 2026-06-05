# PR Draft: Validate User Lookup Not-Found Flags

## Summary

`User.from_name(...)` and `UserCollection.from_names(...)` document `raise_when_not_found` as a boolean, but malformed caller-provided values were accepted at the public user lookup boundary. Truthy strings such as `"false"` could turn a lookup that should skip or return `None` into a raising lookup, while integers such as `0` and `1` could silently act as booleans.

This change validates `raise_when_not_found` before profile GET request construction. Malformed values now raise `ValueError("raise_when_not_found must be a boolean")`. Existing valid `False` skip/return-`None` behavior and valid `True` not-found raising behavior remain unchanged.

## Outcome

User/profile lookup callers now get deterministic Python-side preflight validation for malformed not-found controls instead of surprising not-found behavior, accidental request work, or configuration strings being treated as truthy booleans.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `client.user.get(...)`, `client.user.get_bulk(...)`, `User.from_name(...)`, or `UserCollection.from_names(...)` for identity lookup, membership checks, migration tooling, moderation workflows, audit ledgers, or browser-free user resolution.

## Current Evidence

Local rollout-backed drafts repeatedly identify user/profile lookup and user identity parsing as practical read surfaces. Existing drafts [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), and [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md) cover profile title fidelity, empty request batches, request client reuse, profile parser context, malformed profile ID href diagnostics, and caller-provided username validation. QuickModule-related drafts [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md), and [339-pr-quickmodule-json-decode-context.md](339-pr-quickmodule-json-decode-context.md) establish user lookup and user identity parsing as operationally important adjacent surfaces.

Those prior slices are not duplicates. They covered username shape, request batching, profile-page parsing, QuickModule user/member lookup diagnostics, and client accessor delegation. They did not validate the boolean `raise_when_not_found` control before profile GET work or not-found branching. This slice follows the boolean-control preflight pattern from [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), but applies it to browser-free user lookup rather than page writes.

## Related Issue

Builds directly on [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [341-pr-client-string-masks-username.md](341-pr-client-string-masks-username.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), and [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `raise_when_not_found` in `User.from_name(...)` before delegating to bulk lookup.
- Validate `raise_when_not_found` in `UserCollection.from_names(...)` before profile GET request construction.
- Preserve valid `raise_when_not_found=False` behavior for skipped or missing users.
- Preserve valid `raise_when_not_found=True` behavior for not-found exceptions.
- Preserve username validation, profile URL construction, profile-title parsing, profile ID parsing, avatar URL construction, collection ordering, and client user accessor delegation.

## Type Of Change

- Input validation
- Public API behavior hardening
- User/profile lookup control preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `User.from_name(..., raise_when_not_found=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("raise_when_not_found must be a boolean")` before profile GET requests. |
| R2 | `UserCollection.from_names(..., raise_when_not_found=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("raise_when_not_found must be a boolean")` before profile GET requests. |
| R3 | Valid `raise_when_not_found=False` behavior must remain unchanged: missing single-user lookup returns `None`, and bulk lookup skips missing users. |
| R4 | Valid `raise_when_not_found=True` behavior must remain unchanged: missing users raise `NotFoundException`. |
| R5 | Existing username validation, profile parser diagnostics, profile title spacing, profile ID extraction, avatar URL generation, collection ordering, client user accessors, and request helper behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, user tests, adjacent user/client/request tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed single-user not-found controls fail before `UserCollection.from_names(...)` can construct profile requests. | `TestUserFromName.test_from_name_rejects_non_bool_raise_when_not_found_before_request` failed RED for `None`, `"false"`, `0`, and `1` by reaching profile GET work, then passed GREEN after validation was added. | Treating `"false"` as truthy, accepting `0`/`1` as booleans, constructing profile GET URLs, or returning/raising based on malformed controls rejects this local completion claim. | Single user lookup preflight | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Malformed bulk not-found controls fail before profile request construction. | `TestUserCollection.test_from_names_rejects_non_bool_raise_when_not_found_before_request` failed RED for `None`, `"false"`, `0`, and `1` by reaching profile GET work, then passed GREEN after validation was added. | Sending profile GET requests, skipping users, or raising not-found exceptions based on malformed controls rejects this local completion claim. | Bulk user lookup preflight | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Valid false controls still skip missing users. | Existing `test_from_name_not_found_no_raise` and `test_from_names_skip_not_found` passed after validation was added. | Raising for valid `False`, returning placeholder users, or changing skipped-user behavior rejects this local completion claim. | User lookup not-found behavior | `tests/unit/test_user.py` |
| R4 | Valid true controls still raise for missing users. | Existing `test_from_name_not_found_raise` passed after validation was added. | Returning `None`, silently skipping a user, or changing exception type for valid `True` rejects this local completion claim. | User lookup not-found behavior | `tests/unit/test_user.py` |
| R5 | Adjacent user and request behavior remains green. | `tests/unit/test_user.py` passed 27 tests, adjacent user/client/requestutil tests passed 70 tests, and full unit tests passed 1114 tests. | Regressing profile URLs, title spacing, ID href parsing, missing profile diagnostics, user collection ordering, `client.user.get(...)`, `client.user.get_bulk(...)`, or request helper behavior rejects this local completion claim. | User lookup workflow | affected user, client, and request tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private profile content, private user data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, user tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4c73819 fix(user): validate lookup not-found flag`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_user.py -k 'raise_when_not_found and non_bool'` failed 8 selected tests before the fix because malformed controls reached profile GET request work.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_user.py -k 'raise_when_not_found and non_bool'` passed 8 tests after adding boolean preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_user.py` passed 27 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_user.py tests/unit/test_client.py tests/unit/test_requestutil.py` passed 70 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1114 tests.
- `.venv/bin/ruff check src/wikidot/module/user.py tests/unit/test_user.py` passed.
- `.venv/bin/ruff format src/wikidot/module/user.py tests/unit/test_user.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `User.from_name(client, "user", raise_when_not_found=None)`, `raise_when_not_found="false"`, `raise_when_not_found=0`, and `raise_when_not_found=1` raise `ValueError("raise_when_not_found must be a boolean")` before profile GET work.
- `UserCollection.from_names(client, ["user"], raise_when_not_found=None)`, `raise_when_not_found="false"`, `raise_when_not_found=0`, and `raise_when_not_found=1` raise `ValueError("raise_when_not_found must be a boolean")` before profile GET work.
- `raise_when_not_found=False` still returns `None` for missing single-user lookup and skips missing users in bulk lookup.
- `raise_when_not_found=True` still raises `NotFoundException` for missing users.
- Existing user/profile lookup, client user accessor delegation, and request helper behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `0` or `1` tightens behavior for callers that previously used integers as booleans. Mitigation: the documented API type is `bool`; accepting integer controls can hide config parsing mistakes and accidentally change not-found behavior.
- Risk: Rejecting string values can expose CLI, environment, JSON, YAML, or spreadsheet parsing bugs. Mitigation: text configuration should parse `"true"`/`"false"` into real booleans before calling wikidot.py.
- Risk: The change could be confused with username validation. Mitigation: username validation remains unchanged; this slice only validates the not-found control flag.

## Dependencies

- Existing `UserCollection.from_names(...)` remains the source of truth for bulk profile lookup.
- Existing `User.from_name(...)` continues to delegate to `UserCollection.from_names(...)` after validating the single name and flag.
- Existing request helper behavior, profile parser behavior, user dataclasses, and client accessors remain unchanged.
- The validation is local to `src/wikidot/module/user.py` and does not affect QuickModule user lookup, site member lookup, private-message recipients, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered user lookup not-found flag validation path.

## Upstream-Safe Motivation

User lookup helpers are often called from migration ledgers, moderation scripts, generated member lists, CLI tools, and browser-free account resolution workflows. Since `raise_when_not_found` controls whether a missing user is an omitted result or a raised exception, malformed truthy strings and integer stand-ins should fail deterministically before request work rather than changing not-found behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established user/profile lookup as a practical workflow through profile-page parsing, QuickModule user/member lookups, client user accessors, request batching, title spacing, user ID href diagnostics, and username input validation.
- Existing user/profile drafts covered username shape, profile parser diagnostics, title spacing, ID extraction, request batching, and adjacent QuickModule user/member lookup diagnostics; they did not validate the caller-provided `raise_when_not_found` control.
- This slice only validates `raise_when_not_found` inputs. It does not change username normalization, profile GET URLs, missing-user page detection, valid not-found behavior, profile title parsing, avatar URL construction, collection ordering, request helper behavior, QuickModule behavior, site member lookup, private-message behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private profile content, private user data, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed not-found controls instead of coercing them. Callers that load this flag from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve it into a real boolean before calling `User.from_name(...)` or `UserCollection.from_names(...)`.
