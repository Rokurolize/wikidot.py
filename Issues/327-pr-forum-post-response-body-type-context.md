# PR Draft: Report Malformed Forum Post Response Body Types

## Summary

`ForumPostCollection.acquire_all_in_thread(...)` and `ForumPostCollection.acquire_all_in_threads(...)` parse `forum/ForumViewThreadPostsModule` response `body` values as generated forum post-list HTML. `ForumPostCollection.get_post_sources()` and lazy `ForumPost.source` parse `forum/sub/ForumEditPostFormModule` response `body` values as generated edit-form HTML for source extraction. `ForumPost.edit(...)` uses that same edit-form module as a read-before-mutation preflight before sending `saveEditPost`. Earlier local slices made these paths retry-aware, cache-aware, duplicate-aware, parser-scoped, context-rich for missing response bodies, and safe around malformed edit forms. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the code passed that value into BeautifulSoup and leaked a low-level parser `AttributeError`.

This local slice validates present forum post-list, source-form, and edit-form response `body` values before HTML parsing. Non-string bodies now raise `NoElementException` with site/thread/page or site/post context plus `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw forum HTML, response JSON, local rollout paths, credentials, account material, post source text, titles, or post content.

## Outcome

Malformed forum-post response body types now fail at the module response boundary with actionable forum context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, moderation tooling, archival scans, source extraction, migration helpers, or post-edit workflows.

## Related Issue

Builds on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [099-pr-ignore-forum-post-content-pager-markup.md](099-pr-ignore-forum-post-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [143-pr-reuse-cached-duplicate-thread-posts.md](143-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [173-pr-forum-post-edit-form-fetch-failure-context.md](173-pr-forum-post-edit-form-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), and [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md) through [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md). Those drafts established forum post acquisition, source extraction, and edit preflight as practical read-heavy workflows with explicit diagnostics while leaving present non-string response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), and [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate forum post-list response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string post-list body values into site/thread/page-specific `NoElementException`.
- Validate forum post source response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string source-form body values into site/post-specific `NoElementException`.
- Validate forum post edit-form response `body` values are strings before BeautifulSoup parsing.
- Convert present non-string edit-form body values into site/post-specific `NoElementException` before current-revision lookup or any save action.
- Preserve missing-body diagnostics, retry-exhausted behavior, skipped failed source retries, cache behavior, duplicate handling, pagination, parser diagnostics, source extraction, no-save-on-malformed-edit-form behavior, replies, and adjacent forum workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A post-list response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | A post source response with a present non-string `body` field must fail before BeautifulSoup parsing and must not mark source as acquired. |
| R3 | An edit-form response with a present non-string `body` field must fail before BeautifulSoup parsing, current-revision lookup, or any save action. |
| R4 | Malformed-body-type errors must identify the affected site/thread/page or site/post, `field=body`, expected type, and observed type while omitting raw generated forum content. |
| R5 | Existing missing-body diagnostics, retry handling, cache behavior, duplicate handling, parser diagnostics, source extraction, edit behavior, and adjacent forum workflows must remain compatible. |
| R6 | Focused, forum-post, adjacent forum, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumPostCollection.acquire_all_in_thread(thread)` raises contextual `NoElementException` when `forum/ForumViewThreadPostsModule` returns a list-valued `body`. | `TestForumPostCollectionAcquireAll.test_acquire_all_malformed_first_page_response_body_type_includes_thread_and_page_context` expects `Forum post list response body is malformed for site: test-site, thread: 3001, page: 1 (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, fabricating an empty collection, seeding `thread._posts`, or entering post-row parsing rejects this local completion claim. | Forum post-list reads | `tests/unit/test_forum_post.py` |
| R2 | `ForumPostCollection.get_post_sources()` raises contextual `NoElementException` when `forum/sub/ForumEditPostFormModule` returns a list-valued source-form `body`, and leaves `_source` unset. | `TestForumPostCollectionGetSources.test_get_post_sources_malformed_response_body_type_includes_site_post_and_type_context` expects `Forum post source response body is malformed for site: test-site, post: 5001 (field=body, expected=str, actual=list)` and asserts `_source is None`. | Leaking BeautifulSoup `AttributeError`, fabricating source text, marking source acquired, or entering source textarea parsing rejects this local completion claim. | Forum post source reads | `tests/unit/test_forum_post.py` |
| R3 | `ForumPost.edit(...)` raises contextual `NoElementException` when the pre-save edit-form response returns a list-valued `body`, and no save request is sent. | `TestForumPostEdit.test_edit_malformed_form_response_body_type_includes_site_post_and_type_context` expects `Forum post edit form response body is malformed for site: test-site, post: 5001 (field=body, expected=str, actual=list)`, asserts no plain AMC save call, and leaves `_source is None`. | Leaking BeautifulSoup `AttributeError`, calling `saveEditPost`, updating local source/title state, or entering current-revision parsing rejects this local completion claim. | Forum post edit preflight | `tests/unit/test_forum_post.py` |
| R4 | The malformed-body-type diagnostics include only structural identifiers, field name, expected type, and observed type. | The focused regressions match the full message shapes using synthetic list-valued bodies. | Including raw response JSON, generated forum HTML, post source text, post titles, post content, credentials, local rollout paths, or account names rejects this local completion claim. | Forum post diagnostics | `src/wikidot/module/forum_post.py` |
| R5 | Existing forum-post behavior and adjacent forum behavior remain green. | The forum-post suite passed 68 tests, the adjacent forum category/thread/post/revision run passed 198 tests, and the full unit suite passed 897 tests. | Regressing missing-body diagnostics, retry exhaustion, skipped failed source retries, cache behavior, duplicate thread/post handling, pagination, parser contexts, source extraction, no-save behavior, replies, or adjacent forum workflows rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_post.py`; `tests/unit/test_forum_category.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_post_revision.py` |
| R6 | Repository quality gates pass in the local dependency environment. | `ruff`, `mypy`, full unit, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `6cedece fix(forum_post): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_thread_and_page_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued post-list body.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted -q` passed 4 tests.
- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_malformed_response_body_type_includes_site_post_and_type_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued source-form body.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_malformed_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_success tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_skips_failed_retry_response tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_direct_source_textarea_includes_context -q` passed 5 tests.
- RED: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_form_response_body_type_includes_site_post_and_type_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued edit-form body.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_raises_when_paginated_retry_is_exhausted tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_malformed_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_success tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_skips_failed_retry_response tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_form_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_form_response_body_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_raises_when_form_fetch_retry_is_exhausted -q` passed 12 tests.
- `uv run --extra test pytest tests/unit/test_forum_post.py -q` passed 68 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 198 tests.
- `uv run --extra test pytest tests/unit -q` passed 897 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- Forum post-list reads still request `forum/ForumViewThreadPostsModule` with the existing thread/page payloads.
- Forum post source reads still request `forum/sub/ForumEditPostFormModule` with the existing thread/post payloads.
- Forum post edit preflight still requests `forum/sub/ForumEditPostFormModule` before save with the existing thread/post payloads.
- Missing `body` fields still raise the existing not-found diagnostics from Issues 208, 209, and 210.
- Present non-string `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The post-list malformed-body-type message includes site, thread, page, `field=body`, expected type, and observed type.
- The source-form malformed-body-type message includes site, post, `field=body`, expected type, and observed type.
- The edit-form malformed-body-type message includes site, post, `field=body`, expected type, and observed type, and no save request or local state update occurs.
- The malformed-body-type messages do not include raw response JSON, generated forum HTML, post source text, post titles, post content, credentials, local rollout paths, private site data, or private account material.
- Existing retry-exhausted behavior, skipped failed source retries, cached post/source behavior, duplicate handling, pagination, parser diagnostics, source extraction, edit success behavior, no-save-on-malformed-form behavior, `ForumThread.posts`, and replies remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real forum response body, local rollout path, account material, private forum content, post source text, or generated forum HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose forum content. Mitigation: messages include only site/thread/page or site/post identifiers and type names, not raw generated HTML, source text, or post text.
- Risk: Edit preflight validation could accidentally allow a save attempt after malformed input. Mitigation: the public edit regression asserts the plain AMC save path is not called and local source remains unset.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Forum post-list, source-form, and edit-form HTML parser behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this forum-post change beyond post-list, source-form, and edit-form response boundaries.

## Upstream-Safe Motivation

Forum post-list, source extraction, and edit preflight are practical browser-free workflows for indexing, moderation, archival, migration, source inspection, and post-edit operations. If Wikidot returns a present non-string generated response body, wikidot.py should report the affected forum read path and type mismatch before BeautifulSoup internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failures showed list-valued post-list, source-form, and edit-form `body` values leaking BeautifulSoup `AttributeError`.
- Existing Issues 208, 209, and 210 covered missing `body` fields but intentionally left present malformed values as separate boundaries.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, and forum-thread reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated forum HTML, post source text, thread titles, post titles, post content, and private site data out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid forum post behavior while making malformed present response bodies actionable without retaining generated forum content or source text.
