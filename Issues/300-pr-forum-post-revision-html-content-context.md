# PR Draft: Require Forum Post Revision HTML Content

## Summary

`ForumPostRevision.html`, `ForumPostRevisionCollection.get_htmls()`, and `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` fetch rendered forum post revision HTML through `forum/sub/ForumPostRevisionModule`. Earlier local slices made this read path retry-aware, deduplicated repeated revision IDs, reused cached duplicate HTML, surfaced lazy retry exhaustion, added site/post/revision lazy failure context, validated revision-list response bodies, cached direct revision-list acquisition, and preserved batch partial-success behavior for retry results that remain `None`. One malformed-response gap remained at the revision-HTML response boundary: when Wikidot returned a decoded response object without `content`, wikidot.py converted `data.get("content", "")` into an empty HTML string and marked the revision as acquired.

This follow-up keeps retry-exhausted `None` responses as skipped partial successes in batch acquisition, but treats an actual JSON response missing `content` or carrying `content=None` as malformed. It raises `NoElementException` with site unix name, post ID, revision ID, and `field=content` instead of caching empty HTML. Valid rendered HTML content, explicit empty-string content, duplicate revision-ID propagation, cached reads, request payloads, retry policy, revision-list parsing, and lazy exhausted-retry behavior remain unchanged.

## Outcome

Malformed forum post revision HTML module responses no longer masquerade as successfully acquired empty revision HTML.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who inspect forum edit history for rollback review, moderation, archival indexing, migration, diffing, or audit ledgers.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), and [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md). Those drafts established forum post revision history as a practical retry-aware, cache-aware, parser-scoped read path with contextual revision-list diagnostics and revision HTML acquisition ergonomics.

No upstream issue was filed from this local workspace.

## Changes

- Add a shared revision-HTML response helper that requires `content` to be present and non-`None`.
- Raise `NoElementException` with site unix name, post ID, revision ID, and `field=content` when a rendered revision HTML response is malformed.
- Apply the helper to both `ForumPostRevisionCollection.get_htmls()` and `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)`.
- Preserve retry-exhausted `None` response partial-success behavior.
- Preserve valid rendered HTML acquisition, cached duplicate HTML reuse, duplicate revision-ID propagation, lazy property retry behavior, request payloads, retry policy, and revision-list parsing.
- Add focused public regressions for lazy `ForumPostRevision.html` and eager `acquire_all_for_posts(..., with_html=True)` missing-content responses.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum post revision HTML response validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A decoded `ForumPostRevisionModule` response without `content` must not be cached as acquired empty HTML. |
| R2 | The malformed revision-HTML response error must identify site, post, revision, and `field=content`. |
| R3 | Lazy `ForumPostRevision.html` and eager `acquire_all_for_posts(..., with_html=True)` must share the same malformed-content contract. |
| R4 | Existing retry-exhausted `None` partial-success behavior, cached reads, duplicate revision-ID propagation, and valid HTML acquisition must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A response JSON object with no `content` does not set `_html` and does not let `revision.html` return an empty string. | `TestForumPostRevisionHtml.test_html_property_missing_response_content_includes_site_post_revision_and_field_context` returns `{}` from the HTML response and expects `NoElementException`. | Returning `""`, caching placeholder HTML, or marking the revision acquired rejects this local completion claim. | `ForumPostRevision.html` | `tests/unit/test_forum_post_revision.py` |
| R2 | The exception names site, post, revision, and `field=content`. | Both focused regressions assert `Forum post revision HTML response content is not found for site: test-site, post: 5001, revision: 9001, field=content`. | Omitting site, post, revision, or field makes the failure ambiguous and rejects this local completion claim. | Revision HTML diagnostics | `tests/unit/test_forum_post_revision.py` |
| R3 | Lazy and eager public acquisition paths reject malformed content consistently. | Focused GREEN includes the lazy property regression and `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_with_html_missing_response_content_includes_context`. | Fixing only the lazy path or only the eager batch path rejects this local completion claim. | `get_htmls()` and `acquire_all_for_posts(..., with_html=True)` | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing forum revision HTML workflows stay green. | `test_forum_post_revision.py` passed 48 tests and adjacent forum workflow tests passed 191 tests. | Regressing retry skipping for `None`, duplicate revision HTML dedupe, cached duplicate propagation, cached reads, valid HTML acquisition, or revision-list parsing rejects this local completion claim. | Forum revision workflows | `tests/unit/test_forum_post_revision.py`; `tests/unit/test_forum_post.py`; `tests/unit/test_forum_thread.py`; `tests/unit/test_forum_category.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `178db20 fix(forum_post_revision): require revision HTML content`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_missing_response_content_includes_site_post_revision_and_field_context -q` failed before the fix because no `NoElementException` was raised and the missing `content` response was accepted.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_missing_response_content_includes_site_post_revision_and_field_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_with_html_missing_response_content_includes_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed 48 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q` passed 191 tests.
- `uv run --extra test pytest tests/unit -q` passed 858 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevision.html` raises `NoElementException` when a fetched rendered revision HTML response lacks `content`.
- `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` raises the same contextual `NoElementException` for the same malformed response shape.
- The malformed-content exception includes the site unix name, post ID, revision ID, and `field=content`.
- The affected revision is not marked acquired after the malformed response.
- Retry-exhausted `None` responses in batch HTML acquisition still leave only the failed revision unacquired instead of raising from the batch helper.
- Valid `content` values still populate all matching duplicate revision IDs, and explicit empty-string `content` remains a valid acquired value.
- Existing revision-list parsing, response-body validation, malformed revision ID diagnostics, malformed timestamp diagnostics, malformed user diagnostics, cached revision-list reuse, optional `with_html=True`, duplicate HTML fetch deduplication, lazy exhausted-retry failure context, forum post source fetching, forum post editing, and thread/category workflows remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated revision HTML, forum post content, credentials, cookies, or local rollout paths are required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Raising for missing `content` could change batch partial-success semantics. Mitigation: the helper is used only after a non-`None` response exists; retry-exhausted `None` responses are still skipped as before.
- Risk: Empty rendered revision HTML might be a legitimate value for an empty post revision. Mitigation: the implementation rejects missing or `None` `content`, not an explicit empty string.
- Risk: A shared helper could over-broaden the change. Mitigation: the helper is local to forum post revision HTML responses and leaves revision-list response `body` parsing, shared parsers, and unrelated modules untouched.

