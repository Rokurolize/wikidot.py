# PR Draft: Include Site Context In Application Mismatch Errors

## Summary

`SiteApplication.acquire_all(...)` parses pending site join applications from `managesite/ManageSiteMembersApplicationsModule`. The parser intentionally raises `UnexpectedException` when multiple structural application headers resolve to the same application text table, because that means the generated application user/text pairing is malformed. Before this fix, the message only said `Length of application users and text tables are different`.

This follow-up keeps the existing mismatch failure behavior, parser boundary, and application output shape, but includes the affected site and observed counts in the error message: `Length of application users and text tables are different for site: <unix_name> (users=<n>, text_tables=<m>)`. That makes pending-application parser failures diagnosable from plain-text logs without saving raw manager-page HTML.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), and [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md).

No upstream issue was filed from this local workspace.

## Changes

- Make pending-application user/text-table mismatch errors include the affected site `unix_name`.
- Include the observed structural application header count and distinct text-table count.
- Extend the existing mismatch test to assert the site context and counts.
- Preserve retry-aware fetch behavior, forbidden detection, empty application handling, nested body-markup filtering, application text spacing, user parsing, accept/decline actions, and successful `SiteApplication` output.

## Type Of Change

- Bug fix / diagnostics improvement
- Pending-application parser error-context ergonomics
- Test modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Malformed application header/text-table pairing still fails. | `TestSiteApplicationAcquireAll.test_acquire_all_length_mismatch` still expects `UnexpectedException` for two structural headers sharing one text table. | A change that silently drops, duplicates, or fabricates an application rejects this local completion claim. |
| The mismatch error identifies the affected site and observed counts. | The focused test asserts `Length of application users and text tables are different for site: test-site (users=2, text_tables=1)`. | The RED test failed before the fix because the exception message omitted the site and counts. |
| Adjacent site application workflows remain green. | `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 110 tests. | Regressions in retry, forbidden handling, empty applications, parser boundaries, body text spacing, site accessors, site-member behavior, or accept/decline actions reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `009a913 fix(site_application): include site context in mismatch errors`.

- RED: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_length_mismatch -q` failed before the fix because the parser raised `Length of application users and text tables are different` without site context or counts.
- GREEN: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_length_mismatch -q`
- `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 110 tests.
- `uv run pytest tests/unit -q` passed 715 tests.
- `uv run ruff check`
- `uv run ruff format --check`
- `uv run mypy src tests --install-types --non-interactive`
- `git diff --check`

Not run: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A pending-application response whose structural application headers cannot be paired one-to-one with distinct application text tables still raises `UnexpectedException`.
- The raised mismatch message includes the site `unix_name`, observed application-header count, and observed distinct text-table count.
- Successful pending-application parsing, nested application-body markup filtering, retry behavior, forbidden detection, empty application lists, text spacing, `SiteApplication` fields, and accept/decline action payloads remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Pending site applications are an administrative workflow where failures may be logged by site name rather than by raw HTML. If Wikidot returns malformed generated application markup, wikidot.py should continue to fail instead of inventing application records, but the error should identify which site and what structural counts were observed so maintainers can triage without preserving sensitive applicant text.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established pending site applications as a practical read/action workflow, including retry-aware application-list fetches, application body parser boundaries, response-body reuse, decline action text, and application text spacing.
- Recent parser and direct-property context work showed that target-specific errors improve plain-text logs and resumable ledgers without changing successful behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, applicant text, and saved page contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change `SiteApplication.acquire_all(...)` request construction, login checks, forbidden handling, empty result handling, successful parser output, nested body-markup filtering, application text extraction, user parsing, `SiteApplication.accept()`, `SiteApplication.decline()`, or live Wikidot behavior. It only adds site and count context to an existing parser mismatch failure.
