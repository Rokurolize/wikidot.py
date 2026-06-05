# PR Draft: Validate ForumThreadCollection Search IDs

## Summary

`ForumThreadCollection.find(id)` documents `id` as an integer, but malformed caller-provided search keys were not rejected at the public collection lookup boundary. Values such as `None` and strings were treated as ordinary misses, while floats could compare equal to stored integer thread IDs and booleans remain a Python `int` subclass.

This change validates the search key before scanning stored forum threads. Malformed `id` values now raise `ValueError("id must be an integer")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for non-boolean integer thread IDs.

## Outcome

Forum thread collection callers now get deterministic Python-side preflight validation for malformed thread search IDs instead of misleading misses, accidental float equality matches, or boolean/int comparison surprises.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum thread reads for moderation ledgers, translation review tooling, forum migration checks, archival jobs, local indexing, generated workflows, cached category scans, or source-preserving forum transformations.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum thread-list and forum thread-detail reads as practical read surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), and [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md) cover thread-list acquisition, direct thread-detail acquisition, retries, duplicate response reduction, cache reuse, parser diagnostics, response diagnostics, parsed-field diagnostics, and acquisition ID validation. Adjacent search preflight drafts [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md) and [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md) cover nearby forum collection lookup keys.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, or validate acquisition IDs for forum thread workflows, but they do not validate the caller-provided search key to an already loaded `ForumThreadCollection.find(...)` before scanning stored threads.

## Related Issue

Builds directly on the forum thread acquisition/detail hardening line from [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), and the adjacent `find(...)` preflight pattern from [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `ForumThreadCollection.find(id=...)` accepts only non-boolean integer IDs before scanning stored threads.
- Preserve valid `collection.find(3001)` behavior when a matching thread exists.
- Preserve valid unknown integer behavior: a well-formed absent ID still returns `None`.
- Preserve category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, cached category thread collections, lazy `ForumCategory.threads`, and lazy `ForumThread.posts` semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum thread lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection.find(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")` before scanning threads. |
| R2 | Valid lookup must remain unchanged for well-formed non-boolean integer IDs that match stored threads. |
| R3 | Valid not-found behavior must remain unchanged for well-formed non-boolean integer IDs that are absent from the collection. |
| R4 | Existing category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, cached collection reuse, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, forum post reads, forum category reads, and forum post revision reads must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed thread IDs fail before collection iteration can compare them with stored thread IDs. | `TestForumThreadCollectionInit.test_find_rejects_non_integer_ids` failed RED before the fix for `None`, `True`, `"3001"`, and `3001.0`, then passed GREEN after validation was added. | Treating malformed IDs as ordinary misses, coercing values, scanning threads, or matching floats/booleans as integer IDs rejects this local completion claim. | Forum thread ID search preflight | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Matching non-boolean integer search keys still return the stored `ForumThread`. | Existing `test_find_existing` passed after validation was added. | Changing returned thread identity, rejecting valid integer IDs, or comparing unrelated fields rejects this local completion claim. | Forum thread collection lookup | `tests/unit/test_forum_thread.py` |
| R3 | Missing non-boolean integer search keys still return `None`. | Existing `test_find_nonexistent` passed after validation was added. | Raising for a valid but absent integer ID or changing not-found behavior rejects this local completion claim. | Forum thread collection lookup | `tests/unit/test_forum_thread.py` |
| R4 | Adjacent forum behavior remains green. | `tests/unit/test_forum_thread.py` passed 76 tests, adjacent forum tests passed 256 tests, and full unit tests passed 1090 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, cached thread collections, parser diagnostics, forum post reads, category reads, or forum post revision behavior rejects this local completion claim. | Forum thread workflow | affected forum-thread, forum-post, forum-category, and forum-post-revision tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum source, private forum content, private comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-thread tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1425ecd fix(forum_thread): validate thread search ids`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_find_rejects_non_integer_ids` failed 4 parameterized cases before the fix: malformed IDs did not raise, and comparison was reachable for every malformed value.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_find_rejects_non_integer_ids` passed 4 tests after adding ID search preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_thread.py` passed 76 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 256 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1090 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `.venv/bin/ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("3001")`, and `collection.find(3001.0)` raise `ValueError("id must be an integer")`.
- A well-formed integer ID matching an existing thread still returns that thread.
- A well-formed integer ID that is absent from the collection still returns `None`.
- Existing category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, cached category thread collections, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, forum post reads, forum category reads, and forum post revision reads remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` tightens behavior for values that could previously compare equal to integer search keys. Mitigation: `bool` is not a meaningful forum thread ID, and accepting it can hide caller payload bugs.
- Risk: Rejecting float or string search keys can expose upstream caller bugs. Mitigation: the documented API type is an integer; callers loading IDs from JSON, CLI flags, spreadsheets, or generated ledgers should normalize to non-boolean integers before calling `find(...)`.
- Risk: Diagnostics could expose private forum context. Mitigation: the new error message contains only the input-field name and expected type, not thread titles, descriptions, post text, rendered content, site names, or account details.

## Dependencies

- Existing `ForumThreadCollection` storage and iteration semantics remain authoritative for valid integer search keys.
- Existing category thread-list acquisition and direct thread-detail acquisition code remains unchanged.
- Existing forum thread parser diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/forum_thread.py` and does not affect category acquisition, forum post acquisition, forum post source reads, forum post revision behavior, page behavior, site search, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered forum thread search-ID validation path.

## Upstream-Safe Motivation

Forum thread lookup is often fed by generated forum inventories, moderation ledgers, translation tooling, migration scripts, archival indexes, or cached category scans. Since `find(...)` compares supplied values against stored thread IDs, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses or accidentally matching float values to integer thread IDs.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum thread data as a practical workflow through category thread-list acquisition, direct thread-detail acquisition, retry behavior, duplicate fetch reduction, parser diagnostics, response-body diagnostics, parsed-field diagnostics, cache reuse, and lazy post reads.
- Existing forum-thread drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, caller-provided acquisition IDs, stored thread fields, and lazy post reads; they did not validate caller-provided search keys to `ForumThreadCollection.find(id=...)`.
- This slice only validates `ForumThreadCollection` search-ID inputs. It does not change category thread-list acquisition, direct thread-detail acquisition, parser field extraction, cached category thread collections, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, forum post behavior, category behavior, forum post revision behavior, page behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum post source, raw rendered forum content, comments from private forums, source text from real sites, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search IDs instead of coercing them. Callers that load forum thread search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into non-boolean integers before calling `ForumThreadCollection.find(...)`.
