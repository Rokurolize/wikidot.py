# PR: Validate private-message retry response counts

## Summary

`PrivateMessageCollection._amc_request_with_retry(...)` expects `client.amc_client.request(..., return_exceptions=True)` to return one result for each requested body. Before this change, a lower-level connector, mock, or adapter that returned too few retry results could leave the helper with stale failures and later raise an unrelated raw exception instead of reporting the broken request/result contract.

This change validates the result count after the initial private-message AMC batch request and after each retry request. A mismatch now raises `UnexpectedException("Private message retry response count mismatch ...")` with expected count, actual count, batch start, and attempt number. Existing valid retry behavior, exhausted retry diagnostics, no-message permission mapping, list/detail parsing, inbox/sent wrappers, and send behavior remain unchanged.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 397, which validates private-message retry control inputs such as `retry_batch_size` and `retry_max_retries`. This slice validates the lower-level response arity contract after a valid request has been issued.

This is distinct from local Issues 822 and 823, which validate decoded private-message list/detail response payload roots before reading `body`. This slice validates the count of returned AMC result objects before any per-message payload parsing can begin.

## Problem Statement

Private-message reads use a custom retry helper so transient detail/list failures can be retried while forbidden `no_message` responses retain their existing mapping. The helper indexed retry responses by position against the prior failed request indices, but it did not first confirm that the retry response sequence had the same length as the failed request slice.

That meant a malformed retry result such as one response for two failed message detail requests could leave one stale exception in `batch_results`. The public `from_ids(...)` path then raised the stale raw `RuntimeError` for the second message instead of a deterministic private-message retry contract error.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify private-message reads as practical authenticated dashboard surfaces. Existing drafts covered retry-aware private-message fetching, deduplication, empty fetch batches, retry control validation, message ID validation, list/detail response payload validation, and parser diagnostics. They did not validate that each private-message AMC request attempt returned one result per request body.

The local fix is committed as `03e5c2f`.

## Affected Workflows

- `PrivateMessageCollection.from_ids(...)` when transient message detail fetches are retried.
- `PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)` when list page fetches or detail fetches are retried.
- Tests, stubs, generated adapters, or connector changes that return malformed result sequences from `amc_client.request(..., return_exceptions=True)`.

## Proposed Fix

Add a small private-message retry response-count guard. Validate that each initial batch response and each retry response is a list or tuple with the expected number of entries before indexing it against request-body positions. Raise `UnexpectedException` with compact batch context if the contract is violated.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_mismatched_retry_response_count_includes_batch_context -q --tb=short
uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_mismatched_retry_response_count_includes_batch_context -q
uv run pytest tests/unit/test_private_message.py -q
uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_amc_client.py -q --tb=short
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright src tests
git diff --check
```

The focused RED run failed before the fix with raw `RuntimeError: temporary-2` from the stale second failed result. The focused GREEN run passed after adding the count guard. Full unit verification passed 3958 tests, ruff and pyright were clean, mypy reported only existing untyped-function notes with no issues, and whitespace checks passed.

## Acceptance Criteria

- A retry response sequence with fewer entries than the failed request slice raises `UnexpectedException` with expected count, actual count, batch start, and retry attempt.
- Initial batch response sequences are also validated before per-result retry classification.
- Valid private-message retry behavior still retries transient failures, preserves `no_message` permission mapping, and returns parsed messages in requested order.
- Existing private-message list/detail parsing, inbox/sent wrappers, client/AMC adjacent behavior, and send behavior remain green.
- The diagnostic does not include raw private-message bodies, subjects, recipients, raw response JSON, credentials, cookies, auth JSON, local rollout paths, or account material.

## Scope

This slice does not change retry policy, retry control validation, request body construction, response payload parsing, forbidden/no-message mapping, message ID validation, inbox/sent wrapper APIs, private-message send behavior, raw AMC behavior, live Wikidot behavior, or upstream filing state.

## Upstream-Safe Motivation

Private-message retry handling relies on positional correspondence between requested AMC bodies and returned results. When that correspondence is broken, wikidot.py should report the contract failure directly instead of letting stale exceptions or positional indexing artifacts escape through unrelated message-detail paths.
