# PR Draft: Validate Forum Action Site Clients

## Summary

`ForumCategory.create_thread(...)`, `ForumThread.reply(...)`, and `ForumPost.edit(...)` now validate retained `site.client` state before authentication. Existing local slices validated forum write text inputs, retained forum parent objects, retained IDs, response statuses, cache invalidation, and adjacent page retained-client paths, but these forum write methods still authenticated through `site.client.login_check()` without checking that the retained client was still a `Client`.

This change adds narrow retained-client validators to the forum category, thread, and post modules. Valid create-thread, reply, and edit behavior, text/ID/site validation precedence, request payloads, response diagnostics, local cache mutation timing, and successful cache invalidation remain unchanged.

## Problem Statement

Forum write helpers should not authenticate, issue AMC requests, parse generated responses, or mutate local caches through corrupted parent-client state. Before this slice, a valid `Site` retained by a `ForumCategory`, `ForumThread`, or `ForumPost.thread` could have its public `client` field replaced after construction. The affected methods then called the malformed client's `login_check()` and continued toward later thread-ID, action-status, or edit-form diagnostics instead of reporting the established `ValueError("client must be a Client")`.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free forum mutations as practical maintenance surfaces. Directly related drafts include [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [578-pr-validate-forum-post-edit-thread.md](578-pr-validate-forum-post-edit-thread.md), [579-pr-validate-forum-post-edit-thread-site.md](579-pr-validate-forum-post-edit-thread-site.md), [683-pr-validate-forum-post-edit-retained-id-state.md](683-pr-validate-forum-post-edit-retained-id-state.md), [784-pr-validate-forum-post-edit-retained-title.md](784-pr-validate-forum-post-edit-retained-title.md), [796-pr-validate-create-thread-retained-category-id.md](796-pr-validate-create-thread-retained-category-id.md), [800-pr-validate-page-save-site-clients.md](800-pr-validate-page-save-site-clients.md), and [801-pr-validate-page-action-site-clients.md](801-pr-validate-page-action-site-clients.md).

This slice is not a duplicate of [701-pr-validate-site-constructor-client.md](701-pr-validate-site-constructor-client.md), which rejects malformed `Site(client=...)` constructor input. It cannot cover a valid `Site` whose public `client` field is replaced later.

This slice is not a duplicate of [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md), which validates retained `Site` request state at `Site.amc_request(...)` and `Site.amc_request_with_retry(...)`. These forum action methods authenticate through `site.client.login_check()` before reaching those request wrappers.

This slice is not a duplicate of [800-pr-validate-page-save-site-clients.md](800-pr-validate-page-save-site-clients.md) or [801-pr-validate-page-action-site-clients.md](801-pr-validate-page-action-site-clients.md). Those drafts cover page save/action entry points; this draft covers forum create-thread, reply, and post-edit entry points.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free forum thread creation through `ForumCategory.create_thread(...)`.
- Browser-free thread replies through `ForumThread.reply(...)`.
- Browser-free forum post edits through `ForumPost.edit(...)`.
- Generated discussion jobs, moderation scripts, migration tooling, serialized forum records, and local tests that may rehydrate or mutate retained `Site` state before write work.

## Proposed Fix

- Add module-local retained-site-client validators that lazily import `Client` and raise `ValueError("client must be a Client")`.
- Use the validators after existing text, retained-site, and retained-ID preflights and before `login_check()`.
- Authenticate through the validated client object.
- For `ForumCategory.create_thread(...)`, also reuse the validated retained `Site` for request work and created-thread lookup.
- Leave request construction, response parsing, local mutation, and cache invalidation behavior unchanged for valid `Site` and `Client` parents.

## Implementation Notes

Implemented locally in commit `99ebe2c fix(forum): validate action site clients`.

The implementation intentionally uses module-local helpers rather than importing the site-module helper directly, matching the existing local validation style and avoiding tighter import coupling. Each helper preserves the existing public diagnostic used by site/client validators: `ValueError("client must be a Client")`.

The focused RED failures demonstrated the shared boundary gap:

- `ForumCategory.create_thread(...)` reached create-thread response handling and failed with a missing-thread-ID diagnostic after the malformed client had authenticated.
- `ForumThread.reply(...)` reached action-status parsing and failed with a malformed `status` diagnostic.
- `ForumPost.edit(...)` reached edit-form response-body parsing and failed with a malformed `body` diagnostic.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `ForumCategory.create_thread(...)` rejects mutated retained `category.site.client` before login, `newThread` request work, created-thread lookup, or thread-cache mutation. | `TestForumCategoryCreateThread.test_create_thread_rejects_mutated_site_client_before_login` failed RED, then passed GREEN after retained-client validation was added. | Calling malformed `login_check()`, calling `site.amc_request(...)`, clearing `_threads`, or leaking returned-thread diagnostics rejects this claim. |
| `ForumThread.reply(...)` rejects mutated retained `thread.site.client` before login, `savePost` request work, counter updates, or cache invalidation. | `TestForumThreadReply.test_reply_rejects_mutated_site_client_before_login` failed RED, then passed GREEN. | Calling malformed `login_check()`, calling `site.amc_request(...)`, changing `post_count`, clearing `_posts`, changing category `posts_count`, or clearing category `_threads` rejects this claim. |
| `ForumPost.edit(...)` rejects mutated retained `post.thread.site.client` before login, edit-form fetch, save work, or local cache mutation. | `TestForumPostEdit.test_edit_rejects_mutated_site_client_before_login_or_form_fetch` failed RED, then passed GREEN. | Calling malformed `login_check()`, fetching the edit form, saving the edit, changing `_source`, clearing `_revisions`, or clearing `thread._posts` rejects this claim. |
| Existing validation precedence and valid forum write behavior remain stable. | Focused action classes passed 89 tests; full touched forum modules passed 692 tests; full unit passed 3888 tests. | Moving retained-client validation before malformed text/ID/site diagnostics or regressing valid forum writes rejects this claim. |
| Repository quality gates remain green. | Ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `99ebe2c fix(forum): validate action site clients`.

