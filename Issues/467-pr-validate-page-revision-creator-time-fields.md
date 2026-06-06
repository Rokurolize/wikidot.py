# PR Draft: Validate Page Revision Creator And Time Fields

## Summary

`PageRevision` records carry the user and timestamp metadata used by browser-free page-history reads, generated revision ledgers, source/HTML comparison, rollback inspection, latest-revision checks, migration audits, and publication verification. Earlier local slices validated parser-side page revision user and timestamp diagnostics, direct parent-page construction, direct identity fields, direct comment fields, collection entries, collection initialization, source/html cache assignment, and loaded-collection lookup, but the public `PageRevision(...)` constructor still accepted malformed direct `created_by` and `created_at` values such as `None`, booleans, integers, strings, dictionaries, epoch integers, date strings, and lists.

This change validates `PageRevision.created_by` and `PageRevision.created_at` at initialization. `created_by` now accepts only `AbstractUser` instances, preserving regular, deleted, anonymous, guest, and Wikidot system users returned by the shared user parser. `created_at` now accepts only `datetime` instances. Malformed values raise stable diagnostics: `ValueError("created_by must be an AbstractUser")` and `ValueError("created_at must be a datetime")`. Existing page revision-list parsing, parser-side revision ID/revision-number/user/timestamp diagnostics, direct `PageRevision.page`, identity-field, and comment-field validation, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, direct source/HTML acquisition, source/html setter validation, collection lookup, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct page revision records with malformed creator or timestamp metadata, while parser-created, fixture-created, and manually created valid revisions continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page revision history, generated revision snapshot ledgers, source/HTML comparison, rollback tooling, publication verification, duplicate revision cache reuse, lazy `Page.revisions`, `Page.latest_revision`, direct `PageRevisionCollection.get_sources()` / `get_htmls()`, or local tests that construct `PageRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision creator/time metadata as a practical workflow surface. Existing drafts [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), and [466-pr-validate-page-revision-comment-field.md](466-pr-validate-page-revision-comment-field.md) establish page revision reads, retry behavior, deduplication, parser diagnostics, response diagnostics, collection/search validation, direct cache assignment validation, parent-page constructor integrity, identity-field constructor integrity, and comment-field constructor integrity as active operational boundaries.

Those prior slices are not duplicates. Issue 303 validates malformed generated `created_by` user metadata at the page revision-list parser boundary. Issue 304 validates malformed generated `created_at` timestamp metadata at the parser boundary. Issue 442 validates the parent `page` field, Issue 465 validates the separate `id` and `rev_no` fields, and Issue 466 validates the separate `comment` field. None validates direct `PageRevision(created_by=..., created_at=...)` construction before malformed creator/time state becomes stored dataclass state in manually constructed revisions, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [466-pr-validate-page-revision-comment-field.md](466-pr-validate-page-revision-comment-field.md), and the adjacent constructor creator/time validation pattern from [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), and [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageRevision.created_by` validation at dataclass initialization.
- Add `PageRevision.created_at` validation at dataclass initialization.
- Reject non-`AbstractUser` creator values with `ValueError("created_by must be an AbstractUser")`.
- Reject non-`datetime` timestamp values with `ValueError("created_at must be a datetime")`.
- Update local page-revision fixtures and parser stubs that construct valid revisions to use real `User` objects instead of untyped placeholders.
- Preserve existing page revision-list parsing, parser diagnostics, lazy `Page.revisions`, `Page.latest_revision`, source/HTML acquisition, source/html setter validation, collection lookup, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page revision creator/time state integrity
- Test addition
- Test fixture cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(created_by=None)`, `True`, `12345`, `"test-user"`, and `{"id": 12345}` must raise `ValueError("created_by must be an AbstractUser")` when every other revision field is valid. |
| R2 | `PageRevision(created_at=None)`, `True`, `1700000000`, `"2023-01-01"`, and `[]` must raise `ValueError("created_at must be a datetime")` when every other revision field is valid. |
| R3 | Valid `AbstractUser` creator values and valid `datetime` timestamp values must remain valid and preserve existing revision fields. |
| R4 | Existing page revision-list parsing, parser-side revision ID/revision-number/user/timestamp diagnostics, direct page/identity/comment validation, lazy revision access, source/HTML acquisition, cache reuse, and adjacent page workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-revision tests, focused page/page-revision tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor creators fail at the public dataclass boundary. | `TestPageRevision.test_init_rejects_malformed_creators` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after creator validation was added. | Accepting missing values, booleans, integers, strings, dictionaries, arbitrary objects, or emitting revision rows with non-`AbstractUser` creator state rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Malformed constructor timestamps fail at the public dataclass boundary. | `TestPageRevision.test_init_rejects_malformed_created_at` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after timestamp validation was added. | Accepting missing values, booleans, epoch integers, date strings, lists, arbitrary objects, or emitting revision rows with non-`datetime` timestamp state rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid revision creator/time semantics stay green. | Existing page-revision tests and page workflow tests passed after valid direct fixtures used real `User` values for `created_by`. | Rejecting valid `AbstractUser` implementations, valid `datetime` values, parser-created revisions, or manually created valid revisions rejects this local completion claim. | Parser-created and manually created revisions | `tests/unit/test_page_revision.py`, `tests/unit/test_page.py` |
| R4 | Existing adjacent page workflows remain green. | `tests/unit/test_page_revision.py` passed 93 tests, focused page/page-revision tests passed 343 tests, adjacent page workflow tests passed 676 tests, and full unit tests passed 1860 tests. | Regressing page history parsing, parser diagnostics, direct revision source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, page source/file/vote workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page revision and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, revision HTML, revision comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0214554 fix(page_revision): validate revision creator metadata`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_creators tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_created_at -q` failed 10 tests before the fix; every malformed `created_by` or `created_at` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 10 tests after `PageRevision` creator/time validation was added.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 93 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py -q` passed 343 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 676 tests.
- `uv run pytest tests/unit -q` passed 1860 tests.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py tests/unit/test_page.py` passed.
- `uv run ruff format --check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py tests/unit/test_page.py` passed with 3 files already formatted.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py tests/unit/test_page.py` passed with no issues in 3 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/page_revision.py tests/unit/test_page_revision.py tests/unit/test_page.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, client mock typing, and site test mock typing issues. The changed source file and changed page/page-revision test files pass pyright together.

