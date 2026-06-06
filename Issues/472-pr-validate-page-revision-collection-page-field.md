# PR Draft: Validate Page Revision Collection Page Field

## Summary

`PageRevisionCollection` stores the optional explicit parent `Page` used by browser-free page history reads, revision source/HTML acquisition, latest-revision workflows, duplicate cached revision-list clones, generated audit ledgers, local fixtures, and rehydrated revision state. Earlier local slices validated revision-list acquisition, parser-side revision diagnostics, collection lookup keys, acquisition-time collection entries, the collection's `revisions` container and entries, direct `Page.revisions` assignment, direct `PageRevision.page`, and direct `PageRevision` identity/comment/creator-time fields, but `PageRevisionCollection(page=..., revisions=...)` still accepted malformed explicit parent pages such as booleans, strings, dictionaries, and arbitrary objects.

This change validates non-`None` `PageRevisionCollection.page` constructor arguments before storing collection state. Malformed explicit values now raise `ValueError("page must be a Page")`. The existing `page=None` behavior remains valid: collections can still infer the parent from a valid first revision, and empty no-parent collections still expose `page is None`. Valid `Page` parents, empty revision lists, valid `PageRevision` lists, iteration, lookup, source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, parser diagnostics, direct `PageRevision` field validation, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct page-revision collections with malformed explicit parent-page state, while parser-created, fixture-created, cached-duplicate, inferred-parent, and manually created valid revision collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free revision list reads, revision source/HTML retrieval, page history audits, translation review ledgers, duplicate cached revision reuse, generated reports, migration scripts, or local fixtures that construct `PageRevisionCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revisions as a practical workflow surface. Existing drafts [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [466-pr-validate-page-revision-comment-field.md](466-pr-validate-page-revision-comment-field.md), and [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md) establish revision acquisition, parsing, cached reuse, lookup validation, assignment validation, collection entry validation, direct revision field validation, and local revision cache state as active operational boundaries.

Those prior slices are not duplicates. Issue 419 validates only the collection's `revisions` container and entries while preserving `PageRevisionCollection(revisions=[valid_revision])` inference. Issue 442 validates the `page` field on individual `PageRevision` records, not the collection parent. Issues 465-467 validate direct `PageRevision` identity, comment, creator, and timestamp fields. Issue 415 validates direct `Page.revisions = ...` assignment, and Issue 365 validates mutated collection entries before source/HTML acquisition. None validates direct non-`None` `PageRevisionCollection(page=...)` construction before malformed parent-page state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [466-pr-validate-page-revision-comment-field.md](466-pr-validate-page-revision-comment-field.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), and the adjacent optional collection parent validation pattern from [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate non-`None` `PageRevisionCollection.page` values at constructor initialization.
- Reject malformed explicit parent-page values with `ValueError("page must be a Page")`.
- Preserve `page=None` inference, empty no-parent construction, valid empty revision collections, valid `PageRevision` lists, iteration, lookup, parser-created collections, duplicate cached revision reuse, source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, and adjacent page workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Page revision parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection(page=True)`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` when `revisions` is otherwise valid. |
| R2 | `PageRevisionCollection(revisions=[valid_revision])` must still infer the page from the first revision, and `PageRevisionCollection(page=None, revisions=[])` must remain constructible with `page is None`. |
| R3 | Valid `Page` parent values, valid empty revision lists, valid `PageRevision` lists, iteration, `find(...)`, source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, duplicate cached revision reuse, parser diagnostics, direct `PageRevision` field validation, and adjacent page workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, page-revision tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent pages fail at the public constructor boundary. | `TestPageRevisionCollection.test_init_rejects_malformed_pages` failed RED for 4 malformed non-`None` values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting revision collections with malformed explicit parent state rejects this local completion claim. | PageRevisionCollection constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Optional no-parent and inference semantics stay green. | Existing empty initialization and page-inference tests passed in the 97-test page-revision module run. | Rejecting `page=None`, losing parent inference from the first valid revision, or changing empty no-parent collections away from `page is None` rejects this local completion claim. | PageRevisionCollection constructor | `tests/unit/test_page_revision.py` |
| R3 | Existing adjacent page workflows remain green. | `tests/unit/test_page_revision.py` passed 97 tests, adjacent page workflow tests passed 719 tests, and full unit tests passed 1903 tests. | Regressing source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, parser diagnostics, duplicate cached revision reuse, revision lookup, page source/file/vote workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page revision and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `eb964c3 fix(page_revision): validate revision collection page`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_init_rejects_malformed_pages -q` failed 4 tests before the fix; every malformed explicit `page` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `PageRevisionCollection` explicit page validation was added.
- `uv run pytest tests/unit/test_page_revision.py -q` passed 97 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 719 tests.
- `uv run pytest tests/unit -q` passed 1903 tests.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed page-revision test file pass pyright together.

## Acceptance Criteria

- `PageRevisionCollection(page=True)`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- `PageRevisionCollection(revisions=[valid_revision])` still infers the page from the first valid revision.
- `PageRevisionCollection(page=None, revisions=[])`, `PageRevisionCollection(page=<valid Page>, revisions=[])`, and `PageRevisionCollection(page=<valid Page>, revisions=[valid_revision])` remain valid.
- Existing valid `PageRevision` lists, iteration, `find(...)`, source/HTML acquisition, lazy `Page.revisions`, `Page.latest_revision`, parser-side revision diagnostics, direct `PageRevision` field validation, and duplicate cached revision reuse remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevisionCollection.page` is the collection-level parent used by source/HTML acquisition, lazy revision state, latest-revision workflows, cached duplicate revision reuse, and local fixture construction. Parser paths already create collections with valid owning pages or infer the parent from valid revisions; direct constructor validation keeps malformed explicit collection parents out of generated ledgers, migration comparisons, publication audits, and downstream tooling while preserving parser and caller paths that intentionally use `page=None` for inference.

## Local Evidence

- Local rollout evidence used browser-free revision acquisition, duplicate cached revision reuse, lazy source/HTML retrieval, revision count sync, edit cache invalidation, and tests that seed revision collections directly.
- Existing local drafts covered revision-list fetch deduplication, duplicate revision-list reuse, source/HTML body diagnostics, revision parser scoping, revision search-ID validation, acquisition-method entry validation, collection revisions/entry validation, direct `Page.revisions` assignment, direct revision parent validation, and direct revision field validation, but did not cover direct non-`None` `PageRevisionCollection(page=...)` construction.
- The focused RED failures showed invalid explicit constructor parent pages were accepted as collection state. The GREEN regression covers boolean, string, dictionary, and arbitrary object values while preserving `None` as the inference/no-parent sentinel.
- This slice only validates page-revision collection explicit parent-page constructor input. It does not change revision-list parsing, source/HTML parsing, collection lookup semantics, page edit behavior, duplicate source/vote/file behavior, publish behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only for explicit non-`None` parent values. It does not compare collection parent identity with each contained revision, coerce dictionaries into pages, reject `page=None`, verify site membership, change the empty no-parent `page is None` state, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
