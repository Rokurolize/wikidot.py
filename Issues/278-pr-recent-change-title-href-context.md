# PR Draft: Require Recent Change Title Hrefs

## Summary

`Site.get_recent_changes()` parses generated `changes/SiteChangesListModule` rows into `SiteChange.page_fullname` by reading the title anchor's `href`. Before this slice, a structurally valid recent-change row with a title `<a>` element but no `href` was accepted and converted into `page_fullname == ""`.

This follow-up treats a missing or blank title link `href` as malformed generated-module input. It raises `NoElementException` with site, recent-changes page number, and structural change-item position before constructing `SiteChange`. Existing behavior for successful recent-change rows, title text spacing, comment markup isolation, retry-aware fetching, pagination, and limit handling remains unchanged.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), and [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md). Those drafts established recent changes as a practical retry-aware site inspection workflow with parser scoping, pagination handling, title/comment text preservation, and contextual malformed-response diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Reject recent-change title anchors whose `href` attribute is missing, non-string, or blank.
- Include site `unix_name`, recent-changes page number, and structural change-item position in the malformed title-href `NoElementException`.
- Keep title text parsing with a space separator.
- Keep valid `href`-derived page fullname parsing for successful recent-change rows.
- Preserve retry-aware acquisition, empty results, zero-limit behavior, real pager handling, comment-pager filtering, comment-markup isolation, flags, revision parsing, modifier parsing, and `SiteChange` field semantics.
- Add a focused public `Site.get_recent_changes()` regression for a recent-change title anchor without `href`.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent-changes parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Missing title link `href` fails instead of fabricating an empty `SiteChange.page_fullname`. | `TestSiteGetRecentChanges.test_get_recent_changes_missing_title_href_includes_site_page_and_item_context` removes the first title anchor's `href` and expects `NoElementException`. | Returning a `SiteChange` with `page_fullname == ""` rejects this local completion claim. |
| Malformed title-href errors identify the affected site, recent-changes page, and structural item. | The focused regression asserts `Title href is not found for site: test (page=1, change=1)`. | Omitting site, page number, or change position rejects this local completion claim. |
| Successful recent-change parsing stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_success`. | Changing normal `page_fullname`, title, flags, revision, user, date, or comment parsing rejects this local completion claim. |
| Existing title text spacing stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_preserves_page_title_text_spacing`. | Collapsing formatted title text such as `First part Second part` rejects this local completion claim. |
| Authored comment markup remains isolated from structural recent-change parsing. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_ignores_comment_change_like_markup`. | Letting comment content create fake changes or flags rejects this local completion claim. |
| Adjacent site/page workflows remain green. | `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 228 tests. | Regressions in site helpers, recent changes, page iteration, page search, page details, page writes, or publish helpers reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `40a11b9 fix(site): require recent change title hrefs`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_missing_title_href_includes_site_page_and_item_context -q` failed before the fix with `Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_missing_title_href_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_preserves_page_title_text_spacing tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_ignores_comment_change_like_markup -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 76 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 228 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 836 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes()` raises `NoElementException` when a structural recent-change title anchor is missing `href`.
- The exception includes site `unix_name`, recent-changes page number, and structural change-item position.
- Valid recent-change rows still parse `page_fullname` from title link `href`.
- Successful recent-change parsing, retry behavior, paginated batching, limit handling, zero-limit behavior, empty-result behavior, structural pager parsing, comment-pager filtering, title/comment text spacing, comment-markup isolation, flags, revision numbers, modifier users, timestamps, and `SiteChange` output fields remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

`SiteChange.page_fullname` is the identifier callers use to reconcile recent-change rows with later page reads, source checks, or audit ledgers. An empty page fullname on an otherwise structural recent-change row is not a useful page identity. Raising a contextual parser exception keeps malformed generated HTML visible without requiring callers to retain raw recent-change HTML or private edit comments in logs.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified recent changes as a practical site-inspection surface for retry handling, pagination batching, source-audit ledgers, parser scoping, and text-preserving row parsing.
- This slice intentionally targets only missing or blank title `href` values. It does not change request payloads, retry policy, empty recent-change results, title text extraction, comment extraction, pager parsing, pagination math, user parsing, date parsing, revision parsing, flags, page mutation methods, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML, saved page contents, page names from real sites, and private edit comments out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It removes a misleading empty-page-name fallback at the recent-change acquisition boundary while preserving successful row parsing and existing malformed-row context.
