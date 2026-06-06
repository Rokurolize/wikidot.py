# PR Draft: Validate ForumCategory ID Field

## Summary

`ForumCategory` records are produced by `ForumCategoryCollection.acquire_all(...)`, lazy `site.forum.categories`, cached category scans, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, local fixtures, and direct `ForumCategoryCollection` construction. Earlier local slices validated forum-category list fetching, parser scoping, response diagnostics, loaded-collection search IDs, collection constructor entries, category thread-cache assignment, and forum thread parent-category state. The public `ForumCategory(..., id=...)` dataclass constructor still accepted malformed stored IDs such as `None`, booleans, strings, and floats.

This change validates `ForumCategory.id` at initialization. Malformed non-integer values now raise `ValueError("id must be an integer")`. Valid integer IDs remain valid, and parsed categories already use integer IDs from the existing category-list parsing path.

## Outcome

Callers cannot silently construct forum-category records whose stored category ID is not an integer, while category-list parsing, `ForumCategoryCollection.find(...)`, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, and adjacent forum thread/post/revision behavior continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, `site.forum.categories`, or fixtures that construct `ForumCategory` records directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-category discovery and stored category records as practical workflow surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-missing-id-context.md](233-pr-forum-category-missing-id-context.md), [252-pr-forum-category-numeric-field-context.md](252-pr-forum-category-numeric-field-context.md), [264-pr-forum-category-metadata-mismatch-context.md](264-pr-forum-category-metadata-mismatch-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignment.md](434-pr-validate-forum-category-threads-assignment.md), and [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md) establish forum category list acquisition, retry behavior, parser scoping, text fidelity, fetch and response diagnostics, loaded-collection search-key validation, collection constructor state integrity, thread-cache assignment validation, and forum thread parent-category validation as active operational boundaries.

Those prior slices are not duplicates. Issue 380 covers `ForumCategoryCollection.find(...)` search-key validation after a category collection already exists. Issue 424 validates the `ForumCategoryCollection(categories=...)` container and stored entry types. Issue 434 validates assignment to the lazily populated `ForumCategory.threads` cache. Issue 447 validates `ForumThread.category`. This slice validates the separate public dataclass `ForumCategory.id` field so malformed category IDs cannot become stored record state in manually constructed categories, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-missing-id-context.md](233-pr-forum-category-missing-id-context.md), [252-pr-forum-category-numeric-field-context.md](252-pr-forum-category-numeric-field-context.md), [264-pr-forum-category-metadata-mismatch-context.md](264-pr-forum-category-metadata-mismatch-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignment.md](434-pr-validate-forum-category-threads-assignment.md), and [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumCategory.id` validation at dataclass initialization.
- Reuse the forum-category ID validator so constructor IDs reject non-integers and booleans with `ValueError("id must be an integer")`.
- Preserve valid integer IDs, category-list parsing, `ForumCategoryCollection.find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and forum thread/post/revision behavior.
- Make two existing invalid-input test fixtures explicit `Any` values so targeted pyright can type-check the changed forum-category test file without weakening runtime coverage.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-category record state integrity
- Test addition
- Test fixture typing cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory(id=None)`, `True`, `"1001"`, and `1001.0` must raise `ValueError("id must be an integer")` when other constructor fields are valid. |
| R2 | Valid integer category IDs must remain valid constructor input. |
| R3 | Existing category-list parsing, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, and forum thread/post/revision workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor ID values fail at the public dataclass boundary. | `TestForumCategoryBasic.test_init_rejects_non_integer_category_id` failed RED for `None`, `True`, `"1001"`, and `1001.0` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, floats, serialized IDs, or emitting `ForumCategory` records with non-integer IDs rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Valid integer ID semantics stay green. | Existing `mock_forum_category_no_http`, `str(...)`, category acquisition, collection lookup, category-owned thread access, reload, and create-thread tests passed. | Rejecting ordinary integer IDs, coercing strings to integers, or changing stored IDs rejects this local completion claim. | Parser-created and manually created categories | `tests/unit/test_forum_category.py` |
| R3 | Existing forum-category and adjacent forum workflows remain green. | `tests/unit/test_forum_category.py` passed 55 tests, adjacent forum tests passed 334 tests, and full unit tests passed 1744 tests. | Regressing category-list parsing, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread category state, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum category and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-category tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f18b22f fix(forum_category): validate category id`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_category_id -q` failed 4 tests before the fix; every malformed `id` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_category_id -q` passed 4 tests.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 55 tests.
- `uv run pyright src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with 0 errors, 0 warnings, and 0 informations after making existing invalid-input fixtures explicit `Any`.
- `uv run mypy src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 334 tests.
- `uv run pytest tests/unit -q` passed 1744 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 66 existing full-tree typing errors outside this slice, including fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumCategory(id=None)`, `True`, `"1001"`, and `1001.0` raise `ValueError("id must be an integer")`.
- Valid integer IDs remain valid.
- Existing category-list parsing, collection initialization, loaded-collection lookup, lazy `site.forum.categories`, category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, and forum thread/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategory` is the record shape behind browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, and `site.forum.categories`. Lookup APIs already validate caller-provided category IDs; the record constructor should apply the same invariant so fixture-created or rehydrated categories cannot carry non-integer IDs into logs, comparisons, searches, or downstream ledgers.

## Local Evidence

- Local rollout evidence used browser-free forum category discovery, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, and tests that seed forum-category records directly.
- Existing local drafts covered forum-category fetch retry behavior, nested-table scoping, text preservation, parse diagnostics, response diagnostics, collection search-key validation, collection constructor validation, thread-cache assignment validation, and forum-thread category validation, but did not cover the `ForumCategory(id=...)` field itself.
- The focused RED failures showed invalid constructor IDs were accepted as dataclass state. The GREEN regression covers missing, boolean, string, and float ID values.
- This slice only validates stored forum-category ID type at construction. It does not change category-list acquisition, parser selectors, title parsing, description parsing, thread/post counts, collection initialization, `find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread parent-category validation, forum post behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load category IDs from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to integers before constructing `ForumCategory` records.
