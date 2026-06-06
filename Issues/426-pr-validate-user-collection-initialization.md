# PR Draft: Validate User Collection Initialization

## Summary

`UserCollection` documents and behaves as a collection of `AbstractUser` objects, but it inherited the raw `list` constructor. A caller could construct `UserCollection("1")`, `UserCollection(("1",))`, or `UserCollection([None])`; the malformed collection then failed later in iteration, generated user ledgers, client user workflows, or downstream identity checks with unstable attribute errors or silently poisoned local state.

This change validates constructor input before storing entries. Non-list non-`None` `users` values now raise `ValueError("users must be a list or None")`; list entries that are not `AbstractUser` now raise `ValueError("users list entries must be AbstractUser")`. `users=None`, empty collections, valid `AbstractUser` lists, profile lookup, not-found skip/raise behavior, profile-title spacing, profile ID parsing, avatar URL construction, collection ordering, client user accessors, request helper behavior, QuickModule parsing, and regular user parser behavior remain unchanged.

## Outcome

Callers cannot silently create malformed `UserCollection` instances through the public constructor, while existing browser-free user profile lookup, client accessor, request helper, and parser workflows remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `client.user.get_bulk(...)`, `UserCollection.from_names(...)`, direct `UserCollection(...)` construction, migration ledgers, moderation scripts, generated member lists, account-resolution tooling, or browser-free identity lookup workflows.

## Current Evidence

Local rollout-backed drafts repeatedly identify user profile lookup and generated user collections as practical workflow surfaces. Existing drafts [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), and [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md) establish profile lookup, rendered title fidelity, parser diagnostics, username validation, and not-found flag validation as active operational boundaries. Adjacent constructor-hardening drafts [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), and [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md) establish the local state-integrity pattern for collection constructors.

Those prior slices are not duplicates. The user/profile drafts covered profile fetching, title spacing, profile ID extraction, parser context, username validation, and the `raise_when_not_found` control in `User.from_name(...)` / `UserCollection.from_names(...)`. None of them validates the `UserCollection(users=...)` constructor itself before malformed user entries become stored list state.

## Related Issue

Builds directly on [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), and the adjacent constructor validation pattern from [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), and [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `UserCollection.__init__(users=...)` validation.
- Preserve omitted `users` and `users=None` as empty collections.
- Reject non-list non-`None` `users` with `ValueError("users must be a list or None")`.
- Reject non-`AbstractUser` list entries with `ValueError("users list entries must be AbstractUser")`.
- Preserve valid empty collections, valid `AbstractUser` entries, iteration, `from_names(...)`, `User.from_name(...)`, `client.user.get(...)`, `client.user.get_bulk(...)`, request helper behavior, profile parser diagnostics, QuickModule parser behavior, and regular user parser behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- User collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `UserCollection(users=True)`, `False`, `"1"`, `("1",)`, and `1` must raise `ValueError("users must be a list or None")` before storing collection entries. |
| R2 | `UserCollection(users=[None])`, `[True]`, `["1"]`, and `[{"id": 1}]` must raise `ValueError("users list entries must be AbstractUser")` before storing collection entries. |
| R3 | `UserCollection()`, `UserCollection(None)`, `UserCollection([])`, and `UserCollection([valid_user])` must remain valid. |
| R4 | Existing profile lookup, not-found skip/raise behavior, profile-title spacing, profile ID parsing, avatar URL construction, collection ordering, client user accessors, request helper behavior, QuickModule parsing, and regular user parser behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, user module tests, adjacent client/request/parser tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestUserCollection.test_init_rejects_non_list_users` failed RED for `True`, `False`, `"1"`, `("1",)`, and `1`, then passed GREEN after constructor validation was added. | Treating strings or tuples as user entries, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | UserCollection constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Non-`AbstractUser` constructor list entries fail at the public constructor boundary. | `TestUserCollection.test_init_rejects_non_user_entries` passed after entry validation was added and covers `None`, `True`, `"1"`, and `{"id": 1}`. | Accepting missing values, booleans, strings, dictionaries, serialized user records, or fixture stand-ins as stored users rejects this local completion claim. | UserCollection constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Valid constructor inputs remain green. | Existing `test_iteration` passed with valid `User` entries, and the focused constructor run passed 9 tests. | Rejecting omitted input, `None`, empty valid lists, valid user lists, or normal iteration rejects this local completion claim. | UserCollection constructor and iteration | `tests/unit/test_user.py` |
| R4 | Existing user workflows remain green. | `tests/unit/test_user.py` passed 36 tests; adjacent user/client/request/parser/QuickModule tests passed 195 tests; full unit tests passed 1576 tests. | Regressing profile URLs, not-found behavior, title spacing, ID href parsing, missing profile diagnostics, user collection ordering, `client.user.get(...)`, `client.user.get_bulk(...)`, request helper behavior, QuickModule parsing, or regular user parser behavior rejects this local completion claim. | User lookup and parser workflows | `tests/unit/test_user.py`, `tests/unit/test_client.py`, `tests/unit/test_requestutil.py`, `tests/unit/parsers/test_user_parser.py`, `tests/unit/test_quick_module.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted user and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a0f38a6 fix(user): validate user collection initialization`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_init_rejects_non_list_users -q` failed 5 tests before the container fix; strings and tuples were accepted, while booleans and integers leaked incidental `TypeError`.
- GREEN: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_init_rejects_non_list_users tests/unit/test_user.py::TestUserCollection::test_init_rejects_non_user_entries -q` passed 9 tests after adding non-list and entry validation.
- `uv run ruff format src/wikidot/module/user.py tests/unit/test_user.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_user.py -q` passed 36 tests.
- `uv run pytest tests/unit/test_user.py tests/unit/test_client.py tests/unit/test_requestutil.py tests/unit/parsers/test_user_parser.py tests/unit/test_quick_module.py -q` passed 195 tests.
- `uv run pytest tests/unit -q` passed 1576 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `UserCollection(users=True)`, `False`, `"1"`, `("1",)`, and `1` raise `ValueError("users must be a list or None")`.
- `UserCollection(users=[None])`, `[True]`, `["1"]`, and `[{"id": 1}]` raise `ValueError("users list entries must be AbstractUser")`.
- `UserCollection()`, `UserCollection(None)`, `UserCollection([])`, and `UserCollection([valid_user])` continue to work.
- Existing profile lookup, not-found skip/raise behavior, profile-title spacing, profile ID parsing, avatar URL construction, collection ordering, client user accessors, request helper behavior, QuickModule parsing, and regular user parser behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`UserCollection` is the stored object shape behind browser-free profile lookup, client bulk user accessors, generated user lists, migration ledgers, and account-resolution tooling. Constructor validation keeps malformed local state out of the collection while preserving existing lookup, parser, request, and client behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free profile lookup, client user accessors, user parser workflows, and tests that seed `UserCollection` directly.
- Existing local drafts covered profile-title spacing, user profile parser context, profile ID href parsing, username validation, and not-found flag validation, but did not cover the `UserCollection(users=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions or was accepted as iterable collection state. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, user lookup, client accessors, request helper behavior, QuickModule parsing, and regular user parser behavior.
- This slice only validates user collection constructor input. It does not change profile GET URL construction, profile parsing selectors, missing-user handling, username normalization, avatar URL construction, `User.from_name(...)`, `UserCollection.from_names(...)`, `client.user.get(...)`, `client.user.get_bulk(...)`, QuickModule parsing, regular user parsing, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed user-like objects and test mocks in `UserCollection`. Callers should construct real `AbstractUser` subclasses before storing them in a user collection.
