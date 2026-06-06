# PR Draft: Validate Client Accessor Parent Clients

## Summary

`ClientUserAccessor`, `ClientPrivateMessageAccessor`, and `ClientSiteAccessor` are the public helper objects behind `Client.user`, `Client.private_message`, and `Client.site`. They are normally created from `Client.__init__`, but their constructors are importable and document `client: Client` as the required parent. Before this change, direct construction accepted malformed parents such as `None`, booleans, strings, dictionaries, and arbitrary objects, storing broken accessor state that failed later inside user lookup, private-message reads/sends, or site lookup.

This change validates accessor constructor parent clients before storing state. Malformed values now raise `ValueError("client must be a Client")`. Valid `Client` parents, normal `Client.__init__` accessor creation, user lookup, private-message workflows, site lookup, and adjacent client/site workflows remain unchanged.

## Outcome

Callers cannot silently construct client accessors with malformed parent-client state, while ordinary `Client.user`, `Client.private_message`, and `Client.site` usage continues to work exactly as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free user lookup, private-message detail reads, inbox/sent-box acquisition, private-message sends, site lookup, generated ledgers, local fixtures, or rehydrated helper state around `Client.user`, `Client.private_message`, and `Client.site`.

## Current Evidence

Local rollout-backed drafts repeatedly identify the three client accessors as practical workflow entry points. User/profile lookup drafts such as [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), and [426-pr-validate-user-collection-initialization.md](426-pr-validate-user-collection-initialization.md) establish `Client.user` as an active operational surface. Private-message drafts such as [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), and [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md) establish `Client.private_message` as an active operational surface. Site lookup drafts such as [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md) and adjacent site/accessor drafts establish `Client.site` as an active operational surface.

