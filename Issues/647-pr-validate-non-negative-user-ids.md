# PR Draft: Validate Non-Negative User IDs

## Summary

`User.id` and `DeletedUser.id` store Wikidot user identity metadata that flows through profile lookup, shared `printuser` parsing, site membership, applications, private messages, page votes, forum metadata, generated ledgers, and local fixtures. Existing local drafts validate malformed user ID types, shared parser user ID diagnostics, special-user identity fields, retained user clients, and QuickModule user IDs, but direct user records could still store negative integers such as `-1`.

This change validates direct user record IDs as non-negative optional integers at the existing `AbstractUser` scalar validator. It deliberately preserves `None` for optional user identity state and preserves `0` because existing deleted-user fallback behavior uses ID `0` for unknown deleted users.

## Outcome

Direct regular and deleted user records can no longer carry negative user IDs, while optional `None`, zero-ID compatibility, malformed direct type diagnostics, profile parsing, shared user parser diagnostics, user collection behavior, special-user identity checks, retained-client checks, QuickModule user result validation, and adjacent Site/User/SiteMember/Application/Page/Forum/PrivateMessage workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use user records in browser-free profile lookup, generated user/member ledgers, site membership tooling, applications, invitations, private messages, page votes, forum metadata, local fixtures, adapters, or serialized/rehydrated user records.

## Current Evidence

