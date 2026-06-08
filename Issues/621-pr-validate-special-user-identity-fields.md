# PR Draft: Validate Special User Identity Fields

## Summary

`DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser` document subtype-specific identity fields, but direct dataclass construction could override those fields after the shared scalar validator accepted the values. Examples included `AnonymousUser(id=12345)`, `GuestUser(unix_name="guest")`, and `WikidotUser(name="System")`, all of which created records whose concrete class contradicted their stored identity state.

This change adds subtype-level `__post_init__` validators after the existing `AbstractUser` scalar and client checks. Deleted users now keep the fixed deleted-account display identity, anonymous users keep `id=None`, fixed anonymous names, and no avatar, guest users keep no ID, UNIX name, or IP, and the Wikidot system user keeps its fixed identity and empty optional fields. `AnonymousUser(client=...)` still allows `ip=None`, preserving parser behavior when anonymous markup has no IP span.

## Outcome

Direct special-user construction can no longer create contradictory deleted, anonymous, guest, or system user records while parser-created records, optional anonymous IP state, regular `User` optional fields, and existing user-client coherence behavior remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who create or rehydrate user records from printuser parsing, profile lookup, page/forum metadata, membership ledgers, private messages, page votes, generated fixtures, or local audit records.

## Current Evidence

User-related local drafts [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), [121-pr-preserve-guest-display-name-spacing.md](121-pr-preserve-guest-display-name-spacing.md), [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [426-pr-validate-user-collection-initialization.md](426-pr-validate-user-collection-initialization.md), [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md), [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md), [550-pr-validate-user-lookup-client.md](550-pr-validate-user-lookup-client.md), and [615-pr-validate-user-record-client.md](615-pr-validate-user-record-client.md) establish user records as active parser, lookup, collection, action, and rehydrated-state surfaces.

This is not a duplicate of Issue 495. Issue 495 validates inherited scalar shapes for `id`, `name`, `unix_name`, `avatar_url`, and `ip`, but explicitly leaves subtype-specific invariants as future work. This slice validates only the concrete special-user invariants after the shared scalar validators have already run.

This is not a duplicate of Issue 615. Issue 615 validates the retained `client` object for all user subclasses. This slice validates the relationship between a concrete special-user class and its own identity fields.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_user_expected_field(...)` for subtype invariant checks that do not coerce values.
- Add `__post_init__` methods to `DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser` that call `super().__post_init__()` before checking subtype identity state.
- Reject contradictory special-user constructor fields with stable messages such as `ValueError("id must be None")`, `ValueError("name must be Anonymous")`, and `ValueError("unix_name must be wikidot")`.
- Preserve `AnonymousUser(client=...)` with `ip=None` and `AnonymousUser(client=..., ip="...")` for parser paths where the remote markup may or may not expose an IP span.
- Add focused RED/GREEN tests for each affected special-user field.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `DeletedUser(...)` must reject overridden `name`, `unix_name`, `avatar_url`, and `ip` fields that contradict deleted-account semantics. |
| R2 | `AnonymousUser(...)` must reject overridden `id`, `name`, `unix_name`, and `avatar_url` fields while continuing to allow `ip=None` and string IP values. |
| R3 | `GuestUser(...)` must reject overridden `id`, `unix_name`, and `ip` fields while continuing to allow optional guest `name` and `avatar_url`. |
| R4 | `WikidotUser(...)` must reject overridden `id`, `name`, `unix_name`, `avatar_url`, and `ip` fields that contradict system-user semantics. |
| R5 | Existing shared scalar and client validation precedence must remain unchanged. |
| R6 | Parser-created deleted, anonymous, guest, Wikidot, and regular user records must remain green. |
| R7 | Full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Deleted-user records keep fixed deleted identity state. | `test_special_user_subclasses_reject_identity_overrides` failed RED for deleted-user `name`, `unix_name`, `avatar_url`, and `ip` overrides with `DID NOT RAISE`, then passed GREEN after `DeletedUser.__post_init__` validated those fields. | Accepting `DeletedUser(name="deleted")`, `DeletedUser(unix_name="deleted")`, avatar URLs, or IPs rejects this local completion claim. | `DeletedUser` constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Anonymous-user records keep anonymous identity state while IP remains optional. | The focused RED/GREEN test covered `AnonymousUser(id=12345)`, name/unix-name/avatar overrides, and `test_anonymous_user_allows_missing_ip` passed before and after the fix. | Requiring an IP for anonymous markup without an IP span, accepting IDs, accepting custom names, or accepting avatar URLs rejects this local completion claim. | `AnonymousUser` constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Guest records keep no ID, UNIX name, or IP while retaining guest display fields. | The focused RED/GREEN test covered guest `id`, `unix_name`, and `ip` overrides; existing guest-default coverage continued to pass. | Rejecting valid guest display names or Gravatar URLs, or accepting guest IDs, UNIX names, or IPs rejects this local completion claim. | `GuestUser` constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R4 | Wikidot system records keep fixed system identity state. | The focused RED/GREEN test covered Wikidot system `id`, `name`, `unix_name`, `avatar_url`, and `ip` overrides. | Accepting a renamed system user, custom UNIX name, avatar URL, IP, or numeric ID rejects this local completion claim. | `WikidotUser` constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R5 | Existing malformed scalar/client diagnostics stay stable. | `tests/unit/test_user.py tests/unit/parsers/test_user_parser.py` passed 119 tests after subtype checks were added after `super().__post_init__()`. | Moving malformed scalar or malformed client values behind subtype-specific diagnostics rejects this local completion claim. | User constructor validation order | `tests/unit/test_user.py` |
| R6 | Parser-created records remain compatible. | User plus parser coverage passed 119 tests, and a direct scan found special-user constructors only in the parser and user tests. | Breaking deleted-user string parsing, deleted printuser parsing, anonymous markup with or without IP, guest Gravatar parsing, or Wikidot system-user parsing rejects this local completion claim. | User parser | `src/wikidot/util/parser/user.py`, `tests/unit/parsers/test_user_parser.py` |
| R7 | Repository quality gates remain green. | Full unit coverage passed 2796 tests; full ruff check, full format check, mypy, pyright, and `git diff --check` passed. | Any unreported test, lint, format, type, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R8 | No live auth material or private state is needed to prove the behavior. | The tests use synthetic `Client` and user records only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `ef69159 fix(user): validate special user identity fields`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserDataclasses::test_anonymous_user_allows_missing_ip tests/unit/test_user.py::TestUserDataclasses::test_special_user_subclasses_reject_identity_overrides -q` failed 16 override cases with `DID NOT RAISE`, while the missing-IP anonymous case passed.
- GREEN focused: the same focused command passed 17 tests after subtype validators were added.
- User plus parser coverage: `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py -q` passed 119 tests.
- Adjacent user-consuming workflow coverage: `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_private_message.py tests/unit/test_page_votes.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 1568 tests.
- `uv run pytest tests/unit -q` passed 2796 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `DeletedUser(client, name="deleted")`, `DeletedUser(client, unix_name="deleted")`, `DeletedUser(client, avatar_url="http://example.com/avatar.png")`, and `DeletedUser(client, ip="192.168.1.1")` raise field-specific `ValueError` diagnostics.
- `AnonymousUser(client, id=12345)`, custom anonymous names, custom anonymous UNIX names, and anonymous avatar URLs raise field-specific `ValueError` diagnostics.
- `AnonymousUser(client)` and `AnonymousUser(client, ip="192.168.1.1")` remain valid.
- `GuestUser(client, id=12345)`, `GuestUser(client, unix_name="guest")`, and `GuestUser(client, ip="192.168.1.1")` raise field-specific `ValueError` diagnostics.
- `GuestUser(client, name="Guest Name", avatar_url="http://gravatar.com/avatar/abc")` remains valid.
- `WikidotUser(client, id=12345)`, custom system names, custom system UNIX names, system avatar URLs, and system IPs raise field-specific `ValueError` diagnostics.
- Existing shared user scalar validation, retained-client validation, user parser behavior, user lookup behavior, user collections, downstream user-client checks, and regular `User` optional-state behavior remain unchanged.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Concrete special-user classes are used to distinguish deleted accounts, anonymous posters, guest posters, and Wikidot system activity from regular registered users. When callers create fixtures or rehydrate local records, the class and stored identity fields should agree. Enforcing that agreement at construction prevents contradictory local state without changing live request behavior, parser selectors, optional anonymous IP handling, or regular user records.

## Local Evidence, Not For Upstream Paste

- The focused RED run showed all tested special-user identity overrides were accepted before this slice.
- Existing local drafts covered printuser parsing, display-name spacing, deleted-user ID parsing, regular-user ID extraction, user lookup inputs, user collections, user scalar shape, user retained clients, and downstream user-client coherence, but did not cover concrete special-user class/field consistency.
- This slice only validates direct construction of special-user identity fields. It does not change profile lookup, user parser branch selection, display-name spacing, action request payloads, page vote lookup, private-message behavior, live Wikidot behavior, authentication semantics, field assignment interception, frozen dataclass behavior, or regular `User` optional-state semantics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw profile HTML, private member data, private messages, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The subtype checks deliberately run after `AbstractUser.__post_init__()`. That keeps malformed type diagnostics such as `id must be an integer or None` and `client must be a Client` stable before the narrower semantic invariant checks run.
