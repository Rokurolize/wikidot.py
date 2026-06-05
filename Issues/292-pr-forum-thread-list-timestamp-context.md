# PR Draft: Report Malformed Forum Thread List Timestamps

## Summary

`ForumThreadCollection.acquire_all_in_category(category)` parses Wikidot's `forum/ForumViewCategoryModule` thread-list rows into `ForumThread` objects. Earlier local slices made this category thread-list path retry-aware, scoped row parsing to direct generated thread tables, ignored nested thread tables and row-local pager markup, preserved title and description spacing, validated missing response bodies, cached direct category-thread acquisition, converted malformed post-count values into contextual `NoElementException`, and converted malformed created-by `printuser` metadata into contextual `NoElementException`. One adjacent parser-value gap remained: when a structural thread-list row contained a present direct `span.odate` whose `time_*` metadata was malformed, the shared `odate_parse(...)` utility raised raw `ValueError` without identifying the site, forum category, page, row, affected field, or observed timestamp class value.

This follow-up keeps the shared `odate_parse(...)` utility unchanged and catches malformed category thread-list timestamp metadata at the thread-list parser boundary. It raises `NoElementException` with site unix name, category ID, page, structural row, `field=created_at`, and the offending direct `time_*` class value. Valid thread-list parsing, valid timestamp parsing, created-by user diagnostics, malformed post-count diagnostics, pagination, retry behavior, missing response-body diagnostics, cache behavior, direct detail fetching, thread-detail parsing, and thread mutation actions remain unchanged.

## Outcome

Malformed present created-at metadata in a generated category thread-list row is now reported as a forum-thread list parser failure instead of a raw shared-parser failure.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `ForumCategory.threads`, `ForumCategory.reload_threads()`, or direct `ForumThreadCollection.acquire_all_in_category(category)` calls for browser-free forum indexing, audit, migration, or moderation workflows.