User-related drafts [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), [121-pr-preserve-guest-display-name-spacing.md](121-pr-preserve-guest-display-name-spacing.md), [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [426-pr-validate-user-collection-initialization.md](426-pr-validate-user-collection-initialization.md), [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md), [550-pr-validate-user-lookup-client.md](550-pr-validate-user-lookup-client.md), [615-pr-validate-user-record-client.md](615-pr-validate-user-record-client.md), [621-pr-validate-special-user-identity-fields.md](621-pr-validate-special-user-identity-fields.md), and [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md) establish user records and user identity IDs as practical parser, lookup, collection, action, and result-object surfaces.

This slice is not a duplicate of Issues 301, 302, 316, 495, 615, 621, or 646. Issues 301, 302, and 316 are shared parser diagnostics for deleted or regular user metadata. Issue 495 validates inherited user scalar types, but still accepts negative integers. Issue 615 validates retained `client` objects. Issue 621 validates special-user subtype invariants. Issue 646 validates QuickModule `QMCUser` records and returned QuickModule row IDs, not higher-level `User` or `DeletedUser` records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [495-pr-validate-user-scalar-fields.md](495-pr-validate-user-scalar-fields.md), [615-pr-validate-user-record-client.md](615-pr-validate-user-record-client.md), [621-pr-validate-special-user-identity-fields.md](621-pr-validate-special-user-identity-fields.md), and [646-pr-validate-non-negative-quickmodule-user-ids.md](646-pr-validate-non-negative-quickmodule-user-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `User(id=-1, ...)` and `User(id=-100, ...)` with `ValueError("id must be non-negative or None")`.
- Reject direct `DeletedUser(id=-1)` and `DeletedUser(id=-100)` with the same field-level diagnostic.
- Preserve direct `User(id=0, ...)` and `DeletedUser(id=0)` as non-negative identity values.
- Preserve `User(id=None)` and existing optional user scalar behavior.
- Preserve malformed direct type diagnostics for non-integers and booleans.
- Leave profile lookup, shared parser ID extraction, deleted-user missing-ID fallback, special-user identity checks, retained-client validation, user collection behavior, QuickModule user IDs, downstream user-client coherence, and live Wikidot behavior unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- User identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `User(id=-1, ...)` and `User(id=-100, ...)` must raise `ValueError("id must be non-negative or None")`. |
| R2 | Direct `DeletedUser(id=-1)` and `DeletedUser(id=-100)` must raise `ValueError("id must be non-negative or None")`. |
| R3 | Direct `User(id=0, ...)`, `DeletedUser(id=0)`, and `User(id=None, ...)` must remain valid. |
| R4 | Existing malformed direct type diagnostics and existing special-user identity checks must remain stable for covered test cases. |
| R5 | Existing profile lookup, shared user parser, user collection, QuickModule, Site/User/SiteMember/Application/Page/Forum/PrivateMessage workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user/member/site/message/page/forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, user tests, adjacent user-consuming tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct regular user records cannot store negative user IDs. | `TestUserDataclasses.test_user_rejects_negative_id` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_user_id_field(...)` rejected values below zero. | Accepting negative `User.id` values, coercing them to zero, or relying on parser or downstream action code rejects this local completion claim. | User constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Direct deleted user records cannot store negative user IDs. | `TestUserDataclasses.test_deleted_user_rejects_negative_id` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_user_id_field(...)` rejected values below zero. | Accepting negative `DeletedUser.id` values, treating them as unknown deleted users, or masking them with subclass defaults rejects this local completion claim. | DeletedUser constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Optional and zero identity states remain valid. | `test_user_accepts_valid_optional_scalar_fields`, `test_user_accepts_zero_id`, and `test_deleted_user_accepts_zero_id` passed in RED and GREEN runs. | Requiring positive-only IDs, rejecting unknown deleted-user ID `0`, or rejecting optional `None` state rejects this local completion claim. | Constructor compatibility | `tests/unit/test_user.py` |
| R4 | Existing malformed type and special-user diagnostics remain stable where covered. | `test_user_rejects_malformed_id` passed in the same focused RED and GREEN commands, and the full user module passed 112 tests. | Changing `ValueError("id must be an integer or None")`, accepting booleans, or breaking subclass default/invariant tests rejects this local completion claim. | User scalar validation | `tests/unit/test_user.py` |
| R5 | Existing user-consuming workflows remain green. | Adjacent user/parser/site/member/application/QuickModule/page-vote/page-revision/forum/private-message coverage passed 1431 tests, and the full unit suite passed 2937 tests. | Regressing profile lookup, parser ID extraction, deleted-user fallback, user collection behavior, special users, QuickModule result validation, membership workflows, application workflows, invitations, private messages, page votes, page revisions, forum metadata, or downstream user-client checks rejects this local completion claim. | User consumers | `tests/unit/test_user.py`, `tests/unit/parsers/test_user_parser.py`, `tests/unit/test_site.py`, `tests/unit/test_site_member.py`, `tests/unit/test_site_application.py`, `tests/unit/test_quick_module.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_private_message.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw profile HTML from real sites, raw parser markup from real sites, private messages, private member data, page source text, or private site/forum data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, user tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `34ecd05 fix(user): validate non-negative user ids`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserDataclasses::test_user_rejects_malformed_id tests/unit/test_user.py::TestUserDataclasses::test_user_rejects_negative_id tests/unit/test_user.py::TestUserDataclasses::test_user_accepts_zero_id tests/unit/test_user.py::TestUserDataclasses::test_deleted_user_rejects_negative_id tests/unit/test_user.py::TestUserDataclasses::test_deleted_user_accepts_zero_id -q` failed 4 negative user-ID cases before the fix; 6 malformed-input and zero-compatibility guards stayed green.
- GREEN: the same focused command passed 10 tests after user-ID range validation was added.
- `uv run ruff format src/wikidot/module/user.py tests/unit/test_user.py` left both files unchanged.
- Re-running the same focused command after formatting passed 10 tests.
- `uv run pytest tests/unit/test_user.py -q` passed 112 tests.
- `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_quick_module.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_private_message.py -q` passed 1431 tests.
- `uv run pytest tests/unit -q` passed 2937 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `User(client=client, id=-1, ...)` and `User(client=client, id=-100, ...)` raise `ValueError("id must be non-negative or None")`.
- `DeletedUser(client=client, id=-1)` and `DeletedUser(client=client, id=-100)` raise the same `ValueError`.
- `User(client=client, id=0, ...)` remains accepted and stores `0`.
- `DeletedUser(client=client, id=0)` remains accepted and stores `0`.
- `User(client=client, id=None, ...)` remains valid optional local state.
- Direct `User(id=True)`, `User(id="12345")`, `User(id=12345.0)`, and `User(id=object())` continue to raise `ValueError("id must be an integer or None")`.
- Existing shared parser user ID extraction, deleted-user missing-ID fallback, profile lookup, user collection behavior, special-user subtype checks, retained user-client validation, QuickModule user-ID validation, adjacent workflows, live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

User records are shared carrier objects across browser-free lookups, generated parsers, site administration, messaging, votes, forum metadata, and local ledgers. Negative IDs can look like ordinary integers in fixtures, adapters, or rehydrated records, then become impossible user identity state. Non-negative validation catches that impossible state at the constructor boundary while preserving optional `None` and existing unknown deleted-user ID `0` compatibility.

## Local Evidence

- Local rollout-backed drafts repeatedly use user records across profile lookup, shared user parsing, QuickModule results, membership/application workflows, private messages, page votes, page revisions, forum posts, fixtures, and generated ledgers.
- Existing local drafts covered malformed parser IDs, direct user scalar types, user record clients, special-user identity fields, and QuickModule user IDs, but did not cover negative direct `User` or `DeletedUser` IDs.
- The focused RED failures showed negative direct regular and deleted user IDs were accepted before this slice.
- This slice only validates non-negative direct user-record IDs. It does not change profile request URLs, parser selectors, user parser ID extraction, deleted-user missing-ID fallback, special-user subtype invariants for valid covered cases, action request payloads, QuickModule response parsing, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw profile HTML, raw generated user markup from real sites, private member data, private messages, page source text from real sites, and private site/forum data out of upstream discussion.

## Additional Notes

This change intentionally validates direct `User` and `DeletedUser` ID range only. It does not broaden the same rule to `Site.member_lookup(user_id=...)` filters or downstream mutable user-state action preflights; those should stay separate duplicate-checked slices if selected by future evidence.
