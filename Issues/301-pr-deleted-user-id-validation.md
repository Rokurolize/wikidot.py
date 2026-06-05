# PR Draft: Report Malformed Deleted User IDs

## Summary

`wikidot.util.parser.user.user_parse(...)` is the shared parser for Wikidot `span.printuser` markup across recent changes, member lists, private messages, forum threads, forum posts, page metadata, applications, revision lists, votes, and other generated read paths. Earlier local slices mostly kept this shared parser unchanged and wrapped malformed user metadata at module-specific parser boundaries so callers could report site/page/thread/message context. One small shared-parser gap remained in the deleted-user branch: when Wikidot emitted a deleted `printuser` element with a present but non-integer `data-id`, the parser leaked Python's raw `int(...)` failure instead of returning a stable parser-level `ValueError`.

This follow-up keeps all existing valid user parsing behavior, including the existing `data-id`-missing deleted-user fallback to ID `0` and the string `"(user deleted)"` fallback. It only wraps conversion failures for present malformed deleted-user `data-id` values and raises `ValueError("deleted user id is malformed: <value>")`. Downstream module-specific wrappers can still chain that shared parser failure into their own contextual `NoElementException` messages.

## Outcome

Malformed deleted-user IDs now fail with a stable parser message instead of leaking a raw `int()` conversion error.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse generated Wikidot user metadata in browser-free audit, archival, moderation, import, source collection, forum, page, member, or messaging workflows.

## Related Issue

Builds on the shared user parser-boundary diagnostics pattern from [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), and [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md). Those drafts added caller context around shared parser failures; this slice improves the shared deleted-user failure text itself while preserving the parser's existing public behavior for valid and unknown-ID deleted users.

No upstream issue was filed from this local workspace.

## Changes

- Wrap deleted-user `data-id` integer conversion in the shared `user_parse(...)` deleted-user branch.
- Raise `ValueError` with `deleted user id is malformed: <value>` when a deleted `printuser` element has a non-integer `data-id`.
- Preserve valid deleted-user parsing with integer `data-id`.
- Preserve the existing missing-`data-id` deleted-user fallback to ID `0`.
- Preserve the existing string `"(user deleted)"` fallback to `DeletedUser(id=0)`.
- Preserve regular, anonymous, guest, and Wikidot system-user parsing.
- Add a focused parser regression for `data-id="latest"`.

## Type Of Change

- Bug fix / diagnostics improvement
- Shared user parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A deleted `printuser` element with a present non-integer `data-id` must fail with a stable parser-level `ValueError`. |
| R2 | The malformed deleted-user ID error must include the observed value. |
| R3 | Valid deleted-user parsing and the existing unknown-ID fallback must remain unchanged. |
| R4 | Regular, anonymous, guest, Wikidot system-user, and module caller workflows must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `user_parse(...)` raises `ValueError` for `<span class="printuser deleted" data-id="latest">...`. | `TestUserParserDeletedUser.test_parse_deleted_user_with_malformed_data_id_raises` expects `ValueError`. | Leaking `ValueError: invalid literal for int()...`, returning `DeletedUser(id=0)`, or fabricating another ID rejects this local completion claim. | `src/wikidot/util/parser/user.py` | `tests/unit/parsers/test_user_parser.py` |
| R2 | The exception includes the malformed value `latest`. | The focused regression matches `deleted user id is malformed: latest`. | Hiding the observed value makes triage ambiguous and rejects this local completion claim. | Shared user parser diagnostics | `tests/unit/parsers/test_user_parser.py` |
| R3 | Existing deleted-user contracts are preserved. | `tests/unit/parsers/test_user_parser.py` passed 16 tests, including integer `data-id` parsing and missing-`data-id` ID `0` parsing. | Raising for missing `data-id` or changing the string fallback rejects this local completion claim. | Deleted-user parser branch | `tests/unit/parsers/test_user_parser.py` |
| R4 | Adjacent shared-parser callers stay green. | Shared caller suite passed 504 tests across site, site-member, private-message, forum-post, forum-thread, forum-post-revision, page, and site-application tests. | Regressing module-specific user parsing, contextual wrappers, page metadata parsing, forum metadata parsing, message parsing, member parsing, application parsing, or valid user parsing rejects this local completion claim. | Shared parser callers | `tests/unit/test_site.py`; `tests/unit/test_site_member.py`; `tests/unit/test_private_message.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_post_revision.py`; `tests/unit/test_page.py`; `tests/unit/test_site_application.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d3fbe67 fix(user): report malformed deleted user ids`.

