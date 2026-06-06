# PR Draft: Validate Page Constructor Revisions Cache

## Summary

`Page._revisions` is the optional cached `PageRevisionCollection` behind the public `Page.revisions` property. It is used by lazy revision history reads, latest-revision lookup, duplicate cached revision reuse, edit cache invalidation, local fixtures, and rehydrated page records. Public `Page.revisions = ...` assignment already validates assigned values and entries, and `PageRevisionCollection(...)` already validates constructor input, but direct dataclass construction still accepted malformed `_revisions` values such as booleans, strings, raw lists, dictionaries, arbitrary objects, and post-construction mutated collections.

This change validates the direct constructor's optional revisions cache during `Page.__post_init__`. `_revisions=None` remains valid for pages that have not acquired revisions yet, real `PageRevisionCollection` objects remain valid, and malformed non-null values now raise stable `ValueError` diagnostics before they can make `Page.revisions` return malformed local cache state.

## Outcome

Directly constructed `Page` objects now fail early when optional cached revision state is malformed, while preserving lazy revision acquisition for `_revisions=None` and preserving valid preloaded `PageRevisionCollection` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, revision ledgers, latest-revision checks, cached page records, local fixtures, generated adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

[365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md) validates revision collection entries before source or HTML acquisition. [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md) validates public `Page.revisions = ...` assignment before mutating `_revisions`. [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md) validates the public `PageRevisionCollection(page, revisions=...)` constructor. Recent direct `Page` constructor slices validate identity, counts, rating, parent fullname, tags, site, nullable metadata, rating-percent, cached page-ID, and cached source fields.

Those prior slices are not duplicates. Issue 365 covers acquisition methods on an already-built collection, not the `Page` constructor cache field. Issue 415 covers post-construction assignment through the public `Page.revisions` setter, not direct dataclass initialization. Issue 419 covers constructing `PageRevisionCollection` instances, not deciding whether a direct `Page(_revisions=...)` value is a valid page cache. Issues 481 through 490 validate other direct `Page` constructor fields only. None validates direct `Page(_revisions=...)` construction before malformed cached-revision state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), and the direct `Page` constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached revisions validation for direct `Page(...)` construction.
- Preserve `_revisions=None` for pages that should lazily acquire revision history.
- Preserve valid `PageRevisionCollection` objects without coercion.
- Reject booleans, strings, raw lists, dictionaries, arbitrary non-collection objects, and collections mutated with malformed entries using stable `ValueError` diagnostics.
- Add constructor tests for valid optional revision cache state, malformed direct `_revisions` values, and malformed cached collection entries.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached revision state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_revisions=...)` must accept `None` and real `PageRevisionCollection` objects. |
| R2 | `Page(_revisions=...)` must reject non-`None` non-`PageRevisionCollection` values with `ValueError("page.revisions must be PageRevisionCollection or None")`. |
| R3 | `Page(_revisions=...)` must reject `PageRevisionCollection` objects containing non-`PageRevision` entries with `ValueError("page.revisions list entries must be PageRevision")`. |
| R4 | Valid page construction, lazy revision acquisition, public `Page.revisions` assignment validation, `PageRevisionCollection` construction validation, parser-created pages, latest-revision lookup, and page source/revision/file/vote workflows must remain unchanged. |
| R5 | This slice must not change public `Page.revisions = [...]` assignment behavior, revision parsing, revision source/HTML acquisition, revision collection constructor semantics, cache invalidation, live request behavior, or unrelated constructor fields. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid `PageRevisionCollection` cached revision values remain accepted. | `TestPageInit.test_init_accepts_valid_optional_revisions` passed RED and GREEN, preserving `_revisions=None` and returning a valid cached `PageRevisionCollection` through `page.revisions`. | Rejecting missing cached revisions, triggering revision lookup during construction, or coercing valid collection objects rejects this local completion claim. | `Page` constructor cached-revision state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed optional cached revision values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_revisions` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, raw lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor cached-revision state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Mutated revision collections with malformed entries fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_revision_entries` failed RED because a valid collection mutated with `object()` was accepted, then passed GREEN after entry validation was added. | Trusting a mutated collection, storing malformed entries, or deferring failure to `Page.latest_revision` or source/HTML acquisition rejects this local completion claim. | `Page` constructor cached-revision entries | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R4 | Existing page and revision workflows remain green. | Constructor tests passed 123 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 724 tests; full unit tests passed 2105 tests. | Regressing lazy revision acquisition, `Page.revisions` assignment validation, `PageRevisionCollection` construction validation, parser-created pages, latest-revision lookup, duplicate cached revision reuse, edit cache invalidation, or page source/revision/file/vote workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R5 | Broader revision semantics remain outside scope. | Existing revision parser, public setter, collection constructor, source/HTML acquisition, cache invalidation, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing public list assignment behavior, changing lazy acquisition, changing request construction, changing parser conversion, changing collection construction, or touching live request behavior rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7862a39 fix(page): validate constructor revisions cache`.

