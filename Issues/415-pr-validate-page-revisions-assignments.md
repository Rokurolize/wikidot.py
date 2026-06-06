# PR Draft: Validate Page Revisions Assignments

## Summary

`Page.revisions` is a public property that lazily acquires and caches a `PageRevisionCollection`. The setter documented `value` as `list[PageRevision] | PageRevisionCollection`, but it accepted any non-list object and stored it directly. A caller could assign `page.revisions = None`, `page.revisions = True`, `page.revisions = "100"`, or `page.revisions = {"id": 100}`, causing later `Page.revisions`, `Page.latest_revision`, or cache reuse code to operate on malformed local state.

The setter also wrapped arbitrary list entries into a `PageRevisionCollection`, and accepted already-built `PageRevisionCollection` instances with malformed entries. This change validates direct `Page.revisions` assignments before mutating `_revisions`. Invalid assignment shapes now raise `ValueError("page.revisions must be a list or PageRevisionCollection")`; invalid entries now raise `ValueError("page.revisions list entries must be PageRevision")`; previously cached valid revisions are preserved when validation fails.

## Outcome

Manually constructed, fixture-created, duplicate-reused, or ledger-rehydrated `Page` objects can no longer silently corrupt their cached revision collection through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page revision reads, source/HTML comparison, page publishing audits, translation review tooling, generated page ledgers, migration scripts, or local tests that construct `Page` objects directly.

## Current Evidence

Local rollout evidence repeatedly uses page revision caching as a practical workflow boundary. Existing drafts [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), and [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md) establish page revision state as an active operational surface.

Those prior slices are not duplicates. Issues040, 153, and 196 improved lazy page revision and latest-revision failure visibility; Issues063, 074, and 128 improved revision-list deduplication, parsing reuse, and cached duplicate reuse; Issues094, 114, 199, 222, 304, and 332 hardened revision-list parsing and response boundaries; Issue260 invalidated cached revisions after page edits; Issue262 synced revision counts after edits; Issue365 validated malformed entries before `PageRevisionCollection.get_sources()` and `get_htmls()` acquisition work; Issue376 validated `PageRevisionCollection.find(...)` IDs; Issues413 and 414 validated direct `Page.id` and `Page.source` assignment. None of them validates direct public `Page.revisions = ...` assignments before cached state mutation.

## Related Issue

