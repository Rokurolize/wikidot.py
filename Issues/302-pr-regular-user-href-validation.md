# PR Draft: Require Regular User Hrefs

## Summary

`wikidot.util.parser.user.user_parse(...)` is the shared parser for Wikidot `span.printuser` markup across recent changes, member lists, private messages, forum threads, forum posts, page metadata, applications, revision lists, votes, and other generated read paths. Earlier local slices wrapped malformed user metadata at module-specific parser boundaries and recently improved the deleted-user branch so malformed present `data-id` values no longer leaked raw `int(...)` conversion text. One adjacent shared-parser gap remained in the normal user branch: if the selected user anchor had a parseable `userInfo(...)` `onclick` but no `href`, wikidot.py created a `User` with `unix_name=""`.

This follow-up keeps valid regular user parsing, relative and absolute `/user:info/...` URL extraction, valid `onclick` ID extraction, deleted-user parsing, anonymous-user parsing, guest-user parsing, and Wikidot system-user parsing unchanged. It only rejects missing or empty regular-user `href` attributes with `ValueError("user href is not found")` before constructing a `User`, so caller-specific wrappers can still add their own site/page/thread/message context around the shared parser failure.

## Outcome

Regular user `printuser` markup without a usable `href` no longer produces a `User` whose `unix_name` is empty.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse generated Wikidot user metadata in browser-free audit, archival, moderation, import, source collection, forum, page, member, or messaging workflows.

## Related Issue

Builds on the shared user parser-boundary diagnostics pattern from [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), and [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md). Those drafts established shared user metadata as a practical parser boundary; this slice prevents a missing normal-user identity link from becoming an empty `unix_name`.

No upstream issue was filed from this local workspace.

## Changes

- Require the selected regular-user anchor to have a non-empty string `href` before constructing `User`.
- Raise `ValueError("user href is not found")` when normal user markup has `onclick="...userInfo(...)"` but no usable `href`.
- Preserve existing valid regular user parsing with HTTP and HTTPS user-info links.
- Preserve regular user display-name spacing, `onclick` ID extraction, and avatar URL generation.
- Preserve deleted-user, anonymous-user, guest-user, and Wikidot system-user parsing.
- Add a focused parser regression for a normal user anchor missing `href`.

## Type Of Change

