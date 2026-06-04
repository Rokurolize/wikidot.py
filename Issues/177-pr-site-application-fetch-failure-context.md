# PR Draft: Include Site Context In Site Application Fetch Failures

## Summary

`SiteApplication.acquire_all(site)` already uses retry-aware AMC fetching for pending site join applications. When the retry-aware request was exhausted, it raised `UnexpectedException("Cannot retrieve site applications")`, which did not identify the affected Wikidot site.

This follow-up preserves retry-aware pending-application fetching, forbidden-page handling, empty-list parsing, nested body-markup rejection, application text spacing, contextual parser errors, accept/decline behavior, and no-direct-AMC fallback behavior, but includes site unix name in the exhausted application-list fetch failure.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), and [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), because those drafts established retry-aware application fetching, body parsing stability, and site-context diagnostics for malformed application markup.

No upstream issue was filed from this local workspace.

## Changes

- Include the site unix name when `SiteApplication.acquire_all(site)` exhausts retry-aware pending-application fetching.
- Strengthen the existing exhausted-retry unit test to assert `Cannot retrieve site applications for site: test-site`.
- Preserve retry usage, forbidden handling, empty application lists, application parsing, parser context, and accept/decline actions.

## Type Of Change

- Bug fix / diagnostics improvement
- Site application list fetch failure context
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Exhausted retry-aware application-list fetches still fail. | `TestSiteApplicationAcquireAll.test_acquire_all_raises_when_retry_is_exhausted` raises `UnexpectedException` when retry returns `None`. | Returning an empty application list or parsing a missing body rejects this local completion claim. |
| The exhausted-retry failure identifies the failed site. | The focused test asserts `Cannot retrieve site applications for site: test-site`. | The RED test failed before the fix because the message only said `Cannot retrieve site applications`. |
| The retry-aware path is preserved. | The same focused test asserts non-retry `amc_request(...)` is not called. | A change that falls back to direct non-retry AMC rejects this local completion claim. |
| Site application behavior remains green. | `uv run pytest tests/unit/test_site_application.py -q` passed 19 tests. | Regressions in retry, forbidden handling, empty lists, nested body-markup rejection, text spacing, parser context, or accept/decline actions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `312c015 fix(site_application): include site in fetch failures`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q` failed before the fix because the exhausted-retry message lacked site context.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_raises_when_retry_is_exhausted -q`
- `uv run pytest tests/unit/test_site_application.py -q` passed 19 tests.
- `uv run pytest tests/unit -q` passed 724 tests.
- `uv run ruff check src tests`
- `uv run ruff format --check src tests`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Exhausted retry-aware pending site-application list fetching still raises `UnexpectedException`.
- The exception includes the site unix name.
- Successful application parsing, forbidden detection, empty-list parsing, parser-context errors, retry usage, and accept/decline behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Pending application reads are site-scoped. When a retry-aware fetch fails across a multi-site run, the exception should identify the site without requiring raw AMC response bodies, private rollout paths, credentials, or local account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established pending-application fetching and parser behavior as practical local Codex surfaces.
- Recent site-context slices showed that compact site names improve multi-site ledgers without changing successful behavior or leaking raw response content.
- The refreshed complexity memo continues to keep parser/source collection helpers, action/read boundaries, and direct property/parser failure messages as follow-up leads, but this slice only claims site-application fetch diagnostics.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw AMC responses, application text, and private site/user data out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, retry policy, forbidden detection, body parsing, empty-list behavior, application text extraction, parser-context errors, accept/decline actions, or live Wikidot behavior. It only adds site context to the existing exhausted-retry application-list failure.
