# PR Draft: Validate Forum Category Collection Site Field

## Summary

`ForumCategoryCollection` stores the optional explicit parent `Site` used by browser-free forum category discovery, lazy `site.forum.categories`, cached category inventories, category-owned thread reads, generated forum migration or audit ledgers, local fixtures, and rehydrated category state. Earlier local slices validated category-list fetching, response bodies, parser diagnostics, lookup IDs, collection `categories` containers and entries, category thread-cache assignment, direct `ForumCategory` identity/count/text fields, and adjacent `ForumThreadCollection.site`, but `ForumCategoryCollection(site=..., categories=...)` still accepted malformed explicit parent sites such as booleans, strings, dictionaries, and arbitrary objects.

This change validates non-`None` `ForumCategoryCollection.site` constructor arguments before storing collection state. Malformed explicit values now raise `ValueError("site must be a Site")`. The existing `site=None` inference behavior remains valid when a collection is built from a valid first category. Valid `Site` parents, empty category lists, valid `ForumCategory` lists, iteration, lookup, category-list acquisition, lazy `site.forum.categories`, category thread-list acquisition, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, direct category field validation, and adjacent forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-category collections with malformed explicit parent-site state, while parser-created, fixture-created, inferred-parent, cached, and manually created valid category collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, `site.forum.categories`, or local tests that construct `ForumCategoryCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category discovery as a practical workflow surface and as the entry point for downstream thread, post, and revision workflows. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), and [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md) establish category-list acquisition, retry behavior, parser scoping, text fidelity, response diagnostics, count parser diagnostics, loaded-collection search-key validation, collection entry validation, thread-cache assignment validation, direct category field validation, and adjacent collection parent-site validation as active operational boundaries.

Those prior slices are not duplicates. Issue 424 validates only the collection's `categories` container and entries while preserving valid site-supplied construction. Issue 434 validates assignment to the lazily populated `ForumCategory.threads` cache. Issue 447 validates `ForumThread.category`, not the category collection parent. Issues 452-454 validate direct `ForumCategory` identity, count, title, and description fields. Issue 475 validates the adjacent `ForumThreadCollection.site` parent, not `ForumCategoryCollection.site`. None validates direct non-`None` `ForumCategoryCollection(site=...)` construction before malformed parent-site state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), and the adjacent optional collection parent validation pattern from [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), and [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate non-`None` `ForumCategoryCollection.site` values at constructor initialization.
- Reject malformed explicit parent-site values with `ValueError("site must be a Site")`.
- Preserve `site=None` inference from a valid first category, valid empty category collections with an explicit valid site, valid `ForumCategory` lists, iteration, lookup, parser-created collections, category-list acquisition, lazy `site.forum.categories`, category thread-list acquisition, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum category parent-site state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategoryCollection(site=True)`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` when `categories` is otherwise valid. |
| R2 | `ForumCategoryCollection(categories=[valid_category])` must still infer the site from the first category, and `ForumCategoryCollection(site=<valid Site>, categories=[])` must remain constructible. |
| R3 | Valid `Site` parent values, valid empty category lists, valid `ForumCategory` lists, iteration, `find(...)`, category-list acquisition, lazy `site.forum.categories`, category thread-list acquisition, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, direct category field validation, and adjacent forum workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-category tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent sites fail at the public constructor boundary. | `TestForumCategoryCollectionInit.test_init_rejects_malformed_sites` failed RED for 4 malformed non-`None` values because the constructor did not raise, then passed GREEN after site validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting category collections with malformed explicit parent-site state rejects this local completion claim. | ForumCategoryCollection constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Optional inference and valid empty collection semantics stay green. | Existing empty initialization and category-entry tests passed in the 21-test constructor run and 75-test forum-category module run. | Losing parent-site inference from the first valid category, rejecting empty valid collections with explicit valid sites, or changing stored site identity rejects this local completion claim. | ForumCategoryCollection constructor | `tests/unit/test_forum_category.py` |
| R3 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_category.py` passed 75 tests, adjacent forum workflow tests passed 444 tests, and full unit tests passed 1919 tests. | Regressing category-list acquisition, parser diagnostics, response diagnostics, ID lookup, lazy site category reads, category thread-list reads, category create-thread behavior, forum thread workflows, forum post workflows, or forum post revision workflows rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `4ec7897 fix(forum_category): validate category collection site`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_init_rejects_malformed_sites -q` failed 4 tests before the fix; every malformed explicit `site` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `ForumCategoryCollection` explicit site validation was added.
- `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit -q` passed 21 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 75 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 444 tests.
- `uv run pytest tests/unit -q` passed 1919 tests.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed forum-category test file pass pyright together.

## Acceptance Criteria

- `ForumCategoryCollection(site=True)`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` raise `ValueError("site must be a Site")`.
- `ForumCategoryCollection(categories=[valid_category])` still infers the site from the first valid category.
- `ForumCategoryCollection(site=<valid Site>, categories=[])` and `ForumCategoryCollection(site=<valid Site>, categories=[valid_category])` remain valid.
- Existing valid `ForumCategory` lists, iteration, `find(...)`, category-list acquisition, lazy `site.forum.categories`, parser-side category diagnostics, direct category field validation, category thread cache behavior, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategoryCollection.site` is the collection-level parent used by browser-free forum category discovery, cached category inventories, lazy `site.forum.categories`, category-owned thread reads, and generated moderation or migration ledgers. Parser paths already create collections with valid owning sites or infer the parent from valid categories; direct constructor validation keeps malformed explicit collection parents out of generated ledgers, migration comparisons, publication audits, and downstream tooling while preserving parser and caller paths that intentionally use site inference.

## Local Evidence

- Local rollout evidence used browser-free forum category discovery, cached category scans, category-owned thread reads, and tests that seed category collections directly.
- Existing local drafts covered forum category fetch retry behavior, nested-table filtering, parser contexts, text spacing, response diagnostics, count parsing, response-body type validation, search-key validation, collection categories/entry validation, category thread-cache assignment validation, and direct category field validation, but did not cover direct non-`None` `ForumCategoryCollection(site=...)` construction.
- The focused RED failures showed invalid explicit constructor parent sites were accepted as collection state. The GREEN regression covers boolean, string, dictionary, and arbitrary object values while preserving inference from valid categories.
- This slice only validates forum-category collection explicit parent-site constructor input. It does not change category-list acquisition, parser selectors, category ID parsing, title/description parsing, count parsing, cached behavior, `find(...)`, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only for explicit non-`None` parent values. It does not compare collection parent identity with each contained category, coerce dictionaries into sites, change site inference from a valid first category, verify category/thread membership, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
