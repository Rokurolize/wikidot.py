# PR Draft: Validate ForumThread Direct Lookup Site Argument

## Summary

`ForumThreadCollection.acquire_from_thread_ids(site, thread_ids)`, also exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, is the browser-free direct forum-thread detail read boundary. Earlier local slices validated retry-aware direct thread fetches, duplicate thread-ID handling, empty valid batches, thread-ID inputs, response-body diagnostics, parser diagnostics, collection state, direct `ForumThread.site`, and adjacent forum thread record fields. One adjacent public read-input gap remained: direct non-empty calls such as `ForumThreadCollection.acquire_from_thread_ids(None, [3001])`, `"test-site"`, dictionaries, booleans, or arbitrary objects reached `site.amc_request_with_retry(...)` and leaked raw `AttributeError`.

This change reuses the existing `_validate_forum_thread_site(...)` helper at the `ForumThreadCollection.acquire_from_thread_ids(...)` entry point after existing `thread_ids` validation and before empty/non-empty request handling. Malformed direct `site` arguments now raise `ValueError("site must be a Site")` deterministically, while invalid thread-ID precedence, empty valid batches, valid direct thread acquisition, duplicate-ID handling, response-body diagnostics, parser diagnostics, returned thread parent state, and adjacent forum workflows remain unchanged.

## Outcome

Direct forum-thread detail callers now get the same deterministic parent-site preflight used by stored forum-thread records and explicit thread-collection parents, instead of incidental attribute errors from malformed call inputs.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who call `ForumThreadCollection.acquire_from_thread_ids(site, thread_ids)` directly, use `Site.get_thread(...)` / `Site.get_threads(...)`, or build generated discussion inventories where a malformed deserialized or fixture-provided parent site should fail before AMC request construction.

## Current Evidence

Local rollout-backed drafts repeatedly identify direct forum-thread detail reads as practical workflow surfaces. Existing drafts [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), and [539-pr-preserve-empty-forum-thread-parent.md](539-pr-preserve-empty-forum-thread-parent.md) establish direct thread acquisition, parser diagnostics, response diagnostics, ID preflight, direct record state, cache state, collection state, and empty parent behavior as active operational boundaries.

This is not a duplicate of Issue 503. Issue 503 validates direct `ForumThread(site=...)` construction after thread records already exist or are manually rehydrated. This slice validates the caller-provided `site` argument to the static `ForumThreadCollection.acquire_from_thread_ids(site, thread_ids)` read helper before request work.

No upstream issue was filed from this local workspace.

## Changes

- Add a focused regression for malformed direct `ForumThreadCollection.acquire_from_thread_ids(site=...)` inputs.
- Validate the `site` argument with `_validate_forum_thread_site(...)` after existing thread-ID validation and before request work.
- Preserve invalid thread-ID precedence, empty valid batches, valid direct thread request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, duplicate-ID output ordering, returned thread parent state, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public read-boundary hardening
- Direct forum-thread detail preflight
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection.acquire_from_thread_ids(None, [3001])`, `True`, `"test-site"`, `{"unix_name": "test-site"}`, and `object()` must raise `ValueError("site must be a Site")` before direct thread request work. |
| R2 | Existing malformed `thread_ids` values must still raise their existing thread-ID validation errors before validating or using the site argument. |
| R3 | Valid direct thread acquisition, empty valid batches, duplicate-ID handling, request payloads, retry-exhausted diagnostics, response-body diagnostics, parser diagnostics, and returned `ForumThread.site` parent state must remain unchanged. |
| R4 | Forum thread, adjacent forum, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct thread-detail `site` inputs fail at the public read boundary. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_rejects_malformed_site_before_fetch` failed RED for all 5 malformed values with raw `AttributeError`, then passed GREEN after validation was added. | Reaching `site.amc_request_with_retry`, accepting site-like dictionaries, returning an empty collection, or leaking raw attribute errors rejects this local completion claim. | `ForumThreadCollection.acquire_from_thread_ids(...)` | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Existing thread-ID preflight remains first. | Focused GREEN included `test_acquire_from_ids_rejects_non_integer_thread_id_entries_before_fetch`. | Requiring a valid site before rejecting malformed thread IDs or changing thread-ID error messages rejects this local completion claim. | Direct thread ID validation | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Valid direct thread behavior remains stable. | Focused GREEN included `test_site_get_threads_empty_input_skips_fetch` and `test_acquire_from_ids_success`; the full forum-thread file passed 138 tests. | Changing empty valid batch handling, request module names, retry behavior, duplicate output ordering, parser output, response diagnostics, or returned thread parent state rejects this local completion claim. | Direct forum-thread reads | `tests/unit/test_forum_thread.py` |
| R4 | Existing repository quality gates remain green. | Adjacent forum tests passed 504 tests, full unit tests passed 2573 tests, full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state; this draft contains no credentials, cookies, auth JSON, raw response bodies, private forum content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `c89c2b8 fix(forum_thread): validate direct thread site`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_malformed_site_before_fetch -q` failed 5 tests before the fix because malformed sites reached `site.amc_request_with_retry(...)` and leaked raw `AttributeError`.
- GREEN focused: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_malformed_site_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_integer_thread_id_entries_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_site_get_threads_empty_input_skips_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success -q` passed 11 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 138 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 504 tests.
- `uv run pytest tests/unit -q` passed 2573 tests.
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

- Malformed direct `ForumThreadCollection.acquire_from_thread_ids(site=...)` inputs raise `ValueError("site must be a Site")`.
- Malformed `thread_ids` still raise the existing thread-ID validation errors first.
- Valid direct thread reads, empty valid batches, duplicate-ID handling, request payloads, response diagnostics, parser diagnostics, and returned thread parent state stay unchanged.
- Adjacent forum category/thread/post/revision workflows stay green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: The new validation could change malformed thread-ID precedence. Mitigation: validation remains after `_validate_thread_ids(...)`, and focused GREEN includes malformed thread-ID entries.
- Risk: Empty valid batches could accidentally start rejecting malformed sites differently from the existing constructor path. Mitigation: empty valid batches still return an empty `ForumThreadCollection` with a valid site and no request work; malformed site values now fail through the same site validator before collection construction.

## Dependencies

- Existing `_validate_forum_thread_site(...)` remains the canonical local parent-site validator.
- Existing `Site` constructor validation remains responsible for site scalar fields such as `id`, `title`, `unix_name`, `domain`, and `ssl_supported`.

## Open Questions

None for this local slice.

## Upstream-Safe Motivation

`ForumThreadCollection.acquire_from_thread_ids(...)` is the direct read entry point behind browser-free forum thread detail discovery. Validating the supplied parent `Site` before request work gives generated callers and fixtures deterministic errors for malformed inputs without changing live Wikidot behavior, thread-ID semantics, request shape, retries, parsing, diagnostics, duplicate handling, or downstream forum traversal.

## Local Evidence, Not For Upstream Paste

- The focused RED failures showed malformed direct `site` arguments crossing the public static read boundary and leaking `AttributeError` from `site.amc_request_with_retry`.
- This slice only validates the `ForumThreadCollection.acquire_from_thread_ids(...)` caller-provided parent type. It does not change direct thread-detail acquisition, parser selectors, response-body diagnostics, thread ID/title/description/count/user/timestamp parsing, duplicate-ID ordering, collection initialization, direct thread field validation, lazy `ForumCategory.threads`, `ForumThread.posts`, `ForumThread.reply(...)`, forum category/post/revision behavior, live site behavior, or client authentication.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum HTML, forum source text, private messages, and private site data out of upstream discussion.
