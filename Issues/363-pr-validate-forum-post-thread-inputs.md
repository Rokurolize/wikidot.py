# PR Draft: Validate Forum Post Thread Inputs

## Summary

`ForumPostCollection.acquire_all_in_threads(threads)` and `ForumPostCollection.acquire_all_in_thread(thread)` document `ForumThread` object inputs, but malformed caller-provided thread objects were not rejected at the public API boundary. A string batch such as `"3001"` reached `.site` lookup and leaked `AttributeError("'str' object has no attribute 'site'")`, while invalid batch entries such as `None`, `True`, or `"3001"` reached cache inspection and leaked unstable `AttributeError` failures through `._posts`.

This change validates forum-post thread inputs before empty batch handling, site selection, cache scans, cached duplicate reuse, duplicate request handling, retry-aware AMC request construction, pagination, parser work, or cache assignment. Invalid batch containers now raise `ValueError("threads must be a list")`; invalid batch entries now raise `ValueError("threads list entries must be ForumThread")`; invalid single-thread inputs now raise `ValueError("thread must be a ForumThread")`. Empty valid batches still return `{}` without fetching, and valid post-list reads keep the existing retry, deduplication, cache reuse, pagination, malformed response diagnostics, parser diagnostics, source, edit, and reply behavior.

## Outcome

Forum-post read callers now get deterministic Python-side preflight validation for malformed thread-object inputs instead of accidental attribute failures from later cache, request, or parser stages.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum-post reads for moderation ledgers, translation review tooling, forum migration checks, thread archival jobs, local indexing, or generated workflows that pass thread objects from previous forum-thread lookups.

## Current Evidence

Local rollout evidence repeatedly treats thread post acquisition as a practical read surface. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), and [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md) establish forum-post list acquisition as an active practical workflow.

Those prior slices are not duplicates. They covered retry behavior, duplicate request handling, empty/cached post-list behavior, direct-thread cache population, parser context, malformed response body diagnostics, scoped content parsing, and malformed post field diagnostics. They did not validate caller-provided `threads` containers or `thread` objects before public post-list site selection, cache inspection, request construction, or batch delegation. This slice follows the recent input-boundary pattern from [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), and [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), but applies it to forum-post thread-object reads.

## Related Issue

