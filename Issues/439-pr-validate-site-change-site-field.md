# PR Draft: Validate Site Change Site Field

## Summary

`SiteChange` records returned by `Site.get_recent_changes(...)` carry the parent `Site` object along with the changed page identity, revision number, actor, timestamp, flags, and comment. Earlier recent-change slices validated parser-side site IDs, response-body handling, user/timestamp/revision/page metadata, direct flags, direct revision numbers, direct text fields, and direct actor/time fields. The public dataclass constructor still accepted malformed direct `site` values such as `None`, booleans, strings, dictionaries, and arbitrary objects, letting callers create recent-change ledger rows whose parent site was not a `Site`.

This change validates `SiteChange.site` at initialization. Malformed values now raise `ValueError("site must be a Site")`. Valid recent-changes parsing, flags validation, revision-number validation, text-field validation, comment validation, actor/time validation, title/comment spacing, parser diagnostics, retry/pagination/limit behavior, and adjacent site workflows remain unchanged.

## Outcome

Callers cannot silently create malformed recent-change ledger records with non-`Site` parent state, while existing recent-changes fetching and valid `SiteChange(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, browser-free change monitoring, multi-site source collection reports, or generated recent-change reports.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent-changes records and site identity as practical workflow surfaces. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), and [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md) establish recent-change fetch retry, pagination, parser scoping, text fidelity, parse/fetch diagnostics, typed value extraction, response-body validation, site identity in result ledgers, site-name input validation, `limit` validation, and direct `SiteChange` constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issue 338 adds site identity to source/publish result ledger exports, Issue 359 validates public site lookup UNIX names, parser-side issues validate generated recent-change metadata before parser-side `SiteChange` construction, and Issues 427, 436, 437, and 438 validate direct `SiteChange.flags`, `revision_no`, text fields, and actor/time fields. None validates direct `SiteChange(site=...)` construction before malformed parent-site state becomes stored dataclass state.

## Related Issue

Builds directly on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), and [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteChange.site` validation.
- Reject non-`Site` values with `ValueError("site must be a Site")`.
- Preserve existing `flags`, `revision_no`, text-field, comment, actor, and timestamp validation precedence by running the new site validator after already-covered `SiteChange` field validators.
- Preserve `Site.get_recent_changes(...)`, recent-change parser diagnostics, fetch retry behavior, pagination batching, `limit` validation, comment/title spacing, page name/title/revision/timestamp/user parsing, and response-body validation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Recent-change ledger parent-state integrity

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` before storing record state when all previously covered fields are valid. |
| R2 | Valid `Site` instances must remain valid and preserve stored values. |
| R3 | Existing `SiteChange.flags`, `revision_no`, page text-field, comment, `changed_by`, and `changed_at` validation must remain unchanged, including diagnostics precedence when already-covered fields are malformed. |
| R4 | Existing `Site.get_recent_changes(...)` parser workflows, recent-change fetch retry, pagination, limit validation, parser diagnostics, page/user parsing, timestamp parsing, revision parsing, title/comment text handling, and response-body validation must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, recent-change tests, site tests, full unit tests, lint, format, mypy, source-file pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor sites fail at the public dataclass boundary. | `TestSiteChangeDataclass.test_init_rejects_malformed_site` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after site validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting ledger rows with non-`Site` parent state rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid site semantics stay green. | Existing valid constructor coverage, recent-change parser tests, site tests, and full unit tests passed after the new validator was added. | Rejecting valid `Site` instances or changing stored site object identity rejects this local completion claim. | SiteChange constructor and recent-change parser | `tests/unit/test_site.py`, `tests/unit` |
| R3 | Existing direct SiteChange validators stay intact. | Focused recent-change coverage included malformed flags, malformed flag-entry, valid flags, malformed revision numbers, malformed text fields, optional comments, malformed actor/time values, and valid recent-change construction coverage. | Weakening Issues 427, 436, 437, or 438, changing their diagnostics, accepting malformed flags/revision/text/comment/actor/time values, or validating site before already-covered malformed fields rejects this local completion claim. | SiteChange constructor | `tests/unit/test_site.py` |
| R4 | Existing recent-changes workflows remain green. | `tests/unit/test_site.py::TestSiteChangeDataclass` and `tests/unit/test_site.py::TestSiteGetRecentChanges` passed 75 tests, `tests/unit/test_site.py` passed 236 tests, and full unit tests passed 1682 tests. | Regressing recent-change parsing, user extraction, timestamp extraction, page fullname extraction, page-title extraction, comment extraction, revision extraction, flags extraction, retry behavior, pagination, limit validation, response-body diagnostics, or adjacent site workflows rejects this local completion claim. | Recent changes and adjacent site workflows | `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted recent-change tests passed, site tests passed, full unit passed, ruff, format, mypy, source-file pyright, and whitespace checks passed; broad pyright was run and reported existing full-tree typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b7aaf03 fix(site): validate site change site`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_site -q` failed 5 tests before the fix; every malformed `site` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 5 tests after site validation was added.
- `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 75 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 236 tests.
- `uv run pytest tests/unit -q` passed 1682 tests.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file passes pyright.

## Acceptance Criteria

- `SiteChange(site=None)`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- Valid `Site` instances remain valid as `site`.
- Existing `flags`, `revision_no`, page text-field, comment, `changed_by`, and `changed_at` validation remains unchanged.
- Existing recent-change parser rows still produce valid `SiteChange` records.
- Existing `Site.get_recent_changes(...)`, recent-change parser diagnostics, retry/pagination behavior, `limit` validation, page/user/timestamp/revision parsing, response-body validation, and title/comment text handling remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteChange.site` is the parent context behind browser-free recent-change monitoring, moderation dashboards, audit exports, generated reports, and multi-site migration checks. Constructor validation keeps malformed local parent-site state out of recent-change records while preserving the existing parser path that constructs `SiteChange` records from a real `Site`.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used recent-change fetches, recent-change pagination, parser diagnostics, response-body validation, page/title/comment/user/timestamp/revision extraction, result-ledger site fields, site lookup validation, and tests that construct `SiteChange` directly.
- Existing local drafts covered recent-change fetch retry, pagination batching, comment/title scoping and spacing, parse/fetch diagnostics, response-body validation, typed page/fullname/title/revision/timestamp/user parsing, site identity in source/publish result ledgers, site lookup name validation, `limit` validation, direct flags validation, direct revision-number validation, direct text-field validation, and direct actor/time validation, but did not cover direct `SiteChange(site=...)` construction.
- The focused RED failures showed invalid constructor site fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, string, dictionary, and arbitrary object site values, plus direct constructor validators and recent-change parsing.
- This slice only validates site-change parent-site constructor input. It does not change recent-change request URLs, pagination, parser selectors, flag-code semantics, comment extraction, title extraction, page fullname parsing, parser-side revision extraction, parser-side timestamp extraction, parser-side user parsing, response-body validation, `limit` validation, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `site` is a `Site` instance. It does not validate site IDs, UNIX-name syntax, domain fields, or client authentication state at `SiteChange` construction time; those are separate site object and lookup concerns.