- RED: `uv run --extra test pytest -q tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_revisions tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_revisions tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_revision_entries` failed 6 malformed `_revisions` cases before the fix with `DID NOT RAISE`, while the valid optional-revisions case passed.
- GREEN: the same focused command passed 7 tests after optional cached revisions validation was added.
- `uv run --extra test pytest -q tests/unit/test_page_constructor.py` passed 123 tests.
- `uv run --extra test pytest -q tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py` passed 724 tests.
- `uv run --extra test pytest -q tests/unit` passed 2105 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 44 existing full-tree test typing errors outside this slice, including intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and touched test module pass pyright together.

## Acceptance Criteria

- `Page(_revisions=None)` remains valid and lazy revision acquisition remains available.
- `Page(_revisions=PageRevisionCollection(...))` remains valid and `page.revisions` returns the cached object without a lookup.
- `Page(_revisions=True)`, `Page(_revisions="cached revisions")`, `Page(_revisions=[])`, `Page(_revisions={"revisions": []})`, and `Page(_revisions=object())` raise `ValueError("page.revisions must be PageRevisionCollection or None")` when every other constructor field is valid.
- `Page(_revisions=collection_mutated_with_non_revision)` raises `ValueError("page.revisions list entries must be PageRevision")` when every other constructor field is valid.
- Existing parser-created pages, direct page fixtures, page collection behavior, lazy `Page.revisions`, public `Page.revisions` setter validation, `PageRevisionCollection` construction validation, latest-revision lookup, source/HTML acquisition, duplicate cached revision reuse, edit cache invalidation, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not validate revision collection ownership, revision parser contents, live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Cached revisions are a shared state surface for revision history reads, latest-revision lookup, duplicate cache reuse, edit invalidation, and generated ledgers. Direct construction is useful for fixtures and rehydrated records, but malformed cached revision values should fail at construction instead of making `Page.revisions` return unusable state.

## Local Evidence

- Local rollout evidence used cached page revision state in browser-free page inventories, revision ledgers, latest-revision checks, cached page records, and generated audit records.
- Existing local drafts covered revision acquisition entry validation, direct `Page.revisions` assignment, and `PageRevisionCollection` construction, but did not cover direct optional cached-revisions construction on `Page`.
- Existing unit fixtures already relied on `_revisions=None` being valid for lazy revision acquisition and `PageRevisionCollection` being valid for preloaded revision records, so this change validates only malformed non-null values and mutated entries.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, source/vote/file/meta cache semantics, live Wikidot behavior, site client internals, revision source/HTML retrieval, or unrelated constructor fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The validator deliberately does not change public `Page.revisions = [revision]` assignment behavior. The direct `_revisions` constructor field is the stored cache field and therefore accepts only the annotated cache object shape, while the public setter keeps its existing list-to-collection convenience.
