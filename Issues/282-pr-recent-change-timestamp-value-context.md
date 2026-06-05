# PR Draft: Report Recent Change Timestamp Values

## Summary

`Site.get_recent_changes()` parses the generated recent-change `span.odate` element into `SiteChange.changed_at`. When the structural timestamp element existed but carried a malformed `time_...` class, `odate_parse(...)` raised a raw `ValueError` such as `invalid literal for int()`, without identifying the site, recent-changes page, structural change item, affected field, or observed class value.

This follow-up keeps the common `odate` parser behavior unchanged, but catches malformed timestamp values at the recent-changes parser boundary and raises `NoElementException` with `field=changed_at` and the offending `time_...` class. Successful recent-change parsing, missing-odate handling, title validation, page fullname validation, revision parsing, user parsing, flags, comments, retry-aware fetching, pagination, and limit handling remain unchanged.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), and [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md). Those drafts established recent changes as a practical retry-aware site inspection workflow with parser scoping, pagination handling, title/comment text preservation, and contextual malformed-response diagnostics.

No upstream issue was filed from this local workspace.

## Changes

- Preserve the existing missing-odate-element `NoElementException`.
- Convert malformed recent-change timestamp class values from raw `ValueError` into contextual `NoElementException`.
- Include site `unix_name`, recent-changes page number, structural change-item position, `field=changed_at`, and the offending `time_...` class, such as `value=time_latest`.
- Preserve the shared `odate_parse(...)` utility behavior and parser tests.
- Preserve successful recent-change parsing, title validation, title `href` validation, page fullname validation, revision parsing, comment parsing, pager handling, retry-aware acquisition, flags, modifier parsing, and `SiteChange` field semantics.
- Add a focused public `Site.get_recent_changes()` regression for a malformed timestamp class.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent-changes parser hardening
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A structural recent-change row whose `span.odate` has a malformed `time_...` class fails at the recent-changes parser boundary. | `TestSiteGetRecentChanges.test_get_recent_changes_malformed_odate_includes_raw_class_context` changes `time_1700000000` to `time_latest` and expects `NoElementException`. | Leaking a raw `ValueError`, fabricating a timestamp, or constructing `SiteChange` rejects this local completion claim. |
| Malformed timestamp errors identify the affected site, recent-changes page, structural item, field, and bad class value. | The focused regression asserts `Odate value is malformed for site: test (page=1, change=1, field=changed_at, value=time_latest)`. | Omitting site, page number, item position, field name, or bad class value makes the failure ambiguous and rejects this local completion claim. |
| Successful recent-change parsing stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_success`. | Changing normal `page_fullname`, title, flags, revision, user, date, or comment parsing rejects this local completion claim. |
| Existing malformed title and revision context stays intact. | The focused GREEN run includes `TestSiteGetRecentChanges.test_get_recent_changes_empty_page_title_includes_site_page_and_item_context` and `TestSiteGetRecentChanges.test_get_recent_changes_malformed_revision_number_includes_raw_value_context`. | Regressing earlier title or revision-context failures rejects this local completion claim. |
| Adjacent site/page workflows remain green. | `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 232 tests. | Regressions in site helpers, recent changes, page iteration, page search, page details, page writes, or publish helpers reject this local completion claim. |
| Broad unit and static quality gates remain green in the repo dependency environment. | `uv run --extra test pytest tests/unit/ -q`; `uv run --extra lint ruff check src tests`; `uv run --extra format ruff format --check src tests`; `uv run --extra lint mypy src tests --install-types --non-interactive`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `435698f fix(site): report recent change timestamp values`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_odate_includes_raw_class_context -q` failed before the fix because a malformed `time_latest` class leaked `ValueError: invalid literal for int() with base 10: 'latest'`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_odate_includes_raw_class_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_revision_number_includes_raw_value_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_empty_page_title_includes_site_page_and_item_context -q` passed 4 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 80 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_page.py -q` passed 232 tests.
- `uv run --extra test pytest tests/unit/ -q` passed 840 tests.
- `uv run --extra lint ruff check src tests`.
- `uv run --extra format ruff format --check src tests`.
- `uv run --extra lint mypy src tests --install-types --non-interactive`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes()` raises `NoElementException` when a structural recent-change timestamp element has a malformed `time_...` class value.
- The exception includes site `unix_name`, recent-changes page number, structural change-item position, `field=changed_at`, and the bad `time_...` class value.
- Missing timestamp elements continue to raise the existing missing-element `NoElementException`.
- Valid recent-change rows still parse `changed_at` through the existing `odate_parse(...)` utility.
- Successful recent-change parsing, retry behavior, paginated batching, limit handling, zero-limit behavior, empty-result behavior, structural pager parsing, comment-pager filtering, title/comment text spacing, comment-markup isolation, page title validation, title `href` validation, page fullname validation, revision parsing, flags, modifier users, and `SiteChange` output fields remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

`SiteChange.changed_at` is a core recent-change ordering and audit field. When Wikidot's generated module emits a malformed timestamp class, wikidot.py should report a structured parser failure that tells callers which row and field failed, rather than leaking a raw integer conversion exception. Including the offending class value makes the failure actionable without requiring logs to retain generated recent-change HTML or private edit comments.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified recent changes as a practical site-inspection surface for retry handling, pagination batching, parser scoping, text-preserving row parsing, and contextual malformed-response diagnostics.
- This slice intentionally targets only malformed timestamp class values in recent-change rows. It does not change request payloads, retry policy, missing timestamp element handling, title parsing, title validation, page fullname handling, revision parsing, empty recent-change results, comment extraction, pager parsing, pagination math, user parsing, flags, page mutation methods, the shared `odate_parse(...)` utility, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML, saved page contents, page names from real sites, and private edit comments out of upstream discussion.

## Additional Notes

This is a parser observability fix. It keeps the valid timestamp path and common parser untouched while making malformed recent-change timestamp rows self-contained enough for logs and audit ledgers.
