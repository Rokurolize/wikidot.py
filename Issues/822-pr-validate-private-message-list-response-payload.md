# PR Draft: Validate Private Message List Response Payloads

## Summary

`PrivateMessageCollection._acquire(...)` uses the shared private-message list response helper for both inbox and sent-box reads. The helper already converted missing `body` fields and present non-string `body` values into contextual `NoElementException` diagnostics, but it still assumed `response.json()` returned a mapping before calling `.get("body")`.

This change validates the decoded response payload root before reading `body`. A non-mapping private-message list payload now raises `NoElementException` with the dashboard module name, page number, expected root type, and observed type. Existing missing-body and malformed-body diagnostics remain distinct, and no raw response JSON, private-message HTML, previews, subjects, bodies, credentials, cookies, auth JSON, local rollout paths, or account material is included.

## Related Issue

Builds on [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md) and [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md).

This is not a duplicate of Issue 207 because that draft covered mapping responses with missing `body`. It is not a duplicate of Issue 321 because that draft covered mapping responses whose present `body` value had the wrong type. This slice covers a malformed decoded payload root such as `["not", "a", "mapping"]`, which previously failed before the existing body-field checks.

No upstream issue was filed from this local workspace.

## Changes

- Validate that the private-message list response payload returned by `response.json()` is a mapping before reading `body`.
- Raise module/page-specific `NoElementException` for non-mapping payload roots.
- Add a focused inbox acquisition regression for a list-valued payload root.
- Preserve existing missing-body, non-string-body, pager, row parser, retry, detail-fetch, inbox/sent wrapper, and send behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message list response payload validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A non-mapping first-page private-message list response payload fails before body extraction, pager parsing, row parsing, or detail fetching. | `TestPrivateMessageCollection.test_acquire_malformed_first_page_response_payload_type_includes_module_page_and_type_context` returns `["not", "a", "mapping"]` from the first AMC response and expects `NoElementException`. | Leaking `AttributeError`, fabricating an empty list, parsing rows, calling `from_ids(...)`, or omitting module/page/type context rejects this local completion claim. |
| Existing missing-body and malformed-body diagnostics remain distinct. | Focused GREEN included `test_acquire_missing_first_page_response_body_includes_module_and_page_context` and `test_acquire_malformed_first_page_response_body_type_includes_module_page_and_type_context`. | Reclassifying `{}` or `{"body": 123}` as a payload-root error, dropping `field=body`, or changing the existing messages rejects this local completion claim. |
| Existing private-message behavior remains compatible. | `uv run pytest tests/unit/test_private_message.py -q` passed 181 tests. | Regressing login checks, retry behavior, first-page body reuse, pager filtering, row parser context, nested-row handling, duplicate-ID deduplication, detail fetches, inbox/sent wrappers, collection behavior, or send behavior rejects this local completion claim. |
| Broad unit and static gates remain green. | `uv run pytest tests/unit -q` passed 3919 tests; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `uv run pyright`; `git diff --check`. | Any failed unit, lint, format, type, pyright, or whitespace gate rejects this local completion claim. |
| Diagnostics remain privacy-preserving. | The new message includes only module name, page number, expected root type, and observed type. | Including raw response JSON, generated private-message HTML, message previews, message subjects, message bodies, credentials, cookies, auth JSON, local rollout paths, account material, or private site data rejects this local completion claim. |

## Testing

Implemented locally in commit `4d78b03 fix(private_message): validate list response payload`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_first_page_response_payload_type_includes_module_page_and_type_context -q` failed before the fix with `AttributeError: 'list' object has no attribute 'get'`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_first_page_response_body_includes_module_and_page_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_first_page_response_body_type_includes_module_page_and_type_context tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_first_page_response_payload_type_includes_module_page_and_type_context -q` passed 3 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 181 tests.
- `uv run pytest tests/unit -q` passed 3919 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests` passed with existing notes about unchecked untyped function bodies and the unused `pyproject.toml` lxml module section.
- `uv run pyright`.
- `git diff --check`.

## Acceptance Criteria

- `PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)` still use the same shared list acquisition path and login checks.
- A list-valued decoded response payload for a private-message list page raises `NoElementException` matching `Message list response payload is malformed for module: dashboard/messages/DMInboxModule, page: 1 (expected=dict, actual=list)`.
- Mapping payloads without `body` still raise the existing missing-body message.
- Mapping payloads with non-string `body` still raise the existing malformed-body message with `field=body`, `expected=str`, and the observed body type.
- Successful list parsing, retry handling, pager behavior, first-page body reuse, row parser context, row-pager filtering, nested-row handling, duplicate-ID deduplication, detail fetch delegation, inbox/sent wrappers, collection behavior, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message list acquisition cannot safely parse list pages unless the AMC JSON root is a mapping with a `body` field. Rejecting non-mapping roots at the response boundary keeps caller diagnostics compact and actionable while avoiding raw private-message content or response payload disclosure.

## Local Evidence, Not For Upstream Paste

- Issue 207 established missing private-message list body context.
- Issue 321 established present non-string private-message list body context.
- The immediately prior response-payload series applied the same boundary distinction to site applications, forum categories, site members, and forum post revisions.
- Complexity scanning reported no obvious hotspots in `src/wikidot/module/private_message.py`; this slice did not introduce a new abstraction or alter acquisition control flow.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw response JSON, private-message HTML, message previews, subjects, bodies, and private site content out of upstream discussion.

## Additional Notes

This slice intentionally does not change login checks, request payloads, retry policy, first-page body reuse, pager parsing, row parsing, detail fetch behavior, inbox/sent wrappers, collection APIs, send behavior, live Wikidot behavior, or upstream filing state. It only validates the decoded private-message list response payload root before the existing `body` validation.
