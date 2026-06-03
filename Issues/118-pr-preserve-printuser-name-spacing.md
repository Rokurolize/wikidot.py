# PR Draft: Preserve Printuser Display Name Spacing

## Summary

`wikidot.util.parser.user.user_parse(...)` is the shared `span.printuser` parser used by page revisions, recent changes, forum posts and threads, private messages, site members, pending site applications, and ListPages user fields.

Before this fix, regular user display names were extracted from the selected user link with `_user.get_text()`. When a rendered display-name link contained adjacent formatted child elements, visible text could be concatenated and incidental surrounding whitespace could be preserved. The focused regression changed the user link to `<span>First <em>Part</em></span><span>User</span>`; before the fix, `User.name` became `\nFirst PartUser\n`.

This fix extracts regular Wikidot user display names with a space separator and `strip=True`, preserving visible word boundaries and trimming incidental wrapper whitespace while keeping deleted-user, anonymous-user, guest-user, Wikidot-system-user, href/unix-name parsing, onclick user ID parsing, avatar URL construction, and every caller's output object shape unchanged.

## Related Issue

Builds on parser-boundary drafts that already depend on `span.printuser`, including [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), and [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), because those drafts established shared printuser parsing as a practical read path across private messages, forum metadata, votes, and member lists.

The text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), and [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental structural-parser changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract regular Wikidot user display names with `get_text(" ", strip=True)` instead of raw `get_text()`.
- Add a public `user_parse(...)` regression where adjacent formatted display-name chunks keep a space between visible text chunks.
- Preserve deleted-user parsing, anonymous-user IP parsing, guest-user detection, Wikidot system user detection, last-link selection, href/unix-name parsing, onclick user ID parsing, generated avatar URL behavior, and caller-facing `User` object fields.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Regular Wikidot user display names should not concatenate adjacent rendered name chunks or preserve incidental wrapper whitespace. | `TestUserParserRegularUser.test_parse_regular_user_preserves_display_name_text_spacing` asserts `result.name == "First Part User"` through `user_parse(...)`. | The RED test failed before the fix because the parsed name was `\nFirst PartUser\n`. |
| Non-regular printuser variants should remain unchanged. | `uv run pytest tests/unit/parsers/test_user_parser.py -q` passed 14 parser tests covering regular users, onclick ID extraction, HTTPS profile URLs, deleted users, anonymous users with/without IPs, guests with/without display text, Wikidot system user, no-link errors, special characters, and image-only first links. | If deleted, anonymous, guest, Wikidot, href, onclick, image, or no-link behavior regresses, the parser suite rejects the local completion claim. |
| Shared printuser caller workflows should remain green. | `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_private_message.py tests/unit/test_page.py -q` passed 372 tests. | Regressions in recent changes, site members, pending applications, forum thread/post metadata, forum revisions, private message metadata, page revisions, ListPages user fields, or user model behavior reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `b27a661 fix(user): preserve printuser name spacing`.

- RED: `uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_preserves_display_name_text_spacing -q` failed before the fix because `result.name` was `\nFirst PartUser\n`.
- GREEN: `uv run pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_preserves_display_name_text_spacing -q`
- `uv run pytest tests/unit/parsers/test_user_parser.py -q` passed 14 tests.
- `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/test_user.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_private_message.py tests/unit/test_page.py -q` passed 372 tests.
- `uv run pytest tests/unit -q` passed 670 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Regular `span.printuser` display names preserve a separator between adjacent rendered display-name chunks and formatted child text.
- Incidental wrapper whitespace around regular display-name links is stripped.
- Deleted users, anonymous users, guest users, and the Wikidot system user remain parsed as their existing user classes.
- `href`-derived `unix_name`, onclick-derived numeric ID, and generated avatar URL behavior remain unchanged for regular users.
- Shared printuser callers in recent changes, site members, pending site applications, forum threads, forum posts, forum post revisions, private messages, page revisions, and ListPages user fields remain green.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`span.printuser` is a shared parser surface for many Wikidot read APIs. A regular user's display name should preserve visible word boundaries from rendered HTML without changing profile URL parsing, user ID parsing, avatar URL generation, non-regular user handling, or caller output shapes.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), and [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md) established printuser parsing as a practical local target across several rollout-backed workflows.
- Text-fidelity drafts [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md) through [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag shared parser-heavy collection code as audit-worthy, and `user_parse(...)` is invoked by multiple high-traffic read paths.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and page content out of upstream discussion.

## Additional Notes

This slice does not change printuser element selection, deleted/anonymous/guest/Wikidot classification, profile URL parsing, user ID extraction, generated avatar URLs, or caller object ownership. It only changes how regular user display-name link text is flattened into `User.name`.
