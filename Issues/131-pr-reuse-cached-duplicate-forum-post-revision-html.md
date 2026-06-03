# PR Draft: Reuse Cached Duplicate Forum Post Revision HTML

## Summary

`ForumPostRevisionCollection.get_htmls()` already skips revisions whose HTML is cached, and it already deduplicates uncached duplicate revision IDs before fetching `forum/sub/ForumPostRevisionModule`. Before this fix, a collection containing both a cached revision and an uncached duplicate with the same revision ID still fetched revision HTML for the uncached duplicate instead of reusing the cached HTML already present in the same collection.

This fix indexes cached revision HTML by revision ID, copies that HTML into uncached same-ID duplicates before building AMC requests, and only fetches revision IDs that remain unresolved. Public collection membership and ordering remain unchanged.

## Related Issue

Builds directly on [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), which established that duplicate forum post revision IDs should not trigger duplicate HTML requests. It also preserves retry-aware revision-list and HTML behavior from [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), optional `with_html=True` duplicate handling from [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), parser scoping from [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), and follows the cached duplicate reuse pattern from [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md) and [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md).

No upstream issue was filed from this local workspace.

## Changes

- Build a `revision.id -> html` map from already cached forum post revisions in the collection.
- Populate uncached duplicate revisions from that map before constructing `forum/sub/ForumPostRevisionModule` requests.
- Keep first-seen request order and existing uncached duplicate grouping for the remaining unresolved revision IDs.
- Add a focused regression where one duplicate forum post revision has cached HTML and another duplicate with the same revision ID is uncached.
- Preserve retry-aware HTML fetches, failed retry handling, duplicate uncached propagation, lazy `ForumPostRevision.html`, revision-list acquisition, forum post source behavior, edit behavior, reply behavior, and adjacent forum workflows.

## Type Of Change

- Performance/reliability improvement
- Cache behavior improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Cached HTML from a duplicate forum post revision ID must be reused within the same collection. | `TestForumPostRevisionCollectionGetHtmls.test_get_htmls_reuses_cached_duplicate_revision_html` asserts the uncached duplicate receives `<p>Cached revision HTML</p>`. | The RED test failed before the fix because the duplicate path attempted a new `ForumPostRevisionModule` fetch and hit `ValueError: zip() argument 2 is shorter than argument 1` with no returned response. |
| Reusing cached duplicate HTML must avoid unnecessary network work. | The same focused test asserts neither plain `amc_request(...)` nor retry-aware `amc_request_with_retry(...)` is called. | A regression that fetches HTML for the duplicate fails the not-called assertions. |
| Existing forum post revision HTML behavior remains intact. | `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls -q` passed 6 tests, and `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 33 tests. | Regressions in retry, exhausted retry, cached skipping, duplicate uncached propagation, optional HTML fetching, or lazy behavior reject this local completion claim. |
| Adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q` passed 132 tests. | Regressions in post parsing, post source fetching, edit behavior, thread parsing, category parsing, revision parsing, or replies reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `30c0b07 perf(forum_post_revision): reuse cached duplicate html`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_reuses_cached_duplicate_revision_html -q` failed before the fix because the uncached duplicate attempted a new revision HTML fetch instead of using the already cached HTML.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_reuses_cached_duplicate_revision_html -q`
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls -q` passed 6 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 33 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q` passed 132 tests.
- `uv run pytest tests/unit -q` passed 686 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- A cached HTML string on one forum post revision object is reused for uncached collection entries with the same revision ID.
- No AMC revision HTML request is sent when every uncached revision can be satisfied from cached duplicates in the same collection.
- Uncached duplicate revision IDs with no cached HTML still use the existing one-request-per-ID fetch path.
- Exhausted retry results still leave only unresolved revision IDs unacquired.
- Existing retry-aware HTML fetching, duplicate uncached grouping, lazy `ForumPostRevision.html`, `acquire_all(...)`, `acquire_all_for_posts(..., with_html=True)`, forum post parsing, source fetching, editing, replies, and adjacent forum workflows remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post revision HTML inspection is a read-heavy workflow for moderation, archiving, diffing, and audit tooling. If a caller holds multiple `ForumPostRevision` objects for the same revision ID and one already has HTML cached, fetching the same revision module again adds avoidable AMC work and another failure point. Reusing cached duplicate HTML keeps collection HTML acquisition consistent with the existing cached skip and duplicate-ID dedupe rules while preserving the caller-visible collection shape.

## Local Evidence, Not For Upstream Paste

- Existing local drafts established forum post revision reads as a practical rollout-backed surface for inspection, archiving, history comparison, and audit workflows.
- Issue 057 established duplicate forum post revision IDs as a realistic performance lead for HTML fetching, and Issue 058 applied the same one-request-per-ID rule to the optional `with_html=True` acquisition path.
- Issues 125 and 126 showed the same cached-duplicate reuse gap after request deduplication in adjacent forum post source and page revision source/HTML paths.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_post_revision.py` around revision acquisition as a worthwhile audit area.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved forum/page contents out of upstream discussion.

## Additional Notes

This slice does not change revision HTML request construction, retry policy, response parsing, duplicate uncached grouping, lazy property return types, revision-list acquisition, forum post source fetching, editing, replies, or mutation methods. It only lets already cached HTML satisfy duplicate uncached revision entries in the same collection before any revision HTML fetch request is built.
