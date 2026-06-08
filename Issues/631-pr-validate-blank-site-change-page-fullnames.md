# PR Draft: Validate Blank Site Change Page Fullnames

## Summary

`Site.get_recent_changes(...)` already rejects generated-module rows whose title `href` is missing, blank, or normalizes to an empty page fullname before constructing `SiteChange`. Earlier direct constructor validation also rejects non-string `SiteChange.page_fullname`, `page_title`, and malformed `comment` values. One adjacent public boundary remained: direct `SiteChange(page_fullname="")` and whitespace-only page fullnames were accepted as valid string state.

This change rejects blank and whitespace-only direct `SiteChange.page_fullname` values after the existing string-type check. Blank `page_title` remains valid direct display text, and `comment=None`, blank string comments, and ordinary string comments remain valid. Existing parser-side recent-change title-link, page-fullname, page-title, revision, timestamp, user, flag, pagination, retry, and response-body behavior remains unchanged.

## Outcome

Direct recent-change ledger records cannot store a missing page identity, while valid non-empty page fullnames and display-only title/comment compatibility remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in local ledgers, generated recent-change reports, moderation dashboards, migration checks, browser-free change monitoring, or tests that synthesize recent-change records.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent-changes records as a practical workflow surface. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), and [509-pr-validate-site-change-actor-client.md](509-pr-validate-site-change-actor-client.md) establish recent-change fetch retry, pagination, parser scoping, text fidelity, parse/fetch diagnostics, typed value extraction, response-body validation, `limit` validation, and direct `SiteChange` constructor validation as active operational boundaries.

This is not a duplicate of Issues 278, 279, or 280, which validate parser-side generated title links, derived page fullnames, and rendered page titles before parser-side `SiteChange` construction. It is not a duplicate of Issue 437, which validates direct constructor text-field types and explicitly does not add non-empty checks. This slice covers the remaining direct-constructor blank-page-identity boundary only.

No upstream issue was filed from this local workspace.

## Changes

