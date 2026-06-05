# PR Draft: Report Malformed Forum Post Revision Response Body Types

## Summary

`ForumPostRevisionCollection.acquire_all()` and `ForumPostRevisionCollection.acquire_all_for_posts()` parse `forum/sub/ForumPostRevisionsModule` response `body` values as generated revision-list HTML before extracting edit-history rows. Earlier local slices made this workflow retry-aware, duplicate-post-aware, duplicate-revision-aware for optional HTML acquisition, cached-revision-aware, parser-scoped, and context-rich for missing response bodies and malformed row metadata. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, both revision-list paths passed it directly to BeautifulSoup, leaking a low-level parser `AttributeError`.

This local slice validates present forum post revision-list response `body` values before BeautifulSoup parsing. Non-string bodies now raise `NoElementException` with site/post context plus `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw generated revision-list HTML, response JSON, forum post text, revision HTML, local rollout paths, credentials, account material, or private forum content.

## Outcome

Malformed forum post revision-list response body types now fail at the module response boundary with actionable site/post context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history inspection, moderation audit helpers, post-source review, or revision HTML collection workflows.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-user-context.md](284-pr-forum-post-revision-user-context.md), [285-pr-forum-post-revision-date-context.md](285-pr-forum-post-revision-date-context.md), and [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md). Those drafts established forum post revision acquisition as a practical retry-aware workflow with parser boundaries, duplicate handling, cached reuse, and site/post/revision diagnostics while leaving present non-string revision-list response bodies as a separate parser-entry boundary.

This also follows the response-body type diagnostic pattern from [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [323-pr-site-member-response-body-type-context.md](323-pr-site-member-response-body-type-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), and [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared forum post revision-list response-body helper for direct and batched acquisition paths.
- Preserve existing missing-body diagnostics from Issue 217.
- Validate present revision-list `body` values are strings before BeautifulSoup parsing.
- Convert present non-string revision-list body values into site/post-specific `NoElementException`.
- Preserve retry-exhausted behavior, cached direct revision-list reuse, duplicate post-ID deduplication, duplicate cached post revision copying, optional `with_html` behavior, duplicate revision-ID HTML grouping, successful row parsing, lazy revision HTML behavior, and adjacent forum workflows.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A direct revision-list response with a present non-string `body` field must fail before BeautifulSoup parsing. |
| R2 | A batched revision-list response with a present non-string `body` field must identify the affected post and fail before BeautifulSoup parsing. |
| R3 | Malformed-body-type errors must identify the affected site, post, `field=body`, expected type, and observed type while omitting raw generated forum content. |
| R4 | Existing missing-body diagnostics, retry handling, duplicate handling, cache behavior, optional HTML acquisition, lazy HTML behavior, and adjacent forum workflows must remain compatible. |
| R5 | Focused, module-level, adjacent forum, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumPostRevisionCollection.acquire_all(post)` raises contextual `NoElementException` when `forum/sub/ForumPostRevisionsModule` returns a list-valued `body`. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_malformed_response_body_type_includes_site_post_and_type_context` expects `Forum post revision list response body is malformed for site: test-site, post: 5001 (field=body, expected=str, actual=list)` and asserts `_revisions is None`. | Leaking low-level `AttributeError`, fabricating an empty revision list, caching a collection, or entering revision-row parsing rejects this local completion claim. | Direct revision-list reads | `tests/unit/test_forum_post_revision.py` |
| R2 | `ForumPostRevisionCollection.acquire_all_for_posts([...])` raises contextual `NoElementException` for the affected post when one batched response returns a list-valued `body`. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_malformed_response_body_type_includes_site_post_and_type_context` expects `Forum post revision list response body is malformed for site: test-site, post: 5002 (field=body, expected=str, actual=list)` and leaves both post caches unset. | Generic batch failure, wrong post ID, partial cache mutation, BeautifulSoup internals, or silent partial success rejects this local completion claim. | Batched revision-list reads | `tests/unit/test_forum_post_revision.py` |
| R3 | The malformed-body-type diagnostics include only structural identifiers, field name, expected type, and observed type. | The focused regressions match the full message shapes using synthetic list-valued bodies. | Including raw response JSON, generated revision-list HTML, post text, revision HTML, credentials, local rollout paths, or account names rejects this local completion claim. | Forum post revision diagnostics | `src/wikidot/module/forum_post_revision.py` |
| R4 | Existing forum post revision and adjacent forum behavior remain green. | The focused run passed 10 tests, the forum-post-revision suite passed 50 tests, the adjacent forum run passed 200 tests, and the full unit suite passed 901 tests. | Regressing missing-body diagnostics, retry exhaustion, duplicate post-ID grouping, cached duplicate reuse, optional HTML acquisition, duplicate revision-ID HTML grouping, row parsing, lazy HTML access, or category/thread/post workflows rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_post_revision.py` |
| R5 | Repository quality gates pass in the local dependency environment. | `ruff`, `mypy`, full unit, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e3ade79 fix(forum_post_revision): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_post_and_type_context -q` failed before the fix with `AttributeError` from BeautifulSoup for the list-valued direct revision-list body.
- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_malformed_response_body_type_includes_site_post_and_type_context -q` failed before the fix with `AttributeError` from BeautifulSoup for the list-valued batched revision-list body.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_malformed_response_body_type_includes_site_post_and_type_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_raises_when_retry_is_exhausted tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_missing_response_body_includes_site_and_post_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_malformed_response_body_type_includes_site_post_and_type_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_retries_transient_fetch_failures tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_deduplicates_duplicate_post_ids tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_raises_when_retry_is_exhausted tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_deduplicates_duplicate_revision_ids -q` passed 10 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed 50 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 200 tests.
- `uv run --extra test pytest tests/unit -q` passed 901 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all()` still requests `forum/sub/ForumPostRevisionsModule` with the existing post payload.
- `ForumPostRevisionCollection.acquire_all_for_posts()` still requests `forum/sub/ForumPostRevisionsModule` with the existing per-post payloads.
- Missing `body` fields still raise the existing not-found diagnostics from Issue 217.
- Present non-string direct revision-list `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- Present non-string batched revision-list `body` values raise contextual `NoElementException` before BeautifulSoup parsing.
- The malformed direct-body-type message includes site, post, `field=body`, expected type, and observed type.
- The malformed batched-body-type message includes site, affected post, `field=body`, expected type, and observed type.
- The malformed-body-type messages do not include raw response JSON, generated revision-list HTML, post text, revision HTML, credentials, local rollout paths, private forum content, or private account material.
- Existing retry-exhausted behavior, cached direct revision-list reuse, duplicate post-ID deduplication, duplicate cached post revision copying, optional `with_html` behavior, duplicate revision-ID HTML grouping, successful row parsing, lazy `ForumPostRevision.html`, and adjacent forum workflows remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real revision-list response body, local rollout path, account material, private forum content, post text, or generated revision-list HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated revision-list HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose forum content. Mitigation: messages include only site/post identifiers and type names, not raw generated HTML, post text, revision HTML, or response JSON.
- Risk: Batched acquisition could leave partial cache state on malformed later responses. Mitigation: the regression asserts both post caches remain unset after the malformed second response.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Forum post revision row parsing and optional revision HTML content handling remain unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this forum post revision change beyond revision-list response boundaries.

## Upstream-Safe Motivation

Forum post edit-history inspection is a practical browser-free workflow for moderation, review, and audit tooling. If Wikidot returns a present non-string generated response body, wikidot.py should report the affected post and type mismatch before parser internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failures showed list-valued direct and batched revision-list `body` values leaking low-level `AttributeError`.
- Existing Issue 217 covered missing forum post revision-list `body` fields but intentionally left present malformed values as separate boundaries.
- The recent response-body type series showed the same boundary pattern in private messages, forum categories, site members, site applications, direct page-file reads, forum-thread reads, forum-post reads, and page-revision reads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated revision-list HTML, revision HTML, post text, and private forum content out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid forum post revision-list behavior while making malformed present response bodies actionable without retaining generated forum content or revision HTML.
