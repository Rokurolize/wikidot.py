# PR Draft: Validate Create Thread Retained Category ID

## Summary

`ForumCategory.create_thread(...)` already validates public title, description, and source inputs before authentication, validates returned `newThread` action status, classifies malformed returned `threadId` values, and preserves cached thread lists on failed create results. One retained identity field still crossed the create-thread authentication boundary late: if a valid `ForumCategory` was later mutated, fixture-loaded, or rehydrated with a malformed or negative cached `id`, `create_thread(...)` called `login_check()` and could build `newThread` request work before the retained category-ID error surfaced elsewhere.

This change validates the present retained `ForumCategory.id` with `_validate_forum_category_id(self.id)` after public text-input validation and before login checks, AMC request construction, returned-ID parsing, action-status handling, created-thread lookup, or local thread-cache invalidation. Valid category IDs still produce the same `category_id` payload and successful create-thread behavior.

## Outcome

Forum thread creation can no longer authenticate or build `newThread` request work through corrupted retained category-ID state. Valid category IDs still create threads, returned thread-ID diagnostics still use the same site/category context, and failed retained-ID preflight preserves the existing `_threads` cache.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum creation, migration fixtures, generated forum ledgers, moderation tools, local forum tests, or serialized and rehydrated `ForumCategory` records before calling `ForumCategory.create_thread(...)`.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category traversal and thread creation as practical workflow surfaces. Existing drafts [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [644-pr-validate-non-negative-forum-category-ids.md](644-pr-validate-non-negative-forum-category-ids.md), [670-pr-validate-forum-category-collection-retained-id-state.md](670-pr-validate-forum-category-collection-retained-id-state.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), [684-pr-validate-forum-thread-reply-retained-id-state.md](684-pr-validate-forum-thread-reply-retained-id-state.md), and [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md) establish create-result diagnostics, adjacent reply action-status validation, forum write text-input validation, returned boolean `threadId` rejection, direct category-ID validation, collection retained-ID validation, category thread-list acquisition retained-ID validation, adjacent reply retained thread-ID validation, and create-thread action-status type validation.

This slice is not a duplicate of those drafts. Issue 354 validates caller-provided text inputs. Issues 167, 407, and 719 validate data returned by Wikidot after request work. Issues 644 and 670 validate direct category construction and collection lookup. Issue 681 validates retained category IDs before thread-list acquisition and cache return, not before `newThread` mutation work. Issue 684 validates `ForumThread.reply(...)` retained thread IDs, not category IDs used by `ForumCategory.create_thread(...)`.

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `self.id` at the start of `ForumCategory.create_thread(...)` with `_validate_forum_category_id(self.id)`.
- Run retained-ID validation before `login_check()` and before `newThread` AMC request construction.
- Use the validated `category_id` in the `newThread` request payload.
- Use the validated `category_id` in returned thread-ID diagnostics.
- Add focused regressions for malformed and negative retained category IDs that previously reached login and AMC work before failing.

## Type Of Change

- State validation
- Forum create-thread hardening
- Retained identity integrity
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory.create_thread(...)` must reject retained malformed `id` values such as `None`, `True`, `False`, `"1001"`, `1001.0`, and `[]` with `ValueError("id must be an integer")`. |
| R2 | `ForumCategory.create_thread(...)` must reject retained negative `id=-1` with `ValueError("id must be non-negative")`. |
| R3 | Retained-ID rejection must happen before `login_check()`, AMC request construction, returned-ID parsing, action-status handling, created-thread lookup, or local `_threads` invalidation. |
| R4 | Valid category IDs must preserve existing `newThread` payloads, returned thread-ID diagnostics, action-status diagnostics, created-thread lookup, and cache invalidation after confirmed success. |
| R5 | Public title, description, and source validation must retain precedence over retained category-ID validation. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum content, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, create-thread coverage, forum-category coverage, adjacent forum/site coverage, full unit tests, lint, format, mypy, pyright, whitespace, Brooks, and Clawpatch gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Create-thread rejects malformed retained category IDs before authentication. | `TestForumCategoryCreateThread.test_create_thread_rejects_malformed_retained_category_ids_before_login` failed RED for six malformed values because the path reached login/AMC work and then raised create-result `NoElementException`; it passed GREEN after retained-ID validation moved before login. | Accepting booleans/floats, coercing values, authenticating, sending AMC requests, or surfacing returned-thread diagnostics instead of retained state diagnostics rejects this local completion claim. | `ForumCategory.create_thread(...)` retained category-ID preflight | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Create-thread rejects negative retained category IDs before authentication. | `TestForumCategoryCreateThread.test_create_thread_rejects_negative_retained_category_id_before_login` failed RED by reaching the same request/result path, then passed GREEN with the non-negative diagnostic before login. | Treating a negative retained ID as a request category, authenticating before the local state error, or changing the diagnostic rejects this local completion claim. | `ForumCategory.create_thread(...)` retained category-ID preflight | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R3 | Validation is side-effect free for corrupted retained IDs. | The regressions assert `login_check()` and `site.amc_request(...)` are not called, and that retained `id` and cached `_threads` remain unchanged. | Calling login, constructing or sending `newThread`, parsing responses, fetching the created thread, clearing `_threads`, or coercing retained IDs rejects this local completion claim. | Create-thread preflight | focused tests |
| R4 | Existing successful create-thread behavior remains stable. | `TestForumCategoryCreateThread` passed 21 tests, `tests/unit/test_forum_category.py` passed 157 tests, adjacent forum/site coverage passed 1289 tests, and full unit coverage passed 3869 tests. | Regressing valid payloads, returned thread-ID diagnostics, status diagnostics, created-thread lookup, cache invalidation after success, or adjacent forum workflows rejects this local completion claim. | Forum create-thread and adjacent workflows | `tests/unit` |
| R5 | Public text validation keeps precedence. | Existing `test_create_thread_rejects_non_string_text_inputs_before_login` stayed green in focused and broader runs. | Checking malformed retained IDs before rejecting invalid title/description/source values rejects this local completion claim. | Create-thread input validation | `tests/unit/test_forum_category.py` |
| R6 | The local proof stays unit-level and private-data-free. | All regressions use synthetic local fixtures and mocks. | Using live Wikidot, credentials, cookies, auth JSON, raw private forum content, raw rollout paths, private site names, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository gates pass in the local dependency environment. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch doctor/provenance checks passed before the docs commit. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `db083e7 fix(forum_category): validate create thread category id`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_rejects_malformed_retained_category_ids_before_login tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_rejects_negative_retained_category_id_before_login -q --tb=short` failed seven retained category-ID cases before the fix because corrupted IDs reached login/AMC work and then surfaced as `Thread ID is not found ... category: <bad id>`.
- GREEN focused: the same command passed 7 tests after retained category-ID validation moved before login.
- Create-thread-focused coverage: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread -q --tb=short` passed 21 tests.
- Forum-category coverage: `uv run pytest tests/unit/test_forum_category.py -q --tb=short` passed 157 tests.
- Adjacent forum/site coverage: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py tests/unit/test_site.py -q --tb=short` passed 1289 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3869 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumCategory.create_thread(...)` raises `ValueError("id must be an integer")` when retained `id` is `None`, `True`, `False`, `"1001"`, `1001.0`, or `[]`.
- The same method raises `ValueError("id must be non-negative")` when retained `id` is `-1`.
- The retained-ID failure occurs before login checks, AMC request construction, returned-ID parsing, action-status handling, created-thread lookup, or local `_threads` invalidation.
- Failed retained-ID preflight does not coerce or rewrite the corrupted retained `id`.
- Invalid title, description, and source values still fail before retained-ID validation and before login/request work.
- Valid create-thread calls still use the same `newThread` payload, validate returned `threadId`, validate action status, clear `_threads` after confirmed success, and return the created `ForumThread`.
- Existing direct category-ID construction validation, collection retained-ID lookup validation, category thread-list acquisition retained-ID validation, reply retained thread-ID validation, parser diagnostics, and adjacent forum workflows remain unchanged.
- No browser, live Wikidot action, upstream Issue, or upstream PR action is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Callers with mutated or rehydrated malformed `ForumCategory.id` values now fail before create-thread work. Mitigation: direct constructor, collection lookup, thread-list acquisition, and cache ownership validation already define malformed or negative retained category IDs as invalid state.
- Risk: This could be mistaken for returned thread-ID validation. Mitigation: Issues 167 and 407 remain the returned `threadId` boundaries; this slice covers the category ID used to send the create request.
- Risk: This could be mistaken for create-thread action-status validation. Mitigation: Issue 719 remains the status-type boundary; this slice only changes the pre-auth retained category-ID boundary.
- Risk: This could change text-input validation order. Mitigation: public title, description, and source validation still runs before retained-ID validation.

## Dependencies

- Existing `_validate_forum_category_id(...)` remains the canonical retained category-ID validator.
- Existing `ForumCategory.create_thread(...)` text validation, request shape, returned thread-ID parsing, status diagnostics, created-thread lookup, and cache invalidation timing remain unchanged for valid values.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered create-thread retained category-ID path.

## Upstream-Safe Motivation

`ForumCategory.create_thread(...)` is the direct forum thread creation primitive. A retained category ID should satisfy the same integer and non-negative contract as directly constructed categories, category collection lookup, and category thread-list acquisition before authentication or `newThread` request work can happen. Validating retained IDs locally keeps corrupted fixture or rehydrated state from becoming a create-thread category identifier while preserving valid forum creation behavior and existing returned-result diagnostics.

## Local Evidence

- Local rollout-backed work established forum category traversal and thread creation as practical workflows through create-result context, forum write input validation, returned thread-ID validation, create-thread status diagnostics, category ID construction validation, category collection retained-ID validation, category thread-list retained-ID validation, and adjacent reply retained-ID validation.
- Existing local drafts covered public text inputs, returned `threadId` parsing, returned action status shape, direct category construction, collection lookup, category thread-list acquisition, and forum reply retained thread IDs; they did not cover present malformed retained `ForumCategory.id` state used by `ForumCategory.create_thread(...)` before its entry login.
- The focused RED failure showed malformed and negative retained category-ID state could call `login_check()` and reach mocked AMC work before failing as a returned thread-ID diagnostic.
- This slice only validates present retained category IDs used by `ForumCategory.create_thread(...)`. It does not change returned thread-ID parsing, action-status parsing, created-thread lookup, category thread-list acquisition, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw forum content, private page content, private site data, and private forum metadata out of upstream discussion.

## Additional Notes

The implementation intentionally validates the retained category ID once and reuses that validated integer in the create request and returned-ID diagnostics. That keeps the change local to the create-thread boundary while preventing corrupted non-integer or negative retained identity state from crossing authentication.
