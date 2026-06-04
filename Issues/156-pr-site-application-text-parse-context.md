# PR Draft: Include Site Context In Application Text Parse Errors

## Summary

`SiteApplication.acquire_all(...)` parses pending site join applications from `managesite/ManageSiteMembersApplicationsModule`. The parser already fails when generated application markup is malformed, but the remaining application text-table, text-row, and text-cell failures only named the missing element. A plain log line such as `Application text cell is not found` did not identify which site or which structural application entry produced the malformed shape.

This follow-up keeps the existing `NoElementException` failure behavior and application output shape, but includes the affected site `unix_name`, structural application index, total structural application count, and observed text-cell count where relevant. That makes pending-application parse failures diagnosable from plain-text logs without saving raw manager-page HTML or applicant text.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), and [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small pending-application parse-context helper for site name, structural application index, total structural application count, and optional observed counts.
- Include that context in missing application text-table, text-row, and text-cell `NoElementException` messages.
- Extend the existing missing text-cell regression to assert `Application text cell is not found for site: test-site (application=1, applications=1, cells=1)`.
- Preserve retry-aware fetch behavior, forbidden detection, empty application handling, nested body-markup filtering, application mismatch failure behavior, application text spacing, user parsing, accept/decline actions, and successful `SiteApplication` output.

## Type Of Change

- Bug fix / diagnostics improvement
- Pending-application parser error-context ergonomics
- Test modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed application text-cell structure still fails. | `TestSiteApplicationAcquireAll.test_acquire_all_missing_text_cell` still expects `NoElementException` for an application text row with only one direct cell. | A change that silently accepts the malformed row, fabricates empty text, or shifts parser output rejects this local completion claim. |
| The missing text-cell error identifies the affected site and structural application position. | The focused test asserts `Application text cell is not found for site: test-site (application=1, applications=1, cells=1)`. | The RED test failed before the fix because the exception message was only `Application text cell is not found`. |
| Related malformed application text-table and text-row failures use the same site/application context helper. | Source inspection of `src/wikidot/module/site_application.py` shows table, row, and cell `NoElementException` messages all append the parse context. | A future partial context change that only updates one malformed path would leave the other two paths as generic log lines. |
| Adjacent site application workflows remain green. | `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 110 tests. | Regressions in retry, forbidden handling, empty applications, parser boundaries, body text spacing, mismatch errors, site accessors, site-member behavior, or accept/decline actions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1ecefac fix(site_application): include context in text parse errors`.

- RED: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_missing_text_cell -q` failed before the fix because the parser raised `Application text cell is not found` without site, application index, total count, or observed cell count.
- GREEN: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_missing_text_cell -q`
- `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 110 tests.
- `uv run pytest tests/unit -q` passed 715 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A pending-application response whose application text row lacks the expected direct text cell still raises `NoElementException`.
- The raised missing text-cell message includes the site `unix_name`, structural application index, total structural application count, and observed direct text-cell count.
- Missing text-table and missing text-row failures also include the same site/application position context.
- Successful pending-application parsing, nested application-body markup filtering, retry behavior, forbidden detection, empty application lists, text spacing, user parsing, mismatch failure behavior, and accept/decline action payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Pending site applications are an administrative workflow where malformed generated markup can appear in large site-management or moderation logs. The parser should still fail instead of guessing at applicant text, but the failure should identify the affected site and structural position so maintainers can triage without storing applicant messages or raw manager-page HTML.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established pending site applications as a practical read/action workflow, including retry-aware application-list fetches, application body parser boundaries, response-body reuse, decline action text, application text spacing, and mismatch failure context.
- Recent parser and direct-property context work showed that target-specific errors improve plain-text logs and resumable ledgers without changing successful behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, applicant text, raw manager-page HTML, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `SiteApplication.acquire_all(...)` request construction, login checks, forbidden handling, empty result handling, successful parser output, nested body-markup filtering, application text extraction, user parsing, existing mismatch failure semantics, `SiteApplication.accept()`, `SiteApplication.decline()`, or live Wikidot behavior. It only adds site and structural-position context to existing malformed application text parse failures.
