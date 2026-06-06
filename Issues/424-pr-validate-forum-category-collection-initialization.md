# PR Draft: Validate Forum Category Collection Initialization

## Summary

`ForumCategoryCollection` documents `categories` as `list[ForumCategory] | None`, but its constructor accepted malformed containers and arbitrary list entries. A caller could construct `ForumCategoryCollection(site, categories=False)`, which silently became an empty collection, or `ForumCategoryCollection(site, categories="1001")`, `ForumCategoryCollection(site, categories=("1001",))`, and `ForumCategoryCollection(site, categories=[None])`, which could store malformed collection entries or raise incidental low-level exceptions.

This change validates constructor input before storing entries. Non-list non-`None` `categories` values now raise `ValueError("categories must be a list or None")`; list entries that are not `ForumCategory` now raise `ValueError("categories list entries must be ForumCategory")`. `categories=None`, empty collections, valid `ForumCategory` lists, iteration, `find(...)`, category-list acquisition, lazy `site.forum.categories`, category thread-list acquisition, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread acquisition, forum post acquisition, and forum post revision acquisition remain unchanged.

## Outcome

Callers cannot silently create malformed `ForumCategoryCollection` instances through the public constructor, while existing forum category fetch, parser, cache, lookup, thread, post, and post-revision workflows remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, `site.forum.categories`, or local fixtures that construct category collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical workflow surface and as the entry point for downstream thread, post, and revision workflows. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), and [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md) establish category-list acquisition, retry behavior, parser scoping, text fidelity, response diagnostics, count parser diagnostics, create-thread action diagnostics, cache invalidation, response-body type validation, and loaded-collection search-key validation as active operational boundaries. Adjacent constructor-hardening drafts [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), and [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md) establish the local state-integrity pattern for collection constructors.

Those prior slices are not duplicates. The forum category drafts covered fetching, retry behavior, parser scope, parser diagnostics, response diagnostics, create-thread result handling, thread-cache invalidation, and `ForumCategoryCollection.find(id=...)` search validation after a collection already exists. None of them validates the `ForumCategoryCollection(site, categories=...)` constructor itself before malformed category entries become stored list state.

## Related Issue

Builds directly on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), and the adjacent constructor validation pattern from [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), and [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumCategoryCollection.__init__(..., categories=...)` validation.
- Preserve `categories=None` as an empty collection when a site is supplied.
- Reject non-list non-`None` `categories` with `ValueError("categories must be a list or None")`.
- Reject non-`ForumCategory` list entries with `ValueError("categories list entries must be ForumCategory")`.
- Preserve valid empty collections, valid `ForumCategory` entries, iteration, `find(...)`, category-list acquisition, lazy `site.forum.categories`, category thread-list acquisition, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread acquisition, forum post acquisition, and forum post revision acquisition behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Forum category collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategoryCollection(site, categories=True)`, `False`, `"1001"`, `("1001",)`, and `1001` must raise `ValueError("categories must be a list or None")` before storing collection entries. |
| R2 | `ForumCategoryCollection(site, categories=[None])`, `[True]`, `["1001"]`, and `[{"id": 1001}]` must raise `ValueError("categories list entries must be ForumCategory")` before storing collection entries. |
| R3 | `ForumCategoryCollection(site, categories=None)`, `ForumCategoryCollection(site, categories=[])`, and `ForumCategoryCollection(site, categories=[valid_category])` must remain valid when a site is supplied. |
| R4 | Existing iteration, `find(...)`, category-list acquisition, lazy `site.forum.categories`, category thread-list acquisition, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread workflows, forum post workflows, and forum post revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent forum category/thread/post/revision tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestForumCategoryCollectionInit.test_init_rejects_non_list_categories` failed RED for `True`, `False`, `"1001"`, `("1001",)`, and `1001`, then passed GREEN after constructor validation was added. | Treating `False` as empty, accepting strings or tuples as category lists, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | ForumCategoryCollection constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Non-`ForumCategory` constructor list entries fail at the public constructor boundary. | `TestForumCategoryCollectionInit.test_init_rejects_non_category_entries` failed RED for `None`, `True`, `"1001"`, and `{"id": 1001}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized category records, or fixture stand-ins as stored categories rejects this local completion claim. | ForumCategoryCollection constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Valid constructor inputs remain green. | Existing empty-list and valid-category initialization tests passed in the focused 17-test run. | Rejecting `None`, empty valid lists, valid category lists, iteration, or ID lookup rejects this local completion claim. | ForumCategoryCollection constructor and methods | `tests/unit/test_forum_category.py` |
| R4 | Existing forum category and adjacent workflows remain green. | Focused regressions passed 17 tests, forum category/thread/post/revision tests passed 303 tests, and full unit tests passed 1558 tests. | Regressing category-list acquisition, parser diagnostics, response diagnostics, ID lookup, lazy site forum category reads, category thread-list reads, category create-thread behavior, forum thread workflows, forum post workflows, or forum post revision workflows rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7ea7d91 fix(forum_category): validate category collection initialization`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_non_list_categories -q` failed 5 tests before the container fix; `False`, strings, and tuples were accepted, while `True` and `1001` leaked incidental `TypeError`.
- GREEN: the same focused command passed 5 tests after adding non-list validation.
- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_non_category_entries -q` failed 4 tests before the entry fix because malformed list entries were accepted and stored.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit -q` passed 17 tests after adding entry validation and preserving existing initialization plus lookup behavior.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 303 tests.
- `uv run pytest tests/unit -q` passed 1558 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `ForumCategoryCollection(site, categories=True)`, `False`, `"1001"`, `("1001",)`, and `1001` raise `ValueError("categories must be a list or None")`.
- `ForumCategoryCollection(site, categories=[None])`, `[True]`, `["1001"]`, and `[{"id": 1001}]` raise `ValueError("categories list entries must be ForumCategory")`.
- `ForumCategoryCollection(site, categories=None)`, `ForumCategoryCollection(site, categories=[])`, and `ForumCategoryCollection(site, categories=[valid_category])` continue to work when a site is supplied.
- Existing iteration, `find(...)`, category-list acquisition, lazy `site.forum.categories`, category thread-list acquisition, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread behavior, forum post behavior, and forum post revision behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategoryCollection` is the stored object shape behind browser-free forum category discovery, lazy `site.forum.categories`, category-owned thread reads, create-thread workflows, and downstream forum thread, post, and revision traversal. Constructor validation keeps malformed local state out of the collection while preserving existing fetch, parser, cache, lookup, thread, post, and revision behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free forum category discovery, category-owned thread reads, and tests that seed category collections directly.
- Existing local drafts covered forum category fetch retry behavior, nested-table filtering, parser contexts, text spacing, response diagnostics, count parsing, create-thread result validation, create-thread cache invalidation, response-body type validation, and ID search validation, but did not cover the `ForumCategoryCollection(site, categories=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was treated as empty, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, and adjacent forum workflows.
- This slice only validates forum category collection constructor input. It does not change category-list acquisition, parser selectors, category ID parsing, title/description parsing, count parsing, cached behavior, `find(...)`, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed category-like objects and test mocks in `ForumCategoryCollection`. Callers should construct real `ForumCategory` entries before storing them in a category collection.
