# PR Draft: Validate Forum Category Collection Site Ownership

## Summary

`ForumCategoryCollection` validates explicit collection parent-site types, validates its `categories` container and entries, and each `ForumCategory` validates its own retained `site`, but the public collection constructor did not ensure contained categories all belong to the effective collection site. A caller could construct `ForumCategoryCollection(site_a, [category_from_site_b])`; a caller could also rely on parent inference with `ForumCategoryCollection(site=None, categories=[category_from_site_a, category_from_site_b])`, which inferred `site_a` from the first category while retaining a valid category from `site_b`.

This change validates category entry ownership at the public `ForumCategoryCollection.__init__` boundary after entry validation and effective site selection but before list state is stored. Categories whose retained `category.site` is not the collection site now raise `ValueError("categories must belong to the collection site")`. Valid explicit same-site collections, valid inferred same-site collections, empty no-parent collections, `find(...)`, forum category-list parsing, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum thread/post/revision workflows remain unchanged.

## Outcome

Forum category collections reject different-site category entries before local collection state can represent one site while storing another site's categories.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category inventories, generated forum migration or moderation ledgers, cached category inventories, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, or local tests that construct `ForumCategoryCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery, category-owned thread traversal, and cached category inventories as practical workflow surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-context.md](233-pr-forum-category-count-context.md), [326-pr-forum-category-response-body-type-context.md](326-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md), [538-pr-preserve-empty-forum-category-parent.md](538-pr-preserve-empty-forum-category-parent.md), [542-pr-validate-forum-category-acquire-site.md](542-pr-validate-forum-category-acquire-site.md), and [590-pr-validate-forum-thread-collection-site-ownership.md](590-pr-validate-forum-thread-collection-site-ownership.md) establish category-list acquisition, parser diagnostics, response diagnostics, lookup validation, collection entry validation, explicit collection-site validation, direct category parent validation, cached thread validation, empty no-parent handling, direct acquisition validation, and adjacent forum collection ownership as active operational boundaries.

This slice is not a duplicate of those issues. Issue 476 validates explicit non-`None` `ForumCategoryCollection.site` field type while preserving inference and empty no-parent semantics. Issue 424 validates the collection's `categories` container and entries. Issue 502 validates each `ForumCategory.site` field type. Issue 505 validates a `ForumCategory` object's optional `_threads` cache slot. Issue 538 preserves empty `site=None` collection readability. Issue 590 covers `ForumThreadCollection`, not forum category collections. None validates a valid `ForumCategory` entry whose retained `category.site` is individually valid but does not match the collection site selected explicitly or inferred from the first category.

No upstream issue was filed from this local workspace.

## Changes

- Add a forum-category collection ownership preflight at `ForumCategoryCollection.__init__`.
- Reject explicit different-site category entries with `ValueError("categories must belong to the collection site")`.
- Reject inferred-parent mixed-site category collections with the same diagnostic.
- Preserve explicit valid parents, inferred valid parents, empty no-parent collections, valid category lists, lookup, category-list parsing, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum category parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategoryCollection(site_a, [category_from_site_b])` must reject the different-site category with `ValueError("categories must belong to the collection site")` before storing collection list state. |
| R2 | `ForumCategoryCollection(site=None, categories=[category_from_site_a, category_from_site_b])` must infer `site_a` from the first category and reject the second different-site category with the same diagnostic before storing collection list state. |
| R3 | Valid explicit same-site category collections, valid inferred same-site category collections, and empty no-parent collections must remain valid. |
| R4 | Existing `find(...)`, category-list acquisition, parser diagnostics, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum thread/post/revision workflows must remain unchanged. |
| R5 | Focused RED/GREEN, forum-category module coverage, adjacent forum module coverage, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit different-site category entries fail at the public collection constructor boundary. | `TestForumCategoryCollectionInit.test_init_rejects_category_from_different_site` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("categories must belong to the collection site")`. | Accepting the different-site category, storing a collection for `site_a` that contains a category retained from `site_b`, or deferring failure to lookup/cache code rejects this local completion claim. | `ForumCategoryCollection.__init__` | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Inferred-parent mixed-site category entries fail at the same constructor boundary. | `TestForumCategoryCollectionInit.test_init_rejects_mixed_site_categories_when_site_is_inferred` failed RED with `DID NOT RAISE`, then passed GREEN with the same diagnostic. | Inferring `site_a` from the first category while storing a category retained from `site_b`, accepting mixed inferred collections, or rejecting all inferred collections rejects this local completion claim. | `ForumCategoryCollection.__init__` | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Valid category collection construction semantics stay green. | `tests/unit/test_forum_category.py` passed 98 tests after the ownership preflight. | Rejecting valid same-site explicit collections, valid same-site inferred collections, empty no-parent collections, or normal site inference rejects this local completion claim. | Forum category collections | `tests/unit/test_forum_category.py` |
| R4 | Existing forum category and adjacent forum workflows remain green. | Adjacent forum category/thread/post/revision coverage passed 530 tests, and the full unit suite passed 2697 tests. | Regressing category-list acquisition, parser diagnostics, lookup, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, thread-list acquisition, post-list acquisition, post revision acquisition, or forum thread behavior rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, full `pyright`, and `git diff --check` passed. Full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted; full mypy found no issues in 87 source files. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic valid `Site` and `ForumCategory` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page/forum content from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `a7c4026 fix(forum_category): validate category collection site ownership`.