## Dependencies

- `forum/sub/ForumPostRevisionModule` continues to represent rendered revision HTML in the `content` field.
- `amc_request_with_retry(...)` continues to use `None` for retry-exhausted batch items.
- The existing `NoElementException` family remains the local contract for malformed generated module response shapes.

## Open Questions

None for this local slice. The remaining forum post revision HTML behavior difference is intentional: retry-exhausted `None` responses preserve partial success, while malformed present response JSON now fails.

## Upstream-Safe Motivation

Forum post revision HTML is read when operators inspect edit history, compare revisions, preserve archival copies, or build moderation/audit ledgers. A generated module response that lacks `content` is not the same as a valid empty revision body; accepting it as empty HTML can hide a malformed response and make downstream ledgers think a revision was successfully acquired. Reporting the site, post, revision, and field gives enough context to triage without retaining raw response JSON, rendered HTML, forum content, credentials, or local rollout details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified forum post revision history and revision HTML as practical read-heavy surfaces: retry-aware acquisition, revision-list and revision-HTML deduplication, cached duplicate HTML reuse, optional `with_html=True`, lazy failure visibility, site/post/revision lazy context, response-body validation, cache-aware direct acquisition, and contextual revision-list parser diagnostics.
- The immediate RED failure showed a malformed present response with `{}` was accepted as successful empty HTML rather than a parser/response-boundary failure.
- The complexity scan still flags forum post revision collection loops and HTML batch paths as audit-worthy; this slice improves correctness at that hot read boundary without rewriting the batching algorithm.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML, post source text, post titles from real sites, and private forum content out of upstream discussion.

## Additional Notes

This is a response-shape validation fix. It does not change request construction, retry policy, revision ordering, revision-list parsing, shared user/date parsers, duplicate-ID semantics, cache invalidation, forum post source fetching, post editing, thread acquisition, category acquisition, or live Wikidot behavior.
