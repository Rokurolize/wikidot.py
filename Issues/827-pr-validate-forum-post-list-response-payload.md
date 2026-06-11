# PR Draft: Validate Forum Post List Response Payloads

## Summary

`ForumPostCollection.acquire_all_in_thread(thread)` and `ForumPostCollection.acquire_all_in_threads(threads)` read forum post-list pages from `forum/ForumViewThreadPostsModule`, validate each generated response `body`, parse post rows, and cache the resulting `ForumPostCollection` on each thread. The post-list path already converted retry exhaustion, missing `body`, present non-string `body`, pager issues, and malformed post rows into contextual wikidot.py exceptions, but it still assumed `response.json()` returned a mapping before calling `.get("body")`.

This change validates the decoded forum post-list response payload root before reading `body`. A non-mapping first-page or paginated payload now raises `NoElementException` with site, thread, page, expected root type, and observed type. Existing missing-body and malformed-body diagnostics remain distinct, and malformed payloads do not seed `thread._posts` or enter post-list parsing.

## Related Issue

Builds on [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), and [814-pr-validate-forum-post-edit-response-payload.md](814-pr-validate-forum-post-edit-response-payload.md).

This is not a duplicate of Issue 208 because that draft covered mapping responses with missing post-list `body` values. It is not a duplicate of Issue 327 because that draft covered mapping responses whose present post-list `body` value had the wrong type. It is not a duplicate of Issue 814 because that draft covered the edit mutation action response payload, not read-side post-list page payloads.

No upstream issue was filed from this local workspace.

## Problem Statement

If `forum/ForumViewThreadPostsModule` returned a decoded payload such as a list, `ForumPostCollection.acquire_all_in_thread(thread)` attempted `response.json().get("body")` and leaked raw `AttributeError: 'list' object has no attribute 'get'`. That failure omitted the affected site, thread, and page and bypassed the existing wikidot.py response-shape diagnostics.

## Rollout Evidence

- The active rollout-backed audit has repeatedly found module response-boundary failures where `response.json()` is assumed to be a dictionary before field lookup.
- Recent local slices fixed the same non-mapping decoded-payload class for private-message list/detail reads, forum post revision lists, site member lists, forum category lists, site application lists, direct page-file lists, and forum thread list/detail reads.
- Current source evidence before this slice still had `ForumPostCollection._post_list_response_body(...)` calling `response.json().get("body")`.
- Existing Issue 208 and Issue 327 established forum post-list `body` diagnostics as operationally useful, but neither covered non-mapping decoded payload roots.

## Affected Workflows

- `ForumPostCollection.acquire_all_in_thread(thread)`
- `ForumPostCollection.acquire_all_in_threads(threads)`
- `ForumThread.posts`
- Browser-free forum indexing, moderation, archive, migration, and generated fixture workflows that read post lists without retaining raw generated forum HTML.

## Proposed Fix

Decode each forum post-list response once, verify the decoded root is a dictionary, and raise `NoElementException` when it is not. Preserve the existing missing-body and present non-string body branches after the root-shape guard.

## Implementation Notes

- `src/wikidot/module/forum_post.py` now checks the decoded post-list response root in `_post_list_response_body(...)` before reading `body`.
- The diagnostic includes only site unix name, thread ID, page number, expected type, and observed type.
- `tests/unit/test_forum_post.py` adds first-page and paginated list regressions using list-valued decoded payload roots.
- The change intentionally does not alter forum post source-form reads or edit-form reads; those remain separate response helpers and should be considered independently.
- Implemented locally in commit `2a2152e fix(forum_post): validate list response payload`.

## Tests And Verification

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_payload_type_includes_thread_and_page_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'get'`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_payload_type_includes_thread_and_page_context -q` passed 3 tests.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_first_page_response_payload_type_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_malformed_paginated_response_payload_type_includes_thread_and_page_context tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_pagination -q` passed 6 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 300 tests.
- `uv run pytest tests/unit -q` passed 3926 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests` passed with existing notes about unchecked untyped function bodies and the unused `pyproject.toml` lxml module section.
- `uv run pyright`.
- `git diff --check`.

## Compatibility And Risk Notes

- Successful forum post-list parsing remains unchanged for dictionary payloads with string `body`.
- Mapping payloads without `body` still raise the existing missing-body diagnostic.
- Mapping payloads with non-string `body` still raise the existing malformed-body diagnostic with `field=body`.
- Retry-exhausted `None` responses remain `UnexpectedException`.
- Pager handling, cached thread post reuse, duplicate thread handling, post-row parser diagnostics, post source fetching, edit behavior, and reply behavior remain unchanged.
- The guard rejects exotic mapping-like objects that are not `dict`, matching the response-boundary pattern already used in adjacent local slices.
- Diagnostics do not include raw response JSON, generated forum HTML, post titles, post content, credentials, local rollout paths, cookies, or account material.

## Rationale For Upstream Suitability

Forum post-list acquisition cannot safely parse generated forum HTML unless the AMC JSON root is a dictionary with a string `body`. Rejecting non-mapping roots at the response boundary gives maintainers and downstream operators a compact, actionable error while preserving existing successful behavior and avoiding disclosure of private generated forum content.

## Acceptance Criteria

- A first-page list-valued decoded forum post-list payload raises `NoElementException` matching `Forum post list response payload is malformed for site: test-site, thread: 3001, page: 1 (expected=dict, actual=list)`.
- A paginated list-valued decoded forum post-list payload raises the same diagnostic family with page `2`.
- Malformed payload roots do not seed `thread._posts`.
- Existing missing-body and present non-string-body diagnostics remain distinct.
- Successful single-page and paginated post-list acquisition remain compatible.
- No live Wikidot action, upstream Issue, upstream PR, push, private forum content, raw generated HTML, or raw response JSON is required for this local draft.

## Local Evidence, Not For Upstream Paste

- Complexity scanning reported no obvious hotspots in `src/wikidot/module/forum_post.py`; this slice is response-boundary hardening rather than a structural rewrite.
- Focused Brooks changed-file/docs review found no blocking findings; full Brooks auto-sweep was not run because it requires explicit full-repository auto-fix consent.
- Clawpatch provenance used local fork `d89ca91`, provider `codex`, doctor state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

