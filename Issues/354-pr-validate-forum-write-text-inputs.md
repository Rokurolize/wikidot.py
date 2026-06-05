# PR Draft: Validate Forum Write Text Inputs Before Requests

## Summary

`ForumCategory.create_thread(...)`, `ForumThread.reply(...)`, and `ForumPost.edit(...)` document forum write text fields as strings, but malformed non-string values were not rejected at the public API boundary. A caller could pass an integer, list, or other object as a thread title, description, reply title, post source, or edit title and the method would proceed into login checks, AMC request construction, edit-form fetches, action-status parsing, or local cache mutation before surfacing a downstream failure.

This change validates forum write text inputs before login checks or any AMC work. Invalid values now raise `ValueError("{field} must be a string")` for `title`, `description`, or `source`. Valid forum create, reply, and edit behavior remains unchanged.

## Outcome

Browser-free forum mutation callers now get deterministic Python-side preflight validation for malformed text payloads instead of partial write-side progress, remote requests, generated edit-form reads, or unhelpful response/parser errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using forum thread creation, forum replies, and forum post editing in migration scripts, moderation tooling, generated discussion workflows, audit jobs, or browser-free forum maintenance.

## Current Evidence

Local rollout evidence repeatedly treats forum reads and writes as practical operational surfaces. Existing drafts [033-pr-retry-forum-category-list-fetches.md](033-pr-retry-forum-category-list-fetches.md), [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [167-pr-forum-thread-create-result-context.md](167-pr-forum-thread-create-result-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), and [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md) establish forum mutation paths, edit-form boundaries, create-thread result handling, and action-status confirmation as practical surfaces.

Those prior slices are not duplicates: they covered retry/read boundaries, generated edit-form parsing, returned `threadId` validation, action-status validation, and local state updates after successful responses. They did not validate public forum write text inputs before login checks, request construction, or form fetches. This slice follows the adjacent input-boundary pattern from [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md) and [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), but applies it to forum writes.

## Related Issue

Builds directly on [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [251-pr-forum-thread-reply-action-status-context.md](251-pr-forum-thread-reply-action-status-context.md), [252-pr-forum-category-create-thread-action-status-context.md](252-pr-forum-category-create-thread-action-status-context.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), and [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small private module validation helper for documented text fields.
- Validate `ForumCategory.create_thread(title=..., description=..., source=...)` before login checks or `newThread` requests.
- Validate `ForumThread.reply(source=..., title=...)` before login checks or `savePost` requests.
- Validate `ForumPost.edit(source=..., title=...)` before login checks, edit-form fetches, revision parsing, save requests, local title/source mutation, revision-cache invalidation, or thread post-cache invalidation.
- Preserve omitted `ForumPost.edit(title=None)` behavior.
- Preserve valid forum create/reply/edit payloads, action-status diagnostics, retry-aware edit-form fetch behavior, successful cache invalidation, and local state updates after confirmed successful responses.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum write preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumCategory.create_thread(...)` must reject non-string `title`, `description`, and `source` values with stable `ValueError` messages before login checks or AMC requests. |
| R2 | `ForumThread.reply(...)` must reject non-string `source` and `title` values with stable `ValueError` messages before login checks, AMC requests, local post-count increments, or cache invalidation. |
| R3 | `ForumPost.edit(...)` must reject non-string `source` and explicit non-string `title` values with stable `ValueError` messages before login checks, edit-form fetches, save requests, local title/source mutation, revision-cache invalidation, or thread post-cache invalidation. |
| R4 | Valid forum create, reply, parent reply, edit, and edit-title behavior must remain unchanged. |
| R5 | Existing malformed action-status, generated edit-form, revision-ID, response-body, login-required, and cache-invalidation behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, affected forum-module tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Create-thread text inputs fail before side effects. | `TestForumCategoryCreateThread.test_create_thread_rejects_non_string_text_inputs_before_login` failed RED before the fix because invalid values reached login/AMC and then `threadId` parsing; it passed GREEN after validation was added. | Calling `login_check()`, calling `amc_request(...)`, fetching the created thread, or leaking create-result errors rejects this local completion claim. | Forum category create-thread preflight | `src/wikidot/module/forum_category.py`, `tests/unit/test_forum_category.py` |
| R2 | Reply text inputs fail before side effects. | `TestForumThreadReply.test_reply_rejects_non_string_text_inputs_before_login` failed RED before the fix because invalid values reached `savePost` handling; it passed GREEN after validation was added. | Calling `login_check()`, sending `savePost`, incrementing `post_count`, clearing `_posts`, or mutating category counts rejects this local completion claim. | Forum thread reply preflight | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Edit text inputs fail before login or generated form reads. | `TestForumPostEdit.test_edit_rejects_non_string_text_inputs_before_login_or_form_fetch` failed RED before the fix because invalid values reached login and edit-form body parsing; it passed GREEN after validation was added. | Calling `login_check()`, fetching the edit form, sending `saveEditPost`, updating `title` or `_source`, clearing `_revisions`, or clearing `thread._posts` rejects this local completion claim. | Forum post edit preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Valid forum write behavior remains unchanged. | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, and `tests/unit/test_forum_post.py` passed 157 tests after the fix. | Regressing successful create/reply/edit payloads, parent reply IDs, valid edit titles, method chaining, or successful local cache updates rejects this local completion claim. | Forum mutation workflows | affected forum unit tests |
| R5 | Existing response and form diagnostics remain unchanged. | The same affected forum-module run kept action-status, edit-form, revision-ID, response-body, exhausted retry, login-required, and cache-invalidation regressions green. | Replacing contextual response/form failures with generic input errors for valid inputs, changing action-status messages, or weakening cache assertions rejects this local completion claim. | Forum mutation diagnostics | affected forum unit tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, forum content from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0823e26 fix(forum): validate write text inputs`.

- RED: `PYTHONPATH=src pytest -q tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_rejects_non_string_text_inputs_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_non_string_text_inputs_before_login tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_rejects_non_string_text_inputs_before_login_or_form_fetch` failed 7 parameterized cases before the fix because invalid forum write text values reached login, AMC request, or edit-form handling instead of raising stable `ValueError`.
- GREEN: the same focused command passed 7 tests after adding text-field preflight.
- `PYTHONPATH=src pytest -q tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py` passed 157 tests.
- `ruff format src/wikidot/module/_validation.py src/wikidot/module/forum_category.py src/wikidot/module/forum_thread.py src/wikidot/module/forum_post.py tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py` left 7 files unchanged.
- `ruff check src/wikidot/module/_validation.py src/wikidot/module/forum_category.py src/wikidot/module/forum_thread.py src/wikidot/module/forum_post.py tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py` passed.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `.venv/bin/python -m pytest -q tests/unit` passed 961 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumCategory.create_thread(title=3, ...)` raises `ValueError("title must be a string")` before calling `login_check()` or `amc_request(...)`.
- `ForumCategory.create_thread(description=3, ...)` raises `ValueError("description must be a string")` before calling `login_check()` or `amc_request(...)`.
- `ForumCategory.create_thread(source=3, ...)` raises `ValueError("source must be a string")` before calling `login_check()` or `amc_request(...)`.
- `ForumThread.reply(source=3)` and `ForumThread.reply(title=3)` raise stable `ValueError` messages before login checks, AMC requests, post-count updates, or cache invalidation.
- `ForumPost.edit(source=3)` and `ForumPost.edit(title=3)` raise stable `ValueError` messages before login checks, edit-form fetches, save requests, title/source mutation, revision-cache invalidation, or thread post-cache invalidation.
- `ForumPost.edit(title=None)` remains the omit-title path and uses the current post title in the save payload.
- Valid create/reply/edit paths remain green, including reply titles, parent replies, edit titles, create-thread detail lookup, and successful cache invalidation.
- Existing malformed action-status and generated edit-form diagnostics remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum write helpers should reject malformed text payloads before they do login checks, fetch generated edit forms, submit non-retried forum actions, or mutate local caches. This keeps runtime behavior aligned with the documented string API without changing valid request shapes or the existing action-status guards for successful writes.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established forum creation, reply, source acquisition, edit-form retrieval, post editing, and action-status validation as practical surfaces.
- The focused RED failures showed malformed forum write text inputs crossing into login/AMC or edit-form work instead of failing at the public call boundary.
- Existing forum action-status drafts covered returned response validation after remote actions; this slice covers malformed caller input before any action can start.
- Private-message send input validation remains a separate potential follow-up because it is a different module/API surface from forum create/reply/edit.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, forum post content from real sites, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load forum titles, descriptions, or post bodies from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should normalize them to strings before calling wikidot.py forum write helpers.