Builds directly on [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), and [414-pr-validate-page-source-assignments.md](414-pr-validate-page-source-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a direct `Page.revisions` assignment validator.
- Reject non-list and non-`PageRevisionCollection` values with `ValueError("page.revisions must be a list or PageRevisionCollection")`.
- Reject malformed entries in assigned lists or assigned `PageRevisionCollection` objects with `ValueError("page.revisions list entries must be PageRevision")`.
- Validate before assigning `_revisions`, so invalid assignments preserve any previously cached valid revision collection.
- Preserve valid list assignment by wrapping the list in a page-owned `PageRevisionCollection`.
- Preserve valid `PageRevisionCollection` assignment, lazy revision acquisition, `Page.latest_revision`, revision source/HTML acquisition, duplicate cached revision reuse, edit cache invalidation, and adjacent site/page workflows.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `page.revisions = None`, `page.revisions = True`, `page.revisions = "100"`, and `page.revisions = {"id": 100}` must raise `ValueError("page.revisions must be a list or PageRevisionCollection")` before mutating `_revisions`. |
| R2 | `page.revisions = [None]`, `[True]`, `["100"]`, and `[{"id": 100}]` must raise `ValueError("page.revisions list entries must be PageRevision")` before mutating `_revisions`. |
| R3 | `page.revisions = PageRevisionCollection(page, [bad_entry])` must raise the same entry diagnostic before mutating `_revisions`. |
| R4 | Invalid assignments after an already-cached valid `PageRevisionCollection` must preserve that previous collection. |
| R5 | Valid `list[PageRevision]` assignments must still wrap into a page-owned `PageRevisionCollection`, and valid `PageRevisionCollection` assignments must remain allowed. |
| R6 | Lazy revision acquisition, `Page.latest_revision`, revision source/HTML acquisition, duplicate cached revision reuse, page edit revision-cache invalidation, page/file/vote/source workflows, and site/page workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, adjacent page/revision tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list and non-collection assignments fail before local revision cache mutation. | New `TestPageProperties.test_revisions_setter_rejects_invalid_collections` failed RED for `None`, `True`, `"100"`, and `{"id": 100}` because the setter did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, strings, or dictionaries as revision collections, clearing `_revisions`, or surfacing later iteration/cache failures rejects this local completion claim. | Direct page revisions setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | List assignments with malformed entries fail before local revision cache mutation. | `TestPageProperties.test_revisions_setter_rejects_invalid_entries` failed RED for `None`, `True`, `"100"`, and `{"id": 100}` entries because the setter wrapped them into a collection, then passed GREEN after entry validation was added. | Wrapping malformed entries into `PageRevisionCollection`, accepting IDs or serialized records as revisions, or deferring failure to `Page.latest_revision` or source/HTML acquisition rejects this local completion claim. | Direct page revisions setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Assigned `PageRevisionCollection` objects with malformed entries fail before local revision cache mutation. | `TestPageProperties.test_revisions_setter_rejects_invalid_collection_entries` failed RED for `None`, `True`, `"100"`, and `{"id": 100}` entries, then passed GREEN after collection-entry validation was added. | Trusting a prebuilt malformed collection, storing it as `_revisions`, or deferring failure to collection scans rejects this local completion claim. | Direct page revisions setter | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R4 | Invalid assignments preserve the previous valid cached revisions. | Each focused GREEN regression asserts the cached revision comment remains `"cached revision"` after a rejected assignment. | Mutating `_revisions` before raising, clearing cached revisions, or triggering lazy lookup to recover the value rejects this local completion claim. | Local page revision cache | `tests/unit/test_page.py` |
| R5 | Valid revision assignment behavior remains green. | Valid list assignment is used as the setup path in the focused tests, property/acquisition/revision tests passed 153 tests, and adjacent page/site tests passed 502 tests. | Rejecting valid revision lists, failing to wrap lists into `PageRevisionCollection`, rejecting valid collections, or breaking page-owned collection behavior rejects this local completion claim. | Page fixtures and cache setup | `tests/unit/test_page.py`, `tests/unit/test_page_revision.py` |
| R6 | Existing page and revision workflows remain green. | Page property plus acquisition plus page-revision tests passed 153 tests, page/page-file/page-revision/page-votes/site tests passed 502 tests, and full unit tests passed 1480 tests. | Regressing lazy revision lookup, latest-revision matching, revision source/HTML reads, duplicate cached revision reuse, page edit cache invalidation, source/file/vote reads, publish/create/edit, or site/page workflows rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, source text from real sites, revision comments, or revision HTML rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/revision/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `433b3d3 fix(page): validate page revisions assignments`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_collections -q` failed 4 tests before the fix with `Failed: DID NOT RAISE <class 'ValueError'>`; the bad value was accepted by the setter and assigned into `_revisions`.
- GREEN: the same focused command passed 4 tests after adding assignment-shape validation.
- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_entries tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_collection_entries -q` failed 8 tests before the entry fix with `Failed: DID NOT RAISE <class 'ValueError'>`; bad list and collection entries were accepted and assigned into `_revisions`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_collections tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_entries tests/unit/test_page.py::TestPageProperties::test_revisions_setter_rejects_invalid_collection_entries -q` passed 12 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_revision.py -q` passed 153 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 502 tests.
- `uv run --extra test pytest tests/unit -q` passed 1480 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `page.revisions = None`, `page.revisions = True`, `page.revisions = "100"`, and `page.revisions = {"id": 100}` raise `ValueError("page.revisions must be a list or PageRevisionCollection")` without changing an existing cached valid revision collection.
- `page.revisions = [None]`, `page.revisions = [True]`, `page.revisions = ["100"]`, and `page.revisions = [{"id": 100}]` raise `ValueError("page.revisions list entries must be PageRevision")` without changing an existing cached valid revision collection.
- `page.revisions = PageRevisionCollection(page, [bad_entry])` raises `ValueError("page.revisions list entries must be PageRevision")` for the same malformed entries without changing an existing cached valid revision collection.
- `page.revisions = [valid_revision]` still stores a page-owned `PageRevisionCollection`.
- `page.revisions = PageRevisionCollection(page, [valid_revision])` remains valid.
- Existing lazy `Page.revisions` acquisition still runs when `_revisions` is missing and still reports site/page context if acquisition leaves `_revisions` unset.
- Existing `Page.latest_revision`, revision source/HTML acquisition, duplicate cached revision reuse, page edit revision-cache invalidation, page source/file/vote reads, create/edit, publish, and site/page behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.revisions` is shared by lazy revision-list reads, latest-revision selection, revision source/HTML acquisition, duplicate cached revision reuse, edit cache invalidation, and audit ledgers. Direct assignment is useful for tests, caller-created page objects, and data rehydrated from external ledgers, but malformed revision collections should fail at the property boundary instead of silently poisoning later revision scans.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free revision acquisition, latest-revision reads, source/HTML comparison, cached duplicate revision reuse, page edit cache invalidation, and tests that seed revision caches directly.
- Existing local drafts covered lazy revision failure context, revision-list deduplication, parsing reuse, cached duplicate revision reuse, parser/response diagnostics, edit cache invalidation, collection acquisition entry validation, collection find-ID validation, and direct page ID/source setter validation, but did not cover direct `Page.revisions` setter mutation.
- The focused RED failures showed invalid assignments were accepted by the property setter. The GREEN regressions cover malformed assignment shapes, malformed raw list entries, malformed prebuilt collection entries, and previous-cache preservation.
- This slice only validates direct page revisions assignment shape and entry shape; it does not change lazy revision acquisition, revision-list parsing, source/HTML acquisition, `Page.latest_revision` matching, edit cache invalidation, duplicate source/HTML behavior, publish behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, revision comments, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed revision cache objects instead of coercing values. Callers that load revision IDs or serialized revision records from files, generated structures, JSON, YAML, CLI flags, or ledgers should resolve them to `PageRevision` objects before assigning them to `Page.revisions`.