- Bug fix / diagnostics improvement
- Shared user parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A regular `printuser` anchor with a parseable `userInfo(...)` ID but no `href` must fail with a stable parser-level `ValueError`. |
| R2 | The missing-href error must not construct a `User` with empty `unix_name`. |
| R3 | Valid regular-user parsing must remain unchanged. |
| R4 | Deleted, anonymous, guest, Wikidot system-user, and module caller workflows must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `user_parse(...)` raises `ValueError` for `<span class="printuser"><a onclick="WIKIDOT.page.listeners.userInfo(12345); return false;">test-user</a></span>`. | `TestUserParserRegularUser.test_parse_regular_user_without_href_raises` expects `ValueError`. | Returning a `User`, falling back to empty string, or leaking an unrelated error rejects this local completion claim. | `src/wikidot/util/parser/user.py` | `tests/unit/parsers/test_user_parser.py` |
| R2 | The exception message is stable and specific to the missing regular-user `href`. | The focused regression matches `user href is not found`. | Creating `User(unix_name="")` or hiding the malformed identity source rejects this local completion claim. | Shared user parser diagnostics | `tests/unit/parsers/test_user_parser.py` |
| R3 | Valid regular users still parse through existing public parser behavior. | `tests/unit/parsers/test_user_parser.py` passed 17 tests, including regular HTTP, HTTPS, display-name spacing, special-name, and image-without-src cases. | Regressing user ID, display name, unix name, or avatar URL construction rejects this local completion claim. | Regular user parser branch | `tests/unit/parsers/test_user_parser.py` |
| R4 | Adjacent shared-parser callers stay green. | Shared caller suite passed 504 tests across site, site-member, private-message, forum-post, forum-thread, forum-post-revision, page, and site-application tests. | Regressing module-specific user parsing, contextual wrappers, page metadata parsing, forum metadata parsing, message parsing, member parsing, application parsing, or valid user parsing rejects this local completion claim. | Shared parser callers | `tests/unit/test_site.py`; `tests/unit/test_site_member.py`; `tests/unit/test_private_message.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_post_revision.py`; `tests/unit/test_page.py`; `tests/unit/test_site_application.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1571405 fix(user): require regular user hrefs`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_without_href_raises -q` failed before the fix because no `ValueError` was raised and a malformed `User` was returned.
- GREEN: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_without_href_raises -q` passed 1 test.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py -q` passed 17 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_site_application.py -q` passed 504 tests.
- `uv run --extra test pytest tests/unit -q` passed 860 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src`.
- `git diff --check`.

Not run successfully: `uv run pyright` could not spawn `pyright` because no executable was available in this environment.

## Acceptance Criteria

- `user_parse(...)` raises `ValueError("user href is not found")` for a regular user anchor with `userInfo(...)` but no `href`.
- The parser does not construct `User(unix_name="")` from missing-href regular user markup.
- Valid regular user markup with HTTP and HTTPS `/user:info/...` links still extracts the same ID, display name, unix name, and avatar URL.
- Deleted-user, anonymous-user, guest-user, and Wikidot system-user parsing remain unchanged.
- Existing module-specific wrappers can still catch shared-parser `ValueError` and add their own site/page/thread/message context.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated user markup from real sites, credentials, cookies, auth JSON, local rollout paths, or private account details are required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Changing the shared user parser could affect many modules. Mitigation: the change is limited to regular-user anchors with missing or empty `href`, and broad caller tests passed.
- Risk: Some non-standard markup may include `onclick` but no user-info link. Mitigation: constructing an empty `unix_name` loses identity data; caller-specific wrappers can preserve workflow context around the stable `ValueError`.
- Risk: Rejecting malformed regular-user hrefs could be confused with deleted-user unknown-ID behavior. Mitigation: deleted-user logic is handled before the regular-user branch and remains unchanged.

## Dependencies

- BeautifulSoup continues to expose anchor `href` values as attributes.
- Normal Wikidot user metadata continues to identify users through `/user:info/...` links plus `userInfo(...)` IDs.
- Module parsers continue to treat shared user parser failures as `ValueError` at their boundaries.

## Open Questions

None for this local slice. This change rejects only missing or empty regular-user `href`; it does not broaden validation to every non-`/user:info/...` href shape.

## Upstream-Safe Motivation

Regular user markup supplies both an integer user ID and a user-info link-derived unix name. If the link is missing, constructing a `User` with an empty `unix_name` creates a misleading identity object and pushes the malformed source farther downstream. A stable parser-level failure is easier to test and lets existing caller-specific wrappers add site, page, thread, or message context without depending on a fabricated empty identifier.

## Local Evidence, Not For Upstream Paste

- Recent local drafts repeatedly improved parser-boundary diagnostics around the shared user parser in private messages, site members, forum thread lists, forum thread details, forum post lists, forum post edit metadata, recent changes, forum post revisions, and deleted-user ID parsing.
- The immediate RED failure showed a regular user anchor without `href` returned successfully instead of raising.
- A PCRE2 fixture scan found no existing generated fixture that intentionally relies on `userInfo(...)` regular user anchors without `href`.
- The full unit suite and broad shared-caller slice stayed green after preserving valid regular, deleted, anonymous, guest, and Wikidot system-user behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated user markup from real sites, real user names, and private site history out of upstream discussion.

## Additional Notes

This is a shared parser correctness and observability fix. It does not change request behavior, module parser scoping, caller-specific exception wrapping, valid user parsing, deleted-user fallback behavior, cache behavior, live Wikidot behavior, or any upstream filing state.
