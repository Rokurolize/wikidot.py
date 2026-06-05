# PR Draft: Report Malformed Forum Post List Users

## Summary

`ForumPostCollection.acquire_all_in_thread(...)`, used by `ForumThread.posts` and by the multi-thread post-list helper, parses generated forum post-list markup from `forum/ForumViewThreadPostsModule`. Earlier local slices made this read path retry-aware, deduplicated duplicate thread IDs, reused cached thread post lists, filtered pseudo-post/content post markup, scoped metadata spans to generated direct children, preserved title spacing, added site/thread/page/post parser context, validated missing response bodies, and converted malformed structural post IDs into contextual `NoElementException`. One adjacent parser-value gap remained in the normal post-list parser: when a structural post row contained a present direct `span.printuser` whose `userInfo(...)` metadata was malformed, the shared `user_parse(...)` utility raised raw `ValueError("user id is not found")` without identifying the site, thread, page, structural post position, post ID, affected field, or observed `onclick` value.

This follow-up keeps the shared `user_parse(...)` utility unchanged and catches malformed structural forum post-list created-by metadata at the post-list parser boundary. It raises `NoElementException` with site unix name, thread ID, page number, structural post position, parsed post ID, `field=created_by`, and the offending direct `onclick` value. Valid post-list parsing, valid user parsing, malformed post ID diagnostics, metadata scoping, pagination, retry behavior, response-body diagnostics, direct cache population, source fetching, edit behavior, and reply behavior remain unchanged.

## Outcome

