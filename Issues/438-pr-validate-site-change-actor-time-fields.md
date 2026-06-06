# PR Draft: Validate Site Change Actor And Time Fields

## Summary

`SiteChange` records returned by `Site.get_recent_changes(...)` store the actor and timestamp for each recent-change row in `changed_by` and `changed_at`. Earlier recent-change slices validated parser-side user metadata, parser-side timestamp values, direct flags, direct revision numbers, and direct page text fields. The public dataclass constructor still accepted malformed direct actor/time values such as `None`, booleans, integers, strings, dictionaries, and lists, letting callers create recent-change ledger rows whose actor was not an `AbstractUser` or whose timestamp was not a `datetime`.

This change validates `SiteChange.changed_by` and `SiteChange.changed_at` at initialization. `changed_by` now accepts only `AbstractUser` instances, preserving regular, deleted, anonymous, guest, and Wikidot system users parsed by the shared user parser. `changed_at` now accepts only `datetime` instances. Malformed values raise stable `ValueError` diagnostics: `changed_by must be an AbstractUser` and `changed_at must be a datetime`. Valid recent-changes parsing, flags validation, revision-number validation, page text-field validation, comment validation, title/comment spacing, parser diagnostics, retry/pagination/limit behavior, and adjacent site workflows remain unchanged.

## Outcome

Callers cannot silently create malformed recent-change ledger records with non-user actors or non-datetime timestamps, while existing recent-changes fetching and valid `SiteChange(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, browser-free change monitoring, or generated recent-change reports.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent-changes records as practical workflow surfaces. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), and [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md) establish recent-change fetch retry, pagination, parser scoping, text fidelity, parse/fetch diagnostics, typed value extraction, response-body validation, `limit` validation, and direct `SiteChange` constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issues 282 and 299 validate parser-side generated timestamp and user metadata before parser-side `SiteChange` construction. Issues 427, 436, and 437 validate direct `SiteChange.flags`, `revision_no`, `page_fullname`, `page_title`, and `comment`. None validates direct `SiteChange(changed_by=..., changed_at=...)` construction before malformed actor/time state becomes stored dataclass state.

## Related Issue

Builds directly on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), and [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteChange.changed_by` validation.
- Add `SiteChange.changed_at` validation.
- Reject non-`AbstractUser` `changed_by` values with `ValueError("changed_by must be an AbstractUser")`.
- Reject non-`datetime` `changed_at` values with `ValueError("changed_at must be a datetime")`.
- Preserve valid `AbstractUser` subclasses, including users without integer IDs that can be returned by the shared user parser for non-regular user cases.
- Preserve valid `datetime` timestamps without timezone normalization or coercion.
- Preserve existing `flags`, `revision_no`, text-field, and comment validation precedence.
- Preserve `Site.get_recent_changes(...)`, recent-change parser diagnostics, fetch retry behavior, pagination batching, `limit` validation, comment/title spacing, page name/title/revision/timestamp/user parsing, and response-body validation.
- Update recent-change parser tests to use real `User` objects when mocking `user_parser`, matching the public parser return type now enforced by `SiteChange`.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Recent-change ledger state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(changed_by=None)`, `True`, `1`, `"tester"`, and `{"id": 1}` must raise `ValueError("changed_by must be an AbstractUser")` before storing record state. |
| R2 | `SiteChange(changed_at=None)`, `True`, `1`, `"2026-06-06"`, and `[]` must raise `ValueError("changed_at must be a datetime")` before storing record state. |
| R3 | Valid `AbstractUser` instances and valid `datetime` timestamps must remain valid and preserve stored values. |
| R4 | Existing `SiteChange.flags`, `revision_no`, page text-field, and comment validation must remain unchanged, including diagnostics precedence when already-covered fields are malformed. |
| R5 | Existing `Site.get_recent_changes(...)` parser workflows, recent-change fetch retry, pagination, limit validation, parser diagnostics, page/user parsing, timestamp parsing, revision parsing, title/comment text handling, and response-body validation must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, recent-change tests, site tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor actors fail at the public dataclass boundary. | `TestSiteChangeDataclass.test_init_rejects_malformed_changed_by` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after actor validation was added. | Accepting missing values, booleans, numbers, strings, dictionaries, arbitrary objects, or emitting ledger rows with non-user actors rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Malformed constructor timestamps fail at the public dataclass boundary. | `TestSiteChangeDataclass.test_init_rejects_malformed_changed_at` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after timestamp validation was added. | Accepting missing values, booleans, numbers, date strings, lists, arbitrary objects, or emitting ledger rows with non-datetime timestamps rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Valid actor/time semantics stay green. | Existing valid constructor coverage, recent-change parser tests, and full unit tests passed after the new validators were added. | Rejecting valid `AbstractUser` subclasses, changing stored users, coercing timestamps, or rejecting valid `datetime` values rejects this local completion claim. | SiteChange constructor and recent-change parser | `tests/unit/test_site.py`, `tests/unit` |
| R4 | Existing direct SiteChange validators stay intact. | Focused GREEN included malformed flags, malformed flag-entry, valid flags, malformed revision numbers, malformed text fields, optional comments, and valid recent-change construction coverage. | Weakening Issues 427, 436, or 437, changing their diagnostics, accepting malformed flags/revision/text/comment values, or validating actor/time before already-covered malformed fields rejects this local completion claim. | SiteChange constructor | `tests/unit/test_site.py` |
| R5 | Existing recent-changes workflows remain green. | `tests/unit/test_site.py::TestSiteChangeDataclass` and `tests/unit/test_site.py::TestSiteGetRecentChanges` passed 70 tests, `tests/unit/test_site.py` passed 231 tests, and full unit tests passed 1677 tests. | Regressing recent-change parsing, user extraction, timestamp extraction, page fullname extraction, page-title extraction, comment extraction, revision extraction, flags extraction, retry behavior, pagination, limit validation, response-body diagnostics, or adjacent site workflows rejects this local completion claim. | Recent changes and adjacent site workflows | `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted recent-change tests passed, site tests passed, full unit passed, ruff, format, mypy, source-file pyright, and whitespace checks passed; broad pyright was run and reported existing full-tree typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `57aca86 fix(site): validate site change actor time`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_changed_by tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_changed_at -q` failed 10 tests before the fix; every malformed actor/time value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 10 tests after actor/time validation was added.
- `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 70 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 231 tests.
- `uv run pytest tests/unit -q` passed 1677 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted; the final targeted format check also passed.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file passes pyright.

