# PR Draft: Scope WhoRated Vote Parsing

## Summary

`PageCollection._acquire_page_votes(...)` parses `pagerate/WhoRatedPageModule` responses and builds `PageVoteCollection` objects for each page.

Before this fix, the parser selected every descendant `span.printuser` and every descendant `span[style^='color']` in the entire response body, then paired those lists by index. If the module response contained an unrelated colored span outside the actual vote list, such as heading or surrounding decoration markup, the parser treated it as a vote value. That could raise `UnexpectedException("User and value count mismatch")` even though the real vote list was valid.

This fix keeps the existing page vote API, batched request shape, retry path, duplicate-page propagation, and value conversion behavior, but scopes vote parsing to direct child spans of the WhoRated column-count list container. Surrounding markup no longer participates in vote/user pairing.

## Related Issue

Builds on [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md) and [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), because those drafts established page vote acquisition as a practical page-detail path. The parser-boundary motivation follows [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), and [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md).

No upstream issue was filed from this local workspace.

## Changes

- Find the WhoRated vote list container by the generated column-count `div`.
- Parse direct child `span.printuser` elements from that container as voters.
- Parse direct child colored `span` elements from that container as vote values.
- Ignore colored spans in headings or surrounding response markup.
- Preserve existing mismatch detection for malformed structural vote lists.
- Add a regression where a non-vote colored span appears outside the vote list and the page still receives `[1, 1, -1]` votes.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Vote values should come from the generated WhoRated vote list, not arbitrary colored spans in the response body. | `TestPageCollectionAcquire.test_acquire_votes_ignores_non_vote_colored_spans` asserts a surrounding `<span style="color:#777">decorative</span>` is ignored while the real votes parse as `[1, 1, -1]`. | The RED test failed before the fix with `UnexpectedException("User and value count mismatch")`. |
| Existing page vote acquisition behavior should remain green. | `uv run pytest tests/unit/test_page.py -q` passed 96 tests. | Regressions in vote success, missing-ID batching, cached-vote skipping, duplicate page-id propagation, source/revision/file acquisition, or other page behavior reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `bb2f8d1 fix(page): scope who-rated vote parsing`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_ignores_non_vote_colored_spans -q` failed before the fix with `UnexpectedException("User and value count mismatch")`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_ignores_non_vote_colored_spans -q`
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_success -q`
- `uv run pytest tests/unit/test_page.py -q` passed 96 tests.
- `uv run pytest tests/unit -q` passed 645 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- WhoRated parser scopes voters and vote values to the generated vote list container.
- Colored spans outside the vote list cannot create count mismatches or shift parsed vote values.
- Malformed structural vote lists with mismatched direct voter/value counts still raise `UnexpectedException`.
- Missing vote-list containers continue to produce an empty vote collection rather than interpreting unrelated response markup as votes.
- Existing batched request, retry, duplicate-page propagation, and `PageVoteCollection` behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

WhoRated is a page-detail read path and is commonly used alongside page revisions and files when callers hydrate page metadata. The parser should trust the generated vote-list structure, not every colored span in the AMC response. Scoping to the direct children of the generated column-count list makes the parser robust against surrounding markup while preserving the current public API.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records practical page-detail hydration work, including vote-list acquisition hardening in [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md).
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md) through [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md) established the concrete failure pattern: response-wide descendant selectors can confuse generated module structure with surrounding or authored markup.
- The refreshed complexity scan continues to flag `src/wikidot/module/page.py` detail-acquisition parsers as audit-worthy shared paths.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and page content out of upstream discussion.

## Additional Notes

This slice does not change page-id acquisition, retry policy, request batching, duplicate page-id propagation, `PageVote`, or `PageVoteCollection`. It only narrows vote/user element discovery to the generated WhoRated list container.
