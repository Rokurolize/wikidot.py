# PR Draft: Validate Forum Thread ID Inputs

## Summary

`ForumThreadCollection.acquire_from_thread_ids(site, thread_ids)`, `ForumThread.get_from_id(site, thread_id)`, and the `Site.get_threads(...)` / `Site.get_thread(...)` convenience wrappers document thread IDs as integers, but malformed caller-provided ID inputs were not rejected at the public API boundary. A string batch could be treated as an iterable sequence of character IDs, while entries such as `None`, `True`, `"3001"`, or `3001.5` could reach retry-aware AMC request construction and then leak unstable low-level failures such as `ValueError("zip() argument 2 is longer than argument 1")`.

This change validates forum-thread direct lookup IDs before empty/non-empty request handling, duplicate-ID deduplication, AMC request construction, retry handling, response remapping, or detail parsing. Invalid batch values now raise `ValueError("thread_ids must be a list")` or `ValueError("thread_ids list entries must be integers")`; invalid single-thread values now raise `ValueError("thread_id must be an integer")`. Empty valid batches remain a no-fetch no-op, and valid non-empty reads keep the existing retry, deduplication, duplicate output ordering, malformed response diagnostics, parser diagnostics, and site accessor behavior.

## Outcome

Forum-thread read callers now get deterministic Python-side preflight validation for malformed thread ID inputs instead of accidental per-character requests, bool-as-int IDs, malformed AMC payloads, retry work on invalid IDs, or low-level response mapping failures.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum-thread reads for moderation ledgers, translation review tooling, forum migration checks, thread audit scripts, or local jobs that pass thread IDs from generated records, CLI flags, JSON, spreadsheets, or previous crawl output.

## Current Evidence

Local rollout evidence repeatedly treats forum-thread detail retrieval as a practical read surface. Existing drafts [035-pr-retry-forum-thread-fetches.md](035-pr-retry-forum-thread-fetches.md), [060-pr-deduplicate-forum-thread-detail-fetches.md](060-pr-deduplicate-forum-thread-detail-fetches.md), [076-pr-skip-empty-forum-thread-fetch-batches.md](076-pr-skip-empty-forum-thread-fetch-batches.md), [159-pr-forum-thread-detail-fetch-context.md](159-pr-forum-thread-detail-fetch-context.md), [170-pr-forum-thread-detail-parse-context.md](170-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-statistics-context.md](214-pr-forum-thread-statistics-context.md), [238-pr-forum-thread-detail-response-body-context.md](238-pr-forum-thread-detail-response-body-context.md), [293-pr-forum-thread-breadcrumb-title-spacing.md](293-pr-forum-thread-breadcrumb-title-spacing.md), [294-pr-forum-thread-description-spacing.md](294-pr-forum-thread-description-spacing.md), [311-pr-forum-thread-description-pager-scope.md](311-pr-forum-thread-description-pager-scope.md), and [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md) establish direct forum-thread detail reads and site accessors as active practical workflows.

Those prior slices are not duplicates. They covered retry behavior, direct-detail deduplication, empty valid batch no-op behavior, fetch context, parser context, malformed response body diagnostics, scoped parsing, and formatted text preservation. They did not validate caller-provided `thread_ids` or `thread_id` inputs before public direct lookup request construction or retry-aware response mapping. This slice follows the recent input-boundary pattern from [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md) and [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), but applies it to forum-thread read IDs.

## Related Issue

