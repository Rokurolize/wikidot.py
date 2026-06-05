# PR Draft: Report Malformed Regular User Onclick IDs

## Summary

`wikidot.util.parser.user.user_parse(...)` is the shared parser for Wikidot `span.printuser` markup across recent changes, member lists, private messages, forum threads, forum posts, page metadata, applications, revision lists, votes, and other generated read paths. Recent local slices made the deleted-user ID, regular-user href, profile-link ID, module-specific user parser, and QuickModule user ID boundaries more explicit. One adjacent shared-parser gap remained in the normal user branch: a present but non-numeric `userInfo(...)` value, such as `userInfo(latest)`, was reported as if the user ID metadata were absent.

This local slice keeps valid regular user parsing, caller-specific wrappers, missing-`onclick` behavior, missing-`href` behavior, deleted-user parsing, anonymous-user parsing, guest-user parsing, and Wikidot system-user parsing unchanged. It only distinguishes a present malformed regular-user `userInfo(...)` value from missing user ID metadata with `ValueError("user id is malformed: latest")`.

## Outcome

Malformed regular-user `onclick` ID values now fail at the shared user parser boundary with the observed scalar value instead of the generic missing-ID message.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse generated Wikidot user metadata in browser-free audit, archival, moderation, import, source collection, forum, page, member, or messaging workflows.

## Related Issue

Builds on the shared user parser-boundary diagnostics pattern from [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), and [310-pr-user-profile-id-validation.md](310-pr-user-profile-id-validation.md). Those drafts established shared user metadata as a practical parser boundary; this slice handles a present malformed regular-user `onclick` scalar without changing the caller wrappers that add site, page, thread, post, message, revision, or application context.

No upstream issue was filed from this local workspace.

## Changes

- Split regular-user `onclick` ID parsing into absent and present-malformed cases.
- Raise `ValueError("user id is malformed: <value>")` when `userInfo(...)` is present but non-numeric.
- Preserve `ValueError("user id is not found")` when no `userInfo(...)` call or only an empty `userInfo()` call is present.
- Preserve valid regular user parsing with HTTP and HTTPS user-info links.
- Preserve regular user display-name spacing, `href` validation, avatar URL generation, deleted-user parsing, anonymous-user parsing, guest-user parsing, and Wikidot system-user parsing.
- Preserve module-specific wrappers that catch shared parser `ValueError` and add caller context.
- Add a focused parser regression for a regular user anchor with `onclick="...userInfo(latest)..."`.

## Type Of Change

