# PR Draft: Validate PageCollection Search Fullnames

## Summary

`PageCollection.find(fullname)` documents `fullname` as a string, but malformed caller-provided search keys were not rejected at the public loaded-collection lookup boundary. Values such as `None`, booleans, integers, and floats were treated as ordinary misses instead of stable caller errors.

This change validates the search key before scanning stored pages. Malformed `fullname` values now raise `ValueError("fullname must be a string")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for string page fullnames.

## Outcome

Page collection callers now get deterministic Python-side preflight validation for malformed page search fullnames instead of silent misses that can hide generated-ledger, JSON, CLI, or spreadsheet input bugs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page search, large page/source collection, page lookup reconciliation, publication checks, archival indexing, migration tooling, or generated page inventories that need stable loaded-collection lookup behavior.

## Current Evidence

Local rollout-backed drafts repeatedly identify page search, ListPages parsing, page-source collection, direct page lookup, and ledger-friendly page/source results as practical read surfaces. Existing drafts [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [005-pr-bound-listpages-pagination-by-limit.md](005-pr-bound-listpages-pagination-by-limit.md), [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [023-pr-search-pagination-validation.md](023-pr-search-pagination-validation.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [092-pr-scope-listpages-field-markup.md](092-pr-scope-listpages-field-markup.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [132-pr-reuse-cached-duplicate-page-ids.md](132-pr-reuse-cached-duplicate-page-ids.md), [203-pr-site-page-get-miss-site-context.md](203-pr-site-page-get-miss-site-context.md), [183-pr-listpages-fetch-failure-context.md](183-pr-listpages-fetch-failure-context.md), [220-pr-listpages-response-body-context.md](220-pr-listpages-response-body-context.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [345-pr-validate-source-iterator-batch-sizes.md](345-pr-validate-source-iterator-batch-sizes.md), and [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md) cover page discovery, pagination, iterator ergonomics, response diagnostics, parser scoping, source ledgers, input validation for search construction, and batch operation entry validation. Adjacent loaded-collection search preflight drafts [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), and [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md) establish the local pattern for validating lookup keys before scanning already loaded objects.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, validate page search construction parameters, validate page collection entries for batch operations, or validate other collection lookup keys. They do not validate the caller-provided search key to an already loaded `PageCollection.find(...)` before scanning stored pages.

## Related Issue

Builds directly on the page discovery and page-source hardening line from [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [049-pr-filter-iterators-by-required-tags.md](049-pr-filter-iterators-by-required-tags.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [330-pr-listpages-response-body-type-context.md](330-pr-listpages-response-body-type-context.md), [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md), [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md), and the adjacent `find(...)` preflight pattern from [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageCollection.find(fullname=...)` accepts only strings before scanning stored pages.
- Preserve valid `collection.find("test-page")` behavior when a matching page exists.
- Preserve valid unknown string behavior: a well-formed absent fullname still returns `None`.
- Preserve ListPages parsing, page lookup fallback, search pagination, source iteration, page detail acquisition, page collection batch operations, and page write helpers.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page collection lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection.find(fullname=...)` must reject `None`, booleans, integers, floats, and other non-string values with `ValueError("fullname must be a string")` before scanning pages. |
| R2 | Valid lookup must remain unchanged for string fullnames that match stored pages. |
| R3 | Valid not-found behavior must remain unchanged for string fullnames that are absent from the collection. |
| R4 | Existing ListPages parsing, direct page lookup fallback, search pagination, source iteration, page detail acquisition, page collection batch operations, and page write helpers must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page tests, adjacent page/site/detail tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed page fullnames fail before collection iteration can compare them with stored page fullnames. | `TestPageCollectionInit.test_find_rejects_non_string_fullnames` failed RED before the fix for `None`, `True`, `123`, and `1.0`, then passed GREEN after validation was added. | Treating malformed fullnames as ordinary misses, coercing values, or scanning pages with non-string keys rejects this local completion claim. | Page collection fullname search preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Matching string search keys still return the stored `Page`. | Existing `test_find_existing_page` passed after validation was added. | Changing returned page identity, rejecting valid string fullnames, or comparing unrelated fields rejects this local completion claim. | Page collection lookup | `tests/unit/test_page.py` |
| R3 | Missing string search keys still return `None`. | Existing `test_find_nonexistent_page` passed after validation was added. | Raising for a valid but absent string fullname or changing not-found behavior rejects this local completion claim. | Page collection lookup | `tests/unit/test_page.py` |
| R4 | Adjacent page behavior remains green. | `tests/unit/test_page.py` passed 204 tests, adjacent page/site/detail tests passed 426 tests, and full unit tests passed 1102 tests. | Regressing `PageCollection.get_by_fullname(...)`, ListPages parsing, search pagination, source iteration, page file/revision/vote acquisition, page collection batch operations, or page write helpers rejects this local completion claim. | Page workflow | affected page, site, page-file, page-revision, and page-vote tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, generated page source from real sites, private page names, private edit comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page tests passed, adjacent page/site/detail tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `9d0d9c0 fix(page): validate page collection search fullnames`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionInit::test_find_rejects_non_string_fullnames` failed 4 parameterized cases before the fix because malformed fullnames did not raise.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionInit::test_find_rejects_non_string_fullnames` passed 4 tests after adding fullname search preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py` passed 204 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py` passed 426 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1102 tests.
- `.venv/bin/ruff check src/wikidot/module/page.py tests/unit/test_page.py` passed.
- `.venv/bin/ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find(123)`, and `collection.find(1.0)` raise `ValueError("fullname must be a string")`.
- A well-formed string fullname matching an existing page still returns that page.
- A well-formed string fullname that is absent from the collection still returns `None`.
- Existing ListPages parsing, direct page lookup fallback, search pagination, source iteration, page detail acquisition, page collection batch operations, page file/revision/vote acquisition, and page write behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private page content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting non-string search keys can expose caller bugs that previously looked like ordinary misses. Mitigation: the documented API type is a string fullname; deterministic preflight is safer than silently hiding malformed generated input.
- Risk: The helper is also used by page-write validation. Mitigation: this change only calls the existing helper in the read-only collection search path; it does not change the helper itself or any write behavior.
- Risk: Diagnostics could expose private page context. Mitigation: the new error message contains only the input-field name and expected type, not page names, source text, response bodies, site names, account names, or edit comments.

## Dependencies

- Existing `PageCollection` storage and iteration semantics remain authoritative for valid string search keys.
- Existing `PageCollection.get_by_fullname(...)` fallback behavior remains unchanged for valid string fullnames.
- Existing ListPages parsing, source iterator, page detail acquisition, and page write helpers remain unchanged.
- The validation is local to `src/wikidot/module/page.py` and does not affect page search request construction, direct source/revision/file/vote acquisition, page mutations, forum behavior, private-message behavior, site-member behavior, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered page collection search-fullname validation path.

## Upstream-Safe Motivation

Page collection lookup is often fed by generated page inventories, search ledgers, source-collection records, migration manifests, publication checks, or CLI/JSON inputs. Since `find(...)` compares supplied values against stored page fullnames, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page search and page/source collection as practical workflows through ListPages retrying, bounded search iteration, source iteration, required-tag filtering, source result ledgers, parser scoping, response-body diagnostics, and page collection batch operations.
- Existing page drafts covered fetching, parsing, response diagnostics, search construction inputs, collection entries for batch operations, source/result ergonomics, and page write inputs; they did not validate caller-provided search keys to `PageCollection.find(fullname=...)`.
- This slice only validates loaded page collection search-fullname inputs. It does not change ListPages request construction, direct page lookup fallback, source iteration, page detail acquisition, page file/revision/vote parsing, batch operations, page mutations, forum behavior, private-message behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page source, raw rendered page content, private page names, private edit comments, forum content from real sites, private message content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search fullnames instead of coercing them. Callers that load page lookup targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into strings before calling `PageCollection.find(...)`.