Builds directly on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), and [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `acquire_all_in_threads(..., threads=...)` receives a `list` before empty-batch handling or site selection.
- Validate every `threads` entry is a `ForumThread` before cache scans, cached duplicate reuse, duplicate request handling, or retry-aware AMC request construction.
- Validate `acquire_all_in_thread(..., thread=...)` receives a `ForumThread` before delegating to the batch path.
- Preserve empty valid batch behavior, valid single-thread and multi-thread reads, duplicate/cached behavior, retry handling, pagination, malformed response body diagnostics, post-list parser diagnostics, direct-thread cache assignment, source, edit, and reply behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum-post read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.acquire_all_in_threads(threads=...)` must reject non-list batch inputs with `ValueError("threads must be a list")` before cache or request work. |
| R2 | `ForumPostCollection.acquire_all_in_threads(threads=[...])` must reject entries that are not `ForumThread` objects with `ValueError("threads list entries must be ForumThread")` before cache or request work. |
| R3 | `ForumPostCollection.acquire_all_in_thread(thread=...)` must reject non-`ForumThread` single inputs with `ValueError("thread must be a ForumThread")` before batch delegation or request work. |
| R4 | Valid empty batches and valid direct/batched post-list reads must remain unchanged. |
| R5 | Existing retry, duplicate request handling, cached duplicate reuse, pagination, malformed response body diagnostics, parser diagnostics, source, edit, and reply behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list post-thread batch inputs fail before cache or request work. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_rejects_non_list_threads_before_fetch` failed RED before the fix by leaking `AttributeError: 'str' object has no attribute 'site'`, then passed GREEN after validation was added. | Treating strings as thread batches, selecting `.site` from a non-thread object, scanning cache state, or calling AMC rejects this local completion claim. | Forum-post batch read preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Batch entries without `ForumThread` objects fail before cache or request work. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_threads_rejects_non_thread_entries_before_fetch` failed RED for `None`, `True`, and `"3001"` by reaching `._posts` cache inspection, then passed GREEN after entry validation was added. | Accepting non-thread entries, scanning invalid entry caches, deduplicating invalid entries, or surfacing `AttributeError` from later internals rejects this local completion claim. | Forum-post batch entry preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Single post-thread lookup inputs without `ForumThread` objects fail before batch delegation or request work. | `TestForumPostCollectionAcquireAll.test_acquire_all_in_thread_rejects_non_thread_before_fetch` failed RED for `None`, `True`, and `"3001"` by delegating malformed values into the batch path and leaking attribute failures, then passed GREEN after single-thread validation was added. | Returning the batch error wording for a single-thread API, calling AMC, or accepting an ID/string in place of a `ForumThread` object rejects this local completion claim. | Forum-post single read preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Valid empty and non-empty post-list reads remain unchanged. | `tests/unit/test_forum_post.py` passed 77 tests, the adjacent forum-post/forum-thread/forum-category/forum-post-revision set passed 223 tests, and the full unit suite passed 1004 tests. | Regressing `[] -> {}`, valid single-thread reads, valid multi-thread reads, direct-thread cache assignment, or site-linked post reads rejects this local completion claim. | Forum-post workflow | `tests/unit/test_forum_post.py`, adjacent forum tests |
| R5 | Existing forum-post diagnostics and helper behavior remain unchanged. | The adjacent 223-test forum set and full 1004-test unit suite covered retry, duplicate/cached behavior, pagination, response body diagnostics, parser diagnostics, source, edit, revision, and reply behavior. | Regressing retry behavior, duplicate request handling, cached duplicate reuse, pagination, malformed response body diagnostics, parser context, source fetches, edit form fetches, or reply behavior rejects this local completion claim. | Forum-post workflow | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post_revision.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic thread objects and malformed local values. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `89056c3 fix(forum_post): validate thread inputs`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_non_list_threads_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_non_thread_entries_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_thread_rejects_non_thread_before_fetch` failed before the fix with 7 failures; malformed values leaked `AttributeError` through `.site` or `._posts`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_non_list_threads_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_threads_rejects_non_thread_entries_before_fetch tests/unit/test_forum_post.py::TestForumPostCollectionAcquireAll::test_acquire_all_in_thread_rejects_non_thread_before_fetch` passed 7 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py` passed 77 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 223 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1004 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumPostCollection.acquire_all_in_threads("3001")` raises `ValueError("threads must be a list")` before cache inspection or AMC work.
- `ForumPostCollection.acquire_all_in_threads([valid_thread, None])`, `[valid_thread, True]`, and `[valid_thread, "3001"]` raise `ValueError("threads list entries must be ForumThread")` before cache inspection or AMC work.
- `ForumPostCollection.acquire_all_in_thread(None)`, `True`, or `"3001"` raises `ValueError("thread must be a ForumThread")` before batch delegation or AMC work.
- `ForumPostCollection.acquire_all_in_threads([])` still returns `{}` without AMC work.
- Valid single-thread and multi-thread post-list reads still submit `forum/sub/ForumViewThreadPostsModule` request bodies with integer thread IDs.
- Existing retry behavior, duplicate request handling, cached duplicate reuse, pagination, malformed response body diagnostics, parser diagnostics, direct-thread cache assignment, source, edit, and reply behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum-post list acquisition depends on real `ForumThread` objects because the implementation reads each thread's site, ID, and post cache before it builds requests. Generated workflows can accidentally pass thread IDs, serialized records, booleans, or missing values into this surface. Those malformed values should fail deterministically at the public API boundary, especially because the valid path contains cache reuse, deduplication, pagination, response parsing, and cache assignment. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established forum-post list retrieval as a practical workflow.
- The focused RED failures showed malformed public thread-object inputs crossing into site selection or cache inspection and leaking unstable attribute failures instead of failing at the public call boundary.
- Existing forum-post read drafts covered retry behavior, empty/cached valid batches, duplicate request handling, direct-thread cache population, fetch context, response body context, parser context, scoped content parsing, and malformed post field diagnostics, but not malformed public thread-object input preflight.
- This slice only validates forum-post thread-object inputs. It does not change forum-post list parsing, thread detail parsing, category thread list parsing, empty valid lookup behavior, retry semantics, source fetches, edit form fetches, reply action validation, site authentication, live Wikidot behavior, or forum dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects IDs, strings, booleans, and missing values instead of treating them as thread objects. Callers that receive forum-thread IDs from text sources should resolve them to `ForumThread` instances before requesting post lists.
