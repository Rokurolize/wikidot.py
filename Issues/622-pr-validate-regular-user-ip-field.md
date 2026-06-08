# PR Draft: Validate Regular User IP Field

## Summary

`User` represents a registered Wikidot account, and its documentation states that `ip` is unavailable for regular users and should remain `None`. After shared scalar validation and special-user identity validation, direct `User(...)` construction could still store a string IP address such as `User(client=client, ip="192.168.1.1")`, creating a regular user record with anonymous-only state.

This change adds a `User.__post_init__` validator after `AbstractUser.__post_init__()`. Regular users now reject string IP values with `ValueError("ip must be None")`, while `User(ip=None)`, parser-created regular users, profile lookup results, anonymous user IP state, shared scalar diagnostics, and downstream user-client checks remain unchanged.

## Outcome

Regular user records can no longer retain an IP address field that belongs to anonymous-user semantics.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who create or rehydrate user records for profile lookup, printuser parsing, page/forum metadata, membership records, private messages, page votes, generated fixtures, or local audit ledgers.

## Current Evidence

Existing user drafts [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md), [550-pr-validate-user-lookup-client.md](550-pr-validate-user-lookup-client.md), [615-pr-validate-user-record-client.md](615-pr-validate-user-record-client.md), and [621-pr-validate-special-user-identity-fields.md](621-pr-validate-special-user-identity-fields.md) establish user scalar shape, retained client state, lookup clients, and special-user subtype identity as active local state boundaries.

This is not a duplicate of Issue 495. Issue 495 validates that `ip` is either a string or `None`; it does not validate that regular `User` records specifically require `ip=None`.

This is not a duplicate of Issue 621. Issue 621 validates deleted, anonymous, guest, and Wikidot system subtype identity fields. It intentionally leaves regular `User` optional state unchanged; this slice handles the adjacent regular-user IP invariant.

No upstream issue was filed from this local workspace.

## Changes

- Add `User.__post_init__()` that calls `super().__post_init__()` and then checks `ip is None`.
- Reject `User(client=valid_client, ip="192.168.1.1")` with `ValueError("ip must be None")`.
- Preserve existing `User(client=..., ip=None)` optional-state behavior.
- Preserve anonymous-user IP behavior; `AnonymousUser(client=..., ip="192.168.1.1")` remains valid.
- Add a focused RED/GREEN regression for regular-user IP state.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `User(..., ip="192.168.1.1")` construction must raise `ValueError("ip must be None")`. |
| R2 | `User(..., ip=None)` and existing regular-user optional fields must remain valid. |
| R3 | Existing malformed non-string IP diagnostics must still be handled by shared scalar validation before the regular-user invariant check. |
| R4 | `AnonymousUser(..., ip="192.168.1.1")` and parser-created anonymous users must remain valid. |
| R5 | Profile lookup, printuser parsing, user-consuming site/page/forum/private-message workflows, full unit, lint, format, mypy, pyright, and whitespace gates must pass. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Regular users reject anonymous-only IP state. | `test_regular_user_rejects_ip` failed RED with `DID NOT RAISE`, then passed GREEN after `User.__post_init__` validated `ip is None`. | Accepting a string IP on `User` rejects this local completion claim. | `User` constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Existing regular optional state remains valid. | `test_user_accepts_valid_optional_scalar_fields` passed in the focused RED and GREEN run and full user coverage. | Rejecting `User(..., id=None, name=None, unix_name=None, avatar_url=None, ip=None)` rejects this local completion claim. | `User` constructor | `tests/unit/test_user.py` |
| R3 | Shared scalar validation remains first. | The new check runs after `super().__post_init__()`, and full `tests/unit/test_user.py` coverage passed existing malformed optional text cases. | Changing `ValueError("ip must be a string or None")` for non-string IP values rejects this local completion claim. | Validation order | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R4 | Anonymous IP state remains valid. | User plus parser coverage passed 120 tests after the change, including existing anonymous-user IP tests and parser coverage. | Rejecting anonymous string IPs, anonymous missing IP markup, or parser-created anonymous users rejects this local completion claim. | `AnonymousUser` and parser | `tests/unit/test_user.py`, `tests/unit/parsers/test_user_parser.py` |
| R5 | Adjacent user-consuming workflows remain green. | Adjacent user/parser/site/member/application/private-message/page/page-vote/page-revision/forum coverage passed 1569 tests, full unit passed 2797 tests, and full static gates passed. | Regressing profile lookup, printuser parsing, site actions, private-message actors, page votes/revisions, forum actors, lint, type, or whitespace checks rejects this local completion claim. | Repository workflows | `tests/unit` |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic `Client` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `3513dad fix(user): validate regular user ip field`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserDataclasses::test_user_accepts_valid_optional_scalar_fields tests/unit/test_user.py::TestUserDataclasses::test_regular_user_rejects_ip -q` failed the regular-user IP case with `DID NOT RAISE`, while the valid optional-state case passed.
- GREEN focused: the same command passed 2 tests after `User.__post_init__` required `ip=None`.
- User plus parser coverage: `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 120 tests.
- Adjacent user-consuming workflow coverage: `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_private_message.py tests/unit/test_page_votes.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 1569 tests.
- `uv run pytest tests/unit -q` passed 2797 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `User(client=valid_client, ip="192.168.1.1")` raises `ValueError("ip must be None")`.
- `User(client=valid_client, ip=None)` remains valid.
- Non-string regular-user IP values still raise the shared `ValueError("ip must be a string or None")` diagnostic.
- `AnonymousUser(client=valid_client, ip="192.168.1.1")` remains valid.
- Parser-created regular, anonymous, deleted, guest, and Wikidot user records remain compatible.
- Existing user lookup, user collections, site member/application/invite workflows, private-message participants/sends, page vote/revision actors, forum actors, full unit tests, lint, format, mypy, pyright, and whitespace checks remain green.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

The shared user model already separates regular accounts from anonymous posters by concrete class. Keeping regular `User.ip` empty prevents rehydrated fixtures, generated ledgers, or direct local records from mixing regular-account identity with anonymous-only state, without changing parser branch selection, anonymous IP handling, lookup requests, live Wikidot behavior, or downstream action payloads.

## Local Evidence, Not For Upstream Paste

- The focused RED run showed a direct regular `User` accepted a string IP before this slice.
- Existing local drafts covered user scalar shape, retained client state, lookup clients, and special-user identity, but did not cover regular-user IP semantics.
- This slice only validates direct regular-user IP state. It does not change anonymous user IP handling, deleted/guest/system user identity checks, regular user ID/name/unix/avatar optionality, profile lookup, parser branch selection, display-name spacing, action request payloads, page vote lookup, private-message behavior, live Wikidot behavior, authentication semantics, field assignment interception, or frozen dataclass behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw profile HTML, private member data, private messages, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The regular-user invariant deliberately runs after shared scalar validation. That keeps malformed type errors separate from valid string values that are semantically invalid for regular registered users.
