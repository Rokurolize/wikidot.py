# PR Draft: Validate Page File Page Field

## Summary

`PageFile` records carry the parent `Page` object used by direct file acquisition, lazy `Page.files`, batch page-file reuse, duplicate page-file cache reuse, attachment inventory ledgers, and file ownership checks. Earlier local slices validated page-file collection entries, `PageFileCollection(...)` initialization, file lookup keys, direct and batch acquisition responses, parser fields, and duplicate file-list ownership, but the public `PageFile(...)` constructor still accepted malformed `page` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `PageFile.page` at initialization. Malformed values now raise `ValueError("page must be a Page")`. Existing direct file acquisition, lazy `Page.files`, batch page-file acquisition, duplicate cached file reuse, parser-created file rows, collection behavior, and adjacent page workflows remain unchanged for valid `Page` objects.

## Outcome

Callers cannot silently construct attachment records whose parent page is not a `Page`, while valid parser-created, fixture-created, and manually created page files continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, page asset audits, generated migration ledgers, attachment search helpers, duplicate page-file cache reuse, direct `PageFileCollection.acquire(page)`, lazy `Page.files`, or local tests that construct `PageFile` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page-file ownership as a practical workflow surface. Existing drafts [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), and [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md) explicitly preserve duplicate page ownership by creating fresh `PageFile(page=page, ...)` objects for each owning page and by asserting parsed `PageFile.page` points at the owning duplicate page. Adjacent page-file drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), and [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md) establish file fetches, parser diagnostics, response diagnostics, lookup validation, and collection constructor integrity as active operational boundaries.

Those prior slices are not duplicates. They covered page-file fetching, retry behavior, parse reuse, cache reuse, duplicate file-list ownership, response diagnostics, parser field diagnostics, lookup key validation, and `PageFileCollection(page, files=...)` initialization. None validates direct `PageFile(page=...)` construction before malformed parent-page state becomes stored dataclass state.

## Related Issue

Builds directly on [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), and the adjacent constructor page-field validation pattern from [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageFile.page` validation at dataclass initialization.
- Reject non-`Page` values with `ValueError("page must be a Page")`.
- Update page-file unit fixtures to use real `Page` objects instead of generic page mocks for valid files and valid acquisition paths.
- Preserve existing direct file acquisition, lazy `Page.files`, batch page-file acquisition, duplicate cached file reuse, parser-created file rows, collection behavior, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page-file parent-page state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFile(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` when every other file field is valid. |
| R2 | Valid `Page` instances must remain valid and preserve existing file fields. |
| R3 | Existing direct file acquisition, lazy `Page.files`, batch page-file acquisition, duplicate cached file reuse, parser-created file rows, collection behavior, page write cache invalidation, and adjacent page workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, adjacent page-file/page tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor pages fail at the public dataclass boundary. | `TestPageFile.test_init_rejects_malformed_pages` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting attachment records with non-`Page` parent state rejects this local completion claim. | PageFile constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Valid page semantics stay green. | Existing page-file unit tests passed after local valid file fixtures were moved to real `Page` objects. | Rejecting valid `Page` instances, coercing page-like mocks, or changing stored file fields rejects this local completion claim. | PageFile fixtures and parser-created files | `tests/unit/test_page_file.py`, `tests/unit/test_page.py` |
| R3 | Existing adjacent page-file workflows remain green. | `tests/unit/test_page_file.py` passed 58 tests, `tests/unit/test_page.py` passed 250 tests, and full unit tests passed 1702 tests. | Regressing direct file acquisition, lazy `Page.files`, batch file acquisition, duplicate cached file reuse, parser-created rows, collection lookup behavior, page write cache invalidation, or adjacent page workflows rejects this local completion claim. | Page-file and page workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, file URLs from private sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `59e0ba1 fix(page_file): validate file page`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFile::test_init_rejects_malformed_pages -q` failed 5 tests before the fix; every malformed `page` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_page_file.py::TestPageFile::test_init_rejects_malformed_pages -q` passed 5 tests.
- `uv run pytest tests/unit/test_page_file.py -q` passed 58 tests.
- `uv run ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `uv run pyright src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_page.py -q` passed 250 tests.
- `uv run pytest tests/unit -q` passed 1702 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 114 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, `MagicMock.__str__` test assignments, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `PageFile(page=None)`, `True`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- Valid `Page` instances remain valid as `page`.
- Existing direct `PageFileCollection.acquire(page)`, lazy `Page.files`, batch `PageCollection.get_page_files()`, cached direct file reuse, duplicate page-file reuse, parser-created rows, and collection lookup behavior remain green.
- Existing page write cache invalidation for delete and rename remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageFile.page` is the parent context behind browser-free attachment inventories, direct file-list acquisition, lazy `Page.files`, collection-level file acquisition, duplicate page-file cache reuse, and file ownership checks. Constructor validation keeps malformed local parent-page state out of attachment rows while preserving parser and caller paths that construct files from real `Page` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used page-owned duplicate file lists and verified each parsed `PageFile.page` points at the owning duplicate page object.
- Existing local drafts covered page-file acquisition, retry behavior, duplicate request deduplication, parse reuse, cached duplicate file reuse, parser field diagnostics, response-body diagnostics, collection initialization validation, and ID/name lookup validation, but did not cover direct `PageFile(page=...)` construction.
- The focused RED failures showed invalid constructor page fields were accepted as dataclass state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object page values.
- This slice only validates page-file parent-page constructor input. It does not change direct file acquisition, collection-level file acquisition, parser selectors, file URL normalization, MIME parsing, size parsing, cached duplicate behavior, `find(...)`, `find_by_name(...)`, page source/revision/vote behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, file URLs from private sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `page` is a `Page` instance. It does not validate page IDs, page fullnames, site identity, file ID shape, file URL shape, MIME type shape, file size shape, or live client authentication at `PageFile` construction time; those are separate page object, parser, file-field, and workflow concerns.
