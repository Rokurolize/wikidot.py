# PR Draft: Validate Forum Thread Href ID ASCII Shape

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, exposed through `ForumCategory.threads` and `ForumCategory.reload_threads()`, parses generated `forum/ForumViewCategoryModule` thread-list title links into `ForumThread.id` values. Issues [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md) and [741-pr-validate-forum-thread-href-routes.md](741-pr-validate-forum-thread-href-routes.md) made embedded malformed `t-<id>` segments and invalid route/scheme/host shapes fail, but the accepted terminal ID segment still used Python regex `\d+`. That allowed Unicode decimal digit glyphs such as `/forum/t-\uff13\uff10\uff10\uff11/test-thread` to normalize into ordinary thread ID `3001`.

This change requires the generated forum thread href ID segment to match ASCII digits before integer conversion. Valid generated routes such as `/forum/t-3001/test-thread` and same-site absolute routes such as `http://test-site.wikidot.com/forum/t-3001/test-thread?from=start#top` remain compatible, while present non-ASCII digit payloads now raise the existing contextual malformed-thread-ID `NoElementException`.

## Outcome

Browser-free category thread-list acquisition no longer fabricates forum thread identities by normalizing non-ASCII digit glyphs from generated thread href metadata. The malformed-value diagnostic remains actionable and does not include raw category-thread-list HTML or private forum content.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum inventories, category-owned thread traversal, moderation summaries, migration ledgers, translation review tooling, cached forum scans, generated fixtures, `ForumCategory.threads`, or `ForumCategory.reload_threads()` where thread identity must come from structurally valid generated thread links.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread-list acquisition as a practical read-heavy workflow and as the entry point for direct thread, post, and revision traversal. Existing drafts cover retry-aware thread-list fetching, nested-table scoping, title/description text fidelity, row-level parser context, response-body diagnostics, post-count parsing, created-by and created-at parser diagnostics, direct thread-detail ID parsing, direct `ForumThread.id` validation, thread-ID range validation, retained category ID validation before thread-list acquisition, generated thread href ID-segment validation, generated thread href route validation, generated thread script ID ASCII-shape validation, and adjacent forum traversal.

This slice is not a duplicate of [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md) or [741-pr-validate-forum-thread-href-routes.md](741-pr-validate-forum-thread-href-routes.md). Issue 727 covers embedded non-ID segment text such as `t-3001-latest`; Issue 741 covers route, scheme, and host shape before accepting a numeric segment. This slice covers Unicode digit normalization in an otherwise valid generated thread href ID segment.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md), [741-pr-validate-forum-thread-href-routes.md](741-pr-validate-forum-thread-href-routes.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), [745-pr-validate-private-message-data-href-id-ascii-shape.md](745-pr-validate-private-message-data-href-id-ascii-shape.md), and [746-pr-validate-forum-category-href-id-ascii-shape.md](746-pr-validate-forum-category-href-id-ascii-shape.md).

## Changes

- Require generated forum thread `t-<id>` path IDs to match `[0-9]+` before `int(...)`.
- Preserve valid relative thread routes and same-site absolute HTTP(S) thread routes.
- Preserve existing no-ID diagnostics, embedded malformed-ID diagnostics, route/scheme/host malformed diagnostics, nested-table scoping, title/description extraction, post-count parsing, created metadata parsing, retry behavior, response-body validation, category-thread cache behavior, direct thread reads, post access, reply behavior, and downstream post/revision traversal.
- Add focused regression coverage for escaped fullwidth thread ID text `\uff13\uff10\uff10\uff11`.

## Type Of Change

