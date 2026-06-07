# PR Draft: Validate Page File Collection Page Ownership

## Summary

`PageFileCollection` validates explicit collection parent types, validates its `files` container and entries, and each `PageFile` validates its own retained `page`, but the public collection constructor did not ensure contained files all belong to the effective collection page. A caller could construct `PageFileCollection(page_a, [file_from_page_b])`; a caller could also rely on parent inference with `PageFileCollection(page=None, files=[file_from_page_a, file_from_page_b])`, which inferred `page_a` from the first file while retaining a valid file from `page_b`.

This change validates file entry ownership at the public `PageFileCollection.__init__` boundary after entry validation and effective page selection but before list state is stored. Files whose retained `file.page` is not the collection page now raise `ValueError("files must belong to the collection page")`. Valid explicit same-page collections, valid inferred same-page collections, empty no-parent collections, ID/name lookup, direct file acquisition, batched page-file acquisition, parser-created collections, lazy `Page.files`, duplicate cached file reuse, file cache invalidation, and adjacent page/source/revision/vote/site workflows remain unchanged.

## Outcome

Page file collections reject different-page file entries before local collection state can represent one page while storing another page's attachments.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free attachment inventories, generated asset ledgers, migration audits, publication checks, duplicate cached file reuse, lazy `Page.files`, direct `PageFileCollection.acquire(page)`, attachment lookup helpers, or local tests that construct `PageFileCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments and page-owned file collections as practical workflow surfaces. Existing drafts [064-pr-deduplicate-page-file-fetches.md](064-pr-deduplicate-page-file-fetches.md), [075-pr-reuse-page-file-list-parsing.md](075-pr-reuse-page-file-list-parsing.md), [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [181-pr-page-file-direct-fetch-context.md](181-pr-page-file-direct-fetch-context.md), [193-pr-page-file-direct-fetch-site-context.md](193-pr-page-file-direct-fetch-site-context.md), [215-pr-page-file-response-body-context.md](215-pr-page-file-response-body-context.md), [224-pr-page-file-batch-response-body-context.md](224-pr-page-file-batch-response-body-context.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [325-pr-page-file-response-body-type-context.md](325-pr-page-file-response-body-type-context.md), [334-pr-page-file-batch-response-body-type-context.md](334-pr-page-file-batch-response-body-type-context.md), [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [383-pr-validate-page-file-find-by-name.md](383-pr-validate-page-file-find-by-name.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [493-pr-validate-page-constructor-files-cache.md](493-pr-validate-page-constructor-files-cache.md), [536-pr-preserve-empty-page-file-parent.md](536-pr-preserve-empty-page-file-parent.md), [586-pr-validate-page-batch-target-site.md](586-pr-validate-page-batch-target-site.md), [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md), and [588-pr-validate-page-vote-collection-page-ownership.md](588-pr-validate-page-vote-collection-page-ownership.md) establish file reads, parser diagnostics, response diagnostics, duplicate cache reuse, lookup validation, collection entry validation, direct file parent validation, explicit collection parent validation, cached-file validation, empty parent handling, and adjacent ownership hardening as active operational boundaries.

This slice is not a duplicate of those issues. Issue 471 validates explicit non-`None` `PageFileCollection.page` field type while preserving inference and empty no-parent semantics. Issue 443 validates each `PageFile.page` field type. Issue 420 validates the collection's `files` container and entries. Issue 536 preserves empty `page=None` collection readability. Issue 493 validates a `Page` object's optional `_files` cache slot. None validates a valid `PageFile` entry whose retained `file.page` is individually valid but does not match the collection page selected explicitly or inferred from the first file.

No upstream issue was filed from this local workspace.

## Changes

