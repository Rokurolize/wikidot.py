# PR Draft: Validate SiteApplication Text Field

## Summary

`SiteApplication` records carry applicant-supplied text used by browser-free pending-application reads, moderation review, generated membership ledgers, site-access audits, and scripts that move parsed application rows between workflow stages. Earlier local slices preserved rendered application text spacing, scoped nested application-like markup, added malformed application text-structure diagnostics, validated response-body shape, guarded applicant parsing, validated accept/decline action users, and validated the direct `SiteApplication.user` field, but the public `SiteApplication(..., text=...)` constructor still accepted malformed text values such as `None`, booleans, integers, lists, and arbitrary objects.

This change validates `SiteApplication.text` at initialization. Malformed non-string values now raise `ValueError("application.text must be a string")`. Valid strings, including the existing empty-string fixtures used by accept/decline tests, remain valid.

## Outcome

Callers cannot silently construct site-application records whose stored application message is not a string, while parser-created application records, application text spacing, malformed application text parse diagnostics, accept/decline behavior, member-cache invalidation, and adjacent site/member/user workflows continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `site.applications`, generated membership ledgers, moderation queues, site-access audits, local fixtures that construct `SiteApplication` directly, or tools that serialize parsed application text for review before accept/decline actions.

## Current Evidence

Local rollout-backed drafts repeatedly identify pending site applications and application text as practical workflow surfaces. Existing drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), and [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md) establish application acquisition, text extraction, text fidelity, parser diagnostics, accept/decline behavior, and application record integrity as active operational boundaries.

Those prior slices are not duplicates. Issues113, 155, and 156 cover parser-side application text extraction, mismatch diagnostics, and missing text table/row/cell context after valid HTML is parsed. Issue449 validates the applicant `user` object at the direct constructor boundary. This slice validates the separate public dataclass `text` field so malformed non-string application messages cannot become stored `SiteApplication` state in manually constructed records, fixtures, or ledger rehydration paths.

## Related Issue

Builds directly on [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md), [324-pr-site-application-response-body-type-context.md](324-pr-site-application-response-body-type-context.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), and the adjacent constructor text-field validation pattern from [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteApplication.text` validation at dataclass initialization.
- Reject malformed non-string constructor values with `ValueError("application.text must be a string")`.
- Preserve valid string text, including empty strings.
- Preserve existing application-list parsing, text spacing, text structure diagnostics, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Site application state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication(text=None)`, `True`, `123`, `["Please let me join"]`, and `object()` must raise `ValueError("application.text must be a string")` when site and user are valid. |
| R2 | Valid string text, including empty strings, must remain valid constructor input. |
| R3 | Existing application-list parsing, text spacing, malformed text-structure diagnostics, applicant parsing, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private applicant data, raw application text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, site-application tests, adjacent site/member/application/user tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor text values fail at the public dataclass boundary. | `TestSiteApplicationDataclass.test_init_rejects_malformed_text` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, numbers, lists, arbitrary objects, or emitting application rows with non-string text rejects this local completion claim. | SiteApplication constructor | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Valid string text semantics stay green. | Existing dataclass tests, parser tests, and accept/decline tests passed, including empty-string text fixtures used for mutation actions. | Rejecting empty strings, coercing non-strings to strings, trimming constructor text, or changing stored text rejects this local completion claim. | Parser-created and manually created applications | `tests/unit/test_site_application.py` |
| R3 | Existing adjacent site/application/member/user workflows remain green. | `tests/unit/test_site_application.py` passed 40 tests, adjacent site/site-member/site-application/user tests passed 369 tests, and full unit tests passed 1736 tests. | Regressing application-list acquisition, retry behavior, nested-body filtering, text spacing, response-body diagnostics, malformed applicant parser diagnostics, action-status diagnostics, accept member-cache invalidation, decline cache preservation, site member workflows, site read/write helpers, or user profile lookup rejects this local completion claim. | Site application and adjacent site workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private applicant names, raw application text, page source text, forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f2982f2 fix(site_application): validate application text`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_malformed_text -q` failed 5 tests before the fix; every malformed `text` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass::test_init_rejects_malformed_text -q` passed 5 tests.
- `uv run pytest tests/unit/test_site_application.py -q` passed 40 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 369 tests.
- `uv run ruff check src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed.
- `uv run pyright src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/site_application.py tests/unit/test_site_application.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit -q` passed 1736 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 70 existing full-tree typing errors, including fixture `None` mismatches, intentional invalid-input test calls, invalid `test_search_pages_query` parameter calls, requestutil response narrowing issues, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `SiteApplication(text=None)`, `True`, `123`, `["Please let me join"]`, and `object()` raise `ValueError("application.text must be a string")`.
- Valid string text, including `""`, remains valid.
- Existing application-list parsing, text spacing, response-body diagnostics, malformed applicant diagnostics, text-structure diagnostics, accept/decline behavior, member-cache invalidation, site member behavior, site workflows, and user workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private applicant data, raw application text, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Application messages are user-visible review content. Parser-side fixes already preserve rendered word boundaries and report malformed text structure, but direct construction should not allow non-string values to enter application rows, exported ledgers, or moderation review objects. This change is narrow: it validates the public dataclass text field while leaving parser extraction, accept/decline actions, and live Wikidot behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used application-list acquisition, text extraction, text spacing, accept/decline actions, member-cache invalidation, adjacent site invitation validation, site member workflows, and generated membership state as practical workflow surfaces.
- Existing local drafts covered application text spacing, nested body markup filtering, malformed application text-table/row/cell diagnostics, response-body diagnostics, malformed parsed applicants, action-status validation, action-user validation, and direct applicant-user constructor validation, but did not cover direct `SiteApplication(text=...)` construction.
- The focused RED failures showed invalid constructor text values were accepted as dataclass state. The GREEN regression covers missing, boolean, numeric, list, and arbitrary object values.
- This slice only validates stored application text type at construction. It does not validate `site`, `user`, user ID, user name, application existence, accept/decline action status, parser selectors, live site behavior, or client authentication at `SiteApplication` construction time.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private applicant data, raw application text, page source text, forum content, private messages, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that construct `SiteApplication` manually should pass already-rendered application text as a string.