- RED explicit target-site ownership: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_category_from_different_site -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused explicit ownership regression: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_category_from_different_site -q` passed 1 test.
- RED inferred target-site ownership: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_mixed_site_categories_when_site_is_inferred -q` failed before the inferred-branch fix with `DID NOT RAISE`.
- GREEN focused ownership coverage: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_category_from_different_site tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_mixed_site_categories_when_site_is_inferred -q` passed 2 tests.
- Forum category module coverage: `uv run pytest tests/unit/test_forum_category.py -q` passed 98 tests.
- Adjacent forum category/thread/post/revision tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 530 tests.
- `uv run pytest tests/unit -q` passed 2697 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategoryCollection(site_a, [category_from_site_b])` raises `ValueError("categories must belong to the collection site")` before storing collection list state.
- `ForumCategoryCollection(site=None, categories=[category_from_site_a, category_from_site_b])` raises the same diagnostic after inferring the first category's site and before storing collection list state.
- `ForumCategoryCollection(site=<valid Site>, categories=[])`, `ForumCategoryCollection(site=<valid Site>, categories=[same_site_category])`, `ForumCategoryCollection(site=None, categories=[same_site_category])`, and `ForumCategoryCollection(site=None, categories=[])` remain valid.
- Existing `find(...)`, category-list acquisition, parser diagnostics, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum thread/post/revision behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategoryCollection.site` and each retained `ForumCategory.site` should describe the same owning site for browser-free forum category inventories, generated moderation ledgers, migration audits, cached category inventories, lazy category-thread state, thread lookup, and downstream post/revision traversal. Parser paths already create categories from the owning site, and same-site category-list helpers already preserve category ownership; constructor ownership validation keeps mismatched rehydrated records, fixtures, or generated ledgers from silently carrying another site's categories under the collection site.

## Local Evidence, Not For Upstream Paste

- The explicit RED failure showed a valid category from another site could be accepted by `ForumCategoryCollection(site, [category])` without ownership rejection.
- The inferred RED failure showed `ForumCategoryCollection(site=None, categories=[category_from_site_a, category_from_site_b])` could infer a collection site from the first category while retaining another site's category.
- Existing local drafts covered category-list acquisition, parser diagnostics, response-body diagnostics, lookup validation, collection categories/entry validation, direct category site validation, explicit collection-site validation, empty no-parent handling, and direct category threads-cache validation, but did not compare each valid `ForumCategory.site` to the effective collection site.
- This slice only validates forum-category collection target-site ownership at collection initialization. It does not change category-list parsing, collection lookup semantics, category thread-list cache invalidation, lazy thread acquisition, create-thread behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page/forum source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally uses object identity. A site-owned category collection should contain `ForumCategory` objects retained from the exact owning `Site` object, matching parser-created categories and direct helper results. It does not infer a collection site from a later category, coerce site-like objects, compare by unix name alone, verify remote site membership, validate a category's cached thread collection ownership, or change live client authentication; those are separate parser, lookup, cache, and workflow concerns.
