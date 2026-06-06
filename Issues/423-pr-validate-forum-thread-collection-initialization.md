# PR Draft: Validate Forum Thread Collection Initialization

## Summary

`ForumThreadCollection` documents `threads` as `list[ForumThread] | None`, but its constructor accepted malformed containers and arbitrary list entries. A caller could construct `ForumThreadCollection(site, threads=False)`, which silently became an empty collection, or `ForumThreadCollection(site, threads="3001")`, `ForumThreadCollection(site, threads=("3001",))`, and `ForumThreadCollection(site, threads=[None])`, which could store malformed collection entries or raise incidental low-level exceptions.

This change validates constructor input before storing entries. Non-list non-`None` `threads` values now raise `ValueError("threads must be a list or None")`; list entries that are not `ForumThread` now raise `ValueError("threads list entries must be ForumThread")`. `threads=None`, empty collections, valid `ForumThread` lists, site inference from a valid first thread, iteration, `find(...)`, category thread-list acquisition, direct thread-detail acquisition, cached category-thread reuse, duplicate direct-thread reuse, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_threads(...)`, `Site.get_thread(...)`, and forum post acquisition remain unchanged.

## Outcome

Callers cannot silently create malformed `ForumThreadCollection` instances through the public constructor, while existing forum thread fetch, parser, cache, lookup, category, and post workflows remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, category thread inventories, direct thread-detail reads, duplicate thread-detail cache reuse, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_threads(...)`, `Site.get_thread(...)`, `ForumThread.get_from_id(...)`, or local fixtures that construct thread collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum thread lists and direct thread detail reads as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), and [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md) establish thread-list acquisition, direct thread-detail acquisition, retry behavior, parser scoping, parser diagnostics, response diagnostics, cache reuse, public thread-ID input validation, reply parent-post validation, and loaded-collection search-key validation as active operational boundaries. Adjacent constructor-hardening drafts [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), and [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md) establish the local state-integrity pattern for collection constructors.

Those prior slices are not duplicates. The forum thread drafts covered fetching, retry behavior, duplicate direct-thread reuse, cached category-thread reuse, parser scope, parser diagnostics, response diagnostics, create/reply result handling, caller-provided thread ID validation, and `ForumThreadCollection.find(id=...)` search validation after a collection already exists. None of them validates the `ForumThreadCollection(site, threads=...)` constructor itself before malformed thread entries become stored list state.

