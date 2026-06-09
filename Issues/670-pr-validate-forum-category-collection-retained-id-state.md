# PR Draft: Validate Forum Category Collection Retained ID State

## Summary

`ForumCategoryCollection.find(id)` validates the caller-provided search ID before scanning stored categories, but the scan still compared each retained `category.id` directly against the search ID. After local fixture, serialized, or rehydrated category state has been mutated incorrectly, booleans and floats can satisfy Python equality against integer category IDs, while `None`, strings, lists, and negative IDs are treated as ordinary not-found misses instead of corrupted retained category-ID state.

This change validates each stored category's retained ID with the existing `_validate_forum_category_id(...)` helper before comparing it to the already validated search ID. Malformed retained category IDs now raise `ValueError("id must be an integer")`, negative retained category IDs now raise `ValueError("id must be non-negative")`, valid zero-ID lookup remains accepted, valid absent integer lookup still returns `None`, and no forum category fetch, parser, cache, or live Wikidot behavior changes.

## Outcome

Loaded forum category collections can no longer return a category by Python's loose numeric equality or hide corrupted retained category IDs behind an ordinary not-found result.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum category inventories, moderation ledgers, translation review tooling, migration records, cached forum category scans, local fixtures, or serialized and rehydrated `ForumCategoryCollection` objects.

## Current Evidence

Local rollout-backed drafts already established forum category discovery and category identity as practical boundaries. [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), [591-pr-validate-forum-category-collection-site-ownership.md](591-pr-validate-forum-category-collection-site-ownership.md), [634-pr-validate-non-negative-forum-category-counts.md](634-pr-validate-non-negative-forum-category-counts.md), [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md), and [668-pr-validate-forum-category-threads-cache-retained-category-id-state.md](668-pr-validate-forum-category-threads-cache-retained-category-id-state.md) cover forum-category acquisition, parser diagnostics, response diagnostics, lookup search-key validation, collection shape, direct ID type/range, site state, collection site ownership, counts, and retained thread-cache category-ID ownership.

This slice is not a duplicate of those drafts. Issue 380 validates the caller-provided `ForumCategoryCollection.find(id=...)` search key before scanning stored categories, but it does not validate retained IDs already stored inside the collection. Issues 452 and 644 validate direct `ForumCategory(id=...)` construction, but they cannot cover a valid category whose ID is corrupted after construction and then reused in a collection. Issue 668 validates retained category IDs in `ForumCategory._threads` cache ownership, not loaded collection lookup rows.

## Related Issue / Non-Duplicate Analysis

