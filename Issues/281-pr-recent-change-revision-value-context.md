# PR Draft: Report Recent Change Revision Values

## Summary

`Site.get_recent_changes()` already rejects recent-change rows whose structural revision cell lacks any digits, but the malformed-response error only identified the site, recent-changes page number, and structural change-item position. It did not include the observed revision-cell text, so callers investigating a malformed generated module response still had to preserve or inspect raw HTML to see what revision value failed.

This follow-up keeps the same exception type and parser boundary, but includes `field=revision_no` and the normalized raw revision-cell text in the `NoElementException` message when revision parsing fails. Successful recent-change parsing, title validation, page fullname validation, date/user parsing, flags, comments, retry-aware fetching, pagination, and limit handling remain unchanged.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), and [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md). Those drafts established recent changes as a practical retry-aware site inspection workflow with parser scoping, pagination handling, title/comment text preservation, and contextual malformed-response diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing `NoElementException` for malformed recent-change revision cells with no digits.
- Include `field=revision_no` in the malformed revision-number message.
- Include the normalized raw revision-cell text, such as `value=rev. latest`, in the malformed revision-number message.
- Preserve the existing missing-revision-cell message.
- Preserve successful recent-change parsing, page title validation, title `href` validation, page fullname validation, comment parsing, pager handling, retry-aware acquisition, flags, timestamp parsing, modifier parsing, and `SiteChange` field semantics.
- Add a focused public `Site.get_recent_changes()` regression for a malformed revision-cell value.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent-changes parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural recent-change row whose revision cell has no digits still fails before constructing `SiteChange`. | `TestSiteGetRecentChanges.test_get_recent_changes_malformed_revision_number_includes_raw_value_context` changes the first revision cell to `rev. latest` and expects `NoElementException`. | Returning a `SiteChange` with a fabricated revision number rejects this local completion claim. |
| Malformed revision-number errors identify the affected site, recent-changes page, structural item, field, and raw value. | The focused regression asserts `Revision number is not found for site: test (page=1, change=1, field=revision_no, value=rev. latest)`. | Omitting site, page number, item position, field name, or raw value rejects this local completion claim. |
| Successful recent-change parsing stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_success`. | Changing normal `page_fullname`, title, flags, revision, user, date, or comment parsing rejects this local completion claim. |
| Existing malformed title context stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_empty_page_title_includes_site_page_and_item_context` and `TestSiteGetRecentChanges.test_get_recent_changes_missing_title_includes_site_page_and_item_context`. | Regressing earlier title-context failures rejects this local completion claim. |
| Adjacent site/page workflows remain green. | `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 231 tests. | Regressions in site helpers, recent changes, page iteration, page search, page details, page writes, or publish helpers reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `1d2bf1b fix(site): report recent change revision values`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_revision_number_includes_raw_value_context -q` failed before the fix because the existing `NoElementException` message omitted `field=revision_no` and the raw `value=rev. latest`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_revision_number_includes_raw_value_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_empty_page_title_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_missing_title_includes_site_page_and_item_context -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 79 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 231 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 839 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes()` still raises `NoElementException` when a structural recent-change revision cell has no parseable digits.
- The exception includes site `unix_name`, recent-changes page number, structural change-item position, `field=revision_no`, and the normalized raw revision-cell text.
- Missing revision cells continue to raise the existing missing-element `NoElementException`.
- Valid recent-change rows still parse `revision_no` from the revision-cell text.
- Successful recent-change parsing, retry behavior, paginated batching, limit handling, zero-limit behavior, empty-result behavior, structural pager parsing, comment-pager filtering, title/comment text spacing, comment-markup isolation, page title validation, title `href` validation, page fullname validation, flags, modifier users, timestamps, and `SiteChange` output fields remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

`SiteChange.revision_no` is a core recent-change identity field. When Wikidot's generated module returns a malformed revision cell, callers need enough low-cardinality context to diagnose which field failed without logging raw generated HTML or private edit comments. Including the field name and observed cell text in the existing parser exception makes malformed recent-change rows auditable while preserving the public API and successful parsing behavior.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified recent changes as a practical site-inspection surface for retry handling, pagination batching, source-audit ledgers, parser scoping, text-preserving row parsing, and contextual malformed-response diagnostics.
- This slice intentionally targets only the malformed revision-cell error message. It does not change request payloads, retry policy, missing revision-cell handling, title parsing, title validation, page fullname handling, empty recent-change results, comment extraction, pager parsing, pagination math, user parsing, date parsing, flags, page mutation methods, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML, saved page contents, page names from real sites, and private edit comments out of upstream discussion.

## Additional Notes

This is a parser observability fix. It makes the existing malformed-revision failure self-contained enough for logs and audit ledgers while preserving successful row parsing and existing malformed-row context.
