# PR Draft: Validate Forum Post Revision Post Inputs

## Summary

`ForumPostRevisionCollection.acquire_all(post)` and `ForumPostRevisionCollection.acquire_all_for_posts(posts, with_html=False)` document `ForumPost` object inputs, but malformed caller-provided post objects were not rejected at the public API boundary. A single malformed post such as `None`, `True`, or `"5001"` reached `._revisions` lookup and leaked `AttributeError`, while a non-list batch such as `"5001"` reached `.thread` lookup and invalid batch entries reached cache inspection before leaking unstable attribute failures.

This change validates forum-post-revision post inputs before empty batch handling, site selection, cache scans, cached duplicate reuse, duplicate request handling, retry-aware revision-list request construction, optional revision-HTML request construction, parser work, or cache assignment. Invalid single-post inputs now raise `ValueError("post must be a ForumPost")`; invalid batch containers now raise `ValueError("posts must be a list")`; invalid batch entries now raise `ValueError("posts list entries must be ForumPost")`. Empty valid batches still return `{}` without fetching, and valid revision-list reads keep the existing retry, deduplication, cache reuse, optional HTML acquisition, malformed response diagnostics, parser diagnostics, lazy HTML, source, edit, and reply behavior.

## Outcome

Forum-post-revision read callers now get deterministic Python-side preflight validation for malformed post-object inputs instead of accidental attribute failures from later cache, request, or parser stages.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum post revision history for moderation ledgers, translation review tooling, edit-history audits, forum migration checks, archival jobs, local indexing, or generated workflows that pass post objects from previous thread-post reads.

## Current Evidence

Local rollout evidence repeatedly treats forum post revision history as a practical read surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), and [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md) establish revision-list and revision-HTML acquisition as active practical workflows.

Those prior slices are not duplicates. They covered retry behavior, duplicate request handling, cached revision-list behavior, cached duplicate reuse, optional revision-HTML deduplication, lazy HTML failure visibility, response body diagnostics, missing HTML content diagnostics, direct helper cache population, parser context, and malformed revision field diagnostics. They did not validate caller-provided `post` or `posts` objects before public revision-list cache inspection, site selection, request construction, optional HTML fetching, or batch delegation. This slice follows the recent input-boundary pattern from [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), and [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), but applies it to forum-post-revision post-object reads.

## Related Issue

