# PR Draft: Validate User Record Client

## Summary

`User`, `DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser` store a `client` reference that downstream objects use for ownership checks, request routing, and object-graph coherence. Earlier local slices validate user scalar fields, direct user lookup clients, client accessor parents, user collections, and many site/page/forum/private-message relationships that compare user-client identity. One base record-state gap remained: direct construction such as `User(client=None, id=12345, ...)` or `DeletedUser(client="test-client", ...)` could still create an `AbstractUser` subclass with a malformed retained `client`.

This change validates `AbstractUser.client` during record construction after existing scalar field validation. Malformed user record clients now raise `ValueError("client must be a Client")`, while existing `id`, `name`, `unix_name`, `avatar_url`, and `ip` diagnostic precedence remains unchanged. Unit test helpers that previously used plain `MagicMock()` as a stand-in client now use inert real `Client` shells, so existing cross-client tests continue to exercise "different valid client" rather than malformed user construction.

## Outcome

Concrete user record objects can no longer retain non-`Client` parent state.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct user records from parsers, profile lookups, cached objects, generated fixtures, or browser-free workflow state before passing those records into site, page, forum, vote, or private-message APIs.

## Current Evidence

Local rollout-backed drafts repeatedly identify user records as active carrier objects for higher-level workflows. Existing drafts [426-pr-validate-user-collection-constructor.md](426-pr-validate-user-collection-constructor.md), [479-pr-validate-client-accessor-parent.md](479-pr-validate-client-accessor-parent.md), [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md), [550-pr-validate-user-lookup-client.md](550-pr-validate-user-lookup-client.md), [510-pr-validate-site-member-user-client.md](510-pr-validate-site-member-user-client.md), [512-pr-validate-forum-thread-creator-client.md](512-pr-validate-forum-thread-creator-client.md), [513-pr-validate-forum-post-actor-clients.md](513-pr-validate-forum-post-actor-clients.md), [514-pr-validate-forum-post-revision-creator-client.md](514-pr-validate-forum-post-revision-creator-client.md), [515-pr-validate-page-revision-creator-client.md](515-pr-validate-page-revision-creator-client.md), [516-pr-validate-page-vote-user-client.md](516-pr-validate-page-vote-user-client.md), [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md), [613-pr-validate-private-message-participant-clients.md](613-pr-validate-private-message-participant-clients.md), and [614-pr-validate-private-message-send-recipient-client.md](614-pr-validate-private-message-send-recipient-client.md) establish user record state and user-client coherence as practical operational boundaries.

This is not a duplicate of Issue 495. Issue 495 validates user scalar fields (`id`, `name`, `unix_name`, `avatar_url`, and `ip`). This slice preserves that scalar precedence and validates the retained `client` field separately.

This is not a duplicate of Issue 550. Issue 550 validates the caller-provided client for `User.from_name(...)` and `UserCollection.from_names(...)`. This slice covers direct record construction for all concrete `AbstractUser` subclasses.

