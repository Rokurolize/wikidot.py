# PR Draft: Validate Page Constructor Files Cache

## Summary

`Page._files` is the optional cached `PageFileCollection` behind the public `Page.files` property. It is used by lazy attachment reads, duplicate cached file-list reuse, direct page-file acquisition, file lookup, page asset inventories, publish/audit ledgers, rename and destroy cache invalidation, local fixtures, and rehydrated page records. Public file collection construction and individual `PageFile` records are already validated, but direct `Page(...)` construction still accepted malformed `_files` values such as booleans, strings, raw lists, dictionaries, arbitrary objects, and post-construction mutated collections.

This change validates the direct constructor's optional files cache during `Page.__post_init__`. `_files=None` remains valid for pages that have not acquired attachments yet, real `PageFileCollection` objects remain valid, and malformed non-null values now raise stable `ValueError` diagnostics before they can make `Page.files` return malformed local cache state.

## Outcome

Directly constructed `Page` objects now fail early when optional cached file state is malformed, while preserving lazy file acquisition for `_files=None` and preserving valid preloaded `PageFileCollection` objects.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free page inventories, attachment audits, page asset migration ledgers, publication verification reports, cached page records, local fixtures, generated adapters, or serialized and rehydrated `Page` objects.

## Current Evidence

[420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md) validates the public `PageFileCollection(page, files=...)` constructor's file container and entries. [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md) validates explicit collection parent pages while preserving `page=None` inference. [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md) and [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md) validate direct `PageFile` fields. File acquisition and cache behavior are covered by drafts such as [009-pr-skip-cached-page-detail-fetches.md](009-pr-skip-cached-page-detail-fetches.md), [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [039-pr-page-files-exhausted-retry-error.md](039-pr-page-files-exhausted-retry-error.md), [041-pr-retry-direct-page-file-acquire.md](041-pr-retry-direct-page-file-acquire.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), [144-pr-skip-cached-direct-page-files.md](144-pr-skip-cached-direct-page-files.md), [230-pr-cache-direct-page-file-acquisition.md](230-pr-cache-direct-page-file-acquisition.md), [266-pr-page-rename-file-cache-invalidation.md](266-pr-page-rename-file-cache-invalidation.md), and [267-pr-page-destroy-cache-invalidation.md](267-pr-page-destroy-cache-invalidation.md). Recent direct `Page` constructor slices validate identity, counts, rating, parent fullname, tags, site, nullable metadata, rating-percent, cached page-ID, cached source, cached revisions, and cached votes fields.

Those prior slices are not duplicates. Issue 420 covers constructing `PageFileCollection` instances, not deciding whether a direct `Page(_files=...)` value is a valid page cache. Issue 471 covers the collection's parent field, not the `Page` object's optional cache slot. Issues 443 and 468 cover individual file records. Acquisition, parser, duplicate-cache, and cache-invalidation drafts prove `_files` is operationally important but do not validate direct dataclass initialization. Issues 490 through 492 validate adjacent direct `Page` cache fields only. None validates direct `Page(_files=...)` construction before malformed cached-file state is stored.

## Related Issue / Non-Duplicate Analysis

