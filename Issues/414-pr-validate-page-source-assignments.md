# PR Draft: Validate Page Source Assignments

## Summary

`Page.source` is a public property that lazily acquires and caches a `PageSource` object. The setter documented `value` as `PageSource`, but it accepted any object. A caller could assign `page.source = None`, `page.source = True`, `page.source = "cached source"`, or `page.source = {"wiki_text": "cached source"}`, causing the public property to clear the cache, return a malformed object, or defer a low-level failure to later code that expects `PageSource.wiki_text`.

This change validates direct `Page.source` assignments as real `PageSource` objects. Invalid assignments now raise `ValueError("page.source must be PageSource")` before mutating `_source`, preserving the last valid cached source when one exists.

## Outcome

Manually constructed, fixture-created, duplicate-reused, or ledger-rehydrated `Page` objects can no longer silently corrupt their cached source object through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page source reads, page publishing, source verification, corpus collection, generated page ledgers, migration scripts, translation audits, or local tests that construct `Page` objects directly.

## Current Evidence

Local rollout evidence repeatedly uses page source caching as a practical workflow boundary. Existing drafts [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [019-pr-page-source-iterator-fallback.md](019-pr-page-source-iterator-fallback.md), [025-pr-source-result-error-page-context.md](025-pr-source-result-error-page-context.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), [051-pr-preserve-source-batch-successes.md](051-pr-preserve-source-batch-successes.md), [052-pr-source-result-context-properties.md](052-pr-source-result-context-properties.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [069-pr-source-result-ledger-record.md](069-pr-source-result-ledger-record.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), [195-pr-source-iterator-site-context.md](195-pr-source-iterator-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), and [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md) establish page source state as an active operational surface.

Those prior slices are not duplicates. Issues013, 194, and 195 improved source acquisition and failure context, Issues019, 025, 027, 051, 052, 069, 225, and 338 improved source iterator and ledger behavior, Issue062 deduplicated source fetches, Issue127 reused cached duplicate source data while preserving ownership, Issue349 validated page source text inputs for write helpers, and Issue413 validated direct `Page.id` assignment. None of them validates direct public `Page.source = ...` assignments before cached state mutation.

## Related Issue

Builds directly on [013-pr-refresh-cached-page-source.md](013-pr-refresh-cached-page-source.md), [062-pr-deduplicate-page-source-fetches.md](062-pr-deduplicate-page-source-fetches.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [194-pr-page-source-site-context.md](194-pr-page-source-site-context.md), [225-pr-source-result-page-id-ledger.md](225-pr-source-result-page-id-ledger.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), and [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `PageSource` object validator for direct `Page.source` assignments.
- Reject `None`, booleans, strings, dictionaries, and other non-`PageSource` values with `ValueError("page.source must be PageSource")`.
- Validate before assigning `_source`, so invalid assignments preserve any previously cached valid source.
- Preserve valid `PageSource` assignments and existing lazy `Page.source` acquisition behavior.
- Preserve existing page source acquisition, refresh, source iterator, duplicate-cache reuse, create/edit, publish, source verification, and source-result ledger behavior.
- Do not add owner identity validation for `PageSource.page`; this slice only enforces the documented object shape and avoids changing legitimate caller-created `PageSource` replacement behavior.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `page.source = None`, `page.source = True`, and `page.source = False` must raise `ValueError("page.source must be PageSource")` before mutating `_source`. |
| R2 | `page.source = "cached source"` and `page.source = {"wiki_text": "cached source"}` must raise the same stable diagnostic before mutating `_source`. |
| R3 | Invalid assignments after an already-cached valid `PageSource` must preserve that previous source object. |
| R4 | Valid `PageSource` assignments must remain allowed. |
| R5 | Lazy source acquisition, explicit source refresh, source iterator, duplicate cached source reuse, create/edit, publish, source verification, and source-result ledger workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent page/site tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Missing and boolean assignments fail before local source cache mutation. | New `TestPageProperties.test_source_setter_rejects_invalid_sources` failed RED for `None`, `True`, and `False` because the setter did not raise, then passed GREEN after validation was added. | Accepting `None`, treating booleans as source objects, clearing `_source`, or surfacing later lazy-fetch/request failures rejects this local completion claim. | Direct page source setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | String and dictionary assignments fail with the same stable diagnostic before local source cache mutation. | The same focused regression failed RED for `"cached source"` and `{"wiki_text": "cached source"}`, then passed GREEN after validation was added. | Returning a raw string or dictionary from `Page.source`, storing the malformed value, or deferring failure to `wiki_text` access rejects this local completion claim. | Direct page source setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Invalid assignments preserve the previous valid cached source. | The focused GREEN asserts `mock_page_with_id.source.wiki_text == "cached source"` after each rejected assignment. | Mutating `_source` before raising, clearing the cached source, or triggering lazy lookup to recover the value rejects this local completion claim. | Local page source cache | `tests/unit/test_page.py` |
| R4 | Real `PageSource` assignments remain valid. | Existing page property, source refresh, source acquisition, and source iterator tests still pass with many fixtures that assign or seed `PageSource` instances. | Rejecting valid `PageSource` objects or changing existing direct cache setup behavior rejects this local completion claim. | Page fixtures and cache setup | `tests/unit/test_page.py`, `tests/unit/test_site.py` |
| R5 | Existing page and site workflows remain green. | Page property plus acquisition/accessor tests passed 112 tests, page and site tests passed 381 tests, and full unit tests passed 1468 tests. | Regressing lazy source lookup, refresh, cached duplicate reuse, source iterator ledgers, create/edit, publish, source verification, metadata updates, or result exports rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, or live Wikidot actions rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `19f4cc0 fix(page): validate page source assignments`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_source_setter_rejects_invalid_sources -q` failed 5 tests before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`; the bad value was accepted by the setter and assigned into `_source`.
- GREEN: the same focused command passed 5 tests after adding page source assignment validation.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_site.py::TestSitePagesAccessor -q` passed 112 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_site.py -q` passed 381 tests.
- `uv run --extra test pytest tests/unit -q` passed 1468 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `page.source = None`, `page.source = True`, and `page.source = False` raise `ValueError("page.source must be PageSource")` without changing an existing cached valid source.
- `page.source = "cached source"` and `page.source = {"wiki_text": "cached source"}` raise `ValueError("page.source must be PageSource")` without changing an existing cached valid source.
- `page.source = PageSource(page, "cached source")` remains valid.
- Existing lazy `Page.source` acquisition still runs when `_source` is missing and still reports site/page context if acquisition leaves `_source` unset.
- Existing source refresh, source iterator ledgers, duplicate cached source reuse, page create/edit, page publish, source verification, metadata updates, and result exports remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.source` is shared by page source reads, explicit refresh, duplicate source cache reuse, source iterators, browser-free publishing, source verification, and source-result ledgers. Direct assignment is useful for test fixtures, caller-created page objects, and data rehydrated from external ledgers, but malformed source cache objects should fail at the property boundary instead of silently poisoning later source reads.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free source acquisition, publish verification, source iterator ledgers, cached duplicate source reuse, and tests that seed source caches directly.
- Existing local drafts covered lazy source acquisition, refresh, duplicate fetch deduplication, duplicate cached source reuse, source iterator result records, page source text input validation for write helpers, and direct page ID setter validation, but did not cover direct `Page.source` setter mutation.
- The focused RED failures showed invalid assignments were accepted by the property setter. The GREEN regression covers missing, boolean, string, and dictionary values and asserts the previous valid source survives.
- This slice only validates direct page source assignment shape; it does not change lazy source acquisition, source parsing, source text validation for writes, `PageSource.page` ownership, duplicate source fetches, source iterator behavior, create/edit, publish, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed source cache objects instead of coercing values. Callers that load source text from files, generated structures, JSON, YAML, CLI flags, or environment variables should normalize the page body to `str` before calling write helpers, and wrap cached source state in `PageSource` before assigning it to `Page.source`.
