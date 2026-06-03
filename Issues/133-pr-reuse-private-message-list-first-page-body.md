# PR Draft: Reuse Private Message List First-Page Body

## Summary

`PrivateMessageCollection._acquire()` already fetches the first inbox/sentbox list page before deciding whether more private-message pages exist. Before this fix, the first response body was decoded and parsed once to inspect pager targets, then decoded and parsed again when page 1 was processed for message ID extraction.

This fix keeps the parsed first-page HTML and reuses it for page 1 message-row extraction. Additional pages are still decoded only when their response is processed, and the existing pager filtering, message-row scoping, duplicate ID dedupe, detail delegation, and retry behavior remain unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), which established private-message acquisition as a rollout-backed performance and reliability surface. It also preserves the parser hardening from [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), and [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), and follows the response-body reuse pattern from [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md).

No upstream issue was filed from this local workspace.

## Changes

- Rename the first parsed private-message list page to `first_html` so its role is explicit.
- Use `first_html` for pager target discovery and for page 1 message ID extraction.
- Decode and parse response bodies for pages 2 and later only when those pages are processed.
- Add a focused regression proving the first list response's `json()` result is consumed once while still extracting message ID `123`.
- Preserve non-numeric pager handling, message-row pager filtering, nested message-row filtering, ID dedupe, paginated retry exhaustion behavior, and direct detail fetching.

## Type Of Change

- Performance improvement
- Response parsing reuse
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| The first private-message list response body must be reused between pager detection and page 1 message ID extraction. | `TestPrivateMessageCollection.test_acquire_reuses_first_page_body_for_message_ids` asserts `mock_response.json.call_count == 1` and that ID `123` reaches `from_ids(...)`. | The RED test failed before the fix because `mock_response.json.call_count` was `2`. |
| Existing structural pager and row filtering must remain intact. | The focused acquisition cluster passed 6 tests covering non-numeric pager targets, row pager markup, nested row markup, ID dedupe, and paginated retry exhaustion. | A regression that treats row-local pager markup as list pagination, accepts nested rows, duplicates IDs, or hides retry exhaustion rejects this local completion claim. |
| The private-message module remains behaviorally stable. | `uv run pytest tests/unit/test_private_message.py -q` passed 32 tests. | Any private-message parser, detail fetch, inbox/sentbox, or deletion regression rejects this local completion claim. |
| Adjacent client behavior remains stable. | `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 51 tests. | Client request shaping regressions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `b4b7878 perf(private_message): reuse first page list body`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_reuses_first_page_body_for_message_ids -q` failed before the fix because `mock_response.json.call_count` was `2`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_reuses_first_page_body_for_message_ids -q`
- `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_non_numeric_pager_targets tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_reuses_first_page_body_for_message_ids tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_message_row_pager_markup tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_ignores_nested_message_row_markup tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_paginated_retry_is_exhausted -q` passed 6 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 32 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 51 tests.
- `uv run pytest tests/unit -q` passed 688 tests.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run ruff format --check src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- The first private-message list response body is decoded once during successful inbox/sentbox acquisition.
- Page 1 message IDs are extracted from the already parsed first-page HTML.
- Additional paginated private-message list responses are still decoded and parsed when processed.
- Non-numeric pager labels are ignored when computing `max_page`.
- Pager-like markup inside message rows does not create extra pagination.
- Nested message rows are ignored.
- Duplicate message IDs are deduplicated while preserving first-seen order.
- Exhausted paginated retries still raise the existing `UnexpectedException`.
- Direct private-message detail fetch delegation remains unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message inbox and sentbox acquisition always begins with page 1, and page 1 is needed both for pagination discovery and for message ID extraction. Reusing the already parsed page removes avoidable JSON/body parsing work and one small failure surface without changing network behavior or caller-visible results. This is especially useful in retry-heavy or large-message workflows where the same acquisition path is used repeatedly.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed private-message drafts repeatedly identified inbox/sentbox list acquisition, direct detail fetches, retry exhaustion, duplicate IDs, and parser scoping as practical surfaces.
- Prior local response-body reuse work showed the same class of redundant response decoding in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved message contents out of upstream discussion.

## Additional Notes

This slice does not change the `pmessage` AMC action, inbox/sentbox module names, retry helper, page-number request construction, message detail parsing, message deletion, or message creation. It only reuses the first list page's already parsed HTML inside the same `_acquire()` call.
