# PR Draft: Skip Empty AMC Retry Batches

## Summary

`Site.amc_request_with_retry(...)` is the shared retry-aware Ajax Module Connector helper used by page search/source collection, recent changes, member lists, applications, forum reads, page metadata reads, and other site-scoped read paths. Before this fix, calling it with an empty body list still read `self.client.amc_client.config` and validated default retry settings even though no AMC request could be sent.

This fix returns `()` immediately for empty `bodies` after validating any explicitly supplied `batch_size` or `max_retries` arguments. Empty retry batches no longer require a configured AMC client or config object, while explicitly invalid options still raise the same `ValueError` shape. Non-empty batching, retry, logging, exception-to-`None` conversion, response ordering, and public return types remain unchanged.

## Related Issue

Builds on [137-pr-skip-empty-requestutil-url-batches.md](137-pr-skip-empty-requestutil-url-batches.md), which made empty direct URL batches no-op before setup work. It also complements [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md) and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), which established empty public read batches as cheap no-ops. Because `Site.amc_request_with_retry(...)` underpins many of the retry-aware drafts from page, site, member, application, forum, and metadata paths, this slice applies the same boundary rule to the central site-scoped AMC helper.

No upstream issue was filed from this local workspace.

## Changes

- Validate explicit `batch_size` and `max_retries` arguments before client configuration access.
- Return `()` immediately when `bodies` is empty.
- Preserve existing config-backed validation for non-empty calls that rely on default retry settings.
- Add a focused regression proving an empty retry batch does not read `client.amc_client`.
- Add a negative regression proving an explicitly invalid empty-batch `batch_size` is still rejected.

## Type Of Change

- Performance improvement
- Empty-input fast path
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Empty AMC retry batches must return an empty tuple without requiring `client.amc_client.config`. | `TestSiteAmcRequest.test_amc_request_with_retry_empty_bodies_returns_empty_without_config` installs a client whose `amc_client` property raises and asserts `site.amc_request_with_retry([]) == ()`. | The RED test failed before the fix because the empty path attempted to read `self.client.amc_client.config`. |
| Empty AMC retry batches must still reject explicitly invalid retry options. | `TestSiteAmcRequest.test_amc_request_with_retry_empty_bodies_still_validates_explicit_batch_size` asserts `batch_size=0` raises `ValueError("batch_size must be positive")`. | A regression that returns `()` before explicit option validation would hide invalid caller input. |
| Non-empty AMC request delegation and site-level retry-adjacent behavior remain stable. | `uv run pytest tests/unit/test_site.py -q` passed 62 tests, and the adjacent site/page/private-message/member/application suite passed 245 tests. | Regressions in AMC delegation, page/source collection, recent changes, private-message acquisition, member lists, or application parsing reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `06b56a5 perf(site): skip empty amc retry batches`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteAmcRequest::test_amc_request_with_retry_empty_bodies_returns_empty_without_config -q` failed before the fix because an empty `bodies` list still accessed `client.amc_client.config`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteAmcRequest -q` passed 3 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 62 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_private_message.py tests/unit/test_site_member.py tests/unit/test_site_application.py -q` passed 245 tests.
- `uv run pytest tests/unit -q` passed 702 tests.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site.py`
- `uv run ruff format --check src/wikidot/module/site.py tests/unit/test_site.py`
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `Site.amc_request_with_retry([])` returns `()` without requiring `client.amc_client.config`.
- `Site.amc_request_with_retry([], batch_size=0)` still raises `ValueError("batch_size must be positive, got 0")`.
- `Site.amc_request_with_retry([], max_retries=-1)` still raises `ValueError("max_retries must be non-negative, got -1")`.
- Non-empty calls still read configured default retry settings, split batches, retry failed responses, preserve result ordering, log retry/failure summaries, and return one tuple entry per input body.
- Site-level page/source/recent-change/member/application/private-message adjacent suites remain green.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Empty AMC body lists naturally arise after caller-side filtering, deduplication, optional follow-up selection, or future helper reuse. A central retry wrapper should make an empty request batch a cheap no-op rather than requiring a fully configured live client. This keeps site-scoped AMC behavior aligned with the empty direct URL batch rule and removes avoidable setup work without changing non-empty retry behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed drafts repeatedly hardened `Site.amc_request_with_retry(...)` callers for page source collection, recent changes, member lists, applications, forum reads, metadata fetches, and duplicate/empty batch boundaries.
- Existing Issues 076, 077, and 137 established empty read batches as practical, non-speculative no-op surfaces after filtering and deduplication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page/message/forum contents out of upstream discussion.

## Additional Notes

This slice does not change request construction, batching for non-empty inputs, retry count defaults, response parsing, logging, exception conversion, or any higher-level collection API. It only makes the already-determined empty result return before client configuration setup that cannot affect an empty output.