Builds directly on [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [468-pr-validate-page-file-scalar-fields.md](468-pr-validate-page-file-scalar-fields.md), the file cache/acquisition drafts listed above, and the direct `Page` constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) through [492-pr-validate-page-constructor-votes-cache.md](492-pr-validate-page-constructor-votes-cache.md).

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached files validation for direct `Page(...)` construction.
- Preserve `_files=None` for pages that should lazily acquire attachment data.
- Preserve valid `PageFileCollection` objects without coercion.
- Reject booleans, strings, raw lists, dictionaries, arbitrary non-collection objects, and collections mutated with malformed entries using stable `ValueError` diagnostics.
- Add constructor tests for valid optional file cache state, malformed direct `_files` values, and malformed cached collection entries.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached attachment state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(_files=...)` must accept `None` and real `PageFileCollection` objects. |
| R2 | `Page(_files=...)` must reject non-`None` non-`PageFileCollection` values with `ValueError("page.files must be PageFileCollection or None")`. |
| R3 | `Page(_files=...)` must reject `PageFileCollection` objects containing non-`PageFile` entries with `ValueError("page.files list entries must be PageFile")`. |
| R4 | Valid page construction, lazy file acquisition, direct `PageFileCollection.acquire(page)`, `PageFileCollection` construction validation, parser-created pages, file lookup, duplicate cached file-list reuse, rename/destroy cache invalidation, and page source/revision/file/vote workflows must remain unchanged. |
| R5 | This slice must not change direct file acquisition, file parsing, URL normalization, size parsing, file lookup semantics, cache invalidation, live request behavior, or unrelated constructor fields. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote/page-revision tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid `PageFileCollection` cached file values remain accepted. | `TestPageInit.test_init_accepts_valid_optional_files` passed RED and GREEN, preserving `_files=None` and returning a valid cached `PageFileCollection` through `page.files`. | Rejecting missing cached files, triggering file lookup during construction, or coercing valid collection objects rejects this local completion claim. | `Page` constructor cached-file state | `tests/unit/test_page_constructor.py` |
| R2 | Malformed optional cached file values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_files` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, strings, raw lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `Page` constructor cached-file state | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Mutated file collections with malformed entries fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_optional_file_entries` failed RED because a valid collection mutated with `object()` was accepted, then passed GREEN after entry validation was added. | Trusting a mutated collection, storing malformed entries, or deferring failure to lazy `Page.files`, duplicate cached file reuse, or file lookup rejects this local completion claim. | `Page` constructor cached-file entries | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R4 | Existing page and file workflows remain green. | Constructor tests passed 137 tests; adjacent page/site/page-file/page-vote/page-revision tests passed 724 tests; full unit tests passed 2119 tests. | Regressing lazy file acquisition, direct file acquisition, collection construction validation, parser-created pages, file lookup, duplicate cached file reuse, rename/destroy cache invalidation, or adjacent page workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_page_revision.py`, `tests/unit` |
| R5 | Broader file semantics remain outside scope. | Existing file acquisition, parser, cache invalidation, collection, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing direct acquisition, request construction, parser conversion, URL normalization, size parsing, file lookup, collection construction, cache invalidation, or live request behavior rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4debf91 fix(page): validate constructor files cache`.

- RED: `uv run --extra test pytest -q tests/unit/test_page_constructor.py::TestPageInit::test_init_accepts_valid_optional_files tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_files tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_optional_file_entries` failed 6 malformed `_files` cases before the fix with `DID NOT RAISE`, while the valid optional-files case passed.
- GREEN: the same focused command passed 7 tests after optional cached files validation was added.
- `uv run --extra test pytest -q tests/unit/test_page_constructor.py` passed 137 tests.
- `uv run --extra test pytest -q tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_page_revision.py` passed 724 tests.
- `uv run --extra test pytest -q tests/unit` passed 2119 tests.
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

- `Page(_files=None)` remains valid and lazy file acquisition remains available.
- `Page(_files=PageFileCollection(...))` remains valid and `page.files` returns the cached object without a lookup.
- `Page(_files=True)`, `Page(_files="cached files")`, `Page(_files=[])`, `Page(_files={"files": []})`, and `Page(_files=object())` raise `ValueError("page.files must be PageFileCollection or None")` when every other constructor field is valid.
- `Page(_files=collection_mutated_with_non_file)` raises `ValueError("page.files list entries must be PageFile")` when every other constructor field is valid.
- Existing parser-created pages, direct page fixtures, page collection behavior, lazy `Page.files`, direct `PageFileCollection.acquire(page)`, `PageFileCollection` construction validation, file lookup, duplicate cached file reuse, rename/destroy cache invalidation, and adjacent page workflows remain green.
- The new tests use unit-level code only and do not validate file collection ownership, file parser contents, live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Cached files are a shared state surface for attachment inventories, page asset audits, duplicate cache reuse, file lookup, publication verification, and cache invalidation after page mutations. Direct construction is useful for fixtures and rehydrated records, but malformed cached file values should fail at construction instead of making `Page.files` return unusable state.

## Local Evidence

- Local rollout evidence used cached page file state in browser-free page inventories, attachment audits, publication verification, generated migration ledgers, and cache-aware page records.
- Existing local drafts covered direct file acquisition, lazy file acquisition, duplicate cached file-list reuse, parser diagnostics, response diagnostics, cache invalidation, collection construction, collection parent validation, individual `PageFile` fields, and direct `Page` cache validation for `_source`, `_revisions`, and `_votes`, but did not cover direct optional cached-files construction on `Page`.
- Existing unit fixtures already relied on `_files=None` being valid for lazy file acquisition and `PageFileCollection` being valid for preloaded file records, so this change validates only malformed non-null values and mutated entries.
- This slice does not change parser extraction, page write behavior, collection inference behavior, query serialization, page ID/source/revision/file/vote acquisition logic, source/revision/vote/meta cache semantics, live Wikidot behavior, site client internals, file action behavior, or unrelated constructor fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The validator deliberately does not change direct `PageFileCollection.acquire(page)` or lazy `Page.files` acquisition behavior. The direct `_files` constructor field is the stored cache field and therefore accepts only the annotated cache object shape plus `None`, while existing file collection constructors remain responsible for normal construction and parent inference semantics.
