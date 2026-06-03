# PR Draft: Skip Empty RequestUtil URL Batches

## Summary

`RequestUtil.request(...)` is the shared retry-aware helper for direct GET/POST URL batches such as user profile lookups. Before this fix, calling it with an empty URL list still read `client.amc_client.config`, built a semaphore, prepared header helpers, and entered the coroutine execution path even though no HTTP request could be sent.

This fix validates the HTTP method first, then returns an empty result immediately when `urls` is empty. Empty GET/POST batches no longer require a fully configured client or event-loop execution, while invalid methods still raise `ValueError("Invalid method")` instead of being hidden by the empty input guard. Non-empty GET/POST retry behavior, header forwarding, status-code handling, timeout retry behavior, and `return_exceptions` behavior remain unchanged.

## Related Issue

Builds on [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md) and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), which established that empty public read batches should return empty collections without unnecessary request work. It also complements user/profile lookup hardening from [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), because `UserCollection.from_names(...)` reaches `RequestUtil.request(...)` for profile-page batches.

No upstream issue was filed from this local workspace.

## Changes

- Normalize and validate the HTTP method before any client configuration access.
- Return `[]` immediately for empty `urls` after method validation.
- Add focused regressions proving empty GET and POST batches return empty results without a configured client.
- Add a negative regression proving empty URL input still rejects unsupported methods.
- Preserve all non-empty request behavior.

## Type Of Change

- Performance improvement
- Empty-input fast path
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Empty GET URL batches must return an empty result without requiring client AMC configuration. | `TestRequestUtilEmpty.test_empty_get_urls_returns_empty_without_client_config` calls `RequestUtil.request(object(), "GET", [])` and asserts `[]`. | The RED test failed before the fix with `AttributeError: 'object' object has no attribute 'amc_client'`, proving the empty path still accessed client config. |
| Empty POST URL batches must follow the same no-work contract. | `TestRequestUtilEmpty.test_empty_post_urls_returns_empty_without_client_config` calls `RequestUtil.request(object(), "POST", [])` and asserts `[]`. | A regression that builds config/semaphore state before the empty guard fails on the unconfigured client object. |
| Empty URL batches must not hide unsupported HTTP methods. | `TestRequestUtilEmpty.test_empty_urls_still_validate_method` asserts `RequestUtil.request(object(), "DELETE", [])` raises `ValueError("Invalid method")`. | Returning `[]` before method validation would incorrectly accept unsupported methods. |
| Existing request behavior remains stable. | `uv run pytest tests/unit/test_requestutil.py -q` passed 17 tests; `uv run pytest tests/unit/test_user.py tests/unit/test_requestutil.py tests/unit/test_private_message.py -q` passed 65 tests. | Regressions in GET/POST success, client-header forwarding, retryable and non-retryable status handling, timeout retry, `return_exceptions`, user lookup, or private-message adjacency reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `c5f173c perf(requestutil): skip empty URL batches`.

- RED: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilEmpty::test_empty_get_urls_returns_empty_without_client_config -q` failed before the fix because `RequestUtil.request(...)` tried to read `client.amc_client.config` for an empty URL list.
- GREEN: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilEmpty::test_empty_get_urls_returns_empty_without_client_config -q`
- `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilEmpty -q` passed 3 empty-input tests.
- `uv run pytest tests/unit/test_requestutil.py -q` passed 17 tests.
- `uv run pytest tests/unit/test_user.py tests/unit/test_requestutil.py tests/unit/test_private_message.py -q` passed 65 tests.
- `uv run pytest tests/unit -q` passed 698 tests.
- `uv run ruff check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py`
- `uv run ruff format --check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `RequestUtil.request(client, "GET", [])` returns `[]` without requiring `client.amc_client.config`.
- `RequestUtil.request(client, "POST", [])` returns `[]` without requiring `client.amc_client.config`.
- Unsupported methods still raise `ValueError("Invalid method")` even when `urls` is empty.
- Non-empty GET/POST request behavior, retry behavior, header forwarding, timeout handling, and `return_exceptions` behavior remain unchanged.
- User/profile lookup and private-message adjacent suites remain green.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Empty batches naturally arise after caller-side filtering, deduplication, or optional work selection. A shared low-level request helper should make that no-op cheap and dependency-light, especially because higher-level callers may use empty inputs as a valid boundary condition. Returning before client configuration access avoids unnecessary setup and makes empty batch behavior consistent with the existing empty thread/private-message fetch fast paths.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts repeatedly improved empty direct read batches, duplicate fetch removal, and request helper behavior because practical Codex workflows often build request inputs from filtered page, message, thread, or user collections.
- Existing Issues 076 and 077 established the same empty-input rule for thread IDs and private message IDs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and message contents out of upstream discussion.

## Additional Notes

This slice does not change request retry limits, backoff, response parsing, header forwarding rules, HTTP client construction for non-empty inputs, or any high-level API return type. It only makes empty URL batches return their already-determined empty result before setup work that cannot affect an empty output.
