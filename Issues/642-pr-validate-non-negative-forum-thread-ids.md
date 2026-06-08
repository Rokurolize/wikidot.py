# PR Draft: Validate Non-Negative ForumThread IDs

## Summary

`ForumThread.id`, `ForumThread.get_from_id(...)`, `ForumThreadCollection.acquire_from_thread_ids(...)`, and `Site.get_thread(...)` / `Site.get_threads(...)` identify concrete forum threads used by browser-free forum indexing, direct thread-detail reads, cached category scans, duplicate direct-thread reuse, lazy post-list reads, reply workflows, migration ledgers, moderation tooling, translation review tooling, local fixtures, and rehydrated records. Existing local drafts validate thread IDs as non-boolean integers, but direct constructors and direct lookup helpers still accepted negative integers such as `-1`. Negative lookup IDs could even reach retry-aware request construction and fail later with response-mapping errors.

This change validates direct `ForumThread.id`, single-thread lookup IDs, and batch thread lookup IDs as non-negative integers at the shared validation boundary. It deliberately preserves `id=0` and lookup `thread_id=0` because prior identity-field drafts avoid stronger positive-ID requirements unless parser or live evidence proves one.

## Outcome

Directly constructed forum-thread records and direct forum-thread lookup calls can no longer store or submit negative thread IDs, while zero-ID compatibility, malformed direct type diagnostics, generated parser IDs, direct thread-detail reads, duplicate lookup deduplication, lazy `ForumThread.posts`, reply behavior, collection lookup, and adjacent forum workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, `ForumThread.posts`, forum replies, local fixtures, or serialized/rehydrated thread records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-thread reads and stored thread records as practical workflow surfaces. [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md) validates malformed generated direct-detail thread IDs with context. [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md) validates direct lookup input types. [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md) validates loaded-collection lookup ID types. [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md) validates direct `ForumThread.id` type. [635-pr-validate-non-negative-forum-thread-post-counts.md](635-pr-validate-non-negative-forum-thread-post-counts.md) validates thread post-count range semantics, not thread ID range semantics.

This slice is not a duplicate of Issues 311, 362, 379, 455, or 635. Issue 311 handles parser-created IDs. Issue 362 rejects non-lists, booleans, strings, floats, and other malformed direct lookup IDs, but still accepts negative integer IDs. Issue 379 validates search-key shape after a collection already exists. Issue 455 rejects malformed direct constructor IDs, but still accepts negative integers. Issue 635 validates post-count range, not identity range.

## Related Issue / Non-Duplicate Analysis

