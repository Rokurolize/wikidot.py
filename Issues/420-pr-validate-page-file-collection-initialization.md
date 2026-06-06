# PR Draft: Validate Page File Collection Initialization

## Summary

`PageFileCollection` documents `files` as `list[PageFile] | None`, but its constructor accepted malformed containers and arbitrary list entries. A caller could construct `PageFileCollection(page, files=False)`, which silently became an empty collection, or `PageFileCollection(page, files="file")`, `PageFileCollection(page, files=("file",))`, and `PageFileCollection(page, files=[None])`, which could store malformed collection entries or raise incidental low-level exceptions.

This change validates constructor input before storing entries. Non-list non-`None` `files` values now raise `ValueError("files must be a list or None")`; list entries that are not `PageFile` now raise `ValueError("files list entries must be PageFile")`. `files=None`, empty collections, valid `PageFile` lists, page inference from a valid first file, iteration, `find(...)`, `find_by_name(...)`, direct file acquisition, lazy `Page.files`, collection-level file acquisition, cached direct file reuse, and duplicate page-file reuse remain unchanged.

## Outcome

Callers cannot silently create malformed `PageFileCollection` instances through the public constructor, while existing page-file fetch, parser, cache, and lookup behavior remains intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventory reads, page asset audits, generated migration ledgers, attachment search helpers, duplicate page-file cache reuse, direct `PageFileCollection.acquire(page)`, lazy `Page.files`, or local fixtures that construct file collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments and page-file inventory as practical workflow surfaces. Existing drafts [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), and [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md) establish page-file acquisition, parser diagnostics, cached and duplicate workflows, response diagnostics, and loaded-collection lookup validation as active operational boundaries. Adjacent constructor-hardening drafts [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), and [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md) establish the local state-integrity pattern for collection constructors.

Those prior slices are not duplicates. Issues039, 041, 064, 075, 130, 144, 181, 193, 215, 224, 325, and 334 covered page-file fetching, retry behavior, cache reuse, response diagnostics, and duplicate file-list reuse; Issues095, 117, 274, 275, 276, 277, and 286 covered parser behavior and parsed file-field diagnostics; Issues375 and 383 validated caller-provided lookup keys after a collection already exists. None of them validates the `PageFileCollection(page, files=...)` constructor itself before malformed file entries become stored list state.

## Related Issue

