# PR Draft: Validate Forum Thread Href Routes

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, exposed through `ForumCategory.threads` and `ForumCategory.reload_threads()`, parses generated `forum/ForumViewCategoryModule` thread-list title links into `ForumThread.id` values. Issue [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md) made malformed `t-<id>` path segments such as `/forum/t-3001-latest/test-thread` fail instead of becoming thread ID `3001`, but the parser still searched the raw href text for a valid-looking `t-<digits>` segment. As a result, `http://example.com/forum/t-3001/test-thread`, `https://other-site.wikidot.com/forum/t-3001/test-thread`, `http:forum/t-3001/test-thread`, `javascript:/forum/t-3001/test-thread`, and `mailto:forum/t-3001/test-thread` could become current-site `ForumThread.id=3001`.

This change validates generated forum thread href route shape before extracting the thread ID. Relative thread links and same-site absolute HTTP(S) thread links remain compatible, while foreign, hostless-HTTP, and non-HTTP(S) present hrefs raise contextual `NoElementException`.

## Outcome

Browser-free category thread-list acquisition no longer fabricates current-site thread identities from foreign absolute URLs, other-site Wikidot URLs, hostless HTTP strings, JavaScript URLs, or mailto URLs. Valid relative thread links such as `/forum/t-3001/test-thread` and same-site absolute links such as `http://test-site.wikidot.com/forum/t-3001/test-thread?from=start#top` continue to parse the same thread IDs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using category-owned thread traversal for browser-free forum inventories, migration ledgers, moderation tooling, translation review tooling, cached category scans, post/revision traversal, generated fixtures, `ForumCategory.threads`, or `ForumCategory.reload_threads()`.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread-list acquisition as a practical read-heavy workflow and as the entry point for direct thread, post, and revision traversal. Existing drafts cover retry-aware thread-list fetching, nested-table scoping, title/description text fidelity, row-level parser context, response-body diagnostics, post-count parsing, created-by and created-at parser diagnostics, direct thread-detail ID parsing, direct `ForumThread.id` validation, thread-ID range validation, retained category ID validation before thread-list acquisition, generated thread href ID-segment validation, and generated category href route validation.

This slice is not a duplicate of [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [642-pr-validate-non-negative-forum-thread-ids.md](642-pr-validate-non-negative-forum-thread-ids.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), or [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md). Issue 727 covers the shape of the `t-<id>` path segment once the generated href is otherwise treated as a thread link. This slice covers route and scheme validation before any `t-<id>` segment is accepted as current-site thread identity.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), and [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md).

## Changes

- Parse generated thread hrefs with `urlsplit(...)`.
- Reject thread hrefs with non-HTTP(S) schemes such as `javascript:` and `mailto:`.
- Reject `http` or `https` hrefs that do not include a host, such as `http:forum/t-3001/test-thread`.
- Reject absolute hrefs whose host does not match the current site's domain.
- Extract thread IDs from the parsed URL path after route validation.
- Preserve valid relative thread hrefs and same-site absolute HTTP(S) thread hrefs.
- Preserve existing missing-ID diagnostics, malformed `t-<id>` segment diagnostics, nested-table scoping, title/description text extraction, post-count parsing, created metadata parsing, retry behavior, response-body validation, category-thread cache behavior, direct thread reads, post access, and reply behavior.

## Type Of Change

