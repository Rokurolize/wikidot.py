# PR Draft: Validate Page Revision Identity Fields

## Summary

`PageRevision` records carry the revision ID used by lazy source/HTML fetch requests and loaded-collection lookup, plus the revision number used by page history ordering, latest-revision selection, audit ledgers, and publication verification. Earlier local slices validated parser-side revision row IDs and revision-number cells, loaded-collection search keys, collection entries, `PageRevisionCollection(...)` initialization, `Page.revisions` assignments, direct `PageRevision.page` construction, and direct `PageRevision.source` / `PageRevision.html` assignments. The public `PageRevision(...)` constructor still accepted malformed direct `id` and `rev_no` values such as `None`, booleans, numeric strings, and floats, letting manually constructed, fixture-created, or rehydrated revision records carry malformed identity state.

This change validates `PageRevision.id` and `PageRevision.rev_no` at initialization. Malformed values now raise `ValueError("id must be an integer")` or `ValueError("rev_no must be an integer")`; valid non-boolean integer values remain valid. Existing page revision-list parsing, parser-side revision ID/revision-number/user/timestamp diagnostics, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, direct source/HTML acquisition, source/html setter validation, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct page revision records with malformed stored identity fields, while parser-created, fixture-created, and manually created valid revisions continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page revision history, source/HTML comparison, revision snapshot ledgers, translation audits, rollback tooling, publication verification, duplicate revision cache reuse, lazy `Page.revisions`, `Page.latest_revision`, direct `PageRevisionCollection.get_sources()` / `get_htmls()`, loaded collection `find(...)`, or local tests that construct `PageRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision identity as a practical workflow surface. Existing drafts [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), and [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md) establish page revision reads, retry behavior, deduplication, cached reuse, parser diagnostics, response diagnostics, collection/search validation, direct cache assignment validation, and parent-page constructor integrity as active operational boundaries.

Those prior slices are not duplicates. Issues 236 and 237 validate malformed generated revision row IDs and revision-number cells before parser-side `PageRevision` construction. Issue 376 validates caller-provided search keys passed to loaded `PageRevisionCollection.find(...)`, not stored constructor fields. Issue 442 validates the parent `page` field, and Issues 431 and 432 validate direct source/html cache assignment. This slice validates direct `PageRevision(id=..., rev_no=...)` construction so malformed identity values cannot become stored record state in manually constructed revisions, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), and the adjacent constructor identity-field validation pattern from [435-pr-validate-publish-result-page-ids.md](435-pr-validate-publish-result-page-ids.md), [451-pr-validate-private-message-id-field.md](451-pr-validate-private-message-id-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), and [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageRevision.id` validation at dataclass initialization.
- Add `PageRevision.rev_no` validation at dataclass initialization.
- Reject non-integer and boolean revision IDs with `ValueError("id must be an integer")`.
- Reject non-integer and boolean revision numbers with `ValueError("rev_no must be an integer")`.
- Preserve valid parser-created and directly constructed revisions with non-boolean integer IDs and revision numbers.
- Preserve existing page revision-list parsing, lazy `Page.revisions`, `Page.latest_revision`, source/HTML acquisition, source/html setter validation, collection lookup, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page revision identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(id=None)`, `True`, `"100"`, and `100.0` must raise `ValueError("id must be an integer")` when every other revision field is valid. |
| R2 | `PageRevision(rev_no=None)`, `True`, `"1"`, and `1.0` must raise `ValueError("rev_no must be an integer")` when every other revision field is valid. |
| R3 | Valid non-boolean integer `id` and `rev_no` values must remain valid and preserve existing revision fields. |
| R4 | Existing page revision-list parsing, parser-side revision ID/revision-number/user/timestamp diagnostics, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, source/HTML acquisition, source/html setter validation, collection lookup, and adjacent page workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page-revision tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor revision IDs fail at the public dataclass boundary. | `TestPageRevision.test_init_rejects_malformed_ids` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after ID validation was added. | Accepting missing values, booleans, numeric strings, floats, arbitrary objects, or emitting revision rows with non-integer `id` state rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Malformed constructor revision numbers fail at the public dataclass boundary. | `TestPageRevision.test_init_rejects_malformed_revision_numbers` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after revision-number validation was added. | Accepting missing values, booleans, numeric strings, floats, arbitrary objects, or emitting revision rows with non-integer `rev_no` state rejects this local completion claim. | PageRevision constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid revision identity semantics stay green. | Existing source, HTML, cache, parser, collection lookup, and page-revision tests passed after constructor validation was added. | Rejecting valid integer revision IDs or revision numbers, coercing numeric strings, or changing stored revision fields rejects this local completion claim. | Parser-created and manually created revisions | `tests/unit/test_page_revision.py` |
| R4 | Existing adjacent page workflows remain green. | `tests/unit/test_page_revision.py` passed 79 tests, adjacent page workflow tests passed 662 tests, and full unit tests passed 1846 tests. | Regressing page history parsing, direct revision source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, parser diagnostics, response diagnostics, page source/file/vote workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page revision and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, revision HTML, revision comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0b33cda fix(page_revision): validate revision identity fields`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_ids tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_malformed_revision_numbers -q` failed 8 tests before the fix; every malformed `id` or `rev_no` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 8 tests after `PageRevision` identity validation was added.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 79 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 662 tests.
- `uv run pytest tests/unit -q` passed 1846 tests.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `uv run ruff format --check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 2 files already formatted.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with no issues in 2 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 61 existing full-tree typing errors outside this slice, including page fixture `None` mismatches, an intentional invalid cookie-name test call, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, client mock typing, and site test mock typing issues. The changed source file and changed page-revision test file pass pyright together.

