# PR Draft: Validate User Scalar Fields

## Summary

`User`, `DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser` all inherit `AbstractUser` scalar state: `id`, `name`, `unix_name`, `avatar_url`, and `ip`. Earlier local slices already covered user parser diagnostics, user profile lookup input validation, user collection initialization, action-call recipient/applicant/member validation, page-vote search-user validation, and adjacent QuickModule user result validation. One local-state gap remained: direct user dataclass construction could store malformed scalar values such as boolean IDs, string IDs, list names, dictionary avatar URLs, or numeric IP values.

This change validates `AbstractUser` scalar fields at dataclass initialization. `id` now accepts only non-boolean integers or `None`, while `name`, `unix_name`, `avatar_url`, and `ip` accept only strings or `None`. Existing subclass defaults, profile parsing, lookup behavior, collection behavior, action-call validation, and downstream corrupted-state guards remain unchanged.

## Outcome

Direct user-record construction can no longer store malformed scalar field values, and existing downstream APIs still defend against user objects whose fields are corrupted after construction.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use user records in profile lookup, printuser parsing, site membership actions, site applications, private messages, page vote searches, generated ledgers, fixtures, or rehydrated local records.

## Current Evidence

User-related drafts [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), [121-pr-preserve-guest-display-name-spacing.md](121-pr-preserve-guest-display-name-spacing.md), [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [316-pr-regular-user-onclick-id-context.md](316-pr-regular-user-onclick-id-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [370-pr-validate-site-invite-user-input.md](370-pr-validate-site-invite-user-input.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [384-pr-validate-user-lookup-not-found-flag.md](384-pr-validate-user-lookup-not-found-flag.md), [410-pr-validate-site-member-action-users.md](410-pr-validate-site-member-action-users.md), [426-pr-validate-user-collection-initialization.md](426-pr-validate-user-collection-initialization.md), [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), and [494-pr-validate-quickmodule-result-text-fields.md](494-pr-validate-quickmodule-result-text-fields.md) establish users as practical record state across parser, lookup, collection, action, and result-object workflows.

Those prior slices are not duplicates. They validate parser-derived user metadata, public lookup arguments, action recipient/applicant/member arguments, loaded collection entries, page-vote search users, site member/application user fields, and QuickModule result objects. None validates direct `User(...)` or inherited `AbstractUser` scalar fields before malformed local state is stored.

## Related Issue / Non-Duplicate Analysis

Builds on the constructor-state hardening pattern used for site, page, forum, vote, file, revision, collection, and result-ledger records, but applies it to common user record fields. The change deliberately does not add subtype-specific invariants such as "regular `User.id` must be present" or "anonymous `ip` must be present", because existing subclasses and parser fixtures use `None` as valid optional state.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_user_id_field(...)` for optional non-boolean integer user IDs.
- Add `_validate_user_optional_text_field(...)` for optional user text fields.
- Add `AbstractUser.__post_init__` to validate `id`, `name`, `unix_name`, `avatar_url`, and `ip` for all user subclasses.
- Add focused constructor tests for valid optional state and malformed scalar fields.
- Update downstream corrupted-state tests to construct valid users first and then mutate fields, preserving action-level validation coverage after constructor validation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Test addition
- Test fixture maintenance for corrupted-state validation

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `User(id=...)` construction must reject non-integer IDs, including booleans, while preserving `None` as valid optional state. |
| R2 | Direct `User(name=...)`, `User(unix_name=...)`, `User(avatar_url=...)`, and `User(ip=...)` construction must reject non-string non-`None` values. |
| R3 | Existing subclass defaults for `DeletedUser`, `AnonymousUser`, `GuestUser`, and `WikidotUser` must remain valid. |
| R4 | Existing profile lookup, user parser, user collection, QuickModule, site member/application/invite, private-message recipient, page-vote search, page-revision, forum-thread/post/revision workflows must remain green. |
| R5 | Downstream APIs that validate corrupted user state after construction must retain their existing boundary checks and diagnostics. |
| R6 | Focused RED/GREEN, user tests, adjacent workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct user IDs fail at construction. | `TestUserDataclasses.test_user_rejects_malformed_id` failed RED for `True`, `"12345"`, `12345.0`, and `object()` with `DID NOT RAISE`, then passed GREEN after validation was added. | Accepting booleans, numeric strings, floats, or arbitrary objects as stored IDs rejects this local completion claim. | User constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R2 | Malformed direct optional text fields fail at construction. | `TestUserDataclasses.test_user_rejects_malformed_optional_text_fields` failed RED for 8 malformed field/value cases with `DID NOT RAISE`, then passed GREEN after validation was added. | Accepting non-string names, unix names, avatar URLs, or IP values rejects this local completion claim. | User constructor | `src/wikidot/module/user.py`, `tests/unit/test_user.py` |
| R3 | Existing defaults and optional state stay valid. | `TestUserDataclasses.test_user_accepts_valid_optional_scalar_fields` passed RED and GREEN, and `tests/unit/test_user.py` passed 49 tests. | Rejecting existing `None` optional state or subclass defaults rejects this local completion claim. | User dataclasses | `tests/unit/test_user.py` |
| R4 | Adjacent user-consuming workflows remain green. | Adjacent user/parser/site/member/application/QuickModule/page-vote/page-revision/forum/private-message tests passed, and full unit tests passed 2156 tests. | Regressing profile parsing, lookup, collection behavior, user-consuming action validation, vote lookup, or forum/page user metadata workflows rejects this local completion claim. | User consumers | `tests/unit` |
| R5 | Downstream corrupted-state validations remain covered. | Existing site member, site application, site invite, private-message recipient, and page-vote search tests now create valid users and mutate scalar fields before invoking the downstream API. | Removing downstream user-state checks or relying only on constructor validation rejects this local completion claim. | Action/search boundaries | `tests/unit/test_site_member.py`, `tests/unit/test_site_application.py`, `tests/unit/test_site.py`, `tests/unit/test_private_message.py`, `tests/unit/test_page_votes.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Full ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright was run and reported as existing unrelated full-tree test typing errors. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `802396d fix(user): validate user scalar fields`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_user.py::TestUserDataclasses::test_user_accepts_valid_optional_scalar_fields tests/unit/test_user.py::TestUserDataclasses::test_user_rejects_malformed_id tests/unit/test_user.py::TestUserDataclasses::test_user_rejects_malformed_optional_text_fields` failed 12 malformed constructor cases before the fix with `DID NOT RAISE`, while the valid optional-state case passed.
- GREEN: the same focused command passed 13 tests after `AbstractUser` scalar validation was added.
- `.venv/bin/python -m pytest -q tests/unit/test_user.py` passed 49 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_quick_module.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py` passed 964 tests after downstream malformed-state fixtures were updated.
- `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessage::test_send_rejects_malformed_user_recipient_before_login` passed 3 tests after the private-message malformed-state fixture was updated.
- `.venv/bin/python -m pytest -q tests/unit` passed 2156 tests.
- `uv run ruff check src/wikidot/module/user.py tests/unit/test_user.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_page_votes.py` passed.
- `uv run ruff format --check src/wikidot/module/user.py tests/unit/test_user.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_page_votes.py` passed with 6 files already formatted.
- `uv run mypy src/wikidot/module/user.py tests/unit/test_user.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_page_votes.py` passed with no issues in 6 source files.
- `uv run pyright src/wikidot/module/user.py tests/unit/test_user.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_page_votes.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 44 existing full-tree test typing errors outside this slice, including intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, invalid test cookie arguments, and existing site test mock typing issues.

## Acceptance Criteria

- `User(client, id=None, name=None, unix_name=None, avatar_url=None, ip=None)` remains valid.
- `DeletedUser(client)`, `AnonymousUser(client)`, `GuestUser(client)`, and `WikidotUser(client)` keep their existing defaults.
- `User(id=True)`, `User(id="12345")`, `User(id=12345.0)`, and `User(id=object())` raise `ValueError("id must be an integer or None")`.
- `User(name=True)`, `User(name=12345)`, `User(unix_name=True)`, `User(unix_name=["test-user"])`, `User(avatar_url=True)`, `User(avatar_url={"url": "http://example.com/avatar.png"})`, `User(ip=True)`, and `User(ip=192168001001)` raise stable field-specific `ValueError` messages.
- Existing profile parsing, user lookup, user collection, QuickModule, private-message, site member, site application, invite, page-vote, page-revision, and forum workflows remain unchanged.
- This slice does not add live Wikidot calls, upstream Issues, upstream PRs, pushes, credential handling, subtype-specific required-field semantics, field assignment interception, or frozen dataclass behavior.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Constructor validation could make existing downstream malformed-user tests fail before reaching the downstream API. Mitigation: tests now construct valid users and then mutate fields to keep corrupted-state boundary coverage.
- Risk: The base `AbstractUser` hook could accidentally impose regular-user-only requirements on deleted, anonymous, guest, or system users. Mitigation: validators allow `None` where annotations already allow it, and subclass default tests remain green.
- Risk: Booleans could be accepted because `bool` is an `int` subclass in Python. Mitigation: `id` validation rejects booleans explicitly.

## Dependencies

- User subclasses remain mutable dataclasses.
- Existing parser and action-call validators remain responsible for context-rich remote-response and public API diagnostics.
- Existing optional `None` user fields remain valid local state where annotations and defaults permit them.

## Open Questions

None for this local slice. Future work should separately evaluate whether subtype-specific required-field invariants are worth adding, because that would be a broader behavior change than this optional scalar-shape guard.

## Upstream-Safe Motivation

User objects are shared across profile lookup, printuser parsing, site membership, private messaging, page votes, forum metadata, and generated local ledgers. Direct constructors should reject malformed scalar state deterministically, while downstream APIs should continue to guard against corrupted mutable state that can appear after construction or from rehydrated records.

## Local Evidence

- Rollout-backed local work repeatedly used user records across profile lookup, QuickModule, membership/application actions, private messages, page votes, page revisions, forum posts, and fixture/ledger workflows.
- Existing local drafts covered parser diagnostics, lookup input validation, collection initialization, action-call user validation, and result-object validation, but did not cover inherited `AbstractUser` scalar fields at direct construction.
- The focused RED failures showed malformed direct `User` scalar values were accepted before this slice.
- This slice does not change user parser selection, profile request URLs, display-name spacing, action request payloads, vote lookup semantics, collection initialization, live Wikidot behavior, or private payload handling.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw profile HTML, private member data, private messages, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

Constructor validation and downstream corrupted-state validation are intentionally both kept. Constructor validation prevents ordinary bad local records; downstream validation still protects callers from mutated objects, deserialized records, or test fixtures that bypass normal construction.
