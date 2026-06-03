# PR Draft: Reuse AsyncClient In RequestUtil URL Batches

## Summary

`RequestUtil.request(...)` is the shared retry-aware helper for direct GET/POST URL batches such as user profile lookups and direct page-ID lookups. Before this fix, each URL attempt opened its own `httpx.AsyncClient`, so a two-URL successful batch created two clients and larger batches created one client per URL before considering retries.

This fix creates one `httpx.AsyncClient` for the non-empty `RequestUtil.request(...)` call and passes it to every concurrent GET or POST task in that batch. Retry limits, backoff timing, semaphore concurrency, per-URL Wikidot header forwarding, non-retryable 4xx behavior, timeout/network retry behavior, `return_exceptions`, empty-input fast path, and public return types remain unchanged.

## Related Issue

Builds on [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), which made empty URL batches return before setup work. It also complements [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), because `UserCollection.from_names(...)` reaches `RequestUtil.request(...)` for profile-page batches, and [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md) plus [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), which reduced direct page-ID GET inputs before they reach the same helper.

No upstream issue was filed from this local workspace.

## Changes

- Move `httpx.AsyncClient(timeout=config.request_timeout)` construction from each `_get(...)` or `_post(...)` attempt into the `_execute(...)` batch scope.
- Pass the shared async client into every per-URL GET/POST coroutine.
- Keep each URL's retry loop, semaphore boundary, header selection, and final response/exception normalization unchanged.
- Add a focused regression proving a multi-URL GET/POST batch constructs exactly one async client per `RequestUtil.request(...)` call.

## Type Of Change

- Performance improvement
- Constant-factor request batching cleanup
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A multi-URL GET batch must create one async HTTP client for the batch, not one per URL. | `TestRequestUtilClientReuse.test_batch_reuses_one_async_client[GET]` monkeypatches `wikidot.util.requestutil.httpx.AsyncClient`, sends two GET URLs, and asserts one client instance. | The first RED test failed before the fix with `assert 2 == 1`, proving the old path created one client per URL. |
| A multi-URL POST batch must follow the same one-client-per-batch behavior. | `TestRequestUtilClientReuse.test_batch_reuses_one_async_client[POST]` sends two POST URLs through the same patched client counter. | A regression that keeps POST constructing clients per URL fails the same one-instance assertion. |
| Existing GET/POST request behavior remains stable. | `uv run pytest tests/unit/test_requestutil.py -q` passed 19 tests. | Regressions in GET/POST success, client-header forwarding, retryable and non-retryable status handling, timeout retry, `return_exceptions`, empty-input validation, or invalid-method handling reject this local completion claim. |
| User/profile and direct page-ID adjacent workflows remain green. | `uv run pytest tests/unit/test_user.py tests/unit/test_requestutil.py tests/unit/test_page.py -q` passed 140 tests. | Regressions in user lookup, RequestUtil URL batching, page ID acquisition, source/revision/vote/file acquisition, or page publish-adjacent paths reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `8923c94 perf(requestutil): reuse async client per batch`.

- RED: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilClientReuse::test_get_batch_reuses_one_async_client -q` failed before the fix because two GET URLs created two `AsyncClient` instances.
- GREEN: `uv run pytest tests/unit/test_requestutil.py::TestRequestUtilClientReuse -q`
- `uv run pytest tests/unit/test_requestutil.py -q` passed 19 tests.
- `uv run pytest tests/unit/test_user.py tests/unit/test_requestutil.py tests/unit/test_page.py -q` passed 140 tests.
- `uv run pytest tests/unit -q` passed 700 tests.
- `uv run ruff check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py`
- `uv run ruff format --check src/wikidot/util/requestutil.py tests/unit/test_requestutil.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `RequestUtil.request(client, "GET", [url1, url2, ...])` creates one `httpx.AsyncClient` for the request call and reuses it for every URL coroutine.
- `RequestUtil.request(client, "POST", [url1, url2, ...])` follows the same one-client-per-call behavior.
- Empty URL batches still return `[]` before client setup after method validation.
- Unsupported methods still raise `ValueError("Invalid method")`.
- Non-empty GET/POST retry behavior, per-URL Wikidot header forwarding, timeout handling, 4xx handling, and `return_exceptions` behavior remain unchanged.
- User/profile lookup and page direct-GET adjacent suites remain green.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Direct URL batches are read-heavy helpers. Creating a new `AsyncClient` per URL loses the benefit of a reusable client context and adds avoidable connection-pool and object setup overhead to profile/page-ID lookup batches. A single client per helper call matches the existing `AjaxModuleConnectorClient.request(...)` shape, keeps retry and concurrency behavior local to each request, and improves the constant factor without changing public APIs.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts repeatedly improved duplicate direct GET inputs, empty request batches, user/profile parsing, and page-ID acquisition because practical Codex workflows build user and page queues from filtered rollout evidence.
- Existing Issues 066, 120, 132, and 137 established `RequestUtil.request(...)` as a shared direct-read helper worth hardening.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and message contents out of upstream discussion.

## Additional Notes

This slice does not change request batching inputs, response parsing, retry limits, backoff calculation, semaphore concurrency, header forwarding rules, empty-input behavior, invalid-method behavior, or high-level API return types. It only scopes the non-empty batch's `AsyncClient` to the whole `RequestUtil.request(...)` call instead of each individual URL attempt.
