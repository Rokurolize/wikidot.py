# PR Draft: Validate Forum Thread List Response Payloads

## Summary

`ForumThreadCollection.acquire_all_in_category(category)` reads category thread-list pages from `forum/ForumViewCategoryModule`, validates each generated response `body`, parses forum thread rows, and caches the resulting `ForumThreadCollection` on the category. The thread-list path already converted retry exhaustion, missing `body`, and present non-string `body` values into contextual wikidot.py exceptions, but it still assumed `response.json()` returned a mapping before calling `.get("body")`.

This change validates the decoded category thread-list response payload root before reading `body`. A non-mapping first-page or paginated payload now raises `NoElementException` with site, category, page, expected root type, and observed type. Existing missing-body and malformed-body diagnostics remain distinct, and malformed payloads do not seed `category._threads` or enter thread-list parsing.

## Related Issue

Builds on [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md) and [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md).

This is not a duplicate of Issue 214 because that draft covered mapping responses with missing `body` values for forum thread list/detail reads. It is not a duplicate of Issue 326 because that draft covered mapping responses whose present `body` value had the wrong type. This slice only covers category thread-list reads whose decoded payload root is not a mapping before `body` lookup.

No upstream issue was filed from this local workspace.

## Problem Statement

If `forum/ForumViewCategoryModule` returned a decoded payload such as a list, `ForumThreadCollection.acquire_all_in_category(category)` attempted `response.json().get("body")` and leaked raw `AttributeError: 'list' object has no attribute 'get'`. That failure omitted the affected site, category, and page and bypassed the existing wikidot.py response-shape diagnostics.

## Rollout Evidence

- The active rollout-backed audit has repeatedly found module response-boundary failures where `response.json()` is assumed to be a dictionary before field lookup.
- Recent local slices fixed the same non-mapping decoded-payload class for private-message list/detail reads, forum post revision lists, site member lists, forum category lists, site application lists, and direct page-file lists.
- Current source evidence before this slice still had `ForumThreadCollection._thread_list_response_body(...)` calling `response.json().get("body")`.
- Existing Issue 214 and Issue 326 established category thread-list `body` diagnostics as operationally useful, but neither covered non-mapping decoded payload roots.

## Affected Workflows

- `ForumThreadCollection.acquire_all_in_category(category)`
- `ForumCategory.threads`
- `ForumCategory.reload_threads()`
- Browser-free forum indexing, moderation, archive, migration, and generated fixture workflows that read category thread lists without retaining raw generated forum HTML.

## Proposed Fix

Decode each category thread-list response once, verify the decoded root is a dictionary, and raise `NoElementException` when it is not. Preserve the existing missing-body and present non-string body branches after the root-shape guard.

## Implementation Notes

- `src/wikidot/module/forum_thread.py` now checks the decoded thread-list response root in `_thread_list_response_body(...)` before reading `body`.
- The diagnostic includes only site unix name, category ID, page number, expected type, and observed type.
- `tests/unit/test_forum_thread.py` adds first-page and paginated list regressions using list-valued decoded payload roots.
- The change intentionally does not alter direct thread-detail reads; that remains a separate response helper and should be considered independently.
- Implemented locally in commit `515e2db fix(forum_thread): validate list response payload`.

## Tests And Verification

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_payload_type_includes_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'get'`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_payload_type_includes_context -q` passed 3 tests.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_first_page_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_body_type_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_first_page_response_payload_type_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_missing_paginated_response_body_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_paginated_response_payload_type_includes_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_pagination -q` passed 6 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 240 tests.
- `uv run pytest tests/unit -q` passed 3923 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests` passed with existing notes about unchecked untyped function bodies and the unused `pyproject.toml` lxml module section.
- `uv run pyright`.
- `git diff --check`.

## Compatibility And Risk Notes

- Successful category thread-list parsing remains unchanged for dictionary payloads with string `body`.
- Mapping payloads without `body` still raise the existing missing-body diagnostic.
- Mapping payloads with non-string `body` still raise the existing malformed-body diagnostic with `field=body`.
- Retry-exhausted `None` responses remain `UnexpectedException`.
- The guard rejects exotic mapping-like objects that are not `dict`, matching the response-boundary pattern already used in adjacent local slices.
- Diagnostics do not include raw response JSON, generated forum HTML, thread titles, descriptions, post content, credentials, local rollout paths, cookies, or account material.

## Rationale For Upstream Suitability

Category thread-list acquisition cannot safely parse generated forum HTML unless the AMC JSON root is a dictionary with a string `body`. Rejecting non-mapping roots at the response boundary gives maintainers and downstream operators a compact, actionable error while preserving existing successful behavior and avoiding disclosure of private generated forum content.

## Acceptance Criteria

- A first-page list-valued decoded category thread-list payload raises `NoElementException` matching `Forum thread list response payload is malformed for site: test-site, category: 1001, page: 1 (expected=dict, actual=list)`.
- A paginated list-valued decoded category thread-list payload raises the same diagnostic family with page `2`.
- Malformed payload roots do not seed `category._threads`.
- Existing missing-body and present non-string-body diagnostics remain distinct.
- Successful single-page and paginated category thread-list acquisition remain compatible.
- No live Wikidot action, upstream Issue, upstream PR, push, private forum content, raw generated HTML, or raw response JSON is required for this local draft.

## Local Evidence, Not For Upstream Paste

- Complexity scanning reported no obvious hotspots in `src/wikidot/module/forum_thread.py`; this slice is response-boundary hardening rather than a structural rewrite.
- Focused Brooks changed-file/docs review found no blocking findings; full Brooks auto-sweep was not run because it requires explicit full-repository auto-fix consent.
- Clawpatch provenance used local fork `d89ca91`, provider `codex`, doctor state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

