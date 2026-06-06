# PR Draft: Validate Page Revision Collection Initialization

## Summary

`PageRevisionCollection` documents `revisions` as `list[PageRevision] | None`, but its constructor accepted malformed containers and arbitrary list entries. A caller could construct `PageRevisionCollection(page, revisions=False)`, which silently became an empty collection, or `PageRevisionCollection(page, revisions="100")`, `PageRevisionCollection(page, revisions=("100",))`, and `PageRevisionCollection(page, revisions=[None])`, which could store malformed collection entries or raise incidental low-level exceptions.

This change validates constructor input before storing entries. Non-list non-`None` `revisions` values now raise `ValueError("revisions must be a list or None")`; list entries that are not `PageRevision` now raise `ValueError("revisions list entries must be PageRevision")`. `revisions=None`, empty collections, valid `PageRevision` lists, page inference from a valid first revision, iteration, `find(...)`, source/HTML acquisition, direct `Page.revisions` assignment validation after post-construction mutation, duplicate cached revision reuse, and edit-cache invalidation remain unchanged.

## Outcome

Callers cannot silently create malformed `PageRevisionCollection` instances through the public constructor, while existing source/HTML acquisition and direct `Page.revisions` assignment guards still defend against later list mutation before request or cache work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free revision list reads, revision source/HTML retrieval, page history audits, translation review ledgers, duplicate cached revision reuse, generated reports, migration scripts, or local fixtures that construct revision collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revisions as a practical workflow surface. Existing drafts [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), and [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md) establish revision acquisition, parsing, cached reuse, lookup, mutation invalidation, and local revision cache state as active operational boundaries.

Those prior slices are not duplicates. Issues014, 094, 114, 222, 304, and 332 covered source/revision parsing and response diagnostics; Issues061, 063, 074, and 128 covered deduplication, parse reuse, and cached duplicate reuse; Issues153, 179, and 199 improved lazy revision failure context; Issues260 and 262 covered edit-related cache invalidation and revision-count sync; Issue365 validates entries before `get_sources()` and `get_htmls()` acquisition work; Issue376 validates `find(id=...)`; Issue415 validates direct `Page.revisions = ...` assignment. None of them validates the `PageRevisionCollection(page, revisions=...)` constructor itself before malformed revision entries become stored list state.

## Related Issue

