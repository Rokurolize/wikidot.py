# PR Draft: Validate Non-Negative ForumCategory IDs

## Summary

`ForumCategory.id` identifies concrete forum categories used by browser-free forum category discovery, cached category inventories, lazy category-owned thread reads, `reload_threads(...)`, `create_thread(...)`, generated forum inventory ledgers, moderation or migration tooling, local fixtures, and rehydrated records. Existing local drafts validate category IDs as non-boolean integers, but direct `ForumCategory(...)` construction still accepted negative integers such as `-1`.

This change validates direct `ForumCategory.id` values as non-negative integers at the shared category-ID validation boundary. It deliberately preserves `id=0` because prior identity-field drafts avoid stronger positive-ID requirements unless parser or live evidence proves one.

## Outcome

Directly constructed forum-category records can no longer store negative category IDs, while zero-ID compatibility, malformed direct type diagnostics, category count validation, generated category-list parsing, collection initialization, collection lookup, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum category discovery, `site.forum.categories`, category-owned thread reads, forum migration checks, generated forum inventory ledgers, moderation tooling, translation review tooling, local fixtures, or serialized/rehydrated forum category records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category records as practical workflow surfaces. [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [157-pr-forum-category-parse-context.md](157-pr-forum-category-parse-context.md), [211-pr-forum-category-list-response-body-context.md](211-pr-forum-category-list-response-body-context.md), [322-pr-forum-category-response-body-type-context.md](322-pr-forum-category-response-body-type-context.md), [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), and [634-pr-validate-non-negative-forum-category-counts.md](634-pr-validate-non-negative-forum-category-counts.md) establish forum-category acquisition, parser diagnostics, response diagnostics, collection state, loaded-collection lookup, direct category scalar fields, parent site validation, and count range semantics as practical operational boundaries.

This slice is not a duplicate of Issues 380, 424, 452, 502, or 634. Issue 380 validates already-loaded collection search-key shape, and this slice intentionally does not alter `find(...)` semantics. Issue 424 validates the `ForumCategoryCollection(categories=...)` container and stored entry types. Issue 452 rejects malformed direct constructor ID types, but still accepts negative integers. Issue 502 validates parent-site state, not category identity range. Issue 634 validates thread/post count ranges, not category ID ranges.

## Related Issue / Non-Duplicate Analysis

Builds directly on [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md), [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), and [634-pr-validate-non-negative-forum-category-counts.md](634-pr-validate-non-negative-forum-category-counts.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `ForumCategory(id=-1)` with `ValueError("id must be non-negative")`.
- Preserve direct `ForumCategory(id=0)` as a non-negative identity value.
- Preserve existing malformed-ID diagnostics for non-integers and booleans.
- Leave generated category-list parsing, category count validation, collection initialization, collection `find(...)` lookup semantics, lazy thread access, `reload_threads(...)`, `create_thread(...)`, and adjacent forum workflows unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-category identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `ForumCategory(id=-1)` must raise `ValueError("id must be non-negative")` when every other category field is valid. |
| R2 | Direct `ForumCategory(id=0)` must remain valid and store `0`. |
| R3 | Existing malformed direct ID diagnostics must remain stable. |
| R4 | Category count validation, generated category-list parsing, collection initialization, collection lookup, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-category tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct forum-category records cannot store negative category IDs. | `TestForumCategoryBasic.test_init_rejects_negative_category_id` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_forum_category_id(...)` rejected values below zero. | Accepting negative category IDs, coercing them to zero, or deferring failure to parser or lookup code rejects this local completion claim. | ForumCategory constructor | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Zero remains valid for direct category IDs. | `TestForumCategoryBasic.test_init_accepts_zero_category_id` passed in RED and GREEN runs. | Requiring positive-only category IDs without separate evidence rejects this local completion claim. | Constructor compatibility | `tests/unit/test_forum_category.py` |
| R3 | Existing malformed direct type diagnostics remain stable. | `TestForumCategoryBasic.test_init_rejects_non_integer_category_id` passed in the same focused RED and GREEN commands. | Changing `ValueError("id must be an integer")`, accepting booleans, or coercing strings/floats rejects this local completion claim. | ForumCategory ID type validation | `tests/unit/test_forum_category.py` |
| R4 | Existing forum-category and adjacent forum workflows remain green. | Forum-category coverage passed 109 tests, adjacent forum category/thread/post/revision coverage passed 577 tests, and the full unit suite passed 2915 tests. | Regressing category-list acquisition, parser diagnostics, response diagnostics, category counts, collection initialization, loaded-collection lookup, lazy category thread reads, `reload_threads(...)`, `create_thread(...)`, forum thread parent-category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum-category and adjacent workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum titles, response bodies, post bodies from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-category tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d00468c fix(forum_category): validate non-negative category ids`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_non_integer_category_id tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_rejects_negative_category_id tests/unit/test_forum_category.py::TestForumCategoryBasic::test_init_accepts_zero_category_id -q` failed 1 negative direct constructor ID case before the fix; 5 malformed-input and zero-compatibility guards stayed green.
- GREEN: the same focused command passed 6 tests after direct category-ID range validation was added.
- `uv run ruff format src/wikidot/module/forum_category.py tests/unit/test_forum_category.py` left both files unchanged.
- Re-running the same focused command after formatting passed 6 tests.
- `uv run pytest tests/unit/test_forum_category.py -q` passed 109 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 577 tests.
- `uv run pytest tests/unit -q` passed 2915 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumCategory(id=-1)` raises `ValueError("id must be non-negative")`.
- `ForumCategory(id=0)` remains accepted and stores `0`.
- `ForumCategory(id=None)`, `True`, `"1001"`, and `1001.0` continue to raise `ValueError("id must be an integer")`.
- Category count validation, generated category-list parsing, collection initialization, collection lookup, lazy `ForumCategory.threads`, `reload_threads(...)`, `create_thread(...)`, and adjacent forum category/thread/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum category IDs are identity metadata for browser-free forum inventories, cached category ledgers, moderation summaries, migration checks, category-owned thread traversal, local fixtures, and rehydrated records. Negative IDs can look like valid integer state in direct fixtures or generated inventory structures but are not useful category identifiers in the current public API surface. Non-negative validation catches that impossible state early while avoiding a stronger positive-only rule.

## Local Evidence

- Local rollout evidence used forum-category discovery, cached forum inventories, category-owned thread reads, generated moderation ledgers, forum migration checks, local fixtures, and records that construct or consume `ForumCategory` objects directly.
- Existing local drafts covered forum-category fetch retry behavior, parser row scoping, response-body diagnostics, parser count diagnostics, write-input validation, collection search-key validation, collection constructor validation, collection parent-site validation, thread-cache assignment validation, direct category ID type validation, direct category count/text validation, and parent-site validation, but did not cover negative direct category IDs.
- The focused RED failure showed negative direct constructor IDs were accepted as category state. The GREEN regressions cover invalid values, zero compatibility, and existing malformed type validation.
- This slice only validates non-negative direct category-ID semantics. It does not change generated category-list parsing, collection `find(...)` lookup semantics, category-list selectors, title parsing, description parsing, thread/post count parsing, lazy thread access, thread creation, forum thread behavior, live site behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, page source text, private messages, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative direct forum-category IDs only. It does not require positive IDs, coerce numeric strings, or change `ForumCategoryCollection.find(...)` lookup semantics because prior local search-key drafts preserved absent integer lookup behavior while generated parser IDs already have their own diagnostics.