Malformed present created-by metadata in a generated forum post-list row is now reported as a forum-post list parser failure instead of a raw shared-parser failure.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `ForumThread.posts`, `ForumPostCollection.acquire_all_in_thread(...)`, or `ForumPostCollection.acquire_all_in_threads(...)` for browser-free discussion inspection, archival indexing, moderation tooling, source extraction, or post-edit workflows.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), and [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md). Those drafts established forum post-list acquisition as a practical, retry-aware, cache-aware, parser-scoped read path. This slice also follows the shared printuser parser-boundary pattern from [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), and [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present forum post-list `span.printuser` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site unix name, thread ID, page number, structural post position, parsed post ID, `field=created_by`, and the observed direct `onclick` value in the parser error.
- Preserve the shared `user_parse(...)` utility behavior and parser tests.
- Preserve successful `ForumPostCollection.acquire_all_in_thread(...)` parsing, direct `_parse(...)` parsing, and valid post-list user handling.
- Preserve existing post-list response-body validation, retry-exhausted behavior, duplicate thread-ID deduplication, cached post-list reuse, pseudo-post filtering, nested content filtering, title spacing, metadata scoping, malformed post ID diagnostics, source fetching, edit behavior, and reply behavior.
- Add a focused public `ForumPostCollection.acquire_all_in_thread(...)` regression for a malformed created-by `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post-list parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A structural forum post-list row with malformed present created-by `span.printuser` metadata must fail at the forum-post list parser boundary. |
| R2 | The malformed user error must identify the affected site, thread, page, structural post position, post ID, field, and observed direct `onclick` value. |
| R3 | Existing valid post-list parsing and direct parser callers must remain compatible. |
| R4 | Existing forum post-list response handling, retries, pagination, caching, pseudo-post filtering, metadata scoping, malformed post ID diagnostics, source fetching, edit behavior, and reply behavior must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumPostCollection.acquire_all_in_thread(thread)` raises `NoElementException` for `userInfo(latest)` in the structural post-list created-by element. | `TestForumPostCollectionAcquireAll.test_acquire_all_malformed_user_includes_thread_page_post_and_value_context` returns a post-list page and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, silently skipping the post, returning `created_by=None`, or returning a malformed `ForumPost` rejects this local completion claim. | `src/wikidot/module/forum_post.py` | `tests/unit/test_forum_post.py` |
| R2 | The error names site, thread, page, structural post position, post ID, `field=created_by`, and the bad direct `onclick` value. | The focused regression asserts `Forum post user is malformed for site: test-site (thread=3001, page=1, post=1, post_id=5001, field=created_by, value=WIKIDOT.page.listeners.userInfo(latest); return false;)`. | Omitting any location field, using only rendered user text, or hiding the raw `onclick` value makes the failure ambiguous and rejects this local completion claim. | Post-list diagnostics | `tests/unit/test_forum_post.py` |
| R3 | Valid post-list rows still parse through the existing public acquisition API and direct parser helper. | Focused GREEN includes public single-page acquisition and direct metadata-scope parser tests. | Regressing post IDs, parent IDs, titles, content, created-by users, timestamps, edit metadata, order, or collection ownership rejects this local completion claim. | `ForumPostCollection.acquire_all_in_thread(...)` and `_parse(...)` | `tests/unit/test_forum_post.py` |
| R4 | Adjacent post-list behaviors stay green. | Focused GREEN includes malformed post ID context, malformed parent post ID context, post info metadata scoping, edit metadata scoping, and single-page acquisition; the whole `test_forum_post.py` file passed 62 tests. | Regressing response-body context, retry behavior, pagination, duplicate-thread handling, cached post-list reuse, pseudo-post filtering, nested content filtering, source fetching, edit behavior, or reply behavior rejects this local completion claim. | Forum post workflows | `tests/unit/test_forum_post.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d3390ec fix(forum_post): report malformed post users`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_user_includes_thread_page_post_and_value_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_user_includes_thread_page_post_and_value_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_post_id_includes_thread_page_and_value_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_parent_post_id_includes_child_post_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_scopes_post_info_metadata_to_direct_children tests/unit/test_forum_post.py::TestForumPostCollectionParse::test_parse_scopes_post_edit_metadata_to_direct_children -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed 62 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 186 tests.
- `uv run --extra test pytest tests/unit -q` passed 852 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_thread(thread)` raises `NoElementException` when a post-list response has a structural created-by `span.printuser` element whose direct `userInfo(...)` metadata cannot be parsed by the shared user parser.
- The malformed created-by error includes the site unix name, thread ID, page number, structural post position, parsed post ID, `field=created_by`, and observed direct `onclick` value.
- Valid post-list rows still parse created-by users through `user_parser(...)`.
- Direct `_parse(thread, html, page=None)` callers remain compatible.
- Existing response-body diagnostics, retry-exhausted handling, pagination, duplicate-thread deduplication, cached post-list reuse, malformed post ID diagnostics, metadata scoping, pseudo-post filtering, nested content filtering, source fetching, edit behavior, and reply action payloads remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated post-list HTML, post contents, forum titles from real sites, or private forum content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected created-by parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only post-list location metadata.
- Risk: Changing the shared user parser could affect unrelated modules. Mitigation: this slice intentionally leaves `user_parse(...)` unchanged and validates parser-adjacent forum behavior through the full unit suite.
- Risk: User-like markup inside post content could be mistaken for the structural created-by user. Mitigation: the existing structural metadata scoping remains unchanged, and the focused GREEN run includes post info and edit metadata scoping tests.

## Dependencies

- BeautifulSoup continues to expose direct forum post-list `span.printuser` elements and direct anchor `onclick` values in the generated post metadata block.
- The shared `user_parse(...)` utility remains the source of truth for valid Wikidot user metadata extraction.
- Post-list pages still identify created-by users through direct `span.printuser` metadata under each structural post `div.info` block.

## Open Questions

None for this local slice. Broader centralization of repeated user/timestamp value helpers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

Forum post-list inspection is a read-heavy prerequisite for discussion inspection, source extraction, revision workflows, edit workflows, archival indexing, and moderation-oriented tooling. If Wikidot emits a structural post-list row with malformed direct created-by metadata, wikidot.py should return a structured parser failure naming the affected site, thread, page, post, field, and observed value instead of forcing operators to infer context from a raw shared helper exception. That keeps forum diagnostics actionable without retaining generated forum HTML, raw response JSON, post content, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established forum post-list acquisition as a practical read-heavy workflow, including retry-aware post-list fetching, duplicate thread-ID deduplication, cache-aware direct acquisition, response-body validation, structural parser context, post ID diagnostics, pseudo-post filtering, nested content filtering, title text spacing, metadata scoping, source fetching, edit behavior, and reply behavior.
- Recent forum workflow drafts validated parser-boundary diagnostics for category thread-list created-by/created-at metadata, direct thread-detail created-by/created-at metadata, and forum post revision created-by metadata. Normal post-list created-by parsing uses the same shared user parser but needs post-list context at its own parser boundary.
- The immediate RED failure showed the same raw `ValueError("user id is not found")` class that prior parser-boundary slices converted in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML, post contents, thread titles from real sites, page names from real sites, and private forum content out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding forum post-list parser diagnostics.
