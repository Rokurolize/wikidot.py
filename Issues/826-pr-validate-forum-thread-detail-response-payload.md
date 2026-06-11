# PR Draft: Validate Forum Thread Detail Response Payloads

## Summary

`ForumThreadCollection.acquire_from_thread_ids(site, thread_ids, category)` reads direct forum thread detail pages from `forum/ForumViewThreadModule`, validates the generated response `body`, parses thread metadata, and restores requested input order. The direct detail path already converted retry exhaustion, missing `body`, present non-string `body`, parser failures, and requested/parsed thread-ID mismatches into contextual wikidot.py exceptions, but it still assumed `response.json()` returned a mapping before calling `.get("body")`.

This change validates the decoded direct forum-thread detail response payload root before reading `body`. A non-mapping payload now raises `NoElementException` with site, thread ID, expected root type, and observed type. Existing missing-body and malformed-body diagnostics remain distinct, and malformed payloads do not enter BeautifulSoup parsing or thread construction.

## Related Issue

Builds on [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), and [825-pr-validate-forum-thread-list-response-payload.md](825-pr-validate-forum-thread-list-response-payload.md).

This is not a duplicate of Issue 214 because that draft covered mapping responses with missing `body` values for forum thread list/detail reads. It is not a duplicate of Issue 326 because that draft covered mapping responses whose present `body` value had the wrong type. It is not a duplicate of Issue 825 because that draft covered category thread-list responses, not direct thread-detail responses.

No upstream issue was filed from this local workspace.

## Problem Statement

If `forum/ForumViewThreadModule` returned a decoded payload such as a list, `ForumThreadCollection.acquire_from_thread_ids(site, [thread_id])` attempted `response.json().get("body")` and leaked raw `AttributeError: 'list' object has no attribute 'get'`. That failure omitted the affected site and thread ID and bypassed the existing wikidot.py response-shape diagnostics.

## Rollout Evidence

- The active rollout-backed audit has repeatedly found module response-boundary failures where `response.json()` is assumed to be a dictionary before field lookup.
- Recent local slices fixed the same non-mapping decoded-payload class for private-message list/detail reads, forum post revision lists, site member lists, forum category lists, site application lists, direct page-file lists, and forum thread-list reads.
- Current source evidence before this slice still had `ForumThreadCollection._thread_detail_response_body(...)` calling `response.json().get("body")`.
- Existing Issue 214 and Issue 326 established direct forum-thread detail `body` diagnostics as operationally useful, but neither covered non-mapping decoded payload roots.

## Affected Workflows

- `ForumThreadCollection.acquire_from_thread_ids(site, thread_ids, category)`
- `Site.get_thread(...)`
- `Site.get_threads(...)`
- `ForumThread.get_from_id(...)`
- Browser-free forum indexing, moderation, archive, migration, and generated fixture workflows that fetch direct thread details without retaining raw generated forum HTML.

## Proposed Fix

Decode each direct thread-detail response once, verify the decoded root is a dictionary, and raise `NoElementException` when it is not. Preserve the existing missing-body and present non-string body branches after the root-shape guard.

## Implementation Notes

- `src/wikidot/module/forum_thread.py` now checks the decoded direct thread-detail response root in `_thread_detail_response_body(...)` before reading `body`.
- The diagnostic includes only site unix name, thread ID, expected type, and observed type.
- `tests/unit/test_forum_thread.py` adds a direct acquisition regression using a list-valued decoded payload root.
- The change intentionally does not alter category thread-list reads; those were handled separately in Issue 825.
- Implemented locally in commit `64bf9e5 fix(forum_thread): validate detail response payload`.

## Tests And Verification

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_response_payload_type_includes_thread_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'get'`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_missing_response_body_includes_thread_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_response_body_type_includes_thread_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_response_payload_type_includes_thread_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_raises_when_retry_is_exhausted -q` passed 5 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 241 tests.
- `uv run pytest tests/unit -q` passed 3924 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests` passed with existing notes about unchecked untyped function bodies and the unused `pyproject.toml` lxml module section.
- `uv run pyright`.
- `git diff --check`.

## Compatibility And Risk Notes

- Successful direct thread-detail parsing remains unchanged for dictionary payloads with string `body`.
- Mapping payloads without `body` still raise the existing missing-body diagnostic.
- Mapping payloads with non-string `body` still raise the existing malformed-body diagnostic with `field=body`.
- Retry-exhausted `None` responses remain `UnexpectedException`.
- Duplicate thread-ID deduplication, requested input order restoration, requested/parsed thread-ID mismatch detection, post-count parsing, user/timestamp diagnostics, and optional category attachment remain unchanged.
- The guard rejects exotic mapping-like objects that are not `dict`, matching the response-boundary pattern already used in adjacent local slices.
- Diagnostics do not include raw response JSON, generated forum HTML, thread titles, descriptions, post content, credentials, local rollout paths, cookies, or account material.

## Rationale For Upstream Suitability

Direct forum-thread detail acquisition cannot safely parse generated forum HTML unless the AMC JSON root is a dictionary with a string `body`. Rejecting non-mapping roots at the response boundary gives maintainers and downstream operators a compact, actionable error while preserving existing successful behavior and avoiding disclosure of private generated forum content.

## Acceptance Criteria

- A list-valued decoded direct forum-thread detail payload raises `NoElementException` matching `Forum thread detail response payload is malformed for site: test-site, thread: 3001 (expected=dict, actual=list)`.
- Existing missing-body and present non-string-body diagnostics remain distinct.
- Successful direct thread-detail acquisition, retry-exhausted handling, duplicate ID deduplication, input-order restoration, parser diagnostics, and requested/parsed thread-ID mismatch checks remain compatible.
- No live Wikidot action, upstream Issue, upstream PR, push, private forum content, raw generated HTML, or raw response JSON is required for this local draft.

## Local Evidence, Not For Upstream Paste

- Complexity scanning reported no obvious hotspots in `src/wikidot/module/forum_thread.py`; this slice is response-boundary hardening rather than a structural rewrite.
- Focused Brooks changed-file/docs review found no blocking findings; full Brooks auto-sweep was not run because it requires explicit full-repository auto-fix consent.
- Clawpatch provenance used local fork `d89ca91`, provider `codex`, doctor state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