## Acceptance Criteria

- `PageRevision(id=None)`, `True`, `"100"`, and `100.0` raise `ValueError("id must be an integer")`.
- `PageRevision(rev_no=None)`, `True`, `"1"`, and `1.0` raise `ValueError("rev_no must be an integer")`.
- Valid non-boolean integer `id` and `rev_no` values remain valid.
- Existing page revision-list parsing, parser-side revision ID/revision-number/user/timestamp diagnostics, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, direct source/HTML acquisition, `PageRevisionCollection.find(...)`, source/html setter validation, and adjacent page workflows remain green.
- Existing page source/file/vote behavior, publish/create/edit behavior, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.id` is used for revision source/HTML module requests and loaded-collection lookup, while `PageRevision.rev_no` is the stable page-history ordering field behind latest-revision selection and generated revision ledgers. Parser paths already derive integer revision IDs from generated `revision-row-*` IDs and integer revision numbers from history table cells or report contextual parser failures. Constructor validation keeps malformed local identity state out of fixtures, generated ledgers, migration comparisons, source/HTML request planning, and downstream audit tooling while preserving parser and caller paths that construct valid revisions.

## Local Evidence

- Local rollout evidence used browser-free page revision reads, duplicate revision-list reuse, revision source/HTML fetches, lazy page revision reads, generated page ledgers, and tests that seed revision objects directly.
- Existing local drafts covered page revision fetch retry behavior, duplicate revision-list and revision data reduction, parser row diagnostics, parser ID/revision-number/user/timestamp diagnostics, response diagnostics, cached direct acquisition, collection entry validation, collection initialization validation, loaded-collection search-key validation, source/html assignment validation, and direct parent-page validation, but did not cover direct `PageRevision(id=..., rev_no=...)` construction.
- The focused RED failures showed invalid constructor identity fields were accepted as dataclass state. The GREEN regressions cover missing, boolean, numeric-string, and float `id` / `rev_no` values.
- This slice only validates page revision identity fields at construction. It does not change revision-list parsing, parser selectors, parser-side revision ID parsing, revision-number cell parsing, revision timestamp parsing, revision user parsing, source/HTML response parsing, cached duplicate behavior, collection lookup semantics, publish/edit behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, revision HTML, revision comments, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only. It does not require positive IDs, require contiguous revision numbers, verify that a revision ID belongs to the parent page, coerce numeric strings, validate creator/time/comment fields, validate direct `_source` or `_html` constructor cache values, or change live client authentication; those are separate object, parser, cache, and workflow concerns.
