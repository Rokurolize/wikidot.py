# PR Draft: Validate Page Collection Retained Page ID State

## Summary

`PageCollection.get_page_ids()` treats any non-`None` retained `Page._id` as already acquired before building direct page-ID lookup requests. After retained page state has been corrupted or rehydrated incorrectly, the collection preflight could silently skip malformed cached IDs such as `True`, `False`, `"333"`, `333.0`, `[]`, or `-1` instead of surfacing the same deterministic validation used by the public `Page.id` getter.

This change validates retained non-`None` `Page._id` values while building the collection's acquired-ID-by-URL reuse map. Malformed retained IDs now raise `ValueError("page.id must be an integer")`, negative retained IDs now raise `ValueError("page.id must be non-negative")`, valid cached IDs including `0` remain reusable, and missing `None` IDs still follow the existing direct page-ID lookup path.

## Outcome

Collection-level page-ID acquisition can no longer silently classify corrupted retained page identity as acquired state or reuse it for duplicate URL propagation.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `PageCollection.get_page_ids()`, page source/revision/vote/file acquisition, page evidence ledgers, duplicate page queues, browser-free publishing helpers, serialized page records, generated migration rows, or local fixtures that may reconstruct `Page` objects before collection preflights.

## Current Evidence

Local rollout-backed drafts already established collection-level page-ID acquisition as a practical boundary. [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md) covers duplicate URL lookup deduplication and acquired-ID reuse. [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), and [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md) cover duplicate page-detail cache reuse. [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md) validates the public `Page.id` getter for corrupted retained state, and [662-pr-validate-page-cache-owner-retained-page-id-state.md](662-pr-validate-page-cache-owner-retained-page-id-state.md) validates retained page IDs at direct page cache-owner boundaries.

This slice is not a duplicate of those drafts. Issue 658 intentionally preserves the behavior that `page.id` does not call `PageCollection.get_page_ids()` for malformed non-`None` retained state, but it does not make `PageCollection.get_page_ids()` itself validate already-retained IDs before skipping them. Issue 066 validates duplicate URL fetch deduplication and cached URL reuse for valid IDs, not corrupted retained state. Issues 127 through 130 depend on collection page-ID preflight behavior but do not validate the preflight's retained-ID skip path.

## Related Issue / Non-Duplicate Analysis