This is not a duplicate of Issues 510, 512, 513, 514, 515, 516, 611, 613, or 614. Those slices validate user-client relationships at site, forum, page, vote, private-message record, and private-message send boundaries. This slice prevents malformed user records from being created in the first place.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_user_client(...)` and call it from `AbstractUser.__post_init__`.
- Add a parameterized regression covering malformed clients for `User`, `DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser`.
- Preserve existing scalar field validation order by running client validation after the existing scalar validators.
- Update unit-test client doubles to use inert real `Client` shells where a valid user client is required without live HTTP or authentication.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `User`, `DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser` must reject `None`, booleans, strings, dictionaries, and arbitrary objects as retained `client` values. |
| R2 | Malformed user record clients must raise `ValueError("client must be a Client")`. |
| R3 | Existing malformed `id`, `name`, `unix_name`, `avatar_url`, and `ip` diagnostics must keep their current precedence. |
| R4 | Parser-created, lookup-created, and fixture-created user records with valid `Client` state must remain unchanged. |
| R5 | Existing site, page, forum, vote, search-query, and private-message user-client workflows must remain green. |
| R6 | Full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Every concrete user subclass rejects malformed retained clients. | The focused RED command failed 25 parameterized cases before the fix because malformed clients were accepted, then passed GREEN after `AbstractUser.__post_init__` validated `client`. | Accepting any malformed retained client rejects this local completion claim. | `AbstractUser.__post_init__` | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | The diagnostic is deterministic and public. | The focused regression asserts `ValueError("client must be a Client")` for all malformed client values and subclasses. | Leaking attribute errors, accepting client-like dictionaries, or raising subclass-specific unrelated diagnostics for valid scalar fields rejects this local completion claim. | User record construction | `tests/unit/test_user.py` |
| R3 | Existing scalar validation precedence remains stable. | `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 102 tests after client validation was added. | Moving malformed scalar fields behind client validation, parser work, request work, or unrelated diagnostics rejects this local completion claim. | User scalar fields and parser records | `tests/unit/test_user.py`, `tests/unit/parsers/test_user_parser.py` |
| R4 | Valid synthetic, parser, and lookup clients still construct user records. | Shared `mock_client_no_http` and affected local helpers now return inert real `Client` shells; user plus parser coverage passed 102 tests. | Requiring live client construction, live authentication, real HTTP, or initialized accessors for simple record construction rejects this local completion claim. | Unit fixtures and parser records | `tests/conftest.py`, `tests/unit/parsers/test_user_parser.py` |
| R5 | Adjacent object-graph checks continue to test coherent valid-client identity. | Adjacent coverage across user, parser, client, RequestUtil, private message, site member, site application, forum, page, page file, page revision, page vote, and search query modules passed 1871 tests. | Regressing cross-client ownership checks, parser-created users, search-query user conversion, page vote users, page/file/revision creators, forum actors, private-message users, or site-member group changes rejects this local completion claim. | Adjacent user-client workflows | `tests/unit` |
| R6 | Repository quality gates remain green. | Full unit coverage passed 2772 tests; full ruff check, full format check, mypy, pyright, and `git diff --check` passed. | Any unreported test, lint, format, type, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | All tests use synthetic `Client` and `User` objects; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `51cbe20 fix(user): validate record client`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserDataclasses::test_user_subclasses_reject_malformed_client -q` failed 25 tests before the fix because malformed retained clients did not raise.
- GREEN regression: the same focused command passed 25 tests.
- User and parser coverage: `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 102 tests.
- Adjacent user-client workflow coverage: `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_requestutil.py tests/unit/test_private_message.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_search_pages_query.py -q` passed 1871 tests.
- `uv run pytest tests/unit -q` passed 2772 tests.
- `uv run ruff format src/wikidot/module/user.py tests/unit/test_user.py tests/conftest.py tests/unit/test_site_member.py tests/unit/test_page_votes.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_search_pages_query.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py` left 11 files unchanged.
- `uv run ruff check src/wikidot/module/user.py tests/unit/test_user.py tests/conftest.py tests/unit/test_site_member.py tests/unit/test_page_votes.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_search_pages_query.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py` passed.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `User(client=None, id=12345, name="test-user", unix_name="test-user")` raises `ValueError("client must be a Client")`.
- `DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser` reject the same malformed retained client values.
- Existing malformed user scalar diagnostics remain unchanged.
- Parser-created and lookup-created users with real `Client` instances continue to construct normally.
- Existing site, page, forum, vote, search-query, and private-message user-client workflows remain unchanged.
- The new tests use unit-level synthetic state only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

User records are reused across many wikidot.py workflows as actor, recipient, member, creator, editor, and voter objects. Validating the retained `client` at base record construction gives those downstream ownership checks a reliable object-graph invariant without introducing network lookups, live auth checks, account-name equivalence rules, or compatibility shims.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed all five concrete user subclasses accepting malformed retained `client` values.
- Existing local drafts covered user scalar fields, direct lookup clients, accessor parent clients, user collections, and many downstream user-client relationship checks, but did not cover direct retained `AbstractUser.client` construction.
- This slice only validates user record client type. It does not change user lookup URL construction, profile parsing, collection semantics, auth behavior, live site behavior, downstream ownership error messages, or remote account equivalence.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private message bodies, recipient names from real messages, and private site data out of upstream discussion.

## Additional Notes

The validator intentionally requires a real `Client` instance and does not attempt to infer equivalence from usernames, IDs, login state, or mock-like attributes. That keeps direct record construction aligned with the existing identity-based ownership checks used across page, forum, site-member, private-message, and vote objects.