## Related Issue

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), and [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md). Those drafts established category thread-list acquisition as a practical, retry-aware, cache-aware, parser-scoped forum surface. This slice also follows the shared odate parser-boundary pattern from [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), and [290-pr-site-member-joined-at-context.md](290-pr-site-member-joined-at-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present category thread-list `span.odate` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site unix name, category ID, thread-list page, structural row number, `field=created_at`, and the observed direct `time_*` class value in the parser error.
- Preserve the shared `odate_parse(...)` utility behavior and parser tests.
- Preserve successful `ForumThreadCollection.acquire_all_in_category(category)` parsing, direct `_parse_list_in_category(...)` parsing, valid thread-list timestamp handling, and valid thread-list user handling.
- Preserve existing thread-list response-body validation, retry-exhausted behavior, pagination, nested-thread-table filtering, row-local pager filtering, title/description text spacing, created-by user diagnostics, post-count diagnostics, category-thread cache population, and cached acquisition behavior.
- Add a focused public `ForumThreadCollection.acquire_all_in_category(category)` regression for a malformed created-at `class="odate time_latest"` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-list parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A structural category thread-list row with malformed present created-at `span.odate` metadata must fail at the forum-thread list parser boundary. |
| R2 | The malformed timestamp error must identify the affected site, category, page, row, field, and observed direct `time_*` class value. |
| R3 | Existing valid category thread-list parsing and direct parser callers must remain compatible. |
| R4 | Existing thread-list response handling, pagination, retries, cache behavior, parser scoping, title/description spacing, created-by user diagnostics, and malformed post-count diagnostics must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumThreadCollection.acquire_all_in_category(category)` raises `NoElementException` for `class="odate time_latest"` in a structural thread-list row. | `TestForumThreadCollectionAcquireAll.test_acquire_all_malformed_odate_includes_category_page_row_and_value_context` returns the category thread-list page and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a timestamp, silently dropping the row, returning `created_at=None`, or returning a `ForumThread` rejects this local completion claim. | `src/wikidot/module/forum_thread.py` | `tests/unit/test_forum_thread.py` |
| R2 | The error names site, category, page, row, `field=created_at`, and the bad direct `time_*` class value. | The focused regression asserts `Forum thread list created_at is malformed for site: test-site (category=1001, page=1, row=1, field=created_at, value=time_latest)`. | Omitting any location field, using only rendered date text, or hiding the raw timestamp class value rejects this local completion claim. | Thread-list diagnostics | `tests/unit/test_forum_thread.py` |
| R3 | Valid category thread-list rows still parse through the existing public acquisition API and direct parser helper. | Focused GREEN includes single-page public acquisition and direct list parse success tests. | Regressing row count, thread IDs, created-by users, timestamps, descriptions, titles, or category assignment rejects this local completion claim. | `ForumThreadCollection.acquire_all_in_category(...)` and `_parse_list_in_category(...)` | `tests/unit/test_forum_thread.py` |
| R4 | Adjacent thread-list behaviors stay green. | Focused GREEN includes created-by user diagnostics, malformed post-count context, and description metadata isolation; the whole `test_forum_thread.py` file passed 52 tests. | Regressing missing response-body context, retry behavior, pagination, nested table filtering, description pager filtering, title/description spacing, created-by user diagnostics, post-count diagnostics, or cache behavior rejects this local completion claim. | Category thread-list workflows | `tests/unit/test_forum_thread.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f306c99 fix(forum_thread): report malformed list timestamps`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_odate_includes_category_page_row_and_value_context -q` failed before the fix with `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_odate_includes_category_page_row_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_user_includes_category_page_row_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_post_count_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionParseListInCategory::test_parse_success tests/unit/test_forum_thread.py::TestForumThreadCollectionParseListInCategory::test_parse_ignores_description_metadata_markup -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 52 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 183 tests.
- `uv run --extra test pytest tests/unit -q` passed 849 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(category)` raises `NoElementException` when a category thread-list response has a structural row with a direct `span.odate` element whose `time_*` metadata cannot be parsed by the shared odate parser.
- The malformed created-at error includes the site unix name, category ID, page number, structural row number, `field=created_at`, and observed direct `time_*` class value.
- Valid thread-list rows still parse timestamps through `odate_parser(...)`.
- Direct `_parse_list_in_category(site, html, category=None, page=None)` callers remain compatible.
- Existing missing response-body diagnostics, retry-exhausted handling, pagination, cached category-thread acquisition, nested-thread-table filtering, row-local pager filtering, description/title spacing preservation, malformed created-by diagnostics, malformed post-count diagnostics, direct thread-detail acquisition, thread-detail parsing, and thread mutation actions remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated thread-list HTML, forum titles from real sites, or private forum content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected created-at parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only thread-list location metadata.
- Risk: Changing the shared odate parser could affect unrelated modules. Mitigation: this slice intentionally leaves `odate_parse(...)` unchanged and validates parser and adjacent forum behavior through the full unit suite.
- Risk: Nested description markup could be mistaken for the row timestamp. Mitigation: the existing direct `:scope > span.odate` selection remains unchanged, and the focused GREEN run includes the description metadata isolation test.

## Dependencies

- BeautifulSoup continues to expose direct thread-list `span.odate` elements and class values in the generated row structure.
- The shared `odate_parse(...)` utility remains the source of truth for valid Wikidot timestamp metadata extraction.
- Category thread lists still identify created-at values through direct `span.odate` metadata in the `td.started` cell.

## Open Questions

None for this local slice. Broader centralization of repeated `_odate_class_value(...)` helpers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

Category thread lists are practical browser-free inputs for forum indexing, audit, migration, and moderation. If Wikidot emits a structural thread-list row with malformed direct created-at metadata, wikidot.py should return a structured parser failure naming the affected site, category, page, row, field, and observed value instead of forcing operators to infer context from a raw shared helper exception. That keeps forum diagnostics actionable without retaining generated forum HTML, raw response JSON, forum content, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established `ForumThreadCollection.acquire_all_in_category(category)` as a retry-aware, cache-aware, parser-scoped read path used by `ForumCategory.threads` and `ForumCategory.reload_threads()`.
- Recent forum workflow drafts validated response-body handling, cache consistency, malformed post-count diagnostics, malformed created-by diagnostics, and parser scoping for category thread lists; this slice targets only the malformed-present created-at `odate` metadata path inside thread-list parsing.
- Shared timestamp work has already covered parser-boundary diagnostics in recent changes, forum post revisions, private-message details, and site-member lists. Category thread lists use the same shared parser but need site/category/page/row context at their own parser boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML, thread titles from real sites, page names from real sites, and private forum content out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding thread-list response and forum diagnostics.