Builds directly on [066-pr-deduplicate-page-id-fetch-urls.md](066-pr-deduplicate-page-id-fetch-urls.md), [127-pr-reuse-cached-duplicate-page-sources.md](127-pr-reuse-cached-duplicate-page-sources.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [130-pr-reuse-cached-duplicate-page-files.md](130-pr-reuse-cached-duplicate-page-files.md), and [658-pr-validate-retained-page-id-getter-state.md](658-pr-validate-retained-page-id-getter-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a retained page-ID validation helper that returns `None` for unloaded pages and validates non-`None` retained IDs with the existing public `Page.id` validator.
- Use that helper before `PageCollection._acquire_page_ids(...)` records an acquired page ID by direct page URL.
- Reject malformed retained IDs such as `True`, `False`, `"333"`, `333.0`, and `[]` with `ValueError("page.id must be an integer")` before direct GET work.
- Reject negative retained IDs such as `-1` with `ValueError("page.id must be non-negative")` before direct GET work.
- Preserve duplicate unresolved URL deduplication, valid cached duplicate URL reuse, missing-ID lookup, valid zero/positive retained IDs, page-detail acquisition callers, and adjacent page workflows.

## Type Of Change

- Input validation
- Retained page-ID hardening
- Collection preflight integrity
- Duplicate page-ID reuse safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageCollection.get_page_ids()` must reject malformed retained `Page._id` values such as `True`, `False`, `"333"`, `333.0`, and `[]` with `ValueError("page.id must be an integer")` before any direct page-ID GET. |
| R2 | `PageCollection.get_page_ids()` must reject negative retained `Page._id` values such as `-1` with `ValueError("page.id must be non-negative")` before any direct page-ID GET. |
| R3 | Malformed and negative retained IDs must not be treated as acquired state, reused for duplicate URL propagation, coerced to integers, or hidden by direct page-ID lookup. |
| R4 | Existing duplicate unresolved URL deduplication, valid cached duplicate URL reuse, missing-ID acquisition, valid zero/positive retained IDs, and page source/revision/vote/file acquisition callers must remain green. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, PageCollection coverage, page module coverage, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained IDs fail at the collection preflight boundary. | `test_acquire_page_ids_rejects_malformed_retained_page_ids_before_fetch` failed RED for five malformed values with `DID NOT RAISE`, then passed GREEN after retained non-`None` page IDs were validated while building the acquired-ID reuse map. | Returning normally, treating booleans as integers, accepting floats or strings, or sending a direct GET rejects this local completion claim. | `PageCollection.get_page_ids()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Negative retained IDs fail at the collection preflight boundary. | `test_acquire_page_ids_rejects_negative_retained_page_id_before_fetch` failed RED with `DID NOT RAISE`, then passed GREEN after retained non-`None` page IDs were validated. | Returning normally, coercing the value, treating it as an acquired ID, or sending a direct GET rejects this local completion claim. | `PageCollection.get_page_ids()` | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Validation remains side-effect-free and local. | The malformed and negative regressions patch `RequestUtil.request` and assert it is not called. | Fetching the direct page URL, mutating retained IDs, or hiding corrupted local state with lookup rejects this local completion claim. | Collection page-ID preflight | `tests/unit/test_page.py` |
| R4 | Existing collection and adjacent workflows remain green. | Focused GREEN coverage passed 8 tests, `TestPageCollectionAcquire` passed 72 tests, `tests/unit/test_page.py` passed 375 tests, adjacent page/page-constructor/page-revision/page-file/page-source/page-votes/site coverage passed 1189 tests, and full unit passed 3070 tests. | Regressing duplicate URL deduplication, cached duplicate URL reuse, source/revision/vote/file acquisition, page property behavior, site accessors, or any unit test rejects this local completion claim. | Page collection and adjacent page-detail workflows | `tests/unit/test_page.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_page_revision.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_source.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic objects and mocked request helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bb5226b fix(page): validate collection retained page ids`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_deduplicates_duplicate_page_urls tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_reuses_cached_duplicate_page_url tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_rejects_malformed_retained_page_ids_before_fetch tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_page_ids_rejects_negative_retained_page_id_before_fetch -q` failed 6 retained collection preflight cases with `DID NOT RAISE`; 2 duplicate URL dedupe and cached URL reuse guards passed.
- GREEN: the same focused command passed 8 tests after validating retained non-`None` page IDs before treating pages as acquired.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire -q` passed 72 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 375 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_page_revision.py tests/unit/test_page_file.py tests/unit/test_page_source.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1189 tests.
- `uv run pytest tests/unit -q` passed 3070 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageCollection.get_page_ids()` raises `ValueError("page.id must be an integer")` when a retained `Page._id` is `True`, `False`, `"333"`, `333.0`, or `[]`.
- `PageCollection.get_page_ids()` raises `ValueError("page.id must be non-negative")` when a retained `Page._id` is `-1`.
- Malformed and negative retained page-ID checks do not call `RequestUtil.request`, AMC helpers, or live Wikidot.
- Valid duplicate unresolved page URLs still use one direct page-ID GET and propagate the parsed ID to both pages.
- A valid acquired page ID for the same URL still populates an unresolved duplicate page without a direct GET.
- Valid retained page IDs, including `0`, remain accepted.
- Missing `_id is None` still follows the existing direct lookup path and missing-ID diagnostics.
- Existing page source, revision, vote, file, constructor, property, and site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageCollection.get_page_ids()` is a shared page identity preflight for large source/revision/vote/file acquisition, duplicate page queues, source-result and publish-result ledgers, and migration tooling. The public `Page.id` getter now rejects corrupted retained state, but the collection preflight still had its own acquired-state shortcut. Validating retained non-`None` IDs before that shortcut keeps collection code from silently preserving invalid page identity while preserving the missing-ID lookup path and duplicate URL reuse semantics.

## Local Evidence

- Existing local drafts covered page-ID request batching, duplicate URL deduplication, cached duplicate detail reuse, public retained `Page.id` getter validation, retained publish/source result page-ID validation, and retained cache-owner page-ID validation.
- None of those drafts covered `PageCollection.get_page_ids()` silently skipping malformed retained `Page._id` values because `page.is_id_acquired()` only checks for non-`None`.
- The focused RED failure showed malformed and negative retained IDs could pass through collection page-ID acquisition with no error and no direct GET. The GREEN regressions cover malformed rejection, negative rejection, no direct GET for invalid retained state, valid duplicate URL deduplication, valid cached URL reuse, adjacent page-detail workflows, and full unit compatibility.
- This slice only validates retained non-`None` page IDs at the collection page-ID preflight boundary. It does not change page URL construction, direct page-ID parsing, source/revision/vote/file AMC request construction, publish behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only the retained value already present on each page. It does not call `Page.id` for unloaded pages, so `_id is None` still means the page should go through the existing batch direct lookup path.