Those prior slices are not duplicates. They validate profile usernames, not-found flags, private-message IDs, private-message send inputs, retry controls, site UNIX names, parser diagnostics, response bodies, and adjacent collection state. Issue 478 validates `SitePagesAccessor`, `SitePageAccessor`, and `SiteForumAccessor` parent sites, not client accessor parent clients. None rejects malformed direct `ClientUserAccessor(client=...)`, `ClientPrivateMessageAccessor(client=...)`, or `ClientSiteAccessor(client=...)` construction before broken parent state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on the client accessor workflow surfaces documented by [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), and the adjacent accessor-parent validation pattern from [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared `_validate_client_accessor_client(...)` helper for the three client accessor constructors.
- Validate `ClientUserAccessor.client`, `ClientPrivateMessageAccessor.client`, and `ClientSiteAccessor.client` before storing parent state.
- Reject malformed parent-client values with `ValueError("client must be a Client")`.
- Preserve valid `Client` parents, normal `Client.__init__` accessor creation, user lookup, private-message reads/sends, site lookup, and adjacent client/site workflows.

## Type Of Change

- Input validation
- Public accessor constructor behavior hardening
- Client parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ClientUserAccessor(client=...)`, `ClientPrivateMessageAccessor(client=...)`, and `ClientSiteAccessor(client=...)` must reject `None`, `True`, `"test-client"`, `{"username": "test-user"}`, and `object()` with `ValueError("client must be a Client")`. |
| R2 | The same constructors must retain a valid `Client` parent by identity. |
| R3 | Normal `Client.__init__` accessor creation, `Client.user`, `Client.private_message`, `Client.site`, user lookup, private-message workflows, site lookup, and adjacent client/site workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, private message bodies/subjects, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, accessor tests, client tests, adjacent user/private-message/site tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct accessor parent clients fail at the constructor boundary. | `TestClientAccessorsInit.test_init_rejects_malformed_client` failed RED for 15 malformed accessor/client combinations because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, booleans, strings, dictionaries, arbitrary objects, or storing accessors with malformed parent-client state rejects this local completion claim. | Client accessor constructors | `src/wikidot/module/client.py`, `tests/unit/test_client_accessors.py` |
| R2 | Valid `Client` parent values remain bound by identity. | `TestClientAccessorsInit.test_init_accepts_client` passed for all three accessor classes in the 18-test focused module run. | Copying, coercing, wrapping, rejecting, or replacing the valid parent client rejects this local completion claim. | Client accessor constructors | `tests/unit/test_client_accessors.py` |
| R3 | Existing adjacent client/user/private-message/site workflows remain green. | `tests/unit/test_client.py` passed 24 tests; `tests/unit/test_client_accessors.py tests/unit/test_client.py tests/unit/test_user.py tests/unit/test_private_message.py tests/unit/test_site.py` passed 414 tests; full unit tests passed 1960 tests. | Regressing normal `Client` initialization, user lookup, private-message reads, private-message sends, inbox/sent-box acquisition, site lookup, or site workflows rejects this local completion claim. | Client, user, private-message, and site workflows | `tests/unit/test_client_accessors.py`, `tests/unit/test_client.py`, `tests/unit/test_user.py`, `tests/unit/test_private_message.py`, `tests/unit/test_site.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private message bodies/subjects, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8f301c4 fix(client): validate accessor parent clients`.

- RED: `uv run pytest tests/unit/test_client_accessors.py::TestClientAccessorsInit::test_init_rejects_malformed_client -q` failed 15 tests before the fix; every malformed direct accessor parent reported `DID NOT RAISE`.
- GREEN: the same focused command passed 15 tests after accessor parent-client validation was added.
- `uv run pytest tests/unit/test_client_accessors.py -q` passed 18 tests.
- `uv run pytest tests/unit/test_client.py -q` passed 24 tests.
- `uv run pytest tests/unit/test_client_accessors.py tests/unit/test_client.py tests/unit/test_user.py tests/unit/test_private_message.py tests/unit/test_site.py -q` passed 414 tests.
- `uv run pytest tests/unit -q` passed 1960 tests.
- `uv run ruff format src/wikidot/module/client.py tests/unit/test_client_accessors.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/client.py tests/unit/test_client_accessors.py` passed.
- `uv run mypy src/wikidot/module/client.py tests/unit/test_client_accessors.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/client.py tests/unit/test_client_accessors.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 84 files already formatted.
- `uv run mypy src tests` passed with no issues in 84 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and new client accessor test module pass pyright together.

## Acceptance Criteria

- `ClientUserAccessor(None)`, `ClientUserAccessor(True)`, `ClientUserAccessor("test-client")`, `ClientUserAccessor({"username": "test-user"})`, and `ClientUserAccessor(object())` raise `ValueError("client must be a Client")`.
- `ClientPrivateMessageAccessor(...)` rejects the same malformed parent-client values with the same error.
- `ClientSiteAccessor(...)` rejects the same malformed parent-client values with the same error.
- Valid `Client` parents are stored by identity for all three accessors.
- `Client.__init__` still creates working `user`, `private_message`, and `site` accessors for valid `Client` objects.
- Existing user lookup, private-message reads/sends, inbox/sent-box acquisition, site lookup, and adjacent client/site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, private message bodies/subjects, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

The three client accessors sit at important workflow boundaries: user lookup, private-message reads/sends, and site lookup. `Client.__init__` already supplies valid parents, so the change is intentionally conservative: it only prevents direct callers, fixtures, generated adapters, or rehydrated helper state from storing malformed parent objects that later fail as less informative attribute errors or request-path errors.

## Local Evidence

- Local rollout evidence used `Client.user` for browser-free profile lookup, user collection acquisition, not-found control handling, and generated user ledgers.
- Local rollout evidence used `Client.private_message` for direct private-message reads, inbox/sent-box acquisition, private-message sends, duplicate-detail reuse, and generated private-message ledgers.
- Local rollout evidence used `Client.site` for site lookup and client-side site accessor delegation.
- Existing local drafts covered profile lookup controls, site lookup controls, private-message IDs, private-message send inputs, retry controls, collection validation, parser diagnostics, and site accessor parent validation, but did not cover direct client accessor constructor parents.
- This slice only validates direct client accessor constructor parent-client input. It does not change authentication, Ajax client setup, user parsing, private-message parsing, private-message send behavior, site lookup semantics, live Wikidot behavior, or `Client.__init__` structure.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private message bodies/subjects, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed parent objects instead of duck-typing anything with `amc_client`, `login_check`, or `is_logged_in`. Accessors depend on the complete `Client` object shape, and `Client.__init__` already provides the canonical construction path.
