# PR Draft: Validate Page File Collection Page Field

## Summary

`PageFileCollection` stores the optional explicit parent `Page` used by browser-free attachment inventories, lazy `Page.files`, duplicate cached file-list clones, generated asset ledgers, local fixtures, and rehydrated page-file state. Earlier local slices validated direct page-file acquisition, parser-side attachment field diagnostics, collection lookup keys, the collection's `files` container and entries, direct `PageFile.page`, and direct `PageFile` scalar/text fields, but `PageFileCollection(page=..., files=...)` still accepted malformed explicit parent pages such as booleans, strings, dictionaries, and arbitrary objects.

This change validates non-`None` `PageFileCollection.page` constructor arguments before storing collection state. Malformed explicit values now raise `ValueError("page must be a Page")`. The existing `page=None` behavior remains valid: collections can still infer the parent from a valid first file, and empty no-parent collections remain unchanged. Valid `Page` parents, empty file lists, valid `PageFile` lists, iteration, ID/name lookup, direct file acquisition, lazy `Page.files`, duplicate cached file reuse, parser diagnostics, direct `PageFile` field validation, and adjacent page workflows remain unchanged.

## Outcome

Callers cannot silently construct page-file collections with malformed explicit parent-page state, while parser-created, fixture-created, cached-duplicate, inferred-parent, and manually created valid file collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, generated asset ledgers, migration audits, publication checks, duplicate cached file reuse, lazy `Page.files`, direct `PageFileCollection.acquire(page)`, or local tests that construct `PageFileCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments and page-file inventories as practical workflow surfaces. Existing drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), and [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md) establish file fetches, parser diagnostics, response diagnostics, duplicate cache reuse, lookup validation, collection entry validation, direct parent-page validation, and direct file scalar/text validation as active operational boundaries.

Those prior slices are not duplicates. Issue 420 validates only the collection's `files` container and entries while explicitly preserving `PageFileCollection(page=None, files=[valid_file])` inference. Issue 443 validates the `page` field on individual `PageFile` records, not the collection parent. Issue 468 validates direct `PageFile` scalar/text fields. Issues 375 and 383 validate loaded-collection lookup keys after a collection exists. None validates direct non-`None` `PageFileCollection(page=...)` construction before malformed parent-page state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), and the adjacent collection parent validation pattern from [470-pr-validate-page-vote-collection-page-field.md](470-pr-validate-page-vote-collection-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate non-`None` `PageFileCollection.page` values at constructor initialization.
- Reject malformed explicit parent-page values with `ValueError("page must be a Page")`.
- Preserve `page=None` inference, empty no-parent construction, valid empty file collections, valid `PageFile` lists, iteration, lookup, parser-created collections, duplicate cached file reuse, direct acquisition, lazy `Page.files`, and adjacent page workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Page file parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection(page=True)`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` must raise `ValueError("page must be a Page")` when `files` is otherwise valid. |
| R2 | `PageFileCollection(page=None, files=[valid_file])` must still infer the page from the first file, and `PageFileCollection(page=None, files=[])` must remain constructible. |
| R3 | Valid `Page` parent values, valid empty file lists, valid `PageFile` lists, iteration, `find(...)`, `find_by_name(...)`, direct file acquisition, lazy `Page.files`, duplicate cached file reuse, parser diagnostics, direct `PageFile` field validation, and adjacent page workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, page-file tests, adjacent page workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent pages fail at the public constructor boundary. | `TestPageFileCollection.test_init_rejects_malformed_pages` failed RED for 4 malformed non-`None` values because the constructor did not raise, then passed GREEN after page validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting file collections with malformed explicit parent state rejects this local completion claim. | PageFileCollection constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Optional no-parent and inference semantics stay green. | Existing page-inference and initialization tests passed in the 82-test page-file module run. | Rejecting `page=None`, losing parent inference from the first valid file, or forcing empty no-parent collections to have a parent rejects this local completion claim. | PageFileCollection constructor | `tests/unit/test_page_file.py` |
| R3 | Existing adjacent page workflows remain green. | `tests/unit/test_page_file.py` passed 82 tests, adjacent page workflow tests passed 715 tests, and full unit tests passed 1899 tests. | Regressing direct acquisition, lazy `Page.files`, parser diagnostics, duplicate cached file reuse, file lookup, page source/revision/vote workflows, publish/create/edit, or site/page workflows rejects this local completion claim. | Page file and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, attachment payloads, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ddda065 fix(page_file): validate file collection page`.

- RED: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_malformed_pages -q` failed 4 tests before the fix; every malformed explicit `page` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `PageFileCollection` explicit page validation was added.
- `uv run pytest tests/unit/test_page_file.py -q` passed 82 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 715 tests.
- `uv run pytest tests/unit -q` passed 1899 tests.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed.
- `uv run mypy src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page_file.py tests/unit/test_page_file.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed page-file test file pass pyright together.

## Acceptance Criteria

- `PageFileCollection(page=True)`, `"test-page"`, `{"fullname": "test-page"}`, and `object()` raise `ValueError("page must be a Page")`.
- `PageFileCollection(page=None, files=[valid_file])` still infers the page from the first valid file.
- `PageFileCollection(page=None, files=[])`, `PageFileCollection(page=<valid Page>, files=[])`, and `PageFileCollection(page=<valid Page>, files=[valid_file])` remain valid.
- Existing valid `PageFile` lists, iteration, `find(...)`, `find_by_name(...)`, direct file acquisition, lazy `Page.files`, parser-side attachment diagnostics, direct `PageFile` field validation, and duplicate cached file reuse remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageFileCollection.page` is the collection-level parent used by cached duplicate file reuse, lazy file state, attachment ledgers, and local fixture construction. Parser paths already create collections with valid owning pages or infer the parent from valid files; direct constructor validation keeps malformed explicit collection parents out of generated ledgers, migration comparisons, publication audits, and downstream tooling while preserving parser and caller paths that intentionally use `page=None` for inference.

## Local Evidence

- Local rollout evidence used browser-free file acquisition, duplicate cached file reuse, lazy file state, attachment ledgers, and tests that seed file collections directly.
- Existing local drafts covered file-list acquisition, direct acquisition retries, duplicate request deduplication, cached duplicate file reuse, parser field diagnostics, response-body diagnostics, loaded-collection lookup validation, collection files/entry validation, direct file parent validation, and direct file scalar/text validation, but did not cover direct non-`None` `PageFileCollection(page=...)` construction.
- The focused RED failures showed invalid explicit constructor parent pages were accepted as collection state. The GREEN regression covers boolean, string, dictionary, and arbitrary object values while preserving `None` as the inference/no-parent sentinel.
- This slice only validates page-file collection explicit parent-page constructor input. It does not change file-list parsing, URL normalization, size parsing, MIME parsing, collection lookup semantics, page file mutation behavior, cache invalidation behavior, page source/revision/vote behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, attachment payloads, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only for explicit non-`None` parent values. It does not compare collection parent identity with each contained file, coerce dictionaries into pages, reject `page=None`, verify site membership, force empty no-parent collections to carry a parent, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