- RED: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_malformed_data_id_raises -q` failed before the fix because the parser raised `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run --extra test pytest tests/unit/parsers/test_user_parser.py::TestUserParserDeletedUser::test_parse_deleted_user_with_malformed_data_id_raises -q` passed 1 test.
- `uv run --extra test pytest tests/unit/parsers/test_user_parser.py -q` passed 16 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_private_message.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_post_revision.py tests/unit/test_page.py tests/unit/test_site_application.py -q` passed 504 tests.
- `uv run --extra test pytest tests/unit -q` passed 859 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src`.
- `git diff --check`.

Not run successfully: `uv run pyright` could not spawn `pyright` because no executable was available in this environment.

## Acceptance Criteria

- `user_parse(...)` raises `ValueError("deleted user id is malformed: latest")` for a deleted `printuser` with `data-id="latest"`.
- Valid deleted-user markup with integer `data-id` still returns `DeletedUser` with that ID.
- Deleted-user markup without `data-id` still returns `DeletedUser(id=0)`.
- The string `"(user deleted)"` fallback still returns `DeletedUser(id=0)`.
- Regular user, anonymous user, guest user, and Wikidot system-user parsing remain unchanged.
- Existing module-specific wrappers can still catch shared-parser `ValueError` and add their own site/page/thread/message context.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated user markup from real sites, credentials, cookies, auth JSON, local rollout paths, or private account details are required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Changing the shared user parser could affect many modules. Mitigation: the change is limited to the deleted-user integer conversion branch and broad caller tests passed.
- Risk: Missing `data-id` might be common in generated deleted-user markup. Mitigation: the existing missing-`data-id` fallback remains ID `0`.
- Risk: A stable shared parser error could still lack caller context. Mitigation: existing module-specific wrappers continue to catch `ValueError` and add their own location metadata where needed.

## Dependencies

- BeautifulSoup continues to expose `data-id` as an attribute value on deleted `span.printuser` elements.
- `DeletedUser(id=0)` remains the existing representation for unknown deleted-user IDs.
- Module parsers continue to treat shared user parser failures as `ValueError` at their boundaries.

## Open Questions

None for this local slice. Treating missing deleted-user `data-id` as ID `0` remains an existing compatibility behavior; this change only improves present malformed values.

## Upstream-Safe Motivation

Deleted-user markup appears in the same generated user metadata surfaces as normal Wikidot users. If a deleted-user element contains a present but malformed `data-id`, wikidot.py should expose a stable parser-level failure that names the malformed value rather than leaking Python's raw integer conversion wording. That makes shared parser regressions easier to test and lets caller-specific wrappers add their own site or workflow context without depending on interpreter-level exception text.

## Local Evidence, Not For Upstream Paste

- Recent local drafts repeatedly improved parser-boundary diagnostics around the shared user parser in private messages, site members, forum thread lists, forum thread details, forum post lists, forum post edit metadata, recent changes, and forum post revisions.
- The immediate RED failure showed a present malformed deleted-user `data-id` leaking a raw `int()` conversion error.
- The full unit suite and broad shared-caller slice stayed green after preserving the existing missing-ID fallback.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated user markup from real sites, real user names, and private site history out of upstream discussion.

## Additional Notes

This is a shared parser correctness and observability fix. It does not change request behavior, module parser scoping, caller-specific exception wrapping, valid user parsing, unknown deleted-user fallback behavior, cache behavior, live Wikidot behavior, or any upstream filing state.
