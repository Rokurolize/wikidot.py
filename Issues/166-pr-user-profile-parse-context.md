# PR Draft: Include Context In User Profile Parse Errors

## Summary

`UserCollection.from_names(...)` fetches Wikidot profile pages and parses required profile elements to build `User` objects. When the fetched profile HTML was malformed and lacked the user ID control, contained a malformed ID link, or lacked the profile title, the parser raised `NoElementException` messages that only named the missing field.

This follow-up keeps the existing profile lookup, not-found handling, ID extraction rules, profile-title normalization, avatar URL construction, collection ordering, and successful `User` output shape, but includes the requested user key and request position in those malformed profile parse failures.

## Related Issue

Builds on [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), and [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), because those drafts established user parsing and profile lookup as practical read paths. It also follows the recent parser-context direction in [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), and [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Track requested username and request index while iterating profile lookup responses.
- Include requested user key and index in missing user ID element, malformed user ID link, and missing profile-title `NoElementException` messages.
- Strengthen the existing malformed profile tests to assert the contextual error messages.
- Preserve GET URL construction, skipped not-found users, raised not-found users, ID extraction from PM/karma links, profile-title text spacing, avatar URL generation, `User.from_name(...)`, collection ordering, and iteration behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- User profile parser error-context ergonomics
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing profile ID controls still fail. | `TestUserCollection.test_from_names_missing_id_element` raises `NoElementException`. | A change that silently accepts a profile without a user ID rejects this local completion claim. |
| Malformed profile ID links still fail. | `TestUserCollection.test_from_names_malformed_id_href_raises` raises `NoElementException`. | A change that fabricates a user ID from a malformed link rejects this local completion claim. |
| Missing profile titles still fail. | `TestUserCollection.test_from_names_missing_name_element` raises `NoElementException`. | A change that fabricates or leaves an empty display name rejects this local completion claim. |
| User profile parse failures identify the requested user and request position. | The focused tests assert `for requested user: bad (index=1)` in all three malformed paths. | The RED tests failed before the fix because messages only named the missing field. |
| User lookup workflows remain green. | `uv run pytest tests/unit/test_user.py -q` passed 16 tests. | Regressions in not-found handling, bulk lookup, ID extraction, profile-title spacing, avatar/unix-name construction, or iteration reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4ee791e fix(user): include context in profile parse errors`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_missing_id_element tests/unit/test_user.py::TestUserCollection::test_from_names_malformed_id_href_raises tests/unit/test_user.py::TestUserCollection::test_from_names_missing_name_element -q` failed before the fix because the messages lacked requested-user/index context.
- GREEN: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_missing_id_element tests/unit/test_user.py::TestUserCollection::test_from_names_malformed_id_href_raises tests/unit/test_user.py::TestUserCollection::test_from_names_missing_name_element -q`
- `uv run pytest tests/unit/test_user.py -q` passed 16 tests.
- `uv run pytest tests/unit -q` passed 722 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Missing user ID elements, malformed user ID links, and missing profile titles still raise `NoElementException`.
- Those exceptions include the requested user key and one-based request index.
- Successful user profile lookup, skipped not-found users, raised not-found users, profile-title spacing, ID extraction, avatar URL generation, `User.from_name(...)`, collection ordering, and iteration remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Bulk profile lookup can request several users at once. When one fetched profile page is malformed, the exception should identify which requested user and response position failed so maintainers can triage logs without saving raw profile HTML.

## Local Evidence, Not For Upstream Paste

- Earlier user/profile drafts established `UserCollection.from_names(...)` as a practical read path and covered profile-title spacing, ID extraction variants, not-found handling, and iteration.
- Recent parser-context slices showed that object-specific `NoElementException` messages improve resumable local ledgers without changing successful behavior.
- The refreshed complexity memo continues to treat parser-heavy collection helpers as audit-worthy, but this slice only claims user profile malformed-response diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw profile HTML, and profile content out of upstream discussion.

## Additional Notes

This slice intentionally does not change request URLs, profile-page existence checks, skipped/raised not-found behavior, ID extraction patterns, title text normalization, `StringUtil.to_unix(...)`, avatar URL construction, returned `User` fields, `User.from_name(...)`, or live Wikidot behavior. It only adds requested-user/index context to existing malformed user profile parser failures.