- Add a `SiteChange.page_fullname` validator that first preserves the existing `ValueError("page_fullname must be a string")` diagnostic for non-string values.
- Reject blank and whitespace-only direct `SiteChange.page_fullname` values with `ValueError("page_fullname must not be empty")`.
- Preserve blank direct `page_title` values as display text.
- Preserve `comment=None`, blank string comments, and ordinary string comments.
- Preserve valid non-empty page fullnames exactly; the validator does not strip, normalize, lowercase, or rewrite stored values.
- Preserve existing `flags`, `revision_no`, `changed_by`, `changed_at`, `site`, and actor-client validation precedence.
- Preserve existing `Site.get_recent_changes(...)` parser-side behavior and diagnostics.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(page_fullname="")` and whitespace-only variants must raise `ValueError("page_fullname must not be empty")` after the existing string-type check. |
| R2 | Non-string `page_fullname` diagnostics must remain `ValueError("page_fullname must be a string")`. |
| R3 | Blank direct `page_title` values must remain valid direct display text; this slice must not broaden into direct title-content validation. |
| R4 | `comment=None`, blank string comments, and ordinary string comments must remain valid. |
| R5 | Valid non-empty `page_fullname` values, valid recent-change parser rows, parser-side missing/blank href diagnostics, parser-side empty derived page-fullname diagnostics, parser-side empty title diagnostics, title/comment spacing, flags, revision, timestamp, user, limit, pagination, retry, and response-body behavior must remain unchanged. |
| R6 | Focused RED/GREEN, recent-change tests, full site tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, upstream PRs, private page names, private comments, or private site data. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Blank direct recent-change page identities fail during construction. | `TestSiteChangeDataclass.test_init_rejects_blank_page_fullnames` failed RED for `""` and `"   "` with `DID NOT RAISE`, then passed GREEN after page-fullname blank-string validation was added. | Accepting blank page fullnames, stripping and storing a modified page fullname, or raising a type diagnostic for blank strings rejects this local completion claim. | SiteChange constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Type diagnostics stay stable. | Existing malformed text-field cases stayed green after the fix because the new validator calls the existing string validator first. | Raising `page_fullname must not be empty` for non-strings or changing the existing `page_fullname must be a string` diagnostic rejects this local completion claim. | Validation precedence | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R3 | Direct title display compatibility stays intact. | `TestSiteChangeDataclass.test_init_allows_blank_page_title` passed in the RED run and after the fix. | Rejecting blank direct page titles, changing stored title values, or adding direct title-content semantics rejects this local completion claim. | SiteChange display field | `tests/unit/test_site.py` |
| R4 | Optional comment compatibility stays intact. | `TestSiteChangeDataclass.test_init_accepts_optional_string_comment` passed for `None`, `""`, and `"Updated source"` in the RED run and after the fix. | Rejecting `comment=None`, rejecting blank string comments, changing stored comment values, or requiring comment contents rejects this local completion claim. | SiteChange comment field | `tests/unit/test_site.py` |
| R5 | Existing recent-change and adjacent site workflows remain green. | `TestSiteChangeDataclass` plus `TestSiteGetRecentChanges` passed 79 tests; `tests/unit/test_site.py` passed 295 tests; adjacent site/page/member/application/client/Ajax coverage passed 791 tests. | Regressing parser-side page fullname extraction, title extraction, href validation, empty derived page-fullname validation, title/comment spacing, flags, revision, timestamp, user, limit, retry, pagination, adjacent page flows, member flows, application flows, client setup, or Ajax behavior rejects this local completion claim. | Recent changes and adjacent workflows | `tests/unit/test_site.py`, `tests/unit` |
| R6 | Repository quality gates pass in the local dependency environment. | Full unit passed 2845 tests; full `ruff check`, `ruff format --check`, `mypy`, `pyright`, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic site-change values only; this draft contains no credentials, cookies, auth JSON, raw rollout paths, private account names, generated recent-change HTML, private page names, private comments, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, generated recent-change HTML from real sites, private page names, private edit comments, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `bb605a0 fix(site): validate blank site change pages`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_blank_page_fullnames tests/unit/test_site.py::TestSiteChangeDataclass::test_init_allows_blank_page_title tests/unit/test_site.py::TestSiteChangeDataclass::test_init_accepts_optional_string_comment -q` failed 2 blank direct `page_fullname` cases with `DID NOT RAISE`; blank direct `page_title` and optional comment compatibility guards passed in the same run.
- GREEN focused: the same command passed 6 tests after page-fullname blank-string validation was added.
- Recent-change coverage: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 79 tests.
- Site coverage: `uv run pytest tests/unit/test_site.py -q` passed 295 tests.
- Adjacent coverage: `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_client.py tests/unit/test_ajax.py -q` passed 791 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run pytest tests/unit -q` passed 2845 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteChange(..., page_fullname="")` and whitespace-only page fullname variants raise `ValueError("page_fullname must not be empty")`.
- Non-string `page_fullname` values still raise `ValueError("page_fullname must be a string")`.
- `SiteChange(..., page_title="")` remains valid and stores `page_title == ""`.
- `SiteChange(..., comment=None)`, `comment=""`, and `comment="Updated source"` remain valid and preserve stored values.
- Valid non-empty page fullnames are stored unchanged.
- Existing parser-side missing or blank title `href`, empty derived page fullname, empty generated page title, title/comment spacing, flags, revision, timestamp, user, pagination, retry, and response-body behavior remains unchanged.
- Existing live Wikidot semantics, upstream Issues, upstream PRs, pushes, credentials, cookies, auth JSON, raw response bodies, private page names, private edit comments, and private site data remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Upstream-Safe Motivation

`SiteChange.page_fullname` is the page identity that callers use to reconcile recent-change rows with follow-up page reads, source checks, audit ledgers, and moderation reports. Parser-produced recent-change rows already treat missing page identities as malformed. Direct `SiteChange(...)` records should follow the same identity invariant so generated or rehydrated ledgers cannot silently store a missing page key.

## Local Evidence, Not For Upstream Paste

- Issue 279 covered parser-side empty derived recent-change page names and proves blank page identities are not useful for real generated recent-change rows.
- Issue 280 covered parser-side empty rendered page titles but does not require the direct constructor to reject blank display titles.
- Issue 437 covered direct `SiteChange` text-field types and explicitly left non-empty direct constructor checks out of scope.
- The focused RED run showed direct `SiteChange(page_fullname="")` and whitespace-only page fullnames were still accepted as dataclass state.
- This slice only validates direct recent-change page identity blankness. It does not validate direct page-title contents, direct comment contents, parser selectors, request URLs, retry policy, pagination math, user parsing, timestamp parsing, revision parsing, flag-code semantics, live site behavior, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML, saved page contents, page names from real sites, private edit comments, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The new validator deliberately does not strip or normalize stored non-empty page fullnames. It rejects strings whose stripped form is empty and preserves all non-empty direct constructor values exactly.
