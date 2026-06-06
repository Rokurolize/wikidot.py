# PR Draft: Validate Forum Thread Collection Site Field

## Summary

`ForumThreadCollection` stores the optional explicit parent `Site` used by browser-free category thread-list reads, direct thread-detail reads, duplicate cached direct-thread reuse, lazy `ForumCategory.threads`, `Site.get_threads(...)`, generated discussion migration or audit ledgers, local fixtures, and rehydrated forum thread state. Earlier local slices validated caller-provided thread IDs before acquisition, loaded collection entries, lookup IDs, collection `threads` containers and entries, direct `ForumThread.category`, direct thread identity/text/post-count fields, and direct thread creator/time fields, but `ForumThreadCollection(site=..., threads=...)` still accepted malformed explicit parent sites such as booleans, strings, dictionaries, and arbitrary objects.

This change validates non-`None` `ForumThreadCollection.site` constructor arguments before storing collection state. Malformed explicit values now raise `ValueError("site must be a Site")`. The existing `site=None` inference behavior remains valid when a collection is built from a valid first thread. Valid `Site` parents, empty thread lists, valid `ForumThread` lists, iteration, lookup, category thread-list acquisition, direct thread-detail acquisition, duplicate cached thread-detail reuse, lazy `ForumCategory.threads`, direct `ForumThread` field validation, and adjacent forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-thread collections with malformed explicit parent-site state, while parser-created, fixture-created, cached-duplicate, inferred-parent, and manually created valid thread collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum thread reads, generated discussion migration ledgers, category thread inventories, duplicate direct-thread cache reuse, direct `ForumThreadCollection.acquire_from_thread_ids(...)`, lazy `ForumCategory.threads`, `Site.get_threads(...)`, `Site.get_thread(...)`, or local tests that construct `ForumThreadCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum thread lists and direct thread detail reads as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), and [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md) establish thread-list acquisition, direct thread-detail acquisition, retry behavior, parser diagnostics, response diagnostics, cache reuse, public thread-ID input validation, collection entry validation, direct thread parent validation, and direct thread field validation as active operational boundaries.

Those prior slices are not duplicates. Issue 423 validates only the collection's `threads` container and entries while preserving `ForumThreadCollection(site=None, threads=[valid_thread])` inference. Issue 447 validates the optional `category` field on individual `ForumThread` records, not the collection parent site. Issues 455-458 validate direct `ForumThread` identity, text, count, creator, and timestamp fields. Issues 362 and 379 validate caller-provided acquisition IDs and loaded-collection search keys. None validates direct non-`None` `ForumThreadCollection(site=...)` construction before malformed parent-site state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md), and the adjacent optional collection parent validation pattern from [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), and [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate non-`None` `ForumThreadCollection.site` values at constructor initialization.
- Reject malformed explicit parent-site values with `ValueError("site must be a Site")`.
- Preserve `site=None` inference from a valid first thread, valid empty thread collections with an explicit valid site, valid `ForumThread` lists, iteration, lookup, parser-created collections, duplicate cached thread reuse, category thread-list acquisition, direct thread-detail acquisition, lazy `ForumCategory.threads`, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum thread parent-site state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection(site=True)`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` when `threads` is otherwise valid. |
| R2 | `ForumThreadCollection(threads=[valid_thread])` must still infer the site from the first thread, and `ForumThreadCollection(site=<valid Site>, threads=[])` must remain constructible. |
| R3 | Valid `Site` parent values, valid empty thread lists, valid `ForumThread` lists, iteration, `find(...)`, category thread-list acquisition, direct thread-detail acquisition, duplicate cached thread-detail reuse, lazy `ForumCategory.threads`, direct `ForumThread` field validation, and adjacent forum workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-thread tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent sites fail at the public constructor boundary. | `TestForumThreadCollectionInit.test_init_rejects_malformed_sites` failed RED for 4 malformed non-`None` values because the constructor did not raise, then passed GREEN after site validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting thread collections with malformed explicit parent-site state rejects this local completion claim. | ForumThreadCollection constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Optional inference and valid empty collection semantics stay green. | Existing empty initialization and site-inference tests passed in the 22-test constructor run and 120-test forum-thread module run. | Losing parent-site inference from the first valid thread, rejecting empty valid collections with explicit valid sites, or changing stored site identity rejects this local completion claim. | ForumThreadCollection constructor | `tests/unit/test_forum_thread.py` |
| R3 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 120 tests, adjacent forum workflow tests passed 440 tests, and full unit tests passed 1915 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, cached direct acquisition, duplicate thread-detail reuse, parser diagnostics, response diagnostics, ID lookup, lazy category thread reads, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e9c8e52 fix(forum_thread): validate thread collection site`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_malformed_sites -q` failed 4 tests before the fix; every malformed explicit `site` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `ForumThreadCollection` explicit site validation was added.
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit -q` passed 22 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 120 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 440 tests.
- `uv run pytest tests/unit -q` passed 1915 tests.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed forum-thread test file pass pyright together.

## Acceptance Criteria

- `ForumThreadCollection(site=True)`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- `ForumThreadCollection(threads=[valid_thread])` still infers the site from the first valid thread.
- `ForumThreadCollection(site=<valid Site>, threads=[])` and `ForumThreadCollection(site=<valid Site>, threads=[valid_thread])` remain valid.
- Existing valid `ForumThread` lists, iteration, `find(...)`, category thread-list acquisition, direct thread-detail acquisition, parser-side thread diagnostics, direct thread field validation, duplicate cached thread reuse, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThreadCollection.site` is the collection-level parent used by browser-free category thread-list reads, duplicate direct thread-detail reuse, lazy `ForumCategory.threads`, collection lookup, and generated moderation or migration ledgers. Parser paths already create collections with valid owning sites or infer the parent from valid threads; direct constructor validation keeps malformed explicit collection parents out of generated ledgers, migration comparisons, publication audits, and downstream tooling while preserving parser and caller paths that intentionally use site inference.

## Local Evidence

- Local rollout evidence used browser-free forum thread acquisition, duplicate cached direct-thread reuse, lazy category thread reads, cached direct acquisition, and tests that seed thread collections directly.
- Existing local drafts covered forum thread fetch retry behavior, duplicate thread-detail reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct/category acquisition, acquisition thread-ID validation, collection threads/entry validation, search-key validation, direct thread category validation, direct thread identity/text validation, direct thread post-count validation, and direct thread creator/time validation, but did not cover direct non-`None` `ForumThreadCollection(site=...)` construction.
- The focused RED failures showed invalid explicit constructor parent sites were accepted as collection state. The GREEN regression covers boolean, string, dictionary, and arbitrary object values while preserving inference from valid threads.
- This slice only validates forum-thread collection explicit parent-site constructor input. It does not change thread-list parsing, direct thread-detail parsing, collection lookup semantics, forum category/post behavior, duplicate page/file/vote/revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only for explicit non-`None` parent values. It does not compare collection parent identity with each contained thread, coerce dictionaries into sites, change site inference from a valid first thread, verify category membership, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
