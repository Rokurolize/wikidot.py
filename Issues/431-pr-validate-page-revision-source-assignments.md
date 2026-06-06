# PR Draft: Validate Page Revision Source Assignments

## Summary

`PageRevision.source` is a public property that lazily acquires and caches a `PageSource` object for one page revision. The setter documented `value` as `PageSource`, but it accepted any object. A caller could assign `revision.source = None`, `revision.source = True`, `revision.source = "cached revision source"`, or `revision.source = {"wiki_text": "cached revision source"}`, causing the public property to store malformed local revision-source state and defer failures to later code that expects `PageSource.wiki_text`.

This change validates direct `PageRevision.source` assignments as real `PageSource` objects. Invalid assignments now raise `ValueError("revision.source must be PageSource")` before mutating `_source`, preserving the last valid cached revision source when one exists. Existing lazy revision source acquisition, source extraction, retry behavior, duplicate cached revision reuse, `PageSource` construction validation, page source assignment validation, and adjacent page/site workflows remain unchanged.

## Outcome

Manually constructed, fixture-created, duplicate-reused, or ledger-rehydrated `PageRevision` objects can no longer silently corrupt their cached revision source through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page revision source reads, source/HTML comparison, revision snapshot ledgers, translation audits, migration scripts, rollback tooling, publication verification, or local tests that construct `PageRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision source state as a practical workflow surface. Existing drafts [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md), [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md), and [429-pr-validate-source-result-outcomes.md](429-pr-validate-source-result-outcomes.md) establish revision source reads, retry behavior, deduplication, cache reuse, response diagnostics, and source object integrity as active operational boundaries.

Those prior slices are not duplicates. Issues014, 015, 061, 078, 128, 145, 179, 201, 216, and 328 improved revision source acquisition, failure visibility, context, parsing, retry, deduplication, and response-body diagnostics. Issue365 validates collection entries before source/HTML acquisition, Issue415 validates direct `Page.revisions = ...` collection assignment, Issue419 validates `PageRevisionCollection(...)` initialization, Issue430 validates `PageSource(..., wiki_text=...)`, Issue414 validates `Page.source = ...`, and Issue429 validates `PageSourceResult(...)` outcome state. None of them validates direct public `PageRevision.source = ...` assignment before single-revision cache mutation.

## Related Issue

Builds directly on [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), and [430-pr-validate-page-source-wiki-text.md](430-pr-validate-page-source-wiki-text.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `PageRevision.source` object validator.
- Reject `None`, booleans, strings, dictionaries, and other non-`PageSource` values with `ValueError("revision.source must be PageSource")`.
- Validate before assigning `_source`, so invalid assignments preserve any previously cached valid revision source.
- Preserve valid `PageSource` assignments.
- Preserve existing lazy revision source acquisition, revision source extraction, source/HTML collection behavior, retry behavior, duplicate cached revision reuse, `PageSource` constructor validation, page source assignment validation, and adjacent page/site workflows.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local revision source cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `revision.source = None`, `revision.source = True`, `revision.source = "cached revision source"`, and `revision.source = {"wiki_text": "cached revision source"}` must raise `ValueError("revision.source must be PageSource")` before mutating `_source`. |
| R2 | Invalid assignments after an already-cached valid `PageSource` must preserve that previous source object. |
| R3 | Valid `PageSource` assignments must remain allowed. |
| R4 | Existing lazy revision source acquisition, revision source extraction, retry behavior, duplicate cached revision reuse, revision collection source/HTML behavior, page workflows, and site workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent page revision tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed revision source assignments fail before local source cache mutation. | `TestPageRevision.test_source_setter_rejects_invalid_sources` failed RED for `None`, `True`, `"cached revision source"`, and `{"wiki_text": "cached revision source"}` because the setter did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or deferring failure to later `wiki_text` access rejects this local completion claim. | Direct page revision source setter | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Invalid assignments preserve the previous valid cached revision source. | The focused GREEN asserts `sample_revision.source == cached_source` after each rejected assignment. | Mutating `_source` before raising, clearing cached source, or triggering lazy lookup to recover the value rejects this local completion claim. | Local revision source cache | `tests/unit/test_page_revision.py` |
| R3 | Real `PageSource` assignments remain valid. | `TestPageRevision.test_source_setter` assigns `PageSource(page=sample_revision.page, wiki_text="cached revision source")` and asserts it is stored unchanged. | Rejecting valid `PageSource` objects, coercing them, or changing direct cache setup behavior rejects this local completion claim. | PageRevision fixtures and cache setup | `tests/unit/test_page_revision.py` |
| R4 | Existing adjacent revision source workflows remain green. | Focused setter/source checks passed 8 tests, `tests/unit/test_page_revision.py tests/unit/test_page.py tests/unit/test_site.py` passed 507 tests, and full unit tests passed 1624 tests. | Regressing lazy revision source reads, retry exhaustion behavior, source extraction, duplicate cached revision source reuse, page source reads, site source iterators, or publish-adjacent workflows rejects this local completion claim. | Page revision, page, and site workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, source text from real sites, revision comments, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent revision/page/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `fc13dc8 fix(page_revision): validate source assignments`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_invalid_sources -q` failed 4 tests before the fix; every malformed source assignment reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after adding setter validation.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run mypy src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_source_setter tests/unit/test_page_revision.py::TestPageRevision::test_source_setter_rejects_invalid_sources tests/unit/test_page_revision.py::TestPageRevision::test_source_property_uses_cache tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_success tests/unit/test_page_revision.py::TestPageRevisionCollection::test_get_sources_reuses_cached_duplicate_revision_source -q` passed 8 tests.
- `uv run pytest tests/unit/test_page_revision.py tests/unit/test_page.py tests/unit/test_site.py -q` passed 507 tests.
- `uv run pytest tests/unit -q` passed 1624 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `revision.source = None`, `revision.source = True`, `revision.source = "cached revision source"`, and `revision.source = {"wiki_text": "cached revision source"}` raise `ValueError("revision.source must be PageSource")` without changing an existing cached valid source.
- `revision.source = PageSource(page=revision.page, wiki_text="cached revision source")` remains valid and stores the same object.
- Existing lazy `PageRevision.source` acquisition still runs when `_source` is missing and still reports site/page/revision context if acquisition leaves `_source` unset.
- Existing revision source extraction, multiline source preservation, duplicate cached revision source reuse, source/HTML collection behavior, page source reads, source iterator rows, and site/page workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision.source` is shared by lazy revision source reads, source/HTML comparison, duplicate cached revision reuse, revision snapshot ledgers, and publication audits. Direct assignment is useful for tests, caller-created revision objects, and data rehydrated from external ledgers, but malformed source cache objects should fail at the property boundary instead of silently poisoning later revision source reads.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used revision source snapshots, source/HTML comparison, cached duplicate revision reuse, source iterator ledgers, and tests that seed revision source caches directly.
- Existing local drafts covered revision source extraction, retry/fallback behavior, duplicate request deduplication, parse-once reuse, lazy failure context, response-body diagnostics, `Page.revisions` assignment validation, `PageRevisionCollection` initialization validation, `PageSource` wiki-text validation, and page/source-result source-object validation, but did not cover direct `PageRevision.source = ...` mutation.
- The focused RED failures showed invalid assignments were accepted by the property setter. The GREEN regression covers missing, boolean, string, and dictionary values and asserts the previous valid source survives.
- This slice only validates direct page revision source assignment shape. It does not change lazy revision acquisition, revision source parsing, source text extraction, `PageSource.page` ownership, revision collection behavior, page source setter validation, source-result outcome validation, create/edit, publish, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, revision comments, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed revision source cache objects instead of coercing values. Callers that load revision source text from files, generated structures, JSON, YAML, CLI flags, spreadsheets, databases, or ledgers should normalize the source text to `str`, wrap it in `PageSource`, and then assign it to `PageRevision.source`.
