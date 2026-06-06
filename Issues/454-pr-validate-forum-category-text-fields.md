# PR Draft: Validate ForumCategory Text Fields

## Summary

`ForumCategory` records carry `title` and `description` values used by browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, local fixtures, and rehydrated records. Earlier local slices validated category-list fetching, parser scoping, parser-side title and description text fidelity, write-side forum text inputs, response-body diagnostics, loaded-collection search IDs, collection constructor entries, category thread-cache assignment, forum thread parent-category state, direct category IDs, and direct category counts. The public `ForumCategory(..., title=..., description=...)` dataclass constructor still accepted malformed stored text fields such as `None`, booleans, integers, and lists.

This change validates `ForumCategory.title` and `ForumCategory.description` at initialization. Malformed non-string values now raise `ValueError("title must be a string")` or `ValueError("description must be a string")`. Valid strings, including empty strings, remain valid, and parsed categories already use strings from the existing `get_text(" ", strip=True)` category-list parser.

## Outcome

Callers cannot silently construct forum-category records whose stored title or description is not a string, while category-list parsing, parser text-fidelity behavior, parser count diagnostics, `ForumCategoryCollection.find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread category state, and adjacent forum thread/post/revision behavior continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, `site.forum.categories`, local fixtures, or serialized/rehydrated category records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-category discovery and stored category records as practical workflow surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), and [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md) establish forum category list acquisition, retry behavior, parser scoping, text fidelity, fetch and response diagnostics, write-input validation, loaded-collection search-key validation, collection constructor state integrity, thread-cache assignment validation, forum thread parent-category validation, direct category-ID validation, and direct count validation as active operational boundaries.

Those prior slices are not duplicates. Issues 108 and 111 validate parser-side visible text spacing when category descriptions or titles are flattened from generated HTML. Issue 354 validates write-side public inputs to `ForumCategory.create_thread(...)`, `ForumThread.reply(...)`, and `ForumPost.edit(...)` before forum mutations. Issue 380 covers `ForumCategoryCollection.find(...)` search keys. Issue 424 validates the `ForumCategoryCollection(categories=...)` container and stored entry types. Issue 434 validates assignment to the lazily populated `ForumCategory.threads` cache. Issue 447 validates `ForumThread.category`. Issue 452 validates `ForumCategory.id`, and Issue 453 validates `ForumCategory.threads_count` and `ForumCategory.posts_count`. This slice validates the separate public dataclass `ForumCategory.title` and `ForumCategory.description` fields so malformed text values cannot become stored record state in manually constructed categories, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), and [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumCategory.title` and `ForumCategory.description` validation at dataclass initialization.
- Reuse the shared text-field validator so constructor title and description fields reject non-strings with field-specific `ValueError` diagnostics.
- Preserve valid string values, including empty strings.
- Preserve category-list parsing, parser text-fidelity behavior, parser count diagnostics, direct ID/count validation, collection initialization, `ForumCategoryCollection.find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and forum thread/post/revision behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-category record state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory(title=None)`, `True`, `1001`, and `["Test Category"]` must raise `ValueError("title must be a string")` when other constructor fields are valid. |
| R2 | `ForumCategory(description=None)`, `True`, `1001`, and `["Test category description"]` must raise `ValueError("description must be a string")` when other constructor fields are valid. |
| R3 | Valid string titles and descriptions, including empty strings, must remain valid constructor input. |
| R4 | Existing category-list parsing, parser-side title/description text fidelity, parser-side count diagnostics, ID/count validation, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread category state, and forum thread/post/revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor title values fail at the public dataclass boundary. | `TestForumCategoryBasic.test_init_rejects_non_string_title` failed RED for `None`, `True`, `1001`, and `["Test Category"]` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, integers, lists, serialized titles, or emitting `ForumCategory` records with non-string `title` rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Malformed constructor description values fail at the public dataclass boundary. | `TestForumCategoryBasic.test_init_rejects_non_string_description` failed RED for `None`, `True`, `1001`, and `["Test category description"]` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, integers, lists, serialized descriptions, or emitting `ForumCategory` records with non-string `description` rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Valid string text semantics stay green. | Existing `mock_forum_category_no_http`, `str(...)`, category acquisition, collection lookup, category-owned thread access, reload, and create-thread tests passed. | Rejecting ordinary strings, coercing non-strings to strings, trimming constructor-supplied strings, or changing stored title/description values rejects this local completion claim. | Parser-created and manually created categories | `tests/unit/test_forum_category.py` |
| R4 | Existing forum-category and adjacent forum workflows remain green. | `tests/unit/test_forum_category.py` passed 71 tests, adjacent forum tests passed 350 tests, and full unit tests passed 1760 tests. | Regressing category-list parsing, parser text fidelity, parser count diagnostics, ID/count validation, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread category state, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-category tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bfb2b49 fix(forum_category): validate category text fields`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_string_title tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_string_description -q` failed 8 tests before the fix; every malformed title/description value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_string_title tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_string_description -q` passed 8 tests.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 71 tests.
- `uv run pyright src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 350 tests.
- `uv run pytest tests/unit -q` passed 1760 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 66 existing full-tree typing errors outside this slice, including fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumCategory(title=None)`, `True`, `1001`, and `["Test Category"]` raise `ValueError("title must be a string")`.
- `ForumCategory(description=None)`, `True`, `1001`, and `["Test category description"]` raise `ValueError("description must be a string")`.
- Valid string titles and descriptions, including empty strings, remain valid.
- Existing category-list parsing, parser-side title/description text fidelity, parser-side count diagnostics, ID/count validation, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, and forum thread/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategory` is the record shape behind browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, and `site.forum.categories`. Parser-side title and description extraction already returns strings and prior write-input validation protects forum mutation inputs; the record constructor should apply the same text invariant so fixture-created or rehydrated categories cannot carry non-string titles or descriptions into logs, comparisons, searches, downstream ledgers, or string rendering.

## Local Evidence

- Local rollout evidence used browser-free forum category discovery, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, and tests that seed forum-category records directly.
- Existing local drafts covered forum-category fetch retry behavior, nested-table scoping, title/description parser text fidelity, parse diagnostics, response diagnostics, forum write text-input validation, collection search-key validation, collection constructor validation, thread-cache assignment validation, forum-thread category validation, category ID validation, and category count validation, but did not cover the `ForumCategory(title=..., description=...)` fields themselves.
- The focused RED failures showed invalid constructor title and description values were accepted as dataclass state. The GREEN regression covers missing, boolean, integer, and list values for both `title` and `description`.
- This slice only validates stored forum-category title/description types at construction. It does not change category-list acquisition, parser selectors, category ID parsing, title parsing, description parsing, count parsing, collection initialization, `find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread parent-category validation, forum post behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them with `str(...)`. Callers that load category records from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize title and description fields to strings before constructing `ForumCategory` records.