Builds directly on [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [591-pr-validate-forum-category-collection-site-ownership.md](591-pr-validate-forum-category-collection-site-ownership.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md), and [668-pr-validate-forum-category-threads-cache-retained-category-id-state.md](668-pr-validate-forum-category-threads-cache-retained-category-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate each stored `ForumCategory.id` before `ForumCategoryCollection.find(id)` compares it to the search key.
- Reject retained stored category IDs such as `None`, `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")`.
- Reject retained stored category IDs such as `-1` with `ValueError("id must be non-negative")`.
- Preserve valid zero-ID lookup, valid matching lookup, valid absent integer lookup, collection site ownership, category-list acquisition, parser diagnostics, lazy category thread reads, thread creation, and adjacent forum workflows.

## Type Of Change

- Input validation
- Retained forum-category ID hardening
- Loaded collection lookup integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategoryCollection.find(id)` must reject retained stored `category.id` values such as `None`, `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")` before comparison. |
| R2 | `ForumCategoryCollection.find(id)` must reject retained stored `category.id=-1` with `ValueError("id must be non-negative")` before comparison. |
| R3 | Valid lookup where the stored category ID and search ID are both `0` must remain accepted. |
| R4 | Existing caller search-key validation, valid matching lookup, valid not-found lookup, collection initialization, collection site ownership, category-list acquisition, parser diagnostics, lazy thread access, create-thread behavior, and adjacent forum workflows must remain green. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-category module coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained stored category IDs fail before lookup comparison. | `test_find_rejects_category_with_malformed_retained_ids` failed RED for six malformed values: booleans and `1001.0` could be accepted through Python equality, while `None`, `"1001"`, and `[]` returned ordinary misses. The test passed GREEN after stored category ID validation. | Accepting booleans/floats, returning ordinary `None` misses for corrupted IDs, coercing values, or returning a category from corrupted retained ID state rejects this local completion claim. | Stored `ForumCategory.id` during collection lookup | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Negative retained stored category IDs fail before lookup comparison. | `test_find_rejects_category_with_negative_retained_id` failed RED with an ordinary not-found result, then passed GREEN after stored category ID range validation. | Treating negative stored IDs as ordinary misses, accepting them, matching them, or coercing them rejects this local completion claim. | Stored `ForumCategory.id` during collection lookup | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Zero remains a valid retained category ID for lookup. | `test_find_accepts_category_with_zero_retained_id` passed RED and GREEN. | Rejecting `0`, treating it as missing, coercing it to false, or changing returned category identity rejects this local completion claim. | Forum category collection lookup semantics | `tests/unit/test_forum_category.py` |
| R4 | Existing compatible behavior remains compatible. | Focused GREEN coverage passed 8 tests, `tests/unit/test_forum_category.py` passed 138 tests, adjacent forum/site coverage passed 1015 tests, and full unit passed 3181 tests. | Regressing caller search-key validation, valid matching lookup, valid not-found lookup, collection initialization, collection site ownership, category-list acquisition, parser diagnostics, lazy category thread reads, create-thread behavior, forum thread/post/revision behavior, site workflows, or any unit test rejects this local completion claim. | Forum category collection and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic forum category objects and local unit helpers only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, temporary pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3b4c2f6 fix(forum_category): validate collection retained ids`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_find_accepts_category_with_zero_retained_id tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_find_rejects_category_with_malformed_retained_ids tests/unit/test_forum_category.py::TestForumCategoryCollectionInit::test_find_rejects_category_with_negative_retained_id -q` collected 8 tests: 7 retained stored category-ID cases failed before the fix, and the zero-ID compatibility guard passed.
- GREEN: the same focused command passed 8 tests after stored category IDs were validated before collection lookup comparison.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left both files unchanged.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 138 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q` passed 1015 tests.
- `uv run pytest tests/unit -q` passed 3181 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategoryCollection.find(1001)` raises `ValueError("id must be an integer")` when a stored category's retained `category.id` is `None`, `"1001"`, or `[]`.
- `ForumCategoryCollection.find(1)`, `find(0)`, and `find(1001)` raise `ValueError("id must be an integer")` when stored retained IDs are `True`, `False`, or `1001.0` before they can match through Python equality.
- `ForumCategoryCollection.find(1001)` raises `ValueError("id must be non-negative")` when a stored category's retained `category.id` is `-1`.
- `ForumCategoryCollection.find(0)` still returns a category whose retained ID is valid integer `0`.
- Existing malformed search-key rejection, matching lookup, not-found lookup, collection initialization, collection site ownership, category-list acquisition, parser diagnostics, lazy thread access, create-thread behavior, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumCategoryCollection.find(id)` is a local lookup over already loaded forum category inventories. The search key is already validated, and stored category rows should be held to the same retained-ID contract before comparison. Validating stored IDs prevents corrupted local state from matching through Python's bool/float equality rules or disappearing as an ordinary not-found result, while preserving valid zero IDs, valid not-found behavior, and all parser/network behavior.

## Local Evidence

- Existing local drafts covered forum-category fetch retry behavior, parser row scoping, response-body diagnostics, parser count diagnostics, write-input validation, collection search-key validation, collection constructor validation, collection parent-site validation, direct category ID type/range validation, direct category count/text validation, parent-site validation, and retained `ForumCategory._threads` cache-owner category-ID validation.
- None of those drafts covered malformed retained stored `ForumCategory.id` values inside `ForumCategoryCollection.find(...)` because the scan still compared `category.id == id` directly.
- The focused RED failure showed booleans and floats could be accepted as stored category IDs when they compared equal to lookup integers, while `None`, strings, lists, and negative IDs could be misreported as ordinary not-found results.
- This slice only validates retained stored category IDs at the loaded collection lookup comparison boundary. It does not change category-list acquisition, parser field extraction, cached category collections, lazy `site.forum.categories`, lazy `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumCategory.create_thread(...)`, forum thread behavior, forum post behavior, forum post revision behavior, page behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, page source text, private messages, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally reuses `_validate_forum_category_id(...)`, so retained collection rows now share the same zero-compatible non-negative integer contract as direct `ForumCategory` construction, search-key validation, and the retained `ForumCategory._threads` cache ownership checks.
