# PR Draft: Preserve Guest Display Name Spacing

## Summary

`wikidot.util.parser.user.user_parse(...)` detects guest `span.printuser` elements by their Gravatar image and returns a `GuestUser` with the visible guest display name.

Before this fix, the guest branch used `elem.get_text(strip=True).split(" ", maxsplit=1)[0]`. That had two fidelity problems: adjacent formatted child elements could be concatenated, and guest names containing spaces were truncated to the first word. The focused regression used `<span>First <em>Part</em></span><span>Guest</span> (ゲスト)`; before the fix, `GuestUser.name` became `FirstPartGuest(ゲスト)`.

This fix extracts guest printuser text with a space separator, then removes the trailing guest-kind parenthetical suffix while preserving the display name's own word boundaries. It keeps Gravatar-based guest detection, empty-name handling, avatar URL preservation, and all non-guest `printuser` classifications unchanged.

## Related Issue

Builds on shared user-parser draft [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), because that slice fixed regular Wikidot user display-name spacing while deliberately keeping guest-user behavior unchanged. This draft completes the same text-fidelity class for the Gravatar-backed guest branch.

The same recurring HTML flattening risk appears in [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), and [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md).

No upstream issue was filed from this local workspace.

## Changes

- Extract guest printuser text with `get_text(" ", strip=True)` instead of `get_text(strip=True)`.
- Remove the trailing guest-kind parenthetical suffix from the flattened guest label instead of splitting the name at the first space.
- Add a public `user_parse(...)` regression where a guest display name with formatted child text and spaces returns `GuestUser.name == "First Part Guest"`.
- Preserve deleted-user, anonymous-user, Wikidot-system-user, regular-user, no-link-error, image-only guest, and Gravatar avatar URL behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Guest display names should not concatenate adjacent rendered text chunks or formatted child text. | `TestUserParserGuestUser.test_parse_guest_user_preserves_display_name_text_spacing` asserts `GuestUser.name == "First Part Guest"` through the public `user_parse(...)` path. | The RED test failed before the fix because the parsed name was `FirstPartGuest(ゲスト)`. |
| Guest display names containing spaces should not be truncated to the first token. | The same focused regression uses a three-word guest display name and expects all three words. | Reverting to `split(" ", maxsplit=1)[0]` drops words after the first separator or keeps a concatenated suffix. |
| Existing printuser classification should remain unchanged. | `uv run pytest tests/unit/parsers/test_user_parser.py -q` passed 15 parser tests covering regular users, deleted users, anonymous users, guests with/without display text, Wikidot system user, no-link errors, special characters, and image-only first links. | If non-guest classification, guest avatar extraction, empty guest names, href parsing, onclick ID parsing, or no-link errors regress, the parser suite rejects the local completion claim. |
| Shared caller workflows should remain green. | `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_private_message.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 375 tests. | Regressions in private messages, recent changes, site members, pending applications, forum reads, page reads, or page revision user fields reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `e546d95 fix(user): preserve guest display name spacing`.

- RED: `uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserGuestUser::test_parse_guest_user_preserves_display_name_text_spacing -q` failed before the fix because `result.name` was `FirstPartGuest(ゲスト)`.
- GREEN: `uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserGuestUser::test_parse_guest_user_preserves_display_name_text_spacing -q`
- `uv run pytest tests/unit/parsers/test_user_parser.py -q` passed 15 tests.
- `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_private_message.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py -q` passed 375 tests.
- `uv run pytest tests/unit -q` passed 673 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `GuestUser.name` preserves separators between adjacent rendered guest display-name chunks and formatted child text.
- Guest display names containing spaces are not truncated to the first token.
- The trailing guest-kind parenthetical suffix is omitted from `GuestUser.name`, matching the existing fixture expectation for `guest-user (ゲスト)` while avoiding first-token truncation.
- Gravatar-based guest detection and `GuestUser.avatar_url` preservation remain unchanged.
- Empty-text guest users still parse to `GuestUser.name == ""`.
- Deleted users, anonymous users, Wikidot system users, regular users, no-link errors, regular user ID extraction, and regular user profile URL parsing remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Guest users are part of the same shared `printuser` parser surface as registered Wikidot users. A guest display name should preserve the visible name the poster entered, including spaces and formatted child text, while still excluding Wikidot's rendered guest marker.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts repeatedly use user parsing through site members, forum posts, page revisions, private messages, pending applications, and recent changes.
- Draft [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md) intentionally verified that non-regular printuser variants stayed unchanged while fixing registered-user names; this follow-up addresses the still-unfixed guest variant.
- The refreshed complexity scan continues to flag parser-heavy collection modules as audit-worthy; this slice keeps the change localized to guest display-name flattening rather than broad user parsing refactoring.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and message/profile content out of upstream discussion.

## Additional Notes

This slice does not change how guest users are detected, how Gravatar avatar URLs are retained, or how regular Wikidot users are parsed. It only changes how the guest branch flattens visible text into `GuestUser.name`.
