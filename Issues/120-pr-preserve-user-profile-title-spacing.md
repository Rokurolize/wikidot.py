# PR Draft: Preserve User Profile Title Spacing

## Summary

`UserCollection.from_names(...)` fetches Wikidot profile pages and exposes the visible profile title through `User.name`, then derives `User.unix_name` from that display name.

Before this fix, the profile title was extracted with `name_elem.get_text(strip=True)`. When a rendered `h1.profile-title` contained adjacent formatted child elements, visible text chunks could be concatenated. The focused regression changed the title to `<h1 class="profile-title"><span>First <em>Part</em></span><span>User</span></h1>`; before the fix, `User.name` became `FirstPartUser`.

This fix extracts profile titles with a space separator and `strip=True`, preserving visible word boundaries and incidental wrapper trimming while keeping GET URL construction, not-found handling, user ID extraction, avatar URL construction, `User.from_name(...)`, collection iteration, and profile-derived `unix_name` behavior unchanged.

## Related Issue

Builds on user/parser drafts [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), and private-message/user lookup adjacency in [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), because those drafts established user objects and shared user parsing as practical rollout-backed read paths.

The text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), and [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental structural-parser changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract `h1.profile-title` text with `get_text(" ", strip=True)` instead of `get_text(strip=True)`.
- Add a public `UserCollection.from_names(...)` regression where adjacent formatted profile-title chunks keep a space between visible text chunks.
- Preserve profile GET request construction, profile not-found handling, ID extraction from karma/PM links, avatar URL generation, `StringUtil.to_unix(...)` conversion, `User.from_name(...)`, and collection iteration behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| User profile display names should not concatenate adjacent rendered profile-title chunks or formatted child text. | `TestUserCollection.test_from_names_preserves_profile_title_text_spacing` asserts `result[0].name == "First Part User"` and `result[0].unix_name == "first-part-user"` through `UserCollection.from_names(...)`. | The RED test failed before the fix because the parsed name was `FirstPartUser`. |
| Existing user lookup behavior should remain unchanged. | `uv run pytest tests/unit/test_user.py -q` passed 16 user tests covering dataclasses, single-user lookup, not-found behavior, bulk lookup, skipped missing users, ID extraction, malformed/missing ID errors, missing name errors, and iteration. | If profile-title normalization breaks lookup, not-found handling, ID parsing, avatar/unix-name construction, or iteration, the user suite rejects the local completion claim. |
| Shared user and adjacent read workflows should remain green. | `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_client.py tests/unit/test_private_message.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 393 tests. | Regressions in client user access, printuser parsing, private-message metadata, recent changes, site members, pending applications, forum/page read paths, or page revision user fields reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `c0ae0c0 fix(user): preserve profile title spacing`.

- RED: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_preserves_profile_title_text_spacing -q` failed before the fix because `result[0].name` was `FirstPartUser`.
- GREEN: `uv run pytest tests/unit/test_user.py::TestUserCollection::test_from_names_preserves_profile_title_text_spacing -q`
- `uv run pytest tests/unit/test_user.py -q` passed 16 tests.
- `uv run pytest tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_client.py tests/unit/test_private_message.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 393 tests.
- `uv run pytest tests/unit -q` passed 672 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `User.name` from profile-page lookup preserves a separator between adjacent rendered `h1.profile-title` chunks and formatted child text.
- Incidental wrapper whitespace around the profile title is stripped.
- `User.unix_name` remains derived from the normalized visible profile title.
- Existing ID extraction from `userkarma.php/<id>` and `/account/messages#/new/<id>` links remains unchanged.
- `User.from_name(...)` and `UserCollection.from_names(...)` preserve not-found handling, avatar URL construction, and collection ordering.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Profile page lookup is a public user read path. A rendered profile title should preserve visible word boundaries the same way shared `span.printuser` display-name parsing now does, without changing request construction, user ID parsing, avatar URLs, or collection behavior.

## Local Evidence, Not For Upstream Paste

- Earlier drafts [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md) and [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md) established user parsing and user objects as practical local read paths.
- Text-fidelity drafts [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md) through [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag parser-heavy collection modules as audit-worthy; this slice keeps the change localized to profile-title text flattening rather than broad user lookup refactoring.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and profile content out of upstream discussion.

## Additional Notes

This slice does not change user lookup URLs, profile page existence checks, user ID extraction, avatar URL construction, `StringUtil.to_unix(...)`, or `User.from_name(...)` behavior. It only changes how profile-title element text is flattened into `User.name`.