Builds directly on [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), and the adjacent constructor validation pattern from [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), and [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageFileCollection.__init__(..., files=...)` validation.
- Preserve `files=None` as an empty collection.
- Reject non-list non-`None` `files` with `ValueError("files must be a list or None")`.
- Reject non-`PageFile` list entries with `ValueError("files list entries must be PageFile")`.
- Preserve valid empty collections, valid `PageFile` entries, page inference, iteration, `find(...)`, `find_by_name(...)`, direct acquisition, lazy `Page.files`, collection-level file acquisition, cached direct acquisition, and duplicate page-file reuse behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Page file collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection(page, files=True)`, `False`, `"file"`, `("file",)`, and `100` must raise `ValueError("files must be a list or None")` before storing collection entries. |
| R2 | `PageFileCollection(page, files=[None])`, `[True]`, `["file"]`, and `[{"id": 100}]` must raise `ValueError("files list entries must be PageFile")` before storing collection entries. |
| R3 | `PageFileCollection(page, files=None)`, `PageFileCollection(page, files=[])`, and `PageFileCollection(page, files=[valid_file])` must remain valid, and `PageFileCollection(page=None, files=[valid_file])` must still infer the page from that file. |
| R4 | Existing iteration, `find(...)`, `find_by_name(...)`, direct file acquisition, lazy `Page.files`, collection-level file acquisition, cached direct acquisition, duplicate page-file reuse, page source/revision/vote workflows, and site/page workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent page-file and page acquisition tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestPageFileCollection.test_init_rejects_non_list_files` failed RED for `True`, `False`, `"file"`, `("file",)`, and `100`, then passed GREEN after constructor validation was added. | Treating `False` as empty, accepting strings or tuples as file lists, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | PageFileCollection constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Non-`PageFile` constructor list entries fail at the public constructor boundary. | `TestPageFileCollection.test_init_rejects_non_file_entries` failed RED for `None`, `True`, `"file"`, and `{"id": 100}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized file records, or fixture stand-ins as stored files rejects this local completion claim. | PageFileCollection constructor | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R3 | Valid constructor inputs remain green. | Existing initialization, page-inference, iteration, `find(...)`, and `find_by_name(...)` tests passed in the 53-test page-file module run. | Rejecting `None`, empty valid lists, valid file lists, normal page inference, iteration, ID lookup, or name lookup rejects this local completion claim. | PageFileCollection constructor and methods | `tests/unit/test_page_file.py` |
| R4 | Existing page-file and adjacent workflows remain green. | `tests/unit/test_page_file.py` passed 53 tests, page property/acquisition tests passed 113 tests, page/page-file/page-revision/page-votes/site tests passed 542 tests, and full unit tests passed 1520 tests. | Regressing direct file acquisition, lazy `Page.files`, cached direct acquisition, duplicate page-file reuse, parser diagnostics, response diagnostics, ID/name lookup, page source/revision/vote reads, publish/create/edit, or site/page workflows rejects this local completion claim. | Page file and adjacent page/site workflows | `tests/unit/test_page_file.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page-file/page/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `abdf95d fix(page_file): validate file collection initialization`.

- RED: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_non_list_files -q` failed 5 tests before the container fix; `False`, strings, and tuples were accepted, while `True` and `100` leaked incidental `TypeError`.
- GREEN: the same focused command passed 5 tests after adding non-list validation.
- RED: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_non_file_entries -q` failed 4 tests before the entry fix because malformed list entries were accepted and stored.
- GREEN: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_non_list_files tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_non_file_entries tests/unit/test_page_file.py::TestPageFileCollection::test_init_with_page tests/unit/test_page_file.py::TestPageFileCollection::test_init_infers_page_from_files tests/unit/test_page_file.py::TestPageFileCollection::test_init_with_files -q` passed 12 tests after adding entry validation.
- `uv run ruff format src/wikidot/module/page_file.py tests/unit/test_page_file.py` left 2 files unchanged.
- `uv run --extra test pytest tests/unit/test_page_file.py -q` passed 53 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 113 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 542 tests.
- `uv run --extra test pytest tests/unit -q` passed 1520 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PageFileCollection(page, files=True)`, `False`, `"file"`, `("file",)`, and `100` raise `ValueError("files must be a list or None")`.
- `PageFileCollection(page, files=[None])`, `[True]`, `["file"]`, and `[{"id": 100}]` raise `ValueError("files list entries must be PageFile")`.
- `PageFileCollection(page, files=None)`, `PageFileCollection(page, files=[])`, and `PageFileCollection(page, files=[valid_file])` continue to work.
- `PageFileCollection(page=None, files=[valid_file])` still infers the page from that file.
- Existing iteration, `find(...)`, `find_by_name(...)`, direct file acquisition, lazy `Page.files`, collection-level file acquisition, cached direct acquisition, duplicate page-file reuse, page source/revision/vote reads, create/edit, publish, and site/page behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageFileCollection` is the stored object shape behind browser-free attachment inventories, direct file-list acquisition, lazy `Page.files`, collection-level file acquisition, duplicate page-file cache reuse, and file ID/name lookup. Constructor validation keeps malformed local state out of the collection while preserving existing fetch, parser, cache, and lookup behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free file acquisition, duplicate page-file list reuse, lazy page-file reads, attachment searches, and tests that seed file collections directly.
- Existing local drafts covered page-file fetch retry behavior, duplicate file-list reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct acquisition, and ID/name lookup validation, but did not cover the `PageFileCollection(page, files=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was treated as empty, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, page inference, and adjacent file/page workflows.
- This slice only validates page-file collection constructor input. It does not change direct file acquisition, collection-level file acquisition, parser selectors, file URL normalization, MIME parsing, size parsing, cached duplicate behavior, `find(...)`, `find_by_name(...)`, page source/revision/vote behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed file-like objects and test mocks in `PageFileCollection`. Callers should construct real `PageFile` entries before storing them in a file collection.
