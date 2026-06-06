# PR Draft: Validate ForumCategory Count Fields

## Summary

`ForumCategory` records carry `threads_count` and `posts_count` values used by browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, reply-side category cache synchronization, local fixtures, and rehydrated records. Earlier local slices validated category-list fetching, parser scoping, text fidelity, parser-side malformed count diagnostics, response-body diagnostics, loaded-collection search IDs, collection constructor entries, category thread-cache assignment, forum thread parent-category state, and direct category IDs. The public `ForumCategory(..., threads_count=..., posts_count=...)` dataclass constructor still accepted malformed stored counts such as `None`, booleans, strings, and floats.

This change validates `ForumCategory.threads_count` and `ForumCategory.posts_count` at initialization. Malformed non-integer values now raise `ValueError("threads_count must be an integer")` or `ValueError("posts_count must be an integer")`. Valid integer counts remain valid, and parsed categories already use integers from the existing count parser.

## Outcome

Callers cannot silently construct forum-category records whose stored thread/post counts are not integers, while category-list parsing, contextual parser count failures, `ForumCategoryCollection.find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread reply cache synchronization, and adjacent forum thread/post/revision behavior continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, `site.forum.categories`, forum reply workflows that update category post counts, or fixtures that construct `ForumCategory` records directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-category discovery and stored category records as practical workflow surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), and [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md) establish forum category list acquisition, retry behavior, parser scoping, text fidelity, count parsing, fetch and response diagnostics, create/reply cache behavior, loaded-collection search-key validation, collection constructor state integrity, thread-cache assignment validation, forum thread parent-category validation, and direct category-ID validation as active operational boundaries.

Those prior slices are not duplicates. Issue 233 validates malformed HTML count text during `ForumCategoryCollection.acquire_all(...)` parsing and reports site/row/value context. Issue 380 covers `ForumCategoryCollection.find(...)` search keys. Issue 424 validates the `ForumCategoryCollection(categories=...)` container and stored entry types. Issue 434 validates assignment to the lazily populated `ForumCategory.threads` cache. Issue 447 validates `ForumThread.category`. Issue 452 validates `ForumCategory.id`. This slice validates the separate public dataclass `ForumCategory.threads_count` and `ForumCategory.posts_count` fields so malformed counts cannot become stored record state in manually constructed categories, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), and [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumCategory.threads_count` and `ForumCategory.posts_count` validation at dataclass initialization.
- Reject non-integers and booleans with field-specific `ValueError` diagnostics.
- Preserve valid integer counts, category-list parsing, contextual parser count diagnostics, `ForumCategoryCollection.find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread reply cache synchronization, and forum thread/post/revision behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-category record state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory(threads_count=None)`, `True`, `"10"`, and `10.0` must raise `ValueError("threads_count must be an integer")` when other constructor fields are valid. |
| R2 | `ForumCategory(posts_count=None)`, `True`, `"50"`, and `50.0` must raise `ValueError("posts_count must be an integer")` when other constructor fields are valid. |
| R3 | Valid integer category IDs and valid integer thread/post counts must remain valid constructor input. |
| R4 | Existing category-list parsing, parser-side count diagnostics, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread reply cache synchronization, and forum thread/post/revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor thread-count values fail at the public dataclass boundary. | `TestForumCategoryBasic.test_init_rejects_non_integer_threads_count` failed RED for `None`, `True`, `"10"`, and `10.0` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, floats, serialized counts, or emitting `ForumCategory` records with non-integer `threads_count` rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Malformed constructor post-count values fail at the public dataclass boundary. | `TestForumCategoryBasic.test_init_rejects_non_integer_posts_count` failed RED for `None`, `True`, `"50"`, and `50.0` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, floats, serialized counts, or emitting `ForumCategory` records with non-integer `posts_count` rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Valid integer count semantics stay green. | Existing `mock_forum_category_no_http`, `str(...)`, category acquisition, collection lookup, category-owned thread access, reload, and create-thread tests passed. | Rejecting ordinary integer counts, coercing strings to integers, or changing stored count values rejects this local completion claim. | Parser-created and manually created categories | `tests/unit/test_forum_category.py` |
| R4 | Existing forum-category and adjacent forum workflows remain green. | `tests/unit/test_forum_category.py` passed 63 tests, adjacent forum tests passed 342 tests, and full unit tests passed 1752 tests. | Regressing category-list parsing, contextual count parser failures, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread category state, reply-side category post-count synchronization, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-category tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `cd2543a fix(forum_category): validate category counts`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_threads_count tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_posts_count -q` failed 8 tests before the fix; every malformed count value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_threads_count tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_posts_count -q` passed 8 tests.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 63 tests.
- `uv run pyright src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 342 tests.
- `uv run pytest tests/unit -q` passed 1752 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted after formatting the changed test file.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 66 existing full-tree typing errors outside this slice, including fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumCategory(threads_count=None)`, `True`, `"10"`, and `10.0` raise `ValueError("threads_count must be an integer")`.
- `ForumCategory(posts_count=None)`, `True`, `"50"`, and `50.0` raise `ValueError("posts_count must be an integer")`.
- Valid integer counts remain valid.
- Existing category-list parsing, parser-side count diagnostics, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, and forum thread/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategory` is the record shape behind browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, `site.forum.categories`, and category post-count updates after replies. Parser-side malformed count text already fails with contextual diagnostics; the record constructor should apply the same integer invariant so fixture-created or rehydrated categories cannot carry non-integer counts into logs, comparisons, arithmetic, searches, or downstream ledgers.

## Local Evidence

- Local rollout evidence used browser-free forum category discovery, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, reply-side category post-count synchronization, and tests that seed forum-category records directly.
- Existing local drafts covered forum-category fetch retry behavior, nested-table scoping, text preservation, parser diagnostics, parser-side count diagnostics, response diagnostics, collection search-key validation, collection constructor validation, thread-cache assignment validation, forum-thread category validation, and category ID validation, but did not cover the `ForumCategory(threads_count=..., posts_count=...)` fields themselves.
- The focused RED failures showed invalid constructor counts were accepted as dataclass state. The GREEN regression covers missing, boolean, string, and float count values for both `threads_count` and `posts_count`.
- This slice only validates stored forum-category count types at construction. It does not change category-list acquisition, parser selectors, category ID parsing, title parsing, description parsing, count parsing, collection initialization, `find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread parent-category validation, forum post behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load category counts from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to integers before constructing `ForumCategory` records.
