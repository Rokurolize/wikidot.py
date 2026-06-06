# PR Draft: Validate Forum Thread Category Field

## Summary

`ForumThread` records optionally carry the owning `ForumCategory` used by browser-free category thread-list reads, direct thread-detail reads, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, reply-side category post-count/cache synchronization, duplicate thread-detail reuse, downstream `ForumThread.posts`, and generated forum migration or audit ledgers. Earlier local slices validated forum-thread direct lookup IDs, collection lookup IDs, collection initialization, category thread-list caches, reply parent-post IDs, category `threads` assignments, forum post parent-thread ownership, and parser/fetch diagnostics, but the public `ForumThread(...)` constructor still accepted malformed `category` values such as booleans, strings, dictionaries, and arbitrary objects.

This change validates `ForumThread.category` at initialization. Malformed non-`None` values now raise `ValueError("category must be a ForumCategory or None")`. `category=None`, valid `ForumCategory` objects, category-list parsing, direct thread-detail parsing, lazy `ForumCategory.threads`, direct thread acquisition, lazy `ForumThread.posts`, reply cache synchronization, and adjacent forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum thread records whose parent category is neither `None` nor a `ForumCategory`, while uncategorized thread-detail objects and categorized parser-created or fixture-created threads continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category inventories, direct thread-detail reads, generated discussion migration ledgers, duplicate thread-detail cache reuse, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, `ForumThread.posts`, forum replies, or local tests that construct `ForumThread` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum thread ownership and category thread-list state as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), and [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md) establish category thread-list acquisition, direct thread-detail acquisition, cached category-thread reuse, parser scoping, response diagnostics, reply-side category synchronization, ID validation, collection integrity, and child post ownership as active operational boundaries.

Those prior slices are not duplicates. Issue362 validates caller-provided `thread_id` inputs before direct thread-detail acquisition. Issue379 validates loaded `ForumThreadCollection.find(id=...)` lookup keys. Issue423 validates `ForumThreadCollection(site, threads=...)` constructor state, not a single thread's optional category field. Issue434 validates direct `ForumCategory.threads = ...` cache assignment. Issue446 validates `ForumPost.thread`, which is the child post's parent thread, not the thread's optional parent category. Parser and fetch drafts cover category association after valid records are produced, but do not validate direct `ForumThread(category=...)` construction.

## Related Issue

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [369-pr-validate-forum-thread-reply-parent-id.md](369-pr-validate-forum-thread-reply-parent-id.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), and the adjacent constructor parent-field validation pattern from [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), and [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumThread.category` validation at dataclass initialization.
- Accept `category=None` and valid `ForumCategory` instances.
- Reject malformed non-`None` categories with `ValueError("category must be a ForumCategory or None")`.
- Keep existing negative test fixtures pyright-clean by typing intentionally malformed values through `Any`.
- Preserve existing category thread-list parsing, direct thread-detail parsing, direct thread acquisition, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, lazy `ForumThread.posts`, reply category cache synchronization, forum post workflows, and forum post revision workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum thread parent-category state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(category=True)`, `"1001"`, `{"id": 1001}`, and `object()` must raise `ValueError("category must be a ForumCategory or None")` when every other thread field is valid. |
| R2 | `ForumThread(category=None)` and valid `ForumCategory` instances must remain valid. |
| R3 | Existing category thread-list parsing, direct thread-detail parsing, direct thread acquisition, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, lazy `ForumThread.posts`, reply cache synchronization, forum post workflows, and forum post revision workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor categories fail at the public dataclass boundary. | `TestForumThreadBasic.test_init_rejects_malformed_categories` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after category validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting thread rows with non-`ForumCategory` parent state rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Valid optional-category semantics stay green. | Existing forum-thread fixtures and tests passed with valid `ForumCategory` objects, while direct thread-detail paths remain compatible with `category=None`. | Rejecting `None`, rejecting valid `ForumCategory` instances, coercing category-like mocks, or changing stored thread fields rejects this local completion claim. | Parser-created and manually created threads | `tests/unit/test_forum_thread.py` |
| R3 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 90 tests, adjacent forum-category/forum-post/forum-post-revision tests passed 240 tests, and full unit tests passed 1721 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, cached category-thread reuse, parser diagnostics, response diagnostics, ID lookup, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, reply category sync, post reads, source reads, or revision reads rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum category text, forum thread text, forum post text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5e0c421 fix(forum_thread): validate thread category`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_categories -q` failed 4 tests before the fix; every malformed `category` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_categories -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 90 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 240 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit -q` passed 1721 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 72 existing full-tree typing errors, including fixture `None` mismatches, intentional invalid-input test calls, invalid `test_search_pages_query` parameter calls, requestutil response narrowing issues, and site/application test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumThread(category=True)`, `"1001"`, `{"id": 1001}`, and `object()` raise `ValueError("category must be a ForumCategory or None")`.
- `ForumThread(category=None)` remains valid.
- Valid `ForumCategory` instances remain valid as `category`.
- Existing category thread-list parsing, direct thread-detail parsing, `ForumThreadCollection.find(...)`, direct and batched thread acquisition, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, lazy `ForumThread.posts`, reply category cache synchronization, forum post behavior, and forum post revision behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread.category` is the optional parent context behind browser-free category thread-list reads, category-thread cache reuse, reloads, reply-side category post-count/cache synchronization, direct thread-detail lookup, downstream post-list reads, and generated moderation or migration ledgers. Constructor validation keeps malformed local parent-category state out of thread rows while preserving uncategorized direct thread records and parser/caller paths that construct threads from real `ForumCategory` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free category thread-list reads, direct thread-detail reads, duplicate direct-thread reuse, cached category-thread reuse, lazy category thread reads, reply category synchronization, downstream forum post reads, and tests that seed thread objects directly.
- Existing local drafts covered forum thread fetch retry behavior, duplicate direct-thread reduction, parser scoping, response diagnostics, parser field diagnostics, cached direct/category acquisition, direct thread ID input validation, reply parent-post validation, create-thread returned-ID validation, search-key validation, collection initialization validation, category thread assignment validation, and child forum post parent-thread validation, but did not cover direct `ForumThread(category=...)` construction.
- The focused RED failures showed invalid constructor category fields were accepted as dataclass state. The GREEN regression covers boolean, string, dictionary, and arbitrary object category values.
- This slice only validates optional forum thread parent-category constructor input. It does not change category thread-list request construction, direct thread-detail requests, parser selectors, thread ID parsing, title/description parsing, created metadata parsing, post-count parsing, cached duplicate behavior, `find(...)`, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumThread.posts`, `ForumThread.reply(...)`, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum category text, forum thread text, forum post text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `category` is `None` or a `ForumCategory` instance. It does not validate category IDs, category/site identity consistency, thread IDs, post counts, title/description text, creator shape, timestamp shape, post-cache content, or live client authentication at `ForumThread` construction time; those are separate category object, parser, cache, and workflow concerns.