- Bug fix / diagnostics improvement
- Shared user parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A regular `printuser` anchor with a present non-numeric `userInfo(...)` value must fail with a stable parser-level malformed-ID `ValueError`. |
| R2 | The malformed-ID error must include the observed scalar value and must not collapse it into the generic missing-ID message. |
| R3 | Missing or absent regular-user ID metadata must keep the existing `ValueError("user id is not found")` behavior. |
| R4 | Valid regular-user parsing must remain unchanged. |
| R5 | Deleted, anonymous, guest, Wikidot system-user, regular-user href validation, profile-link ID validation, and module caller workflows must remain unchanged. |
| R6 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `user_parse(...)` raises `ValueError` for `<span class="printuser"><a href="http://www.wikidot.com/user:info/bad-user" onclick="WIKIDOT.page.listeners.userInfo(latest); return false;">bad-user</a></span>`. | `TestUserParserRegularUser.test_parse_regular_user_with_malformed_onclick_id_raises` expects `ValueError`. | Returning a `User`, leaking a raw conversion error, or hiding the observed `latest` value rejects this local completion claim. | `src/wikidot/util/parser/user.py` | `tests/unit/parsers/test_user_parser.py` |
| R2 | The exception message is stable and specific to the malformed `onclick` ID value. | The focused regression matches `user id is malformed: latest`. | Reporting only `user id is not found` rejects this local completion claim because it loses the present scalar. | Shared user parser diagnostics | `tests/unit/parsers/test_user_parser.py` |
| R3 | Missing `onclick`, absent `userInfo(...)`, or empty `userInfo()` remains a missing-ID parser failure. | Existing caller tests and parser coverage keep the generic missing-ID path available. | Treating absent metadata as a malformed value would break caller-specific missing-ID wrappers. | Shared user parser diagnostics | `src/wikidot/util/parser/user.py`; broad caller tests |
| R4 | Valid regular users still parse through existing public parser behavior. | `tests/unit/parsers/test_user_parser.py` passed 18 tests, including regular HTTP, HTTPS, display-name spacing, href validation, deleted-user, anonymous-user, guest-user, Wikidot user, special-name, and image-without-src cases. | Regressing user ID, display name, unix name, avatar URL construction, or href validation rejects this local completion claim. | Regular user parser branch | `tests/unit/parsers/test_user_parser.py` |
| R5 | Adjacent shared-parser callers stay green. | Shared caller suite passed 531 tests across site, site-member, private-message, forum-post, forum-thread, forum-post-revision, page, and site-application tests. | Regressing module-specific user parsing, contextual wrappers, page metadata parsing, forum metadata parsing, message parsing, member parsing, application parsing, or valid user parsing rejects this local completion claim. | Shared parser callers | `tests/unit/test_site.py`; `tests/unit/test_site_member.py`; `tests/unit/test_private_message.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_post_revision.py`; `tests/unit/test_page.py`; `tests/unit/test_site_application.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7f5ad4b fix(user): report malformed regular user ids`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_with_malformed_onclick_id_raises -q` failed before the fix because the parser raised `ValueError("user id is not found")` for `userInfo(latest)`.
- GREEN: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserRegularUser::test_parse_regular_user_with_malformed_onclick_id_raises -q` passed 1 test.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py -q` passed 18 tests.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_site_application.py -q` passed 531 tests.
- `uv run --extra test pytest tests/unit -q` passed 879 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `user_parse(...)` raises `ValueError("user id is malformed: latest")` for a regular user anchor whose `onclick` contains `userInfo(latest)`.
- The parser does not collapse a present malformed regular-user `onclick` scalar into `ValueError("user id is not found")`.
- Missing regular-user ID metadata still raises `ValueError("user id is not found")`.
- Valid regular user markup with HTTP and HTTPS `/user:info/...` links still extracts the same ID, display name, unix name, and avatar URL.
- Deleted-user, anonymous-user, guest-user, Wikidot system-user, regular-user href validation, and profile-link ID validation remain unchanged.
- Existing module-specific wrappers can still catch shared-parser `ValueError` and add their own site, page, thread, post, message, revision, or application context.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated user markup from real sites, private access material, local rollout paths, or private account details are required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Changing the shared user parser could affect many modules. Mitigation: the change is limited to regular-user anchors with present non-numeric `userInfo(...)` values, and broad caller tests passed.
- Risk: Treating present malformed IDs differently from absent IDs could disturb caller-specific missing-ID wrappers. Mitigation: the parser still raises `user id is not found` when no `userInfo(...)` call is present or the call is empty.
- Risk: Reporting the observed scalar could expose too much source detail. Mitigation: the diagnostic includes only the malformed scalar already inside the parser input and omits raw generated markup, site names, URLs beyond fixture text, private access material, and local rollout context.

## Dependencies

- BeautifulSoup continues to expose anchor `onclick` values as attributes.
- Normal Wikidot user metadata continues to identify users through `/user:info/...` links plus numeric `userInfo(...)` IDs.
- Module parsers continue to treat shared user parser failures as `ValueError` at their boundaries.

## Open Questions

None for this local slice. Broader validation of non-standard `onclick` syntax remains a separate parser-boundary question if concrete rollout evidence selects it.

## Upstream-Safe Motivation

Regular user markup supplies both an integer user ID and a user-info link-derived unix name. When the `userInfo(...)` call is present but contains a non-numeric value, reporting only that the user ID is missing loses the malformed scalar that would help maintainers distinguish parser drift from absent metadata. A stable parser-level malformed-value error is easier to test and lets existing caller-specific wrappers add site, page, thread, post, message, revision, or application context without depending on raw Python exception text.

## Local Evidence, Not For Upstream Paste

- Recent local drafts repeatedly improved parser-boundary diagnostics around the shared user parser in private messages, site members, forum thread lists, forum thread details, forum post lists, forum post edit metadata, recent changes, forum post revisions, deleted-user ID parsing, regular-user href parsing, page revision users, listpages users, whorated users, site application users, and user profile ID href parsing.
- The immediate RED failure showed a regular user anchor with `userInfo(latest)` raised the generic missing-ID message.
- The full unit suite and broad shared-caller slice stayed green after preserving valid regular, deleted, anonymous, guest, and Wikidot system-user behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, private access material, generated user markup from real sites, real user names, and private site history out of upstream discussion.

## Additional Notes

This is a shared parser diagnostics fix. It does not change request behavior, module parser scoping, caller-specific exception wrapping, valid user parsing, deleted-user fallback behavior, cache behavior, live Wikidot behavior, or any upstream filing state.
