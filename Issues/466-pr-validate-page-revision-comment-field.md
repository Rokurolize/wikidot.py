# PR Draft: Validate Page Revision Comment Field

## Summary

`PageRevision.comment` stores the page-history edit comment used by browser-free revision ledgers, latest-revision inspection, source/HTML comparisons, migration audits, and publication verification. Earlier local slices preserved parser-side page revision comment spacing and validated page write comment inputs, but the public `PageRevision(...)` constructor still accepted malformed direct `comment` values such as `None`, booleans, integers, and lists, letting manually constructed, fixture-created, or rehydrated revision records carry non-string comment state.

This change validates `PageRevision.comment` at initialization. Malformed values now raise `ValueError("comment must be a string")`; valid strings, including the empty string, remain valid. Existing page revision-list parsing, comment spacing, parser-side revision ID/revision-number/user/timestamp diagnostics, direct `PageRevision.page` and identity-field validation, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, direct source/HTML acquisition, source/html setter validation, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct page revision records with malformed stored comment fields, while parser-created, fixture-created, and manually created valid revisions continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page revision history, revision snapshot ledgers, source/HTML comparison, rollback tooling, publication verification, duplicate revision cache reuse, lazy `Page.revisions`, `Page.latest_revision`, direct `PageRevisionCollection.get_sources()` / `get_htmls()`, or local tests that construct `PageRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision comment state as a practical workflow surface. Existing drafts [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), and [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md) establish page revision parsing, text fidelity, cache reuse, response diagnostics, collection/search validation, page write comment validation, direct cache assignment validation, parent-page constructor integrity, and identity-field constructor integrity as active operational boundaries.

Those prior slices are not duplicates. Issue 114 preserves visible spacing while parsing generated revision comments. Issue 350 validates explicit page write comment inputs before mutation requests. Issue 465 validates the separate `id` and `rev_no` fields. None validates direct `PageRevision(comment=...)` construction before malformed comment state becomes stored dataclass state in manually constructed revisions, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), and the adjacent direct text-field validation pattern from [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), [450-pr-validate-site-application-text-fields.md](450-pr-validate-site-application-text-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), and [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageRevision.comment` validation at dataclass initialization.
- Reject non-string comments with `ValueError("comment must be a string")`.
- Preserve valid empty-string and ordinary string comments.
- Preserve existing page revision-list parsing, comment spacing, lazy `Page.revisions`, `Page.latest_revision`, source/HTML acquisition, source/html setter validation, collection lookup, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page revision comment state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(comment=None)`, `True`, `1`, and `[]` must raise `ValueError("comment must be a string")` when every other revision field is valid. |
| R2 | Valid string comments, including `""`, must remain valid and preserve stored values. |
| R3 | Existing page revision-list parsing, comment spacing, parser diagnostics, direct page/identity validation, lazy revision access, source/HTML acquisition, cache reuse, and adjacent page workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, page-revision tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor comments fail at the public dataclass boundary. | `TestPageRevision.test_init_rejects_malformed_comments` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after comment validation was added. | Accepting missing values, booleans, integers, lists, arbitrary objects, or emitting revision rows with non-string `comment` state rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Valid comment semantics stay green. | Existing page-revision tests and adjacent page tests passed after constructor validation was added. | Rejecting empty strings or ordinary strings, coercing non-strings, or changing stored comments rejects this local completion claim. | Parser-created and manually created revisions | `tests/unit/test_page_revision.py`, `tests/unit/test_page.py` |
| R3 | Existing adjacent page workflows remain green. | `tests/unit/test_page_revision.py` passed 83 tests, adjacent page workflow tests passed 666 tests, and full unit tests passed 1850 tests. | Regressing page history parsing, comment spacing, direct revision source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, parser diagnostics, response diagnostics, page source/file/vote workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page revision and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, revision HTML, revision comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8cc6946 fix(page_revision): validate revision comments`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_comments -q` failed 4 tests before the fix; every malformed `comment` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `PageRevision` comment validation was added.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 83 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 666 tests.
- `uv run pytest tests/unit -q` passed 1850 tests.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `uv run ruff format --check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 2 files already formatted.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with no issues in 2 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 61 existing full-tree typing errors outside this slice, including page fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, client mock typing, and site test mock typing issues. The changed source file and changed page-revision test file pass pyright together.

## Acceptance Criteria

- `PageRevision(comment=None)`, `True`, `1`, and `[]` raise `ValueError("comment must be a string")`.
- `PageRevision(comment="")` and ordinary string comments remain valid.
- Existing page revision-list parsing, page revision comment spacing, parser diagnostics, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, direct source/HTML acquisition, `PageRevisionCollection.find(...)`, source/html setter validation, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.comment` is the page-history edit-comment field used by revision ledgers, audit summaries, rollback inspection, and publication checks. Parser paths already produce strings from generated revision comment cells and preserve visible word boundaries. Constructor validation keeps malformed local comment state out of fixtures, generated ledgers, migration comparisons, and downstream audit tooling while preserving parser and caller paths that construct valid revisions.

## Local Evidence

- Local rollout evidence used browser-free page revision reads, duplicate revision-list reuse, revision source/HTML fetches, latest-revision checks, generated page ledgers, and tests that seed revision objects directly.
- Existing local drafts covered page revision comment spacing, page write comment inputs, page revision parser diagnostics, collection validation, source/html assignment validation, direct parent-page validation, and direct identity-field validation, but did not cover direct `PageRevision(comment=...)` construction.
- The focused RED failures showed invalid constructor comment fields were accepted as dataclass state. The GREEN regression covers missing, boolean, integer, and list comments.
- This slice only validates page revision comment shape at construction. It does not change revision-list parsing, comment extraction, comment spacing, parser selectors, source/HTML response parsing, cached duplicate behavior, collection lookup semantics, publish/edit behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, revision HTML, revision comments, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed comment values instead of coercing them. It does not validate creator/time fields, enforce non-empty comments, trim comments, alter generated comment spacing, or change live client authentication; those are separate parser, object, and workflow concerns.
