# PR Draft: Surface Lazy Forum Post Revision HTML Fetch Failures

## Summary

`ForumPostRevisionCollection.get_htmls()` intentionally preserves partial batch successes: when `amc_request_with_retry(...)` returns `None` for one revision after exhausting retries, successful sibling revisions still receive their HTML and the failed revision remains uncached. Before this fix, the single-revision lazy property `ForumPostRevision.html` reused that batch helper but returned the still-uncached `None` value directly. That made a transient or exhausted retry failure look like a valid nullable property result even though the public property is the single-item read path.

This fix keeps batch behavior unchanged and adds an acquisition-aftercheck only to the lazy property. If the single forum post revision is still uncached after the retry-aware acquisition attempt, `html` raises `UnexpectedException("Cannot retrieve forum post revision HTML: ...")`.

## Related Issue

Builds on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), which made forum post revision list and HTML acquisition retry-aware, [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), which reused cached same-ID forum post revision HTML, and [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), which applied the same single-item failure-visibility rule to page revisions.

No upstream issue was filed from this local workspace.

## Changes

- Make `ForumPostRevision.html` return `str` and raise if retry-aware lazy acquisition leaves `_html` unset.
- Add a focused regression for an exhausted retry result from `revision.html`.
- Keep `ForumPostRevisionCollection.get_htmls()` partial-success semantics unchanged for batch callers.

## Type Of Change

- Bug fix
- Failure visibility improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Lazy `ForumPostRevision.html` must not return `None` after retry exhaustion. | `TestForumPostRevisionHtml.test_html_property_raises_when_retry_is_exhausted` asserts an `UnexpectedException` and verifies `forum/sub/ForumPostRevisionModule` uses `amc_request_with_retry(...)`. | The RED test failed before the fix because `html` returned `None` and did not raise. |
| Batch forum post revision HTML acquisition keeps partial-success behavior. | `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 39 tests, including existing failed-retry response and duplicate HTML tests. | A change that raises from `get_htmls()` on a single `None` batch response rejects this local completion claim. |
| Adjacent forum post revision workflows remain stable. | `uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py -q` passed 85 tests. | Regressions in revision-list acquisition, optional `with_html=True`, cached duplicate revision lists, forum post source, edit form, or lazy post revisions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `3f0ebc1 fix(forum_post_revision): surface lazy html fetch failures`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_raises_when_retry_is_exhausted -q` failed before the fix because `html` returned `None` and did not raise `UnexpectedException`.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 39 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py -q` passed 85 tests.
- `uv run pytest tests/unit -q` passed 711 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevision.html` performs its existing lazy retry-aware acquisition when `_html` is unset.
- `ForumPostRevision.html` raises `UnexpectedException` if `_html` remains unset after that acquisition attempt.
- Cached `html` values are returned unchanged without new AMC requests.
- `ForumPostRevisionCollection.get_htmls()` still preserves partial batch successes and leaves failed retry entries uncached.
- `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` behavior remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Forum post revision HTML is commonly read through the ergonomic single-item property after selecting a revision from a post's edit history. In that context, returning `None` after the retry-aware request path is misleading: callers asked for the revision's rendered HTML, and the library should surface that the remote read failed instead of handing back a value outside the property's useful contract. Batch helpers still retain the existing partial-success behavior for callers that explicitly process many revisions at once.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed forum drafts repeatedly identified forum post revision reads as practical read-heavy surfaces: retry-aware revision-list fetching, cached direct revision-list skipping, cached duplicate revision-list reuse, duplicate revision HTML reuse, optional `with_html=True`, and parser scoping.
- This slice came from comparing the hardened batch retry behavior with the still-nullable lazy property path and then proving the silent failure with a focused RED property test.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not change `ForumPostRevisionCollection.get_htmls()`, `acquire_all_for_posts(...)`, deduplication, response parsing, cache-copy behavior, retry policy, or batch partial-success behavior. It only makes the single-revision lazy property fail visibly when its own acquisition attempt did not populate the requested HTML.