- Bug fix
- Forum thread parser route-shape validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated thread href with a non-HTTP(S) scheme such as `javascript:` or `mailto:` must fail before constructing `ForumThread`. |
| R2 | An `http` or `https` href without a host must fail before constructing `ForumThread`. |
| R3 | An absolute thread href whose host does not match the current site domain must fail before constructing `ForumThread`. |
| R4 | Malformed href diagnostics must include site unix name, parent category ID, thread-list page number, structural row number, `field=id`, and the observed href value. |
| R5 | Valid relative thread hrefs must continue to parse the same thread IDs. |
| R6 | Valid same-site absolute HTTP(S) thread hrefs must continue to parse the same thread IDs. |
| R7 | Existing malformed `t-<id>` segment errors, missing-ID errors, nested-row scoping, title/description text, post-count parsing, created metadata parsing, thread collection behavior, post access, and adjacent forum workflows must remain compatible. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw generated forum HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, full forum-thread tests, adjacent forum tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `javascript:/forum/t-3001/test-thread` and `mailto:forum/t-3001/test-thread` raise `NoElementException` before `ForumThread` construction. | The focused RED failed with `DID NOT RAISE`; focused GREEN passed after href route validation. | Storing a thread ID from a non-HTTP(S) scheme rejects this local completion claim. | Forum thread parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | `http:forum/t-3001/test-thread` raises the contextual malformed-ID error. | The parametrized malformed-route regression covers hostless HTTP. | Treating hostless HTTP text as a relative thread route rejects this local completion claim. | Forum thread parser | forum-thread tests |
| R3 | `http://example.com/forum/t-3001/test-thread` and `https://other-site.wikidot.com/forum/t-3001/test-thread` raise the contextual malformed-ID error. | The parametrized malformed-route regression covers foreign absolute and other-site Wikidot hosts. | Extracting current-site thread IDs from a foreign host rejects this local completion claim. | Forum thread parser | forum-thread tests |
| R4 | The malformed-href diagnostic includes site, category, page, row, field, and raw href value. | The regression matches `Thread ID is malformed for site: test-site (category=1001, page=1, row=1, field=id, value=<href>)`. | Omitting structural location or observed href rejects this local completion claim. | Parser diagnostics | forum-thread tests |
| R5 | `/forum/t-3001/test-thread` still parses thread ID `3001`. | Existing `test_acquire_all_single_page` passed in focused and full forum-thread coverage. | Rejecting valid relative thread links or changing parsed thread IDs rejects this local completion claim. | Relative thread href compatibility | forum-thread tests |
| R6 | `http://test-site.wikidot.com/forum/t-3001/test-thread?from=start#top` still parses thread ID `3001`. | `test_acquire_all_preserves_same_site_absolute_thread_href` passed. | Rejecting same-site absolute HTTP(S) thread routes rejects this local completion claim. | Same-site absolute thread href compatibility | forum-thread tests |
| R7 | Existing forum thread and adjacent forum workflows remain green. | Focused nearby tests, full `test_forum_thread.py`, adjacent forum category/thread/post/revision tests, and full unit tests passed. | Regressing malformed segment diagnostics, missing-ID diagnostics, nested-table filtering, title/description text, post-count parsing, created metadata parsing, category-thread cache behavior, post/revision traversal, or adjacent forum workflows rejects this local completion claim. | Forum workflow | `tests/unit` |
| R8 | No live site state or private material is needed. | All regressions use synthetic generated category-thread-list HTML and mocked AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private forum names, private thread titles, page source, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-thread tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `57ca8d4 fix(forum_thread): validate thread href routes`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_malformed_thread_href_routes -q` failed before the fix with 5 `DID NOT RAISE` malformed-route cases.
- GREEN focused: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_malformed_thread_href_routes tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_same_site_absolute_thread_href tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_thread_id_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_title_text_spacing tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_preserves_description_text_spacing tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_ignores_nested_thread_tables -q` passed 11 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 231 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 899 tests.
- `uv run pytest tests/unit -q` passed 3734 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(...)` raises contextual `NoElementException` for `http://example.com/forum/t-3001/test-thread`.
- `ForumThreadCollection.acquire_all_in_category(...)` raises the same diagnostic family for `https://other-site.wikidot.com/forum/t-3001/test-thread`.
- `ForumThreadCollection.acquire_all_in_category(...)` raises the same diagnostic family for `http:forum/t-3001/test-thread`.
- `ForumThreadCollection.acquire_all_in_category(...)` raises the same diagnostic family for `javascript:/forum/t-3001/test-thread`.
- `ForumThreadCollection.acquire_all_in_category(...)` raises the same diagnostic family for `mailto:forum/t-3001/test-thread`.
- The malformed-href error includes site unix name, parent category ID, thread-list page number, structural row number, `field=id`, and the raw href value.
- Valid relative thread links such as `/forum/t-3001/test-thread` still parse the same thread ID.
- Valid same-site absolute thread links such as `http://test-site.wikidot.com/forum/t-3001/test-thread?from=start#top` still parse the same thread ID.
- Existing malformed ID-segment behavior remains on the `Thread ID is malformed ...` path.
- Existing no-ID behavior remains on the `Thread ID is not found ...` path.
- Existing nested-table filtering, title/description spacing, post-count parsing, created metadata parsing, category-thread cache behavior, lazy `ForumCategory.threads`, `reload_threads(...)`, direct thread detail acquisition, post access, reply behavior, and post/revision traversal remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real category-thread-list HTML, local rollout path, private forum name, private thread title, page source, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening forum thread href route parsing could reject an unusual but valid generated thread link. Mitigation: relative thread links remain supported, same-site absolute HTTP(S) links remain supported, and the validation only rejects foreign hosts, hostless HTTP(S), and non-HTTP(S) schemes when an ID-looking thread segment is present.
- Risk: This could be confused with Issue 727. Mitigation: Issue 727 validates the `t-<id>` path segment shape; this slice validates route scheme and host before accepting an otherwise valid `t-<id>` segment.
- Risk: This could blur previous missing-ID diagnostics. Mitigation: hrefs without any thread ID candidate still use `Thread ID is not found ...`; present hrefs with ID-looking malformed routes use `Thread ID is malformed ...`.
- Risk: Diagnostics could expose raw generated forum HTML. Mitigation: the new diagnostic reports only the scalar href value plus site/category/page/row/field context, not full response bodies, credentials, cookies, local paths, page source, private forum content, or private site data.

## Dependencies

- `forum/ForumViewCategoryModule` continues to represent thread links as relative or same-site HTTP(S) hrefs.
- `ForumThread.id` remains a parsed integer thread identity; direct constructor validation is unchanged.
- `ForumThreadCollection.acquire_all_in_category(...)` remains the public category-thread-list parser for `ForumCategory.threads`.

## Open Questions

None for this local slice. Future forum thread parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

`ForumThread.id` is durable identity metadata for browser-free forum inventories, moderation summaries, migration checks, cached category ledgers, category-owned post traversal, and downstream forum revision traversal. A thread href from another host, a non-HTTP scheme, or a hostless HTTP string is not a current-site generated forum thread route. Validating route shape keeps malformed module output visible while preserving normal relative and same-site absolute thread links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: five malformed present href routes did not raise and were accepted as current-site thread IDs.
- Existing local drafts covered category-thread-list retrying, parser scoping, missing thread IDs, malformed `t-<id>` path segments, title/description/count/user/timestamp diagnostics, response-body typing, direct record fields, collection construction, retained category state, and adjacent forum traversal; they did not validate present generated thread href route/scheme/host shape before `ForumThread.id` is stored.
- This slice does not change request payloads, retry policy, thread row selectors, title text extraction, description text extraction, post-count parsing, created metadata parsing, direct `ForumThread` constructor rules, direct `ForumThreadCollection` constructor rules, lazy category-thread cache behavior, live Wikidot behavior, upstream filing state, or valid relative/same-site HTTP(S) thread output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated category-thread-list HTML from real sites, private forum names, private thread titles, page source, private forum content, and private site data out of upstream discussion.