- Add a page-file collection ownership preflight at `PageFileCollection.__init__`.
- Reject explicit different-page file entries with `ValueError("files must belong to the collection page")`.
- Reject inferred-parent mixed-page file collections with the same diagnostic.
- Preserve explicit valid parents, inferred valid parents, empty no-parent collections, valid file lists, ID/name lookup, direct file acquisition, batched page-file acquisition, parser-created collections, duplicate cached file reuse, lazy `Page.files`, file cache invalidation, and adjacent page workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Page file parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection(page_a, [file_from_page_b])` must reject the different-page file with `ValueError("files must belong to the collection page")` before storing collection list state. |
| R2 | `PageFileCollection(page=None, files=[file_from_page_a, file_from_page_b])` must infer `page_a` from the first file and reject the second different-page file with the same diagnostic before storing collection list state. |
| R3 | Valid explicit same-page file collections, valid inferred same-page file collections, and empty no-parent collections must remain valid. |
| R4 | Existing `find(...)`, `find_by_name(...)`, direct file acquisition, batched page-file acquisition, parser diagnostics, lazy `Page.files`, duplicate cached file reuse, file cache invalidation, and adjacent page source/revision/vote/site workflows must remain unchanged. |
| R5 | Focused RED/GREEN, page-file module coverage, page/page-file coverage, adjacent page/page-revision/page-file/page-vote/site tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit different-page file entries fail at the public collection constructor boundary. | `TestPageFileCollection.test_init_rejects_file_from_different_page` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("files must belong to the collection page")`. | Accepting the different-page file, storing a collection for `page_a` that contains a file retained from `page_b`, or deferring failure to lookup/cache code rejects this local completion claim. | `PageFileCollection.__init__` | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | Inferred-parent mixed-page file entries fail at the same constructor boundary. | `TestPageFileCollection.test_init_rejects_mixed_page_files_when_page_is_inferred` failed RED with `DID NOT RAISE`, then passed GREEN with the same diagnostic. | Inferring `page_a` from the first file while storing a file retained from `page_b`, accepting mixed inferred collections, or rejecting all inferred collections rejects this local completion claim. | `PageFileCollection.__init__` | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R3 | Valid file collection construction semantics stay green. | `tests/unit/test_page_file.py` passed 90 tests after the ownership preflight. | Rejecting valid same-page explicit collections, valid same-page inferred collections, empty no-parent collections, or normal page inference rejects this local completion claim. | Page file collections | `tests/unit/test_page_file.py` |
| R4 | Existing page file and adjacent page workflows remain green. | Page/page-file coverage passed 386 tests, adjacent page/page-revision/page-file/page-vote/site coverage passed 825 tests, and the full unit suite passed 2693 tests. | Regressing direct acquisition, batched file acquisition, parser diagnostics, file lookup, lazy `Page.files`, duplicate cached file reuse, rename/destroy file cache invalidation, page source/revision/vote behavior, or site/page workflows rejects this local completion claim. | Page file and adjacent page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, full `pyright`, and `git diff --check` passed. Full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted; full mypy found no issues in 87 source files. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic valid `Page` and `PageFile` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, attachment payloads, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `26fae84 fix(page_file): validate file collection page ownership`.

- RED explicit target-page ownership: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_file_from_different_page -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused explicit ownership regression: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_file_from_different_page -q` passed 1 test.
- RED inferred target-page ownership: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_mixed_page_files_when_page_is_inferred -q` failed before the inferred-branch fix with `DID NOT RAISE`.
- GREEN focused ownership coverage: `uv run pytest tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_file_from_different_page tests/unit/test_page_file.py::TestPageFileCollection::test_init_rejects_mixed_page_files_when_page_is_inferred -q` passed 2 tests.
- Page file module coverage: `uv run pytest tests/unit/test_page_file.py -q` passed 90 tests.
- Page/page-file coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_file.py -q` passed 386 tests.
- Adjacent page/page-revision/page-file/page-vote/site tests: `uv run pytest tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 825 tests.
- `uv run pytest tests/unit -q` passed 2693 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFileCollection(page_a, [file_from_page_b])` raises `ValueError("files must belong to the collection page")` before storing collection list state.
- `PageFileCollection(page=None, files=[file_from_page_a, file_from_page_b])` raises the same diagnostic after inferring the first file's page and before storing collection list state.
- `PageFileCollection(page=<valid Page>, files=[])`, `PageFileCollection(page=<valid Page>, files=[same_page_file])`, `PageFileCollection(page=None, files=[same_page_file])`, and `PageFileCollection(page=None, files=[])` remain valid.
- Existing `find(...)`, `find_by_name(...)`, direct file acquisition, batched page-file acquisition, parser diagnostics, lazy `Page.files`, duplicate cached file reuse, file cache invalidation, and adjacent page source/revision/vote/site behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageFileCollection.page` and each retained `PageFile.page` should describe the same owning page for browser-free attachment inventories, duplicate cached file reuse, lazy file state, attachment lookup, generated asset ledgers, migration audits, and file cache invalidation checks. Parser paths already create files from the owning page, and same-page duplicate cache reuse already builds fresh file objects for duplicate page objects; constructor ownership validation keeps mismatched rehydrated records, fixtures, or generated ledgers from silently carrying another page's files under the collection page.

## Local Evidence, Not For Upstream Paste

- The explicit RED failure showed a valid file from another page could be accepted by `PageFileCollection(page, [file])` without ownership rejection.
- The inferred RED failure showed `PageFileCollection(page=None, files=[file_from_page_a, file_from_page_b])` could infer a collection page from the first file while retaining another page's file.
- Existing local drafts covered file-list acquisition, duplicate request deduplication, cached duplicate file reuse, parser diagnostics, response-body diagnostics, file lookup validation, collection files/entry validation, direct file parent validation, direct collection-parent validation, empty no-parent handling, and direct page-files cache validation, but did not compare each valid `PageFile.page` to the effective collection page.
- This slice only validates page-file collection target-page ownership at collection initialization. It does not change file-list parsing, URL normalization, size parsing, MIME parsing, collection lookup semantics, page file mutation behavior, cache invalidation behavior, page source/revision/vote behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, attachment payloads, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally uses object identity. A page-owned file collection should contain `PageFile` objects retained from the exact owning `Page` object, matching parser-created files, duplicate cached file clones, and the existing first-file inference contract. It does not infer a collection page from a later file, coerce page-like objects, compare by fullname alone, verify remote site membership, or change live client authentication; those are separate parser, lookup, and workflow concerns.