## Related Issue

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), and the adjacent constructor validation pattern from [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), and [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumThreadCollection.__init__(..., threads=...)` validation.
- Preserve `threads=None` as an empty collection when a site is supplied.
- Reject non-list non-`None` `threads` with `ValueError("threads must be a list or None")`.
- Reject non-`ForumThread` list entries with `ValueError("threads list entries must be ForumThread")`.
- Preserve valid empty collections, valid `ForumThread` entries, site inference from a valid first thread, iteration, `find(...)`, category thread-list acquisition, direct thread-detail acquisition, cached category-thread reuse, duplicate direct-thread reuse, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_threads(...)`, `Site.get_thread(...)`, and forum post acquisition behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Forum thread collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection(site, threads=True)`, `False`, `"3001"`, `("3001",)`, and `3001` must raise `ValueError("threads must be a list or None")` before storing collection entries. |
| R2 | `ForumThreadCollection(site, threads=[None])`, `[True]`, `["3001"]`, and `[{"id": 3001}]` must raise `ValueError("threads list entries must be ForumThread")` before storing collection entries. |
| R3 | `ForumThreadCollection(site, threads=None)`, `ForumThreadCollection(site, threads=[])`, and `ForumThreadCollection(site, threads=[valid_thread])` must remain valid, and `ForumThreadCollection(site=None, threads=[valid_thread])` must still infer the site from that thread. |
| R4 | Existing iteration, `find(...)`, category thread-list acquisition, direct thread-detail acquisition, cached category-thread reuse, duplicate direct-thread reuse, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_threads(...)`, `Site.get_thread(...)`, forum category workflows, forum post workflows, and forum post revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent forum thread/category/post/revision tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestForumThreadCollectionInit.test_init_rejects_non_list_threads` failed RED for `True`, `False`, `"3001"`, `("3001",)`, and `3001`, then passed GREEN after constructor validation was added. | Treating `False` as empty, accepting strings or tuples as thread lists, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | ForumThreadCollection constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Non-`ForumThread` constructor list entries fail at the public constructor boundary. | `TestForumThreadCollectionInit.test_init_rejects_non_thread_entries` failed RED for `None`, `True`, `"3001"`, and `{"id": 3001}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized thread records, or fixture stand-ins as stored threads rejects this local completion claim. | ForumThreadCollection constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Valid constructor inputs remain green. | Existing empty-list and valid-thread initialization tests plus the new site-inference test passed in the focused 14-test run. | Rejecting `None`, empty valid lists, valid thread lists, normal site inference, iteration, or ID lookup rejects this local completion claim. | ForumThreadCollection constructor and methods | `tests/unit/test_forum_thread.py` |
| R4 | Existing forum thread and adjacent workflows remain green. | Focused regressions passed 14 tests, forum thread/category/post/revision tests passed 294 tests, and full unit tests passed 1549 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, cached category-thread reuse, duplicate direct-thread reuse, parser diagnostics, response diagnostics, ID lookup, lazy category thread reads, category workflows, post workflows, or post revision workflows rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `14d3042 fix(forum_thread): validate thread collection initialization`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_non_list_threads -q` failed 5 tests before the container fix; `False`, strings, and tuples were accepted, while `True` and `3001` leaked incidental `TypeError`.
- GREEN: the same focused command passed 5 tests after adding non-list validation.
- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_non_thread_entries -q` failed 4 tests before the entry fix because malformed list entries were accepted and stored.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_non_list_threads tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_non_thread_entries tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_with_site_and_empty_threads tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_with_site_and_threads tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_infers_site_from_threads tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_find_existing tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_find_nonexistent -q` passed 14 tests after adding entry validation and preserving site inference plus existing lookup behavior.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run --extra test pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 294 tests.
- `uv run --extra test pytest tests/unit -q` passed 1549 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `ForumThreadCollection(site, threads=True)`, `False`, `"3001"`, `("3001",)`, and `3001` raise `ValueError("threads must be a list or None")`.
- `ForumThreadCollection(site, threads=[None])`, `[True]`, `["3001"]`, and `[{"id": 3001}]` raise `ValueError("threads list entries must be ForumThread")`.
- `ForumThreadCollection(site, threads=None)`, `ForumThreadCollection(site, threads=[])`, and `ForumThreadCollection(site, threads=[valid_thread])` continue to work.
- `ForumThreadCollection(site=None, threads=[valid_thread])` still infers the site from that thread.
- Existing iteration, `find(...)`, category thread-list acquisition, direct thread-detail acquisition, cached category-thread reuse, duplicate direct-thread reuse, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_threads(...)`, `Site.get_thread(...)`, forum category behavior, forum post behavior, and forum post revision behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThreadCollection` is the stored object shape behind browser-free category thread-list reads, direct thread-detail reads, lazy `ForumCategory.threads`, category reloads, `Site.get_threads(...)`, `Site.get_thread(...)`, duplicate direct-thread cache reuse, and downstream forum post acquisition. Constructor validation keeps malformed local state out of the collection while preserving existing fetch, parser, cache, lookup, category, and post behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free category thread-list reads, direct thread-detail reads, duplicate thread detail reuse, cached category thread-list reuse, lazy category thread reads, and tests that seed thread collections directly.
- Existing local drafts covered forum thread fetch retry behavior, duplicate direct-thread reduction, parse scoping, response diagnostics, parser field diagnostics, cached direct/category acquisition, thread ID input validation, reply parent-post validation, create-thread returned-ID validation, and ID search validation, but did not cover the `ForumThreadCollection(site, threads=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was treated as empty, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, and adjacent forum workflows.
- This slice only validates forum thread collection constructor input. It does not change category thread-list acquisition, direct thread-detail acquisition, parser selectors, thread ID parsing, title/description parsing, created metadata parsing, cached duplicate behavior, `find(...)`, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_threads(...)`, `Site.get_thread(...)`, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed thread-like objects and test mocks in `ForumThreadCollection`. Callers should construct real `ForumThread` entries before storing them in a thread collection.