Builds directly on [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), and [635-pr-validate-non-negative-forum-thread-post-counts.md](635-pr-validate-non-negative-forum-thread-post-counts.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `ForumThread(id=-1)` and `ForumThread(id=-100)` with `ValueError("thread_id must be non-negative")`.
- Reject direct `ForumThread.get_from_id(site, -1)` and `Site.get_thread(-1)` with `ValueError("thread_id must be non-negative")` before AMC work.
- Reject direct `ForumThreadCollection.acquire_from_thread_ids(site, [-1])` with `ValueError("thread_ids list entries must be non-negative")` before AMC work.
- Preserve direct `ForumThread(id=0)` and direct lookup `thread_id=0` as non-negative identity values.
- Preserve existing malformed-ID diagnostics for non-integers and booleans.
- Leave generated thread-list/detail parsing, collection `find(...)` lookup semantics, duplicate direct lookup deduplication, lazy post access, reply behavior, and adjacent forum workflows unchanged.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Public direct-read input-boundary hardening
- Forum-thread identity state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `ForumThread(id=-1)` and `ForumThread(id=-100)` must raise `ValueError("thread_id must be non-negative")` when every other thread field is valid. |
| R2 | Direct `ForumThread.get_from_id(site, -1)` and `Site.get_thread(-1)` must raise `ValueError("thread_id must be non-negative")` before AMC work. |
| R3 | Direct `ForumThreadCollection.acquire_from_thread_ids(site, [-1])` and `[-100]` must raise `ValueError("thread_ids list entries must be non-negative")` before AMC work. |
| R4 | Direct `ForumThread(id=0)` and direct lookup `thread_id=0` must remain valid and store/request `0`. |
| R5 | Existing malformed direct ID and lookup diagnostics must remain stable. |
| R6 | Generated thread-list/detail parsing, direct acquisition, duplicate lookup deduplication, lazy `ForumThread.posts`, reply behavior, collection lookup, and adjacent forum workflows must remain unchanged. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct forum-thread records cannot store negative thread IDs. | `TestForumThreadBasic.test_init_rejects_negative_thread_id` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after `_validate_thread_id(...)` rejected values below zero. | Accepting negative thread IDs, coercing them to zero, or deferring failure to parser or lookup code rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Single direct thread lookup rejects negative IDs before request work. | `TestForumThreadBasic.test_get_from_id_rejects_negative_thread_id_before_fetch` and `test_site_get_thread_rejects_negative_thread_id_before_fetch` failed RED because negative IDs reached retry-aware mapping and raised `zip() argument 2 is longer than argument 1`, then passed GREEN after single-ID range validation. | Calling `site.amc_request(...)`, calling `site.amc_request_with_retry(...)`, submitting negative `threadId` payloads, or surfacing response-mapping errors rejects this local completion claim. | Direct single thread lookup | `src/wikidot/module/forum_thread.py`, `src/wikidot/module/site.py`, `tests/unit/test_forum_thread.py` |
| R3 | Batch direct thread lookup rejects negative IDs before request work. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_rejects_negative_thread_id_entries_before_fetch` failed RED for `[-1]` and `[-100]` by reaching the retry-aware detail path and leaking `zip()` mapping errors, then passed GREEN after batch-ID range validation. | Submitting negative `threadId` payloads, deduplicating invalid negative IDs, or surfacing low-level mapping failures rejects this local completion claim. | Direct batch thread lookup | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R4 | Zero remains valid for direct thread IDs. | `TestForumThreadBasic.test_init_accepts_zero_thread_id` and `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_accepts_zero_thread_id` passed in RED and GREEN runs. | Requiring positive-only thread IDs without separate evidence rejects this local completion claim. | Constructor and direct lookup compatibility | `tests/unit/test_forum_thread.py` |
| R5 | Existing malformed direct type diagnostics remain stable. | Existing malformed constructor, batch lookup, and single lookup ID tests passed in the same focused RED and GREEN commands. | Changing `ValueError("thread_id must be an integer")`, `ValueError("thread_ids list entries must be integers")`, or `ValueError("thread_ids must be a list")`, accepting booleans, or coercing strings/floats rejects this local completion claim. | ForumThread ID type validation | `tests/unit/test_forum_thread.py` |
| R6 | Existing forum-thread and adjacent forum workflows remain green. | Forum-thread coverage passed 164 tests, adjacent forum coverage passed 575 tests, and the full unit suite passed 2906 tests. | Regressing parser diagnostics, category thread-list parsing, direct thread-detail parsing, duplicate direct lookup deduplication, lazy post acquisition, reply behavior, collection lookup, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum-thread and adjacent workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum titles, post bodies from real sites, response bodies, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-thread tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3595716 fix(forum_thread): validate non-negative thread ids`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_integer_thread_id_entries_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_negative_thread_id_entries_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_accepts_zero_thread_id tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_thread_id tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_negative_thread_id tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_accepts_zero_thread_id tests/unit/test_forum_thread.py::TestForumThreadBasic::test_get_from_id_rejects_non_integer_thread_id_before_fetch tests/unit/test_forum_thread.py::TestForumThreadBasic::test_get_from_id_rejects_negative_thread_id_before_fetch tests/unit/test_forum_thread.py::TestForumThreadBasic::test_site_get_thread_rejects_non_integer_thread_id_before_fetch tests/unit/test_forum_thread.py::TestForumThreadBasic::test_site_get_thread_rejects_negative_thread_id_before_fetch -q` failed 7 negative constructor and lookup ID cases before the fix; 14 malformed-input and zero-compatibility guards stayed green.
- GREEN: the same focused command passed 21 tests after direct thread-ID and thread-ID list range validation was added.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` reformatted 1 file and left 1 file unchanged.
- Re-running the same focused command after formatting passed 21 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 164 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 575 tests.
- `uv run pytest tests/unit -q` passed 2906 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(id=-1)` and `ForumThread(id=-100)` raise `ValueError("thread_id must be non-negative")`.
- `ForumThread.get_from_id(site, -1)` and `Site.get_thread(-1)` raise `ValueError("thread_id must be non-negative")` before AMC work.
- `ForumThreadCollection.acquire_from_thread_ids(site, [-1])` and `[-100]` raise `ValueError("thread_ids list entries must be non-negative")` before AMC work.
- `ForumThread(id=0)` remains accepted and stores `0`.
- `ForumThreadCollection.acquire_from_thread_ids(site, [0])` remains accepted and submits a `{"t": 0, "moduleName": "forum/ForumViewThreadModule"}` request when the caller deliberately asks for thread ID zero.
- `ForumThread(id=None)`, `True`, `"3001"`, and `3001.0` continue to raise `ValueError("thread_id must be an integer")`.
- `ForumThreadCollection.acquire_from_thread_ids(site, [None])`, `[True]`, `["3001"]`, and `[3001.5]` continue to raise `ValueError("thread_ids list entries must be integers")`.
- Generated thread-list/detail parsing, direct acquisition, duplicate direct lookup deduplication, collection lookup, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and adjacent forum category/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum thread IDs are identity metadata for browser-free forum inventories, duplicate direct-thread reuse, generated migration ledgers, moderation summaries, cached category scans, lazy post-list reads, replies, and downstream forum post/revision traversal. Negative IDs can look like valid integer state in direct fixtures or generated lookup queues but are not useful thread identifiers in the current public API surface. Non-negative validation catches that impossible state early while avoiding a stronger positive-only rule.

## Local Evidence

- Local rollout evidence used direct forum-thread reads, site thread accessors, duplicate direct-thread reuse, lazy `ForumThread.posts`, reply workflows, generated moderation ledgers, translation review tooling, and records that construct or consume `ForumThread` objects directly.
- Existing local drafts covered generated malformed thread IDs, direct lookup type validation, loaded-collection lookup IDs, direct thread ID types, and non-negative thread post counts, but did not cover negative direct thread IDs or lookup IDs.
- The focused RED failures showed negative direct constructor IDs were accepted and negative direct lookup IDs advanced into retry-aware request mapping. The GREEN regressions cover invalid values, zero compatibility, and existing malformed type validation.
- This slice only validates non-negative direct thread-ID semantics. It does not change generated parser IDs, collection `find(...)` lookup semantics, category thread-list selectors, direct-detail selectors, title parsing, description parsing, created metadata parsing, post-count parsing, source/post acquisition, reply behavior, live site behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, forum source text, forum titles from private sites, post bodies from private sites, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates non-negative direct thread IDs only. It does not require positive IDs, coerce numeric strings, or change `ForumThreadCollection.find(...)` lookup semantics because prior local search-key drafts preserved absent integer lookup behavior while generated parser IDs already have their own diagnostics.