- RED: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread::test_create_thread_rejects_mutated_site_client_before_login tests/unit/test_forum_thread.py::TestForumThreadReply::test_reply_rejects_mutated_site_client_before_login tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_rejects_mutated_site_client_before_login_or_form_fetch -q --tb=short` failed 3 tests before the fix with later create-thread, reply, and edit-form diagnostics instead of `ValueError("client must be a Client")`.
- GREEN focused: the same focused command passed 3 tests after retained-client validation was added.
- Affected forum action coverage: `uv run pytest tests/unit/test_forum_category.py::TestForumCategoryCreateThread tests/unit/test_forum_thread.py::TestForumThreadReply tests/unit/test_forum_post.py::TestForumPostEdit -q --tb=short` passed 89 tests.
- Full touched forum modules: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py -q --tb=short` passed 692 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3888 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumCategory.create_thread(...)` with a valid retained `Site` whose `client` has been replaced by a non-`Client` object raises `ValueError("client must be a Client")` before login, AMC requests, returned-thread diagnostics, created-thread lookup, or `_threads` invalidation.
- `ForumThread.reply(...)` with a mutated non-`Client` retained `thread.site.client` raises `ValueError("client must be a Client")` before login, AMC requests, action-status parsing, `post_count` updates, `_posts` invalidation, category `posts_count` updates, or category `_threads` invalidation.
- `ForumPost.edit(...)` with a mutated non-`Client` retained `post.thread.site.client` raises `ValueError("client must be a Client")` before login, edit-form fetch, save request work, edit-form diagnostics, source/title mutation, revision-cache invalidation, or thread post-cache invalidation.
- Existing text input validation, retained-site validation, retained-ID validation, edit-form parsing, action-status parsing, successful local mutation, and cache invalidation behavior remain unchanged for valid `Client` parents.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: Earlier client validation could change precedence for calls that pass both malformed retained client state and malformed explicit action inputs. Mitigation: client validation is placed after existing explicit text, retained-site, and retained-ID validators.
- Risk: This could be confused with page retained-client validation. Mitigation: Issues 800 and 801 cover page save/action boundaries; this draft covers forum write entry points.
- Risk: Adding module-local helpers duplicates a small client check. Mitigation: the duplication is narrow, keeps imports local, preserves the established diagnostic, and avoids introducing cross-module coupling for a simple retained-state guard.
- Risk: Valid `ForumCategory.create_thread(...)` diagnostics could accidentally use a stale site reference. Mitigation: the method now reuses the validated `site` object consistently for request work, thread-ID diagnostics, and created-thread lookup.

## Dependencies

- Existing `Client` class identity remains the parent-client contract.
- Existing forum write text validators define public input validation precedence.
- Existing retained `ForumCategory.id`, `ForumThread.id`, `ForumPost.id`, `ForumThread.site`, and `ForumPost.thread` validators define retained object and identity precedence.
- Existing forum response validators continue to define malformed remote response diagnostics after valid authentication and request work.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, result ergonomics, cache ownership checks, cross-owner batch checks, or complexity candidates outside this now-covered forum action retained-client boundary.

## Rationale for Upstream Suitability

The change makes documented forum write helpers fail locally and deterministically when their retained parent client is corrupted, using the same client diagnostic already enforced by constructor, AMC request-state, page save, and page action validators. It prevents authentication and write-side work from starting with malformed parent-client state while preserving valid browser-free thread creation, replies, post edits, response handling, local mutation, and cache invalidation.

## Local Evidence

- Local browser-free maintenance drafts repeatedly use forum thread creation, thread replies, and forum post edits to manage discussions without browser automation.
- Existing local drafts covered forum write text validation, retained parent site/thread validation, retained post/thread/category IDs, forum action response diagnostics, edit-form diagnostics, cache invalidation ordering, and page retained-client validation. They did not cover post-construction retained `Site.client` mutation before forum write authentication.
- This slice only validates retained client state for forum write entry points. It does not change live Wikidot behavior, forum list/detail parsers, edit-form selectors, save response parsing, action response parsing, request payload shapes, cache invalidation timing, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw forum content, private post text, private site data, and private forum metadata out of upstream discussion.

## Additional Notes

Callers that mutate or rehydrate forum records should keep `category.site.client`, `thread.site.client`, and `post.thread.site.client` as real `Client` instances before invoking forum write APIs.
