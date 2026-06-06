# PR Draft: Validate Site Change Text Fields

## Summary

`SiteChange` records returned by `Site.get_recent_changes(...)` store the changed page identity, rendered title, and edit comment in `page_fullname`, `page_title`, and `comment`. Earlier recent-change slices validated parser-side title links, derived page fullnames, rendered page titles, comment/title text fidelity, flags, and revision numbers. The public dataclass constructor still accepted malformed direct text-field values such as `None`, booleans, integers, and lists, letting callers create recent-change ledger rows whose text fields were not strings.

This change validates `SiteChange.page_fullname`, `SiteChange.page_title`, and `SiteChange.comment` at initialization. `page_fullname` and `page_title` now accept only strings. `comment` accepts strings or `None`. Malformed values raise stable `ValueError` diagnostics: `page_fullname must be a string`, `page_title must be a string`, and `comment must be a string or None`. Valid recent-changes parsing, flags validation, revision-number validation, title/comment spacing, parser diagnostics, retry/pagination/limit behavior, and adjacent site workflows remain unchanged.

## Outcome

Callers cannot silently create malformed recent-change ledger records with non-string page identities, page titles, or comments, while existing recent-changes fetching and valid `SiteChange(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, browser-free change monitoring, or generated recent-change reports.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent-changes records as practical workflow surfaces. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), and [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md) establish recent-change fetch retry, pagination, parser scoping, text fidelity, parse/fetch diagnostics, typed value extraction, response-body validation, `limit` validation, and direct `SiteChange` constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issues 278, 279, and 280 validate parser-side generated title links, derived page fullnames, and rendered page titles before parser-side `SiteChange` construction. Issues 112 and 115 preserve visible text spacing from generated recent-change comments and titles. Issue 350 validates page write title/comment inputs, not recent-change ledger fields. Issues 427 and 436 validate direct `SiteChange.flags` and `SiteChange.revision_no`. None validates direct `SiteChange(page_fullname=..., page_title=..., comment=...)` construction before malformed text state becomes stored dataclass state.

## Related Issue

Builds directly on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), and [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteChange.page_fullname` validation.
- Add `SiteChange.page_title` validation.
- Add `SiteChange.comment` validation.
- Reject non-string `page_fullname` values with `ValueError("page_fullname must be a string")`.
- Reject non-string `page_title` values with `ValueError("page_title must be a string")`.
- Reject non-string, non-`None` `comment` values with `ValueError("comment must be a string or None")`.
- Preserve valid string page fullnames, valid string page titles, and `comment=None` or string comments.
- Preserve existing `flags` and `revision_no` validation precedence.
- Preserve `Site.get_recent_changes(...)`, recent-change parser diagnostics, fetch retry behavior, pagination batching, `limit` validation, comment/title spacing, page name/title/revision/timestamp/user parsing, and response-body validation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Recent-change ledger state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(page_fullname=None)`, `True`, `1`, and `[]` must raise `ValueError("page_fullname must be a string")` before storing record state. |
| R2 | `SiteChange(page_title=None)`, `True`, `1`, and `[]` must raise `ValueError("page_title must be a string")` before storing record state. |
| R3 | `SiteChange(comment=True)`, `1`, and `[]` must raise `ValueError("comment must be a string or None")` before storing record state. |
| R4 | Valid string page fullnames, string page titles, and `comment=None`, empty string, or ordinary string comments must remain valid and preserve stored values. |
| R5 | Existing `SiteChange.flags` and `revision_no` validation must remain unchanged, including diagnostics precedence when those already-covered fields are malformed. |
| R6 | Existing `Site.get_recent_changes(...)` parser workflows, recent-change fetch retry, pagination, limit validation, parser diagnostics, page/user parsing, revision parsing, and title/comment text handling must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, recent-change tests, site tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor page fullnames fail at the public dataclass boundary. | `TestSiteChangeDataclass.test_init_rejects_malformed_text_fields` failed RED for 4 malformed page fullname values because the constructor did not raise, then passed GREEN after text-field validation was added. | Accepting missing values, booleans, numbers, lists, arbitrary objects, or emitting ledger rows with non-string page fullnames rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Malformed constructor page titles fail at the public dataclass boundary. | The same focused regression failed RED for 4 malformed page title values, then passed GREEN after text-field validation was added. | Accepting missing values, booleans, numbers, lists, arbitrary objects, or emitting ledger rows with non-string page titles rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Malformed constructor comments fail at the public dataclass boundary. | The same focused regression failed RED for 3 malformed comment values, then passed GREEN after comment validation was added. | Accepting booleans, numbers, lists, arbitrary objects, or emitting ledger rows with non-string non-`None` comments rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Valid text field semantics stay green. | `TestSiteChangeDataclass.test_init_accepts_optional_string_comment` passed for `None`, empty string, and ordinary string comments, and existing valid constructor coverage passed. | Rejecting valid strings, changing stored values, or rejecting `comment=None` rejects this local completion claim. | SiteChange constructor | `tests/unit/test_site.py` |
| R5 | Existing flags and revision-number validation stays intact. | Focused GREEN included malformed flags, malformed flag-entry, valid flags, and malformed revision-number tests. | Weakening Issues 427 or 436, changing their diagnostics, accepting malformed flags/revision numbers, or validating text fields before malformed flags/revision numbers rejects this local completion claim. | SiteChange constructor | `tests/unit/test_site.py` |
| R6 | Existing recent-changes workflows remain green. | `tests/unit/test_site.py::TestSiteChangeDataclass` and `tests/unit/test_site.py::TestSiteGetRecentChanges` passed 60 tests, `tests/unit/test_site.py` passed 221 tests, and full unit tests passed 1667 tests. | Regressing recent-change parsing, page fullname extraction, page-title extraction, comment extraction, revision extraction, flags extraction, retry behavior, pagination, limit validation, timestamp/user diagnostics, or adjacent site workflows rejects this local completion claim. | Recent changes and adjacent site workflows | `tests/unit/test_site.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted recent-change tests passed, site tests passed, full unit passed, ruff, format, mypy, source-file pyright, and whitespace checks passed; broad pyright was run and reported existing full-tree typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d05fea8 fix(site): validate site change text fields`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_text_fields -q` failed 11 tests before the fix; every malformed text-field value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_text_fields tests/unit/test_site.py::TestSiteChangeDataclass::test_init_accepts_optional_string_comment tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_revision_numbers tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_non_list_flags tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_non_string_flag_entries tests/unit/test_site.py::TestSiteChangeDataclass::test_init_accepts_string_flags -q` passed 30 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 60 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 221 tests.
- `uv run pytest tests/unit -q` passed 1667 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file passes pyright.

## Acceptance Criteria

- `SiteChange(page_fullname=None)`, `True`, `1`, and `[]` raise `ValueError("page_fullname must be a string")`.
- `SiteChange(page_title=None)`, `True`, `1`, and `[]` raise `ValueError("page_title must be a string")`.
- `SiteChange(comment=True)`, `1`, and `[]` raise `ValueError("comment must be a string or None")`.
- `SiteChange(comment=None)`, `comment=""`, and `comment="Updated source"` remain valid.
- Existing `flags` and `revision_no` validation remains unchanged.
- Existing recent-change parser rows still produce valid `SiteChange` records.
- Existing `Site.get_recent_changes(...)`, recent-change parser diagnostics, retry/pagination behavior, `limit` validation, page/user parsing, and title/comment text handling remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteChange.page_fullname`, `SiteChange.page_title`, and `SiteChange.comment` are durable text fields behind browser-free recent-change monitoring, moderation dashboards, audit exports, and migration checks. Constructor validation keeps malformed local text state out of recent-change records while preserving the existing parser path that already extracts page identity, rendered title text, and comment text from generated recent-change markup.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used recent-change fetches, recent-change pagination, parser diagnostics, response-body validation, page/title/comment/user/revision extraction, and tests that construct `SiteChange` directly.
- Existing local drafts covered recent-change fetch retry, pagination batching, comment/title scoping and spacing, parse/fetch diagnostics, response-body validation, typed page/fullname/title/revision/timestamp/user parsing, `limit` validation, direct flags validation, and direct revision-number validation, but did not cover direct `SiteChange(page_fullname=..., page_title=..., comment=...)` construction.
- The focused RED failures showed invalid constructor text fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, numeric, and list page fullnames/titles; boolean, numeric, and list comments; `None`/empty/ordinary string comments; flags validation; revision-number validation; and recent-change parsing.
- This slice only validates site-change text-field constructor input. It does not change recent-change request URLs, pagination, parser selectors, flag-code semantics, comment extraction, title extraction, page fullname parsing, parser-side revision extraction, timestamp parsing, user parsing, response-body validation, `limit` validation, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only the type of these text fields. It does not add semantic normalization or non-empty checks for direct constructor values; parser-side generated recent-change rows already reject missing/empty structural page identities and titles before constructing `SiteChange`.