Builds directly on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), and [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `acquire_all(..., post=...)` receives a `ForumPost` before cache inspection or request construction.
- Validate `acquire_all_for_posts(..., posts=...)` receives a `list` before empty-batch handling or site selection.
- Validate every `posts` entry is a `ForumPost` before cache scans, cached duplicate reuse, duplicate request handling, revision-list request construction, or optional revision-HTML request construction.
- Preserve empty valid batch behavior, valid direct and batched revision-list reads, cached direct helper behavior, duplicate/cached behavior, optional `with_html=True` behavior, retry handling, malformed response body diagnostics, missing HTML content diagnostics, revision parser diagnostics, lazy HTML behavior, source, edit, and reply behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum-post-revision read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.acquire_all(post=...)` must reject non-`ForumPost` single inputs with `ValueError("post must be a ForumPost")` before cache or request work. |
| R2 | `ForumPostRevisionCollection.acquire_all_for_posts(posts=...)` must reject non-list batch inputs with `ValueError("posts must be a list")` before empty handling, site selection, cache work, or request work. |
| R3 | `ForumPostRevisionCollection.acquire_all_for_posts(posts=[...])` must reject entries that are not `ForumPost` objects with `ValueError("posts list entries must be ForumPost")` before cache or request work. |
| R4 | Valid empty batches and valid direct/batched revision-list reads must remain unchanged. |
| R5 | Existing retry, duplicate request handling, cached duplicate reuse, direct cache population, optional revision-HTML acquisition, malformed response diagnostics, parser diagnostics, lazy HTML, source, edit, and reply behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, affected forum-post-revision tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Single revision-list inputs without `ForumPost` objects fail before cache or request work. | `TestForumPostRevisionCollectionAcquireAll.test_acquire_all_rejects_non_post_before_fetch` failed RED for `None`, `True`, and `"5001"` by leaking `AttributeError` through `._revisions`, then passed GREEN after single-post validation was added. | Accepting IDs, strings, booleans, or missing values as post objects, scanning invalid caches, calling AMC, or surfacing `AttributeError` rejects this local completion claim. | Forum-post-revision single read preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Non-list post batches fail before empty handling, site selection, cache scans, or request work. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_rejects_non_list_posts_before_fetch` failed RED before the fix by leaking `AttributeError: 'str' object has no attribute 'thread'`, then passed GREEN after validation was added. | Treating strings as post batches, selecting `.thread` from a non-post object, scanning cache state, or calling AMC rejects this local completion claim. | Forum-post-revision batch read preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Batch entries without `ForumPost` objects fail before cache or request work. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_rejects_non_post_entries_before_fetch` failed RED for `None`, `True`, and `"5001"` by reaching `._revisions` cache inspection, then passed GREEN after entry validation was added. | Accepting non-post entries, scanning invalid entry caches, deduplicating invalid entries, issuing revision-list or revision-HTML requests, or surfacing `AttributeError` rejects this local completion claim. | Forum-post-revision batch entry preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | Valid empty and non-empty revision-list reads remain unchanged. | `tests/unit/test_forum_post_revision.py` passed 57 tests, the adjacent forum-post/forum-thread/forum-category/forum-post-revision set passed 230 tests, and the full unit suite passed 1011 tests. | Regressing `[] -> {}`, valid direct reads, valid batched reads, direct helper cache assignment, cached read reuse, duplicate post-ID behavior, or site-linked post reads rejects this local completion claim. | Forum-post-revision workflow | `tests/unit/test_forum_post_revision.py`, adjacent forum tests |
| R5 | Existing forum-post-revision diagnostics and helper behavior remain unchanged. | The adjacent 230-test forum set and full 1011-test unit suite covered retry, duplicate/cached behavior, optional revision HTML, response body diagnostics, missing HTML content diagnostics, parser diagnostics, lazy HTML, source, edit, and reply behavior. | Regressing retry behavior, duplicate request handling, cached duplicate reuse, optional `with_html=True`, malformed response body diagnostics, missing HTML content diagnostics, parser context, lazy HTML failures, source fetches, edit form fetches, or reply behavior rejects this local completion claim. | Forum-post-revision workflow | `tests/unit/test_forum_post_revision.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic post objects and malformed local values. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, page source text from real sites, forum post text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f2592a1 fix(forum_post_revision): validate post inputs`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_non_post_before_fetch` failed before the fix with 3 failures; malformed single-post values leaked `AttributeError` through `._revisions`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_non_post_before_fetch` passed 3 tests after single-post validation.
- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_non_list_posts_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_non_post_entries_before_fetch` failed before the batch fix with 4 failures; malformed batch values leaked `AttributeError` through `.thread` or `._revisions`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_non_post_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_non_list_posts_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_non_post_entries_before_fetch` passed 7 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py` passed 57 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 230 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1011 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all(None)`, `True`, or `"5001"` raises `ValueError("post must be a ForumPost")` before cache inspection or AMC work.
- `ForumPostRevisionCollection.acquire_all_for_posts("5001")` raises `ValueError("posts must be a list")` before empty handling, site selection, cache inspection, or AMC work.
- `ForumPostRevisionCollection.acquire_all_for_posts([valid_post, None])`, `[valid_post, True]`, and `[valid_post, "5001"]` raise `ValueError("posts list entries must be ForumPost")` before cache inspection or AMC work.
- `ForumPostRevisionCollection.acquire_all_for_posts([])` still returns `{}` without AMC work.
- Valid direct and batched revision-list reads still submit `forum/sub/ForumPostRevisionsModule` request bodies with integer post IDs.
- Valid `with_html=True` revision reads still submit `forum/sub/ForumPostRevisionModule` request bodies with integer revision IDs only after valid revision-list acquisition.
- Existing retry behavior, duplicate request handling, cached duplicate reuse, direct helper cache assignment, malformed response body diagnostics, missing HTML content diagnostics, parser diagnostics, lazy HTML behavior, source, edit, and reply behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum post revision-list acquisition depends on real `ForumPost` objects because the implementation reads each post's thread, site, ID, and revision cache before it builds revision-list and optional revision-HTML requests. Generated workflows can accidentally pass post IDs, serialized records, booleans, or missing values into this surface. Those malformed values should fail deterministically at the public API boundary, especially because the valid path contains cache reuse, deduplication, optional HTML fetching, response parsing, and cache assignment. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established forum post revision-list and revision-HTML retrieval as practical workflows.
- The focused RED failures showed malformed public post-object inputs crossing into cache inspection or site selection and leaking unstable attribute failures instead of failing at the public call boundary.
- Existing forum-post-revision drafts covered retry behavior, empty/cached valid batches, duplicate request handling, direct-helper cache population, optional revision-HTML deduplication, lazy failure context, response body context, parser context, and malformed revision field diagnostics, but not malformed public post-object input preflight.
- This slice only validates forum-post-revision post-object inputs. It does not change forum-post-revision list parsing, optional HTML parsing, thread post-list parsing, empty valid lookup behavior, retry semantics, source fetches, edit form fetches, reply action validation, site authentication, live Wikidot behavior, or forum dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, page source text from real sites, forum post text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects IDs, strings, booleans, and missing values instead of treating them as post objects. Callers that receive forum-post IDs from text sources should resolve them to `ForumPost` instances before requesting revision lists.