## Acceptance Criteria

- `PageRevision(created_by=None)`, `True`, `12345`, `"test-user"`, and `{"id": 12345}` raise `ValueError("created_by must be an AbstractUser")`.
- `PageRevision(created_at=None)`, `True`, `1700000000`, `"2023-01-01"`, and `[]` raise `ValueError("created_at must be a datetime")`.
- Valid `AbstractUser` creators and valid `datetime` timestamps remain valid.
- Existing page revision-list parsing, parser-side revision ID/revision-number/user/timestamp diagnostics, direct page/identity/comment validation, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, direct source/HTML acquisition, `PageRevisionCollection.find(...)`, source/html setter validation, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.created_by` and `PageRevision.created_at` are core audit fields for reconstructing page history, comparing revision timelines, and building generated revision ledgers. Parser paths already produce `AbstractUser` instances and `datetime` timestamps or contextual parser failures. Constructor validation keeps malformed local metadata out of fixtures, generated ledgers, migration comparisons, revision summaries, and downstream audit tooling while preserving parser and caller paths that construct valid revisions.

## Local Evidence

- Local rollout evidence used browser-free page revision reads, duplicate revision-list reuse, revision source/HTML fetches, latest-revision checks, generated page ledgers, and tests that seed revision objects directly.
- Existing local drafts covered page revision fetch retry behavior, duplicate revision-list and revision data reduction, parser row diagnostics, parser ID/revision-number/user/timestamp diagnostics, response diagnostics, cached direct acquisition, collection entry validation, collection initialization validation, loaded-collection search-key validation, source/html assignment validation, direct parent-page validation, direct identity-field validation, and direct comment-field validation, but did not cover direct `PageRevision(created_by=..., created_at=...)` construction.
- The focused RED failures showed invalid constructor creator/time fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, integer, string, dictionary, epoch-integer, date-string, and list values.
- This slice only validates page revision creator/time fields at construction. It does not change revision-list parsing, parser selectors, parser-side revision ID parsing, revision-number cell parsing, revision timestamp parsing, revision user parsing, comment extraction, source/HTML response parsing, cached duplicate behavior, collection lookup semantics, publish/edit behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, revision HTML, revision comments, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not verify user membership, compare creator/time fields against parent page metadata, require timezone-aware datetimes, coerce epoch integers or date strings, validate direct `_source` / `_html` constructor cache values, or change live client authentication; those are separate parser, cache, and workflow concerns.