- Bug fix
- Forum thread parser scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated forum thread href with a non-ASCII digit ID segment must fail before `ForumThread` construction. |
| R2 | The malformed thread-ID error must preserve existing site, category, page, row, field, and observed href context. |
| R3 | Valid relative and same-site absolute ASCII thread routes must continue to parse the same thread IDs. |
| R4 | Existing no-ID, embedded malformed-ID, and route/scheme/host diagnostics must remain compatible. |
| R5 | Existing category thread-list workflows and adjacent forum traversal workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw generated forum HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `/forum/t-\uff13\uff10\uff10\uff11/test-thread` raises before a thread is returned. | `test_acquire_all_rejects_non_ascii_digit_thread_href_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only ID validation. | Returning a `ForumThread`, storing ID `3001`, or silently dropping the row rejects this local completion claim. | Forum thread-list parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | The malformed diagnostic includes site, category, page, row, `field=id`, and raw href value. | The focused regression matches the existing malformed-ID message family. | Omitting structural context or the observed href rejects this local completion claim. | Parser diagnostics | focused test |
| R3 | Valid generated ASCII routes continue to work. | Focused GREEN included `test_acquire_all_single_page` and same-site absolute href compatibility. | Rejecting valid relative or same-site absolute thread links rejects this local completion claim. | Valid href compatibility | forum-thread tests |
| R4 | Existing malformed branches stay green. | Focused GREEN included embedded malformed-ID and malformed-route regressions. | Reclassifying no-ID links, embedded malformed-ID links, or invalid routes into a different diagnostic family rejects this local completion claim. | Prior parser branches | forum-thread tests |
| R5 | Adjacent workflows remain green. | `tests/unit/test_forum_thread.py` passed 233 tests, adjacent forum category/thread/post/revision coverage passed 902 tests, and full unit passed 3748 tests. | Regressing category thread-list parsing, nested-table filtering, title/description spacing, post-count parsing, created metadata parsing, category-thread cache behavior, direct thread reads, post/revision traversal, or any unit test rejects this local completion claim. | Forum workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses synthetic unit-level category-thread-list HTML and mocked responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private forum names, private thread titles, page source, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-thread tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `19214a2 fix(forum_thread): validate href id ascii shape`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_thread_href_id -q` failed before the fix with `DID NOT RAISE` because `/forum/t-\uff13\uff10\uff10\uff11/test-thread` was accepted and normalized as thread ID `3001`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_thread_href_id tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_thread_id_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_malformed_thread_href_routes tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_same_site_absolute_thread_href tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_description_text_spacing tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_nested_thread_tables -q` passed 12 tests.
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 233 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 902 tests.
- `uv run --extra test pytest tests/unit -q` passed 3748 tests.
- `uv run --extra lint ruff check src tests` passed.
- `uv run --extra format ruff format --check src tests` passed with 87 files already formatted.
- `uv run --extra lint mypy src tests --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(...)` raises contextual `NoElementException` for a present generated href built from escaped fullwidth digit text `/forum/t-\uff13\uff10\uff10\uff11/test-thread`.
- The exception includes site unix name, parent category ID, page number, structural row number, `field=id`, and raw href value.
- Valid relative thread links such as `/forum/t-3001/test-thread` still parse thread ID `3001`.
- Valid same-site absolute thread links such as `http://test-site.wikidot.com/forum/t-3001/test-thread?from=start#top` still parse thread ID `3001`.
- Existing no-ID behavior, embedded malformed-ID behavior, and malformed route/scheme/host behavior remain on their existing diagnostic paths.
- Existing thread-list parsing, retry handling, empty-result behavior, response-body validation, nested-table filtering, title/description spacing, post-count parsing, created metadata parsing, category-thread cache behavior, lazy `ForumCategory.threads`, `reload_threads(...)`, direct thread detail acquisition, post access, reply behavior, and post/revision traversal remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real category-thread-list HTML, raw rollout path, private forum name, private thread title, page source, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issues 727 or 741. Mitigation: those issues cover embedded malformed-ID segment text and route/scheme/host shape; this slice covers Unicode digit normalization that still passes those branches.
- Risk: Tightening thread ID parsing could reject unusual but valid generated forum output. Mitigation: Wikidot thread IDs in fixtures are ordinary ASCII decimal digits, and valid relative plus same-site absolute thread routes remain tested.
- Risk: Diagnostics could expose private forum content. Mitigation: the diagnostic reports only the scalar href value plus site/category/page/row/field context, not response bodies, credentials, cookies, forum names, thread titles, page source, local paths, or private site data.

## Dependencies

- `forum/ForumViewCategoryModule` continues to represent thread links as relative thread routes or same-site HTTP(S) thread routes.
- `ForumThreadCollection.acquire_all_in_category(...)` remains the public category-thread-list parser for `ForumCategory.threads` and `ForumCategory.reload_threads()`.
- Direct `ForumThread.id` constructor and retained thread-state validation remain unchanged.

## Open Questions

None for this local slice. Future forum thread parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

`ForumThread.id` is durable identity metadata for browser-free forum inventories, moderation summaries, migration checks, cached category ledgers, category-owned post traversal, and downstream forum revision traversal. Unicode digit normalization can silently turn malformed generated thread route metadata into a valid-looking thread ID. Requiring ASCII digits keeps generated identity parsing strict and consistent with adjacent forum-category, page-file, private-message, and forum-thread script scalar-shape fixes while preserving valid thread links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: escaped fullwidth digit route IDs were accepted and normalized to thread ID `3001`.
- Existing local drafts covered category-thread-list retrying, parser scoping, missing thread IDs, embedded malformed `t-<id>` segments, route/scheme/host diagnostics, title/description/count/user/timestamp diagnostics, response-body typing, direct record fields, collection construction, retained category state, and adjacent forum traversal; they did not validate Unicode digit normalization in generated thread href ID scalars.
- This slice does not change request payloads, retry policy, thread row selectors, title text extraction, description text extraction, post-count parsing, created metadata parsing, direct `ForumThread` constructor rules, direct `ForumThreadCollection` constructor rules, lazy category-thread cache behavior, live Wikidot behavior, upstream filing state, or valid relative/same-site HTTP(S) thread output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated category-thread-list HTML from real sites, private forum names, private thread titles, page source, private forum content, and private site data out of upstream discussion.
