# PR Draft: Validate Site Change Revision Numbers

## Summary

`SiteChange` records returned by `Site.get_recent_changes(...)` store `revision_no` as recent-change revision identity. Issue 427 validated `SiteChange.flags`, and Issue 281 plus adjacent parser-context drafts report malformed generated revision cells before parser-side `SiteChange` construction. The public dataclass constructor still accepted malformed direct `revision_no` values such as `None`, booleans, strings, floats, and lists, letting callers create recent-change ledger rows whose revision number was not an integer.

This change validates `SiteChange.revision_no` at initialization. `revision_no` now accepts only non-boolean integers and rejects malformed values with `ValueError("revision_no must be an integer")`. Valid recent-changes parsing, flags validation, title/comment/user/timestamp diagnostics, retry/pagination/limit behavior, response-body validation, and adjacent recent-change workflows remain unchanged.

## Outcome

Callers cannot silently create malformed recent-change ledger records with invalid revision numbers, while existing recent-changes fetching and valid `SiteChange(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, browser-free change monitoring, or generated recent-change reports.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent-changes records as practical workflow surfaces. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), and [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md) establish recent-change fetch retry, pagination, parser scoping, text fidelity, parse/fetch diagnostics, typed value extraction, response-body validation, `limit` validation, and direct `SiteChange` constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issue 281 validates parser-side generated revision cells before `SiteChange` construction, Issue 373 validates `Site.get_recent_changes(limit=...)`, and Issue 427 validates `SiteChange.flags`. None of them validates direct `SiteChange(revision_no=...)` construction before malformed revision-number state becomes stored dataclass state.

## Related Issue

Builds directly on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), and [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `SiteChange.revision_no` validator.
- Reject `None`, booleans, strings, floats, lists, and other non-integer revision numbers with `ValueError("revision_no must be an integer")`.
- Preserve valid non-boolean integer revision numbers.
- Preserve existing `flags` validation and keep flags validation first so existing diagnostics precedence remains stable.
- Preserve `Site.get_recent_changes(...)`, recent-change parser diagnostics, fetch retry behavior, pagination batching, `limit` validation, comment/title spacing, page name/title/revision/timestamp/user parsing, and response-body validation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Recent-change ledger state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(revision_no=None)`, `True`, `False`, `"1"`, `1.0`, and `[]` must raise `ValueError("revision_no must be an integer")` before storing record state. |
| R2 | Valid non-boolean integer revision numbers must remain valid and preserve stored values. |
| R3 | Existing `SiteChange.flags` validation must remain unchanged, including diagnostics precedence when both flags and revision numbers are malformed. |
| R4 | Existing `Site.get_recent_changes(...)` parser workflows, recent-change fetch retry, pagination, limit validation, parser diagnostics, page/user parsing, revision parsing, and title/comment text handling must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, recent-change tests, site tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor revision numbers fail at the public dataclass boundary. | `TestSiteChangeDataclass.test_init_rejects_malformed_revision_numbers` failed RED for 6 malformed values because the constructor did not raise, then passed GREEN after `revision_no` validation was added. | Accepting missing values, booleans, strings, floats, lists, arbitrary objects, or emitting ledger rows with non-integer revision numbers rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid integer revision numbers remain green. | Existing valid `SiteChange` constructor coverage and recent-change parser tests passed after the new validator was added. | Rejecting valid integer revision numbers or changing stored values rejects this local completion claim. | SiteChange constructor and recent-change parser | `tests/unit/test_site.py` |
| R3 | Existing flags validation stays intact. | Existing non-list flags, non-string flag entry, and valid string flag tests passed in the focused GREEN run. | Weakening Issue 427 behavior, changing flags diagnostics, accepting malformed flags, or validating revision numbers before malformed flags rejects this local completion claim. | SiteChange constructor | `tests/unit/test_site.py` |
| R4 | Existing recent-changes workflows remain green. | `tests/unit/test_site.py::TestSiteChangeDataclass` and `tests/unit/test_site.py::TestSiteGetRecentChanges` passed 46 tests, `tests/unit/test_site.py` passed 207 tests, and full unit tests passed 1653 tests. | Regressing recent-change parsing, revision extraction, flags extraction, retry behavior, pagination, limit validation, comment/title spacing, page name/title/revision/timestamp/user diagnostics, or adjacent site workflows rejects this local completion claim. | Recent changes and adjacent site workflows | `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted recent-change tests passed, site tests passed, full unit passed, ruff, format, mypy, source-file pyright, and whitespace checks passed; broad pyright was run and reported existing full-tree typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `38c3092 fix(site): validate site change revision numbers`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_revision_numbers -q` failed 6 tests before the fix; every malformed `revision_no` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_revision_numbers tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_non_list_flags tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_non_string_flag_entries tests/unit/test_site.py::TestSiteChangeDataclass::test_init_accepts_string_flags -q` passed 16 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 46 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 207 tests.
- `uv run pytest tests/unit -q` passed 1653 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file passes pyright.

## Acceptance Criteria

- `SiteChange(revision_no=None)`, `True`, `False`, `"1"`, `1.0`, and `[]` raise `ValueError("revision_no must be an integer")`.
- `SiteChange(revision_no=1)` remains valid.
- Existing `flags` validation remains unchanged, including preserving valid string flags and rejecting malformed flags with the existing diagnostics.
- Existing recent-change parser rows still produce valid `SiteChange` records.
- Existing `Site.get_recent_changes(...)`, recent-change parser diagnostics, retry/pagination behavior, `limit` validation, page/user parsing, and title/comment text handling remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteChange.revision_no` is durable identity for browser-free recent-change monitoring, moderation dashboards, audit exports, and migration checks. Constructor validation keeps malformed local revision-number state out of recent-change records while preserving the existing parser path that already converts generated revision cells to integers before constructing `SiteChange`.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used recent-change fetches, recent-change pagination, parser diagnostics, response-body validation, page/title/comment/user/revision extraction, and tests that construct `SiteChange` directly.
- Existing local drafts covered recent-change fetch retry, pagination batching, comment/title scoping and spacing, parse/fetch diagnostics, response-body validation, typed page/revision/timestamp/user parsing, `limit` validation, and direct flags validation, but did not cover direct `SiteChange(revision_no=...)` construction.
- The focused RED failures showed invalid constructor revision numbers were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, float, and list values, plus valid flags behavior and recent-change parsing.
- This slice only validates site-change revision-number constructor input. It does not change recent-change request URLs, pagination, parser selectors, flag-code semantics, comment extraction, title extraction, page fullname parsing, parser-side revision extraction, timestamp parsing, user parsing, response-body validation, `limit` validation, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects boolean and string revision numbers instead of coercing values. Callers loading recent-change records from JSON, YAML, CLI flags, spreadsheets, generated structures, or ledgers should convert revision numbers to non-boolean integers before constructing `SiteChange`.
