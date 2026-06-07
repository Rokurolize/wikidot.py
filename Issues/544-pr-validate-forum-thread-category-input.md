# PR Draft: Validate ForumThread Category Thread-List Input

## Summary

`ForumThreadCollection.acquire_all_in_category(category)`, also exposed through `ForumCategory.threads` and `ForumCategory.reload_threads()`, is the browser-free category thread-list read boundary. Earlier local slices validated retry-aware category thread-list fetching, cache reuse, response-body diagnostics, parser diagnostics, collection state, direct `ForumThread.category` record state, direct `ForumCategory.site` state, and direct thread-detail site arguments. One adjacent public read-input gap remained: direct calls such as `ForumThreadCollection.acquire_all_in_category(None)`, booleans, strings, dictionaries, or arbitrary objects reached `category._threads` and leaked raw `AttributeError`.

This change adds a required `ForumCategory` validator at the `ForumThreadCollection.acquire_all_in_category(...)` entry point before cache or request work. Malformed direct `category` arguments now raise `ValueError("category must be a ForumCategory")` deterministically, while cached category-thread reuse, valid single-page acquisition, reload behavior, pagination, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, returned thread parent state, and adjacent forum workflows remain unchanged.

## Outcome

Direct category thread-list callers now get deterministic input validation before cache or request work instead of incidental attribute errors from malformed category-like values.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `ForumThreadCollection.acquire_all_in_category(category)` directly, use `ForumCategory.threads` / `reload_threads()`, or build generated forum inventories where a malformed deserialized or fixture-provided category should fail before thread-list request construction.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread-list reads as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [323-pr-forum-thread-list-response-body-type-context.md](323-pr-forum-thread-list-response-body-type-context.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md), [539-pr-preserve-empty-forum-thread-parent.md](539-pr-preserve-empty-forum-thread-parent.md), and [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md) establish category thread-list acquisition, cache behavior, parser diagnostics, response diagnostics, direct record state, collection state, and direct thread-detail preflight as active operational boundaries.

This is not a duplicate of Issue 447. Issue 447 validates the optional `ForumThread(category=...)` field after a thread record already exists or is manually rehydrated. This slice validates the caller-provided `category` argument to the static `ForumThreadCollection.acquire_all_in_category(category)` read helper before cache or request work.

This is not a duplicate of Issue 505. Issue 505 validates the cached `ForumCategory._threads` constructor state. This slice validates that the object passed to the acquisition helper is a real `ForumCategory` before the helper can read `_threads`, `site`, or `id`.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed direct `ForumThreadCollection.acquire_all_in_category(category=...)` inputs.
- Add a required `_validate_forum_category(...)` helper and call it before cache or request work.
- Preserve cached category-thread reuse, valid single-page acquisition, reload behavior, pagination, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, returned thread parent state, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public read-boundary hardening
- Category thread-list preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection.acquire_all_in_category(None)`, `True`, `"1001"`, `{"id": 1001}`, and `object()` must raise `ValueError("category must be a ForumCategory")` before cache or request work. |
| R2 | Cached valid category thread collections must still be returned without request work. |
| R3 | Valid category thread-list acquisition, reload behavior, request payloads, response-body diagnostics, parser diagnostics, and returned `ForumThread.category` parent state must remain unchanged. |
| R4 | Forum thread, adjacent forum, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct category thread-list inputs fail at the public read boundary. | `TestForumThreadCollectionAcquireAll.test_acquire_all_rejects_malformed_category_before_fetch` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `category._threads`, accepting category-like dictionaries, building requests, or leaking raw attribute errors rejects this local completion claim. | `ForumThreadCollection.acquire_all_in_category(...)` | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Cached valid category thread collections remain a no-request path. | Focused GREEN included `test_acquire_all_skips_cached_category_threads`. | Re-fetching cached categories or changing cache identity rejects this local completion claim. | Category thread cache reuse | `tests/unit/test_forum_thread.py` |
| R3 | Valid category thread-list behavior remains stable. | Focused GREEN included `test_acquire_all_single_page` and `test_reload_threads_bypasses_cached_category_threads`; the full forum-thread file passed 143 tests. | Changing request module names, retry behavior, pagination, parser output, response diagnostics, returned thread parent state, or reload cache replacement rejects this local completion claim. | Category thread-list reads | `tests/unit/test_forum_thread.py` |
| R4 | Existing repository quality gates remain green. | Adjacent forum tests passed 509 tests, full unit tests passed 2578 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private forum content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `7f9f6fa fix(forum_thread): validate category thread input`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_malformed_category_before_fetch -q` failed 5 tests before the fix because malformed categories reached `category._threads` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_malformed_category_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_skips_cached_category_threads tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_reload_threads_bypasses_cached_category_threads -q` passed 8 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 143 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 509 tests.
- `uv run pytest tests/unit -q` passed 2578 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy .` passed with no issues in 87 source files.
- `uv run pyright .` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- Malformed direct `ForumThreadCollection.acquire_all_in_category(category=...)` inputs raise `ValueError("category must be a ForumCategory")`.
- Cached valid category thread collections remain a no-request path.
- Valid category thread-list reads, reload behavior, request payloads, response diagnostics, parser diagnostics, and returned thread parent state stay unchanged.
- Adjacent forum category/thread/post/revision workflows stay green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: The new validation could disturb cached category thread reuse. Mitigation: validation accepts real `ForumCategory` objects and focused GREEN includes the cached no-request path.
- Risk: The required-category diagnostic could be confused with optional `ForumThread.category` validation. Mitigation: the new helper uses `ValueError("category must be a ForumCategory")` for the required acquisition input, while existing optional record-state validation keeps `ValueError("category must be a ForumCategory or None")`.

## Dependencies

- Existing `ForumCategory` remains the canonical parent type for category thread-list reads.
- Existing `ForumCategory` constructor and field validators remain responsible for category ID, site, title, description, count, and cached thread state.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`ForumThreadCollection.acquire_all_in_category(...)` is the read entry point behind browser-free forum category inventories. Validating the supplied category object before cache or request work gives generated callers and fixtures deterministic errors for malformed inputs without changing live Wikidot behavior, request shape, retries, parsing, diagnostics, cache reuse, reload behavior, or downstream forum traversal.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `category` arguments crossing the public static read boundary and leaking `AttributeError` from `category._threads`.
- This slice only validates the `ForumThreadCollection.acquire_all_in_category(...)` caller-provided parent type. It does not change category thread-list acquisition, parser selectors, response-body diagnostics, thread ID/title/description/count/user/timestamp parsing, cache reuse, reload behavior, direct thread-detail acquisition, direct thread field validation, lazy `ForumCategory.threads`, `ForumThread.posts`, `ForumThread.reply(...)`, forum category/post/revision behavior, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, private messages, and private site data out of upstream discussion.
