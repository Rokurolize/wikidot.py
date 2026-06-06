# PR Draft: Validate Site Change Flags

## Summary

`SiteChange` documents and behaves as the structured object returned by `Site.get_recent_changes(...)`, but its direct dataclass constructor accepted arbitrary `flags` values. A caller could construct `SiteChange(flags=None)`, `SiteChange(flags="S")`, `SiteChange(flags=("S",))`, or `SiteChange(flags=[{"flag": "S"}])`; that malformed state then looked like a recent-change record until later consumers iterated, serialized, or compared flags and hit unstable type assumptions.

This change validates `flags` at `SiteChange` initialization. Non-list `flags` now raise `ValueError("flags must be a list")`; list entries that are not strings raise `ValueError("flags list entries must be strings")`. Valid `list[str]` values are preserved, and the parser path in `Site.get_recent_changes(...)` remains unchanged because it already builds a list of strings from flag spans.

## Outcome

Callers cannot silently create malformed `SiteChange` instances through the public constructor, while existing recent-changes fetching, pagination, limit validation, parser diagnostics, title/comment text handling, page/user parsing, and flag extraction workflows remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, or browser-free change monitoring workflows.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent-changes records as practical workflow surfaces. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), and [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md) establish fetch retry, pagination, parser scoping, text fidelity, parse/fetch diagnostics, typed value extraction, response-body validation, and `limit` validation as active operational boundaries.

Those prior slices are not duplicates. They covered the `Site.get_recent_changes(...)` parser path and request controls, and [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md) explicitly kept `SiteChange` output shape unchanged. None of them validates direct `SiteChange(flags=...)` construction before malformed flags become stored dataclass state.

## Related Issue

Builds directly on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), and [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteChange.__post_init__()` validation for `flags`.
- Reject non-list `flags` with `ValueError("flags must be a list")`.
- Reject non-string list entries with `ValueError("flags list entries must be strings")`.
- Preserve valid `list[str]` flags without adding semantic validation for specific flag codes.
- Preserve `Site.get_recent_changes(...)`, recent-change parser diagnostics, fetch retry behavior, pagination batching, `limit` validation, comment/title spacing, page name/title/revision/timestamp/user parsing, and response-body validation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Recent-change record state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(flags=None)`, `True`, `"S"`, `("S",)`, and `1` must raise `ValueError("flags must be a list")` before storing record state. |
| R2 | `SiteChange(flags=[None])`, `[True]`, `[1]`, and `[{"flag": "S"}]` must raise `ValueError("flags list entries must be strings")` before storing record state. |
| R3 | `SiteChange(flags=["S", "N"])` and other valid `list[str]` values must remain valid and preserve their string values. |
| R4 | Existing `Site.get_recent_changes(...)` parser workflows, flags extraction, recent-change fetch retry, pagination, limit validation, parser diagnostics, page/user parsing, and title/comment text handling must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, recent-change tests, adjacent site/page/member/application/user tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public dataclass boundary. | `TestSiteChangeDataclass.test_init_rejects_non_list_flags` failed RED for `None`, `True`, `"S"`, `("S",)`, and `1`, then passed GREEN after `SiteChange.__post_init__()` validation was added. | Accepting strings, tuples, booleans, integers, missing values, or deferring failure to later iteration rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Non-string constructor list entries fail at the public dataclass boundary. | `TestSiteChangeDataclass.test_init_rejects_non_string_flag_entries` passed after entry validation was added and covers `None`, `True`, `1`, and `{"flag": "S"}`. | Accepting missing values, booleans, numbers, dictionaries, serialized flag records, or fixture stand-ins as stored flags rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Valid string flags remain green and are not semantically reinterpreted. | `TestSiteChangeDataclass.test_init_accepts_string_flags` passed and preserves `["S", "N"]`. | Rejecting valid strings, copying them into another representation, normalizing flag codes, or adding code-specific validation rejects this local completion claim. | SiteChange constructor | `tests/unit/test_site.py` |
| R4 | Existing recent-changes workflows remain green. | `tests/unit/test_site.py::TestSiteChangeDataclass` and `tests/unit/test_site.py::TestSiteGetRecentChanges` passed 40 tests; adjacent site/page/site-member/site-application/user tests passed 525 tests; full unit tests passed 1586 tests. | Regressing recent-change parsing, flags extraction, retry behavior, pagination, limit validation, comment/title spacing, page name/title/revision/timestamp/user diagnostics, page workflows, member/application workflows, or user workflows rejects this local completion claim. | Recent changes and adjacent workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_site_member.py`, `tests/unit/test_site_application.py`, `tests/unit/test_user.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted recent-change and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `071ae61 fix(site): validate site change flags`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_non_list_flags -q` failed 5 tests before the dataclass fix; all cases reported `DID NOT RAISE`, proving `None`, booleans, strings, tuples, and integers were accepted as stored flags state.
- GREEN: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_non_list_flags tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_non_string_flag_entries -q` passed 9 tests after adding non-list and entry validation.
- `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 40 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run mypy src/wikidot/module/site.py tests/unit/test_site.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 525 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.
- `uv run pytest tests/unit -q` passed 1586 tests.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `SiteChange(flags=None)`, `True`, `"S"`, `("S",)`, and `1` raise `ValueError("flags must be a list")`.
- `SiteChange(flags=[None])`, `[True]`, `[1]`, and `[{"flag": "S"}]` raise `ValueError("flags list entries must be strings")`.
- `SiteChange(flags=["S", "N"])` and other valid `list[str]` values continue to work without semantic flag-code validation.
- Existing `Site.get_recent_changes(...)`, recent-change parser diagnostics, retry/pagination behavior, `limit` validation, flags extraction, page/user parsing, and title/comment text handling remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteChange` is the stored object shape behind browser-free recent-change monitoring, moderation dashboards, audit exports, and migration checks. Constructor validation keeps malformed local flag state out of recent-change records while preserving the existing parser path that extracts flags from Wikidot markup as strings.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used recent-change fetches, recent-change pagination, parser diagnostics, response-body validation, page/title/comment/user extraction, and tests that construct `SiteChange` directly.
- Existing local drafts covered recent-change fetch retry, pagination batching, comment/title scoping and spacing, parse/fetch diagnostics, response-body validation, typed page/revision/timestamp/user parsing, and `limit` validation, but did not cover direct `SiteChange(flags=...)` construction.
- The focused RED failures showed invalid non-list constructor input was accepted as dataclass state. The GREEN regressions cover non-list input, malformed list entries, valid string flag preservation, recent-change parsing, page workflows, member workflows, application workflows, and user workflows.
- This slice only validates site-change flag constructor input. It does not change recent-change request URLs, pagination, parser selectors, flag-code semantics, comment extraction, title extraction, page fullname parsing, revision parsing, timestamp parsing, user parsing, response-body validation, `limit` validation, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only the container and entry types. It does not attempt to define the complete set of legal Wikidot recent-change flag codes.