Builds directly on [035-pr-retry-forum-thread-fetches.md](035-pr-retry-forum-thread-fetches.md), [060-pr-deduplicate-forum-thread-detail-fetches.md](060-pr-deduplicate-forum-thread-detail-fetches.md), and [076-pr-skip-empty-forum-thread-fetch-batches.md](076-pr-skip-empty-forum-thread-fetch-batches.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `thread_ids` is a `list` before checking its length or building any AMC requests.
- Validate every `thread_ids` entry is a non-boolean integer before duplicate-ID deduplication or retry-aware AMC request construction.
- Validate `ForumThread.get_from_id(..., thread_id=...)` receives a non-boolean integer before delegating to the batch path.
- Preserve `Site.get_threads(...)` and `Site.get_thread(...)` through the same public validation path.
- Preserve valid empty batch behavior, valid non-empty direct reads, first-seen duplicate-ID request deduplication, duplicate output ordering, retry handling, malformed response body diagnostics, detail parser diagnostics, post/reply behavior, and successful site accessors.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum-thread read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection.acquire_from_thread_ids(..., thread_ids=...)` must reject non-list batch inputs with `ValueError("thread_ids must be a list")` before AMC requests. |
| R2 | `ForumThreadCollection.acquire_from_thread_ids(..., thread_ids=[...])` must reject non-integer and boolean entries with `ValueError("thread_ids list entries must be integers")` before AMC requests. |
| R3 | `ForumThread.get_from_id(..., thread_id=...)` must reject non-integer and boolean single IDs with `ValueError("thread_id must be an integer")` before AMC requests. |
| R4 | `Site.get_threads(...)` and `Site.get_thread(...)` must reach the same validation path for malformed inputs. |
| R5 | Valid empty batches, valid non-empty direct reads, duplicate-ID deduplication, duplicate output ordering, retry behavior, malformed response body diagnostics, detail parser diagnostics, and post/reply behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, adjacent forum-thread/site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list batch ID inputs fail before AMC request work. | `TestForumThreadCollectionAcquireFromIds.test_site_get_threads_rejects_non_list_thread_ids_before_fetch` failed RED before the fix by letting malformed values reach `site.amc_request_with_retry(...)` and then leaking `zip() argument 2 is longer than argument 1`, then passed GREEN after validation was added. | Calling `site.amc_request(...)`, calling `site.amc_request_with_retry(...)`, accepting strings as ID batches, or splitting a string into per-character thread IDs rejects this local completion claim. | Direct forum-thread batch read preflight | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Batch entries without real integer IDs fail before AMC request work. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_rejects_non_integer_thread_id_entries_before_fetch` failed RED for `None`, `True`, `"3001"`, and `3001.5` by reaching the retry-aware detail path and leaking `zip(strict=True)` length errors, then passed GREEN after entry validation was added. | Treating `bool` as an integer ID, submitting non-integer `threadId` values, deduplicating invalid entries, or surfacing `zip(strict=True)` mapping failures rejects this local completion claim. | Direct forum-thread batch entry preflight | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Single-thread lookup inputs without real integer IDs fail before AMC request work. | `TestForumThreadBasic.test_get_from_id_rejects_non_integer_thread_id_before_fetch` failed RED by delegating malformed IDs into the batch detail path and leaking response mapping errors, then passed GREEN after single-ID validation was added. | Returning the batch error wording for a single-ID API, calling AMC, or accepting `True` as thread ID `1` rejects this local completion claim. | Direct forum-thread single read preflight | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R4 | Site forum-thread accessors expose the same validation behavior. | `TestForumThreadCollectionAcquireFromIds.test_site_get_threads_rejects_non_list_thread_ids_before_fetch` and `TestForumThreadBasic.test_site_get_thread_rejects_non_integer_thread_id_before_fetch` pass through the real `Site` convenience methods and assert AMC calls are not made. | Mock-only accessor coverage, bypassing `ForumThreadCollection.acquire_from_thread_ids(...)` or `ForumThread.get_from_id(...)`, or letting malformed accessor inputs reach AMC rejects this local completion claim. | Site forum-thread accessor | `src/wikidot/module/site.py`, `tests/unit/test_forum_thread.py` |
| R5 | Valid forum-thread reads and existing diagnostics remain unchanged. | Adjacent forum-thread/site tests passed 172 tests; the full unit suite passed 997 tests. | Regressing empty valid batch no-op behavior, valid non-empty reads, request deduplication, duplicate output ordering, retry behavior, malformed response body diagnostics, parser context, post acquisition, reply behavior, or site accessor delegation rejects this local completion claim. | Forum-thread workflow | `tests/unit/test_forum_thread.py`, `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic thread IDs and no real forum content. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `34b34ad fix(forum_thread): validate thread id inputs`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_site_get_threads_rejects_non_list_thread_ids_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_integer_thread_id_entries_before_fetch tests/unit/test_forum_thread.py::TestForumThreadBasic::test_get_from_id_rejects_non_integer_thread_id_before_fetch tests/unit/test_forum_thread.py::TestForumThreadBasic::test_site_get_thread_rejects_non_integer_thread_id_before_fetch` failed before the fix with 9 failures; malformed batch and single-ID paths reached `site.amc_request_with_retry(...)` and leaked `ValueError: zip() argument 2 is longer than argument 1`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_site_get_threads_rejects_non_list_thread_ids_before_fetch tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_integer_thread_id_entries_before_fetch tests/unit/test_forum_thread.py::TestForumThreadBasic::test_get_from_id_rejects_non_integer_thread_id_before_fetch tests/unit/test_forum_thread.py::TestForumThreadBasic::test_site_get_thread_rejects_non_integer_thread_id_before_fetch` passed 9 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py tests/unit/test_site.py` passed 172 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 997 tests.
- `ruff check .` passed.
- `ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `Site.get_threads("3001")` raises `ValueError("thread_ids must be a list")` before `site.amc_request(...)` or `site.amc_request_with_retry(...)`.
- `ForumThreadCollection.acquire_from_thread_ids(site, [None])`, `[True]`, `["3001"]`, and `[3001.5]` raise `ValueError("thread_ids list entries must be integers")` before AMC work.
- `ForumThread.get_from_id(site, None)`, `True`, or `"3001"` raises `ValueError("thread_id must be an integer")` before AMC work.
- `Site.get_threads(...)` and `Site.get_thread(...)` reach the same validation path for malformed inputs.
- `ForumThreadCollection.acquire_from_thread_ids(site, [])` still returns an empty collection without AMC work.
- Valid non-empty direct reads still submit `forum/sub/ForumViewThreadModule` request bodies with integer `threadId` values.
- Existing duplicate-ID request deduplication, duplicate output ordering, retry behavior, malformed response body diagnostics, detail parser diagnostics, post acquisition, reply behavior, category-linked reads, and site accessor delegation remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Direct forum-thread lookup IDs often come from previous crawler output, CLI input, JSON, or generated ledgers. These inputs should fail deterministically at the public API boundary when malformed, especially because the direct lookup path builds retry-aware detail requests and maps responses back to requested IDs. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established forum-thread retrieval and site forum-thread accessors as practical workflows.
- The focused RED failures showed malformed direct ID inputs crossing into retry-aware detail request flow and leaking unstable `zip(strict=True)` mapping failures instead of failing at the public call boundary.
- Existing forum-thread read drafts covered retry behavior, empty valid batches, duplicate ID deduplication, fetch context, response body context, scoped parsing, and detail parser diagnostics, but not malformed public ID input preflight.
- This slice only validates forum-thread direct lookup ID inputs. It does not change forum-thread detail parsing, category thread list parsing, empty valid lookup behavior, retry semantics, reply action validation, site authentication, live Wikidot behavior, post acquisition, or forum dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing strings, floats, or booleans into IDs. Callers that receive forum-thread IDs from text sources should parse and validate them as integers before calling wikidot.py direct forum-thread lookup helpers.