## Acceptance Criteria

- `SiteChange(changed_by=None)`, `True`, `1`, `"tester"`, and `{"id": 1}` raise `ValueError("changed_by must be an AbstractUser")`.
- `SiteChange(changed_at=None)`, `True`, `1`, `"2026-06-06"`, and `[]` raise `ValueError("changed_at must be a datetime")`.
- Valid `User` and other `AbstractUser` instances remain valid as `changed_by`.
- Valid `datetime` values remain valid as `changed_at`.
- Existing `flags`, `revision_no`, page text-field, and comment validation remains unchanged.
- Existing recent-change parser rows still produce valid `SiteChange` records.
- Existing `Site.get_recent_changes(...)`, recent-change parser diagnostics, retry/pagination behavior, `limit` validation, page/user/timestamp/revision parsing, response-body validation, and title/comment text handling remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteChange.changed_by` and `SiteChange.changed_at` are durable actor/time fields behind browser-free recent-change monitoring, moderation dashboards, audit exports, and migration checks. Constructor validation keeps malformed local actor/time state out of recent-change records while preserving the existing parser path that already extracts a real `AbstractUser` and `datetime` from generated recent-change markup.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used recent-change fetches, recent-change pagination, parser diagnostics, response-body validation, page/title/comment/user/timestamp/revision extraction, and tests that construct `SiteChange` directly.
- Existing local drafts covered recent-change fetch retry, pagination batching, comment/title scoping and spacing, parse/fetch diagnostics, response-body validation, typed page/fullname/title/revision/timestamp/user parsing, `limit` validation, direct flags validation, direct revision-number validation, and direct text-field validation, but did not cover direct `SiteChange(changed_by=..., changed_at=...)` construction.
- The focused RED failures showed invalid constructor actor/time fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, numeric, string, dictionary, and list actor/time values, plus direct constructor validators and recent-change parsing.
- This slice only validates site-change actor/time constructor input. It does not change recent-change request URLs, pagination, parser selectors, flag-code semantics, comment extraction, title extraction, page fullname parsing, parser-side revision extraction, parser-side timestamp extraction, parser-side user parsing, response-body validation, `limit` validation, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates actor type only as `AbstractUser`, not as an integer-ID regular `User`, because the shared user parser can return deleted, anonymous, guest, or Wikidot system users for valid Wikidot markup. It also validates timestamp type only and does not add timezone normalization or date-string parsing.
