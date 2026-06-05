# PR Draft: Require Recent Change Page Titles

## Summary

`Site.get_recent_changes()` parses generated `changes/SiteChangesListModule` rows into `SiteChange` records. Recent local slices now reject missing title anchors, missing or blank title `href` values, and title `href` values that normalize to an empty page fullname, but a structural title anchor such as `<a href="/test:test-page"></a>` could still construct `SiteChange.page_title == ""`.

This follow-up treats an empty rendered recent-change page title as malformed generated-module input. It raises `NoElementException` with site, recent-changes page number, and structural change-item position before constructing `SiteChange`. Existing behavior for successful recent-change rows, title text spacing, title `href` validation, page fullname validation, retry-aware fetching, pagination, and limit handling remains unchanged.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), and [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md). Those drafts established recent changes as a practical retry-aware site inspection workflow with parser scoping, pagination handling, title/comment text preservation, and contextual malformed-response diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Validate the rendered `page_title` extracted from the structural recent-change title link.
- Reject structural recent-change rows whose title anchor exists and has a valid page `href`, but no rendered title text.
- Include site `unix_name`, recent-changes page number, and structural change-item position in the malformed page-title `NoElementException`.
- Preserve missing/blank `href` validation and empty normalized page-fullname validation from previous slices.
- Preserve successful recent-change parsing, title spacing, comment parsing, pager handling, retry-aware acquisition, flags, revision parsing, modifier parsing, and `SiteChange` field semantics.
- Add a focused public `Site.get_recent_changes()` regression for an empty title link body.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent-changes parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural recent-change row whose title link has no rendered title text fails before constructing `SiteChange`. | `TestSiteGetRecentChanges.test_get_recent_changes_empty_page_title_includes_site_page_and_item_context` changes the first title link to `<a href="/test:test-page"></a>` and expects `NoElementException`. | Returning a `SiteChange` with `page_title == ""` rejects this local completion claim. |
| Malformed page-title errors identify the affected site, recent-changes page, and structural item. | The focused regression asserts `Page title is not found for site: test (page=1, change=1)`. | Omitting site, page number, or change position rejects this local completion claim. |
| Missing title `href` validation remains intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_missing_title_href_includes_site_page_and_item_context`. | Letting a missing `href` through to later parsing rejects this local completion claim. |
| Empty normalized page-fullname validation remains intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_empty_page_fullname_includes_site_page_and_item_context`. | Returning a `SiteChange` with `page_fullname == ""` rejects this local completion claim. |
| Successful recent-change parsing stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_success`. | Changing normal `page_fullname`, title, flags, revision, user, date, or comment parsing rejects this local completion claim. |
| Existing title text spacing stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_preserves_page_title_text_spacing`. | Collapsing formatted title text such as `First part Second part` rejects this local completion claim. |
| Adjacent site/page workflows remain green. | `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 230 tests. | Regressions in site helpers, recent changes, page iteration, page search, page details, page writes, or publish helpers reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `5ad2fb9 fix(site): require recent change page titles`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_empty_page_title_includes_site_page_and_item_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_empty_page_title_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_missing_title_href_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_empty_page_fullname_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_preserves_page_title_text_spacing -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 78 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 230 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 838 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes()` raises `NoElementException` when a structural recent-change title anchor has no rendered title text.
- The exception includes site `unix_name`, recent-changes page number, and structural change-item position.
- Missing or blank title `href` values continue to raise the existing title-href `NoElementException`.
- Title `href` values that normalize to an empty page fullname continue to raise the existing page-fullname `NoElementException`.
- Valid recent-change rows still parse `page_title` from rendered title-link text.
- Successful recent-change parsing, retry behavior, paginated batching, limit handling, zero-limit behavior, empty-result behavior, structural pager parsing, comment-pager filtering, title/comment text spacing, comment-markup isolation, flags, revision numbers, modifier users, timestamps, and `SiteChange` output fields remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

`SiteChange.page_title` is the display title callers use when rendering recent-change ledgers and comparing rows without fetching every changed page. A generated recent-change row that has a structural title link but no rendered title text is malformed in the same way as missing title metadata: it cannot provide a meaningful `SiteChange` record. Raising a contextual parser exception keeps the malformed generated HTML visible while preserving successful recent-changes parsing and without requiring callers to log raw recent-change HTML.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified recent changes as a practical site-inspection surface for retry handling, pagination batching, source-audit ledgers, parser scoping, and text-preserving row parsing.
- This slice intentionally targets only empty rendered title text on an otherwise structural recent-change title link. It does not change request payloads, retry policy, missing/blank `href` handling, empty page-fullname handling, empty recent-change results, comment extraction, pager parsing, pagination math, user parsing, date parsing, revision parsing, flags, page mutation methods, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML, saved page contents, page names from real sites, and private edit comments out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It removes a misleading empty-page-title fallback while preserving successful row parsing and existing malformed-row context.
