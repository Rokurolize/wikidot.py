# PR Draft: Validate Private Message List Response Bodies

## Summary

`PrivateMessageCollection._acquire(...)` powers both inbox and sent-box list reads through `dashboard/messages/DMInboxModule` and `dashboard/messages/DMSentModule`. Earlier local slices made private-message list reads retry-aware, reused the first page body, filtered row-local pager markup, ignored nested message rows, deduplicated message IDs before detail fetches, and added module/page/row context to list fetch and row parser failures. The remaining malformed response-body path still read `response.json()["body"]` for first and paginated list pages, so an AMC response without a `body` field leaked a raw `KeyError`.

This follow-up keeps login checks, request payloads, retry counts, pager handling, first-page body reuse, non-numeric pager behavior, nested-row filtering, row parser context, duplicate message-ID deduplication, detail fetch delegation, inbox/sent wrappers, and send behavior unchanged. It only treats a missing list response `body` as a malformed list response and raises `NoElementException` with module/page context before pager parsing, row parsing, or detail fetching.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), and [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md). Those drafts established private-message list/detail acquisition as retry-aware, parser-scoped, response-boundary-sensitive, and diagnosable without storing raw private-message HTML or message bodies.

No upstream issue was filed from this local workspace.

## Changes

- Add a small private-message list response-body helper that reads `response.json().get("body")`.
- Convert missing first-page list response `body` into module/page-specific `NoElementException`.
- Convert missing paginated list response `body` into module/page-specific `NoElementException`.
- Add focused regressions for first-page and paginated list response body handling.
- Preserve existing successful list parsing, pager behavior, duplicate-ID handling, and detail fetch delegation.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message list response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A first-page private-message list response without JSON `body` still fails before pager, row, or detail parsing. | `TestPrivateMessageCollection.test_acquire_missing_first_page_response_body_includes_module_and_page_context` returns `{}` from the first AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, fabricates an empty list, calls `from_ids(...)`, or parses rows rejects this local completion claim. |
| A paginated private-message list response without JSON `body` still fails before returning partial list output. | `TestPrivateMessageCollection.test_acquire_missing_paginated_response_body_includes_module_and_page_context` returns page 1 with a real pager and page 2 as `{}` and expects `NoElementException`. | A change that raises raw `KeyError`, returns only page 1 IDs, calls `from_ids(...)`, or silently skips page 2 rejects this local completion claim. |
| Malformed list response errors identify the affected module and page. | The focused regressions assert `Message list response body is not found for module: dashboard/messages/DMInboxModule, page: 1` and page `2`. | A generic parser exception without module/page context rejects this local completion claim. |
| Existing private-message list and detail behavior remains green. | `uv run pytest tests/unit/test_private_message.py -q` passed 36 tests. | Regressions in retry behavior, first-page body reuse, pager filtering, nested-row rejection, row parser context, duplicate-ID deduplication, detail response validation, inbox/sent wrappers, or send behavior reject this local completion claim. |
| Adjacent client/private-message workflows remain green. | `uv run pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed 55 tests. | Regressions in client private-message accessors or inbox/sent-box workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `3d29fdb fix(private_message): validate list response bodies`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_first_page_response_body_includes_module_and_page_context -q` failed before the first fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_first_page_response_body_includes_module_and_page_context -q`.
- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_paginated_response_body_includes_module_and_page_context -q` failed before the second fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_first_page_response_body_includes_module_and_page_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_paginated_response_body_includes_module_and_page_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_reuses_first_page_body_for_message_ids -q`.
- `uv run pytest tests/unit/test_private_message.py -q` passed 36 tests.
- `uv run pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed 55 tests.
- `uv run pytest tests/unit -q` passed 741 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)` still perform the existing login check.
- First-page list requests still use the same module-only AMC body.
- Paginated list requests still use `page=<n>` and the same module name after the first page discovers a real pager.
- Missing first-page list response JSON `body` raises `NoElementException` naming the module and page 1.
- Missing paginated list response JSON `body` raises `NoElementException` naming the module and affected page.
- Malformed list response-body handling does not call `PrivateMessageCollection.from_ids(...)` or return partial message IDs.
- Successful pager parsing, non-numeric pager handling, first-page body reuse, row parser context, row-pager filtering, nested-row rejection, duplicate message-ID deduplication, detail fetch delegation, inbox/sent wrappers, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message inbox and sent-box acquisition depend on Wikidot returning a JSON `body` field before list HTML parsing can start. If that field is missing on the first page or a later page, wikidot.py should report a structured malformed-response failure with the dashboard module and page number, so caller logs can route the failure without preserving raw response JSON, raw private-message HTML, message previews, message bodies, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established private-message list acquisition as retry-aware, page-aware, first-page-body-reusing, duplicate-ID-preserving, and protected from row-local pager or nested-row markup.
- The immediately prior detail-response slice showed the same raw `KeyError` failure mode at the direct detail response boundary.
- Recent context slices showed that compact module/page identifiers improve resumable ledgers without changing successful behavior or storing private message content.
- The refreshed complexity memo continues to list parser/source collection helpers as follow-up leads, but this slice only claims private-message list response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, raw private-message HTML, message previews, and message contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change login checks, request module names, retry policy, pager handling, first-page body reuse, non-numeric pager behavior, row parser context, row-pager filtering, nested-row rejection, duplicate message-ID deduplication, direct detail fetch behavior, inbox/sent wrappers, send behavior, or live Wikidot behavior. It only converts missing private-message list response `body` fields into module/page-context `NoElementException` failures before parser work.
