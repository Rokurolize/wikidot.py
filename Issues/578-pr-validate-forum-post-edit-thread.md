# PR Draft: Validate Forum Post Edit Thread State

## Summary

`ForumPost.edit(...)` validates public edit text inputs before login and edit-form work, and `ForumPost(...)` validates constructor-time parent threads. One action-time retained-state boundary still trusted `self.thread` after construction. If caller code, a fixture, or rehydrated state replaced a valid post's retained thread with a malformed object, edit could proceed into login/form-fetch handling and surface unrelated edit-form diagnostics before reporting the invalid parent.

This change revalidates the retained post thread after edit input validation and before login checks, edit-form fetches, save requests, local source/title mutation, revision-cache invalidation, or thread post-cache invalidation. Malformed action-time parent state now raises `ValueError("thread must be a ForumThread")`. Valid edits, input validation precedence, edit-form parsing, save action-status validation, cache invalidation, source reads, post-list reads, and adjacent forum workflows remain unchanged.

## Outcome

Forum post editing now has explicit action-time retained-thread preflight before malformed local post state can influence authentication, request routing, edit-form parsing, save behavior, or cache mutation.

## Current Evidence

Existing drafts [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [162-pr-forum-post-edit-revision-error-context.md](162-pr-forum-post-edit-revision-error-context.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md), [269-pr-forum-post-edit-thread-cache-invalidation.md](269-pr-forum-post-edit-thread-cache-invalidation.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [576-pr-validate-forum-post-source-collection-thread.md](576-pr-validate-forum-post-source-collection-thread.md), and [577-pr-validate-forum-post-source-thread-site.md](577-pr-validate-forum-post-source-thread-site.md) establish forum post editing, source acquisition, retained parent state, and edit action-status boundaries as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 446 validates constructor-time `ForumPost.thread` input. Issues 354, 044, 124, 162, 185, 205, 210, 250, 263, and 269 validate edit inputs, edit-form fetch/parsing, save response validation, and cache invalidation. Issues 576 and 577 validate forum post source acquisition parent state, not edit action-time parent state. This slice covers a post-construction mutated `ForumPost.thread` at edit time.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.thread` at the start of `ForumPost.edit(...)` after public edit input validation.
- Use the validated thread for login checks, edit-form fetches, save requests, and thread post-cache invalidation.
- Add a regression for a mutated retained edit parent thread that previously reached mocked login/form-fetch handling.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost.edit(...)` must reject a mutated non-`ForumThread` `post.thread` with `ValueError("thread must be a ForumThread")` before login, form fetch, save request, or local mutation. |
| R2 | Malformed `source` and explicit malformed `title` values must retain precedence over retained-thread validation. |
| R3 | Valid edits, edit-form parsing, save action-status validation, local title/source updates, revision-cache invalidation, and thread post-cache invalidation must remain stable. |
| R4 | Source acquisition, post-list reads, forum thread behavior, forum category behavior, and forum post revision behavior must remain stable. |
| R5 | Focused RED/GREEN, edit tests, forum-post tests, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained edit parent thread fails before side-effect surfaces. | `TestForumPostEdit.test_edit_rejects_mutated_thread_before_login_or_form_fetch` failed RED with a malformed edit-form body diagnostic after reaching mocked login/form-fetch handling, then passed GREEN after `ForumPost.edit(...)` revalidated `self.thread`. | Calling `login_check`, calling `amc_request_with_retry`, calling `amc_request`, coercing malformed threads, updating local source/title, clearing caches, or deferring failure to edit-form diagnostics rejects this local completion claim. | `ForumPost.edit(...)` | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Public edit input validation remains first. | `test_edit_rejects_non_string_text_inputs_before_login_or_form_fetch` stayed green in edit coverage. | Checking malformed retained threads before malformed edit text inputs rejects this local completion claim. | Edit input validation | `tests/unit/test_forum_post.py` |
| R3 | Valid edit behavior remains unchanged. | `TestForumPostEdit` passed 17 tests after formatting. | Regressing revision-ID parsing, save action-status validation, title/source updates, revision-cache invalidation, or thread post-cache invalidation rejects this local completion claim. | Forum post edit workflow | `tests/unit/test_forum_post.py` |
| R4 | Adjacent workflows remain stable. | `tests/unit/test_forum_post.py` passed 155 tests, adjacent forum workflow tests passed 515 tests, and the full unit suite passed 2676 tests. | Regressing source reads, post-list reads, forum thread behavior, forum category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic mutated post state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `bf105c4 fix(forum_post): validate edit thread`.

- RED edit-thread validation: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_rejects_mutated_thread_before_login_or_form_fetch -q` failed before the fix with `NoElementException` for a malformed edit-form response body after the malformed parent reached mocked login/form-fetch handling.
- GREEN focused regression: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_rejects_mutated_thread_before_login_or_form_fetch -q` passed.
- Focused edit coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 17 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 155 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 515 tests.
- `uv run pytest tests/unit -q` passed 2676 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted after formatting the touched test file.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPost.edit(...)` rejects mutated malformed `post.thread` values with `ValueError("thread must be a ForumThread")` before login, edit-form fetch, save request, or local mutation.
- Malformed edit `source` and explicit `title` inputs retain earlier failure precedence.
- Valid edits, edit-form parsing, save action-status validation, title/source updates, revision-cache invalidation, and thread post-cache invalidation remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `ForumPost.thread` state reached mocked login/form-fetch handling and then raised an unrelated edit-form response-body diagnostic instead of the existing parent-thread diagnostic.
- This slice only validates retained forum-post edit parent-thread state before edit action work. It does not change thread construction, collection parent validation, source acquisition, post-list parsing, edit-form response parsing, revision-ID parsing, save action-status validation, live site behavior, or authentication semantics for valid threads.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