Builds directly on [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [260-pr-page-edit-revision-cache-invalidation.md](260-pr-page-edit-revision-cache-invalidation.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), and [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PageRevisionCollection.__init__(..., revisions=...)` validation.
- Preserve `revisions=None` as an empty collection.
- Reject non-list non-`None` `revisions` with `ValueError("revisions must be a list or None")`.
- Reject non-`PageRevision` list entries with `ValueError("revisions list entries must be PageRevision")`.
- Update existing source/HTML acquisition and direct `Page.revisions` setter regression fixtures to mutate a valid collection after construction, so those guards still prove later list mutation is rejected.
- Preserve valid empty collections, valid `PageRevision` entries, page inference, iteration, `find(...)`, source/HTML acquisition, direct valid `Page.revisions` assignment, duplicate cached revision reuse, and edit-cache invalidation behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Page revision collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevisionCollection(page, revisions=True)`, `False`, `"100"`, `("100",)`, and `100` must raise `ValueError("revisions must be a list or None")` before storing collection entries. |
| R2 | `PageRevisionCollection(page, revisions=[None])`, `[True]`, `["100"]`, and `[{"id": 100}]` must raise `ValueError("revisions list entries must be PageRevision")` before storing collection entries. |
| R3 | `PageRevisionCollection(page, revisions=None)`, `PageRevisionCollection(page, revisions=[])`, and `PageRevisionCollection(page, revisions=[valid_revision])` must remain valid, and `PageRevisionCollection(revisions=[valid_revision])` must still infer the page from that revision. |
| R4 | A valid `PageRevisionCollection` that is later mutated to contain malformed entries must still be rejected by `get_sources()`, `get_htmls()`, and direct `Page.revisions` assignment before request or cache mutation work. |
| R5 | Existing iteration, `find(...)`, source acquisition, HTML acquisition, lazy page revision acquisition, latest-revision lookup, duplicate cached revision reuse, edit-cache invalidation, page source/vote/file workflows, and site/page workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent page/revision tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestPageRevisionCollection.test_init_rejects_non_list_revisions` failed RED for `True`, `False`, `"100"`, `("100",)`, and `100`, then passed GREEN after constructor validation was added. | Treating `False` as empty, accepting strings or tuples as revision lists, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | PageRevisionCollection constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Non-`PageRevision` constructor list entries fail at the public constructor boundary. | `TestPageRevisionCollection.test_init_rejects_non_revision_entries` failed RED for `None`, `True`, `"100"`, and `{"id": 100}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized revision records, or fixture stand-ins as stored revisions rejects this local completion claim. | PageRevisionCollection constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R3 | Valid constructor inputs remain green. | Existing initialization, page-inference, iteration, and `find(...)` tests passed in the 58-test page-revision module run. | Rejecting `None`, empty valid lists, valid revision lists, normal page inference, iteration, or lookup rejects this local completion claim. | PageRevisionCollection constructor and methods | `tests/unit/test_page_revision.py` |
| R4 | Existing guards still reject malformed entries introduced after construction. | `test_get_sources_rejects_non_revision_entries_before_fetch`, `test_get_htmls_rejects_non_revision_entries_before_fetch`, and `TestPageProperties.test_revisions_setter_rejects_invalid_collection_entries` now create valid collections, mutate their list entries, and pass in the 171-test adjacent run. | Removing method/setter entry validation, allowing mutated collections to reach AMC/cache work, or corrupting an existing valid revision cache rejects this local completion claim. | Revision acquisition and direct page revisions setter | `src/wikidot/module/page_revision.py`, `src/wikidot/module/page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page.py` |
| R5 | Existing page and revision workflows remain green. | Page-revision/property/acquisition tests passed 171 tests, page/page-file/page-revision/page-votes/site tests passed 533 tests, and full unit tests passed 1511 tests. | Regressing lazy revision lookup, latest revision, source/HTML retrieval, duplicate cached revision reuse, edit cache invalidation, page source/vote/file reads, publish/create/edit, or site/page workflows rejects this local completion claim. | Page and site workflows | `tests/unit/test_page.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent page/revision/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `94d9a62 fix(page_revision): validate revision collection initialization`.

- RED: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_init_rejects_non_list_revisions -q` failed 5 tests before the container fix; `False`, strings, and tuples were accepted, while `True` and `100` leaked incidental `TypeError`.
- GREEN: the same focused command passed 5 tests after adding non-list validation.
- RED: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_init_rejects_non_revision_entries -q` failed 4 tests before the entry fix because malformed list entries were accepted and stored.
- GREEN: `uv run --extra test pytest tests/unit/test_page_revision.py::TestPageRevisionCollection::test_init_rejects_non_list_revisions tests/unit/test_page_revision.py::TestPageRevisionCollection::test_init_rejects_non_revision_entries -q` passed 9 tests after adding entry validation.
- Initial adjacent regression check exposed that source/HTML acquisition and `Page.revisions` setter tests were constructing invalid `PageRevisionCollection` instances directly; those fixtures were updated to mutate valid collections after construction so they still prove the later guards.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py tests/unit/test_page.py` left 3 files unchanged.
- `uv run --extra test pytest tests/unit/test_page_revision.py tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 171 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 533 tests.
- `uv run --extra test pytest tests/unit -q` passed 1511 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PageRevisionCollection(page, revisions=True)`, `False`, `"100"`, `("100",)`, and `100` raise `ValueError("revisions must be a list or None")`.
- `PageRevisionCollection(page, revisions=[None])`, `[True]`, `["100"]`, and `[{"id": 100}]` raise `ValueError("revisions list entries must be PageRevision")`.
- `PageRevisionCollection(page, revisions=None)`, `PageRevisionCollection(page, revisions=[])`, and `PageRevisionCollection(page, revisions=[valid_revision])` continue to work.
- `PageRevisionCollection(revisions=[valid_revision])` still infers the page from that revision.
- A valid collection that is later mutated with a malformed entry still causes `get_sources()`, `get_htmls()`, and direct `page.revisions = mutated_collection` to raise `ValueError("revisions list entries must be PageRevision")` before request or cache mutation work.
- Existing `PageRevisionCollection.find(...)`, lazy `Page.revisions` acquisition, `Page.latest_revision`, source/HTML acquisition, duplicate cached revision reuse, edit cache invalidation, page source/vote/file reads, create/edit, publish, and site/page behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevisionCollection` is the stored object shape behind browser-free page history reads, revision source/HTML acquisition, latest-revision lookup, cached duplicate revision reuse, and edit cache invalidation. Constructor validation keeps malformed local state out of the collection while preserving the existing source/HTML and direct-assignment guards against post-construction list mutation.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free revision acquisition, duplicate cached revision reuse, lazy source/HTML retrieval, revision count sync, edit cache invalidation, and tests that seed revision collections directly.
- Existing local drafts covered revision-list fetch deduplication, duplicate revision-list reuse, source/HTML body diagnostics, revision parser scoping, revision search-ID validation, acquisition-method entry validation, and direct `Page.revisions` assignment, but did not cover the `PageRevisionCollection(page, revisions=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was treated as empty, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, and the existing acquisition/setter guards after explicit post-construction mutation.
- This slice only validates revision collection constructor input and updates test fixtures to use explicit post-construction mutation. It does not change lazy revision acquisition, revision-list parsing, source/HTML parsing, `PageRevisionCollection.find(...)`, edit behavior, duplicate source/vote/file behavior, publish behavior, result fields, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed revision-like objects and test mocks in `PageRevisionCollection`. Callers should construct real `PageRevision` entries before storing them in a revision collection; tests that only need mutation-safety coverage should mutate a valid collection after construction.
