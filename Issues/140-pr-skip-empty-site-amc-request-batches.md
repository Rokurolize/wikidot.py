# PR Draft: Skip Empty Site AMC Request Batches

## Summary

`Site.amc_request(...)` is the raw site-scoped Ajax Module Connector helper used before higher-level parsing, retry, and collection logic. Before this fix, calling it with an empty body list still looked up `client.amc_client` and invoked `client.amc_client.request(...)` even though no request body could be sent and the only possible stable result is an empty response tuple.

This fix returns `()` immediately for empty `bodies` for both `return_exceptions=False` and `return_exceptions=True`. Empty site AMC batches no longer require a configured AMC client, while non-empty delegation, positional arguments, site name forwarding, SSL forwarding, exception behavior, and overload return types remain unchanged.

## Related Issue

Builds on [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), which made empty direct URL batches no-op before setup work, and [139-pr-skip-empty-amc-retry-batches.md](139-pr-skip-empty-amc-retry-batches.md), which did the same for `Site.amc_request_with_retry(...)` after explicit retry option validation. This slice applies the same empty-batch rule to the lower-level public site AMC helper.

No upstream issue was filed from this local workspace.

## Changes

- Return `()` immediately when `Site.amc_request(...)` receives an empty `bodies` list.
- Preserve existing non-empty delegation to `client.amc_client.request(...)`.
- Add a parametrized regression covering both `return_exceptions=False` and `return_exceptions=True`.

## Type Of Change

- Performance improvement
- Empty-input fast path
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Empty raw site AMC batches must return an empty tuple without requiring `client.amc_client`. | `TestSiteAmcRequest.test_amc_request_empty_bodies_returns_empty_without_client_request` installs a client whose `amc_client` property raises and asserts empty calls return `()`. | The RED test failed before the fix because the empty path attempted to read `self.client.amc_client`. |
| The empty fast path must cover both `return_exceptions` modes. | The regression is parametrized over `False` and `True`, and calls both `site.amc_request([])` and `site.amc_request([], return_exceptions=True)`. | A fix that handles only the default path would still fail the `return_exceptions=True` case. |
| Non-empty AMC request delegation remains stable. | `TestSiteAmcRequest.test_amc_request_delegates_to_client` still verifies non-empty request forwarding, site name forwarding, and SSL forwarding. | Regressions in non-empty argument forwarding reject this local completion claim. |
| Site-level and broad unit/static quality gates remain green. | `uv run pytest tests/unit/test_site.py -q`; adjacent site/page/private-message/member/application tests; `uv run pytest tests/unit -q`; ruff; mypy; `git diff --check HEAD~1..HEAD`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4c650d1 perf(site): skip empty amc request batches`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteAmcRequest -q` failed before the fix with 2 empty-batch failures because both `return_exceptions` paths attempted to read `client.amc_client`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteAmcRequest -q` passed 5 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 64 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_private_message.py tests/unit/test_site_member.py tests/unit/test_site_application.py -q` passed 247 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_requestutil.py tests/unit/test_private_message.py tests/unit/test_page.py -q` passed 220 tests.
- `uv run pytest tests/unit -q` passed 704 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check HEAD~1..HEAD`

Not run: `uv run pyright` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `Site.amc_request([])` returns `()`.
- `Site.amc_request([], return_exceptions=True)` returns `()`.
- Empty `Site.amc_request(...)` calls do not read `client.amc_client` and do not call `client.amc_client.request(...)`.
- Non-empty calls still pass the original body list, `return_exceptions` flag, `site.unix_name`, and `site.ssl_supported` to the AMC client.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Empty AMC body lists can naturally arise after caller-side filtering, deduplication, optional follow-up selection, or future helper reuse. A raw public site AMC helper should make an empty request batch a cheap no-op rather than requiring a configured client and invoking lower-level request machinery. This keeps site-scoped AMC behavior aligned with the retry wrapper and direct URL batch helpers without changing any non-empty request behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts repeatedly hardened site-scoped AMC callers for page source collection, recent changes, member lists, applications, forum reads, metadata fetches, and duplicate/empty batch boundaries.
- Existing Issues 137 and 139 established empty request batches as practical, non-speculative no-op surfaces after filtering and deduplication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page/message/forum contents out of upstream discussion.

## Additional Notes

This slice does not change request body construction, request execution for non-empty inputs, retry behavior, response parsing, logging, exception conversion, or any higher-level collection API. It only avoids lower-level client access when the public helper already has enough information to determine the empty result.
