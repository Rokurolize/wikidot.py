# PR Draft: Validate Non-Negative Forum Category Counts

## Summary

`ForumCategory` records store `threads_count` and `posts_count` values used by browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, reply-side category cache synchronization, local fixtures, and rehydrated records. Issue 453 validated that direct `ForumCategory.threads_count` and `posts_count` values are non-boolean integers, but it did not cover the separate domain invariant that forum category counts cannot be negative. Issue 233 validates malformed non-integer category count text during forum-start parsing, but parseable negative count text still became stored category state.

This change validates forum category thread and post counts as non-negative integers. Direct negative constructor values now raise field-specific diagnostics such as `ValueError("threads_count must be non-negative")`. Generated forum category list rows with negative `threads` or `posts` cells now raise contextual `NoElementException` diagnostics with site, row, field, and value. Zero counts remain valid because empty categories and empty forums are legitimate.

## Outcome

Direct and parser-created `ForumCategory` records can no longer store negative thread or post counts, while valid zero counts, valid positive counts, existing malformed-type diagnostics, existing malformed-text parser diagnostics, category parsing, category-owned thread reads, and adjacent forum workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, generated forum inventory ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, `site.forum.categories`, category-owned thread reads, forum reply workflows that update category counts, local fixtures, or serialized/rehydrated `ForumCategory` records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-category discovery and stored category records as practical workflow surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [168-pr-forum-category-fetch-failure-context.md](168-pr-forum-category-fetch-failure-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [264-pr-forum-category-create-thread-cache-invalidation.md](264-pr-forum-category-create-thread-cache-invalidation.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [434-pr-validate-forum-category-threads-assignments.md](434-pr-validate-forum-category-threads-assignments.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), and [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md) establish forum category acquisition, retry behavior, parser scoping, text fidelity, count parsing, fetch and response diagnostics, create/reply cache behavior, loaded-collection search-key validation, collection constructor state integrity, cache assignment validation, and direct scalar validation as active operational boundaries.

This slice is not a duplicate of Issue 453. Issue 453 validated integer type and boolean rejection for direct category count fields; this follow-up covers the separate non-negative count invariant while preserving zero counts. This slice is also not a duplicate of Issue 233, which validates malformed non-integer parser text such as `not-a-number`; this follow-up covers parseable but impossible negative generated count values.

## Related Issue / Non-Duplicate Analysis

Builds directly on [233-pr-forum-category-count-parse-context.md](233-pr-forum-category-count-parse-context.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), and [633-pr-validate-non-negative-page-metrics.md](633-pr-validate-non-negative-page-metrics.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a non-negative check to `ForumCategory.threads_count` and `ForumCategory.posts_count` validation after the existing non-boolean integer check.
- Reject direct negative category counts with field-specific `ValueError("<field> must be non-negative")` diagnostics.
- Add a parser-side non-negative check for generated forum category `threads` and `posts` cells.
- Preserve zero counts for empty categories.
- Preserve existing malformed count-type diagnostics, malformed count-text parser diagnostics, successful category-list parsing, empty forum indexes, nested-table filtering, category thread reads, reload behavior, create-thread behavior, reply-side cache synchronization, and adjacent forum thread/post/revision workflows.

## Type Of Change

- Input validation
- Parser diagnostics
- Public dataclass constructor behavior hardening
- Forum-category count state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `ForumCategory(threads_count=-1)` and `ForumCategory(posts_count=-1)` must raise `ValueError("<field> must be non-negative")`. |
| R2 | Direct zero values for `threads_count` and `posts_count` must remain valid. |
| R3 | Existing malformed type diagnostics must remain `ValueError("<field> must be an integer")`. |
| R4 | Generated forum category list rows with negative `threads` or `posts` cells must raise contextual `NoElementException` with site, row, field, and raw value. |
| R5 | Existing malformed non-integer parser diagnostics for category count cells must remain unchanged. |
| R6 | Successful category-list parsing, empty forum indexes, nested-table filtering, title/description parsing, collection initialization, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum thread/post/revision workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, forum-category tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative direct category counts fail at the public constructor boundary. | `TestForumCategoryBasic.test_init_rejects_negative_counts` failed RED for both fields with `DID NOT RAISE`, then passed GREEN after `_validate_forum_category_count(...)` rejected negative integers. | Accepting negative category counts, coercing them to zero, or deferring failure to later forum workflows rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Zero category counts remain valid. | `TestForumCategoryBasic.test_init_allows_zero_counts` passed in RED and GREEN and asserts both fields store `0`. | Rejecting empty categories or requiring positive counts rejects this local completion claim. | ForumCategory constructor compatibility | `tests/unit/test_forum_category.py` |
| R3 | Existing malformed-type diagnostics remain stable. | `test_init_rejects_non_integer_threads_count` and `test_init_rejects_non_integer_posts_count` passed in the focused RED and GREEN commands. | Changing type diagnostics, accepting booleans as integers, or coercing strings/floats rejects this local completion claim. | ForumCategory constructor type validation | `tests/unit/test_forum_category.py` |
| R4 | Negative generated category counts fail with parser context. | `TestForumCategoryCollectionAcquireAll.test_acquire_all_negative_count_includes_site_context` failed RED for `threads=-1` and `posts=-1` with `DID NOT RAISE`, then passed GREEN with contextual `NoElementException` diagnostics. | Returning a `ForumCategory` with negative generated counts, raising a raw constructor `ValueError`, omitting site/row/field/value context, or silently clamping the value rejects this local completion claim. | Forum category parser | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R5 | Existing malformed non-integer parser diagnostics remain stable. | `test_acquire_all_malformed_count_includes_site_context` passed in the focused RED and GREEN commands. | Treating malformed strings as negative, changing `Thread count is malformed` / `Post count is malformed`, or dropping row context rejects this local completion claim. | Forum category parser compatibility | `tests/unit/test_forum_category.py` |
| R6 | Existing forum-category and adjacent forum workflows remain green. | Forum-category coverage passed 107 tests, adjacent forum coverage passed 552 tests, and full unit coverage passed 2861 tests. | Regressing valid category parsing, empty results, nested-table filtering, title/description parsing, category reads, thread reads, post workflows, revision workflows, reply cache synchronization, or thread-cache behavior rejects this local completion claim. | Forum category and adjacent workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `ForumCategory` or forum-start fixture data only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML from real sites, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f778ae6 fix(forum_category): validate non-negative category counts`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_negative_counts tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_allows_zero_counts tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_threads_count tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_posts_count tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_negative_count_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_malformed_count_includes_site_context tests/unit/test_forum_category.py::TestForumCategoryCollectionAcquireAll::test_acquire_all_parse_fields -q` failed 4 new negative-count cases before the fix with `DID NOT RAISE`; zero-count, malformed count-type, malformed count-text parser, and successful parse guards stayed green.
- GREEN: the same focused command passed 16 tests after constructor and parser non-negative validation was added.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 107 tests.
- `uv run ruff check src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` passed.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 552 tests.
- `uv run pytest tests/unit -q` passed 2861 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategory(threads_count=-1)` and `ForumCategory(posts_count=-1)` raise the matching `ValueError("<field> must be non-negative")`.
- `ForumCategory(threads_count=0, posts_count=0)` remains valid.
- Existing malformed type inputs for both fields still raise `ValueError("<field> must be an integer")`.
- A generated category-list `threads=-1` cell raises `NoElementException("Thread count must be non-negative for site: test-site (row=1, field=threads, value=-1)")`.
- A generated category-list `posts=-1` cell raises `NoElementException("Post count must be non-negative for site: test-site (row=1, field=posts, value=-1)")`.
- Existing malformed non-integer category count parser diagnostics remain unchanged.
- Existing category-list parsing, empty forums, nested-table filtering, category reads, category thread caches, create-thread behavior, reply cache synchronization, forum thread behavior, forum post behavior, and forum post revision behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum category thread and post counts cannot be negative. Parser-side integer conversion already makes malformed textual values visible; this follow-up catches parseable but impossible negatives while preserving zero-count compatibility for empty categories. Direct constructor validation keeps generated ledgers, local fixtures, rehydrated records, moderation summaries, and downstream audit tooling from carrying impossible forum category metrics.

## Local Evidence

- Local rollout evidence used browser-free forum category discovery, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, category-owned thread reads, reply-side category post-count synchronization, and tests that seed forum-category records directly.
- Existing local drafts covered forum-category fetch retry behavior, nested-table scoping, text preservation, parser diagnostics, parser-side count diagnostics, response diagnostics, collection search-key validation, collection constructor validation, thread-cache assignment validation, forum-thread category validation, category ID validation, and direct category count-field type validation, but did not cover negative category counts.
- The focused RED failures showed negative direct category counts and negative generated forum category count cells were accepted as category state. The GREEN regressions cover negative values, zero compatibility, pre-existing malformed type validation, existing malformed parser text validation, and contextual parser diagnostics.
- This slice only validates non-negative forum category thread/post counts. It does not change category-list acquisition, parser selectors, category ID parsing, title parsing, description parsing, collection initialization, `find(...)`, lazy `site.forum.categories`, `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, forum thread parent-category validation, forum post behavior, forum post revision behavior, live site behavior, or parsing beyond negative count cells.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw forum HTML from real sites, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates category counts only. `ForumThread.post_count` has its own direct type-validation history and generated parser surfaces, and should be considered in a separate duplicate-checked slice.
