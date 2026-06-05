# PR Draft: Validate ForumPostCollection Search IDs

## Summary

`ForumPostCollection.find(id)` documents `id` as an integer, but malformed caller-provided search keys were not rejected at the public collection lookup boundary. Values such as `None` and strings were treated as ordinary misses, while floats could compare equal to stored integer post IDs and booleans remain a Python `int` subclass.

This change validates the search key before scanning stored forum posts. Malformed `id` values now raise `ValueError("id must be an integer")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for non-boolean integer post IDs.

## Outcome

Forum post collection callers now get deterministic Python-side preflight validation for malformed post search IDs instead of misleading misses, accidental float equality matches, or boolean/int comparison surprises.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum post reads for moderation ledgers, translation review tooling, forum migration checks, archival jobs, local indexing, generated workflows, or source-preserving forum transformations.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post-list and forum post source reads as practical read surfaces. Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), and [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md) cover post-list acquisition, source acquisition, retry behavior, duplicate response reuse, parser diagnostics, response diagnostics, write text preflight, caller-provided thread inputs, and stored collection-entry validation. Adjacent search preflight drafts [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), and [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md) cover nearby collection lookup IDs and revision search keys.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, or validate stored forum post records and acquisition inputs, but they do not validate the caller-provided search key to `ForumPostCollection.find(...)` before scanning stored posts.

## Related Issue

Builds directly on the forum post acquisition/source hardening line from [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), and the adjacent `find(...)` preflight pattern from [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `ForumPostCollection.find(id=...)` accepts only non-boolean integer IDs before scanning stored posts.
- Preserve valid `collection.find(5001)` behavior when a matching post exists.
- Preserve valid unknown integer behavior: a well-formed absent ID still returns `None`.
- Preserve forum post-list acquisition, source acquisition, parser diagnostics, cached post collections, lazy `ForumThread.posts`, and lazy `ForumPost.source` semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum post lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.find(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")` before scanning posts. |
| R2 | Valid lookup must remain unchanged for well-formed non-boolean integer IDs that match stored posts. |
| R3 | Valid not-found behavior must remain unchanged for well-formed non-boolean integer IDs that are absent from the collection. |
| R4 | Existing forum post-list acquisition, source acquisition, parser diagnostics, cached collection reuse, lazy `ForumThread.posts`, lazy `ForumPost.source`, forum thread reads, forum category reads, and forum post revision reads must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed post IDs fail before collection iteration can compare them with stored post IDs. | `TestForumPostCollectionInit.test_find_rejects_non_integer_ids` failed RED before the fix for `None`, `True`, `"5001"`, and `5001.0`, then passed GREEN after validation was added. | Treating malformed IDs as ordinary misses, coercing values, scanning posts, or matching floats/booleans as integer IDs rejects this local completion claim. | Forum post ID search preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Matching non-boolean integer search keys still return the stored `ForumPost`. | Existing `test_find_existing` passed after validation was added. | Changing returned post identity, rejecting valid integer IDs, or comparing unrelated fields rejects this local completion claim. | Forum post collection lookup | `tests/unit/test_forum_post.py` |
| R3 | Missing non-boolean integer search keys still return `None`. | Existing `test_find_nonexistent` passed after validation was added. | Raising for a valid but absent integer ID or changing not-found behavior rejects this local completion claim. | Forum post collection lookup | `tests/unit/test_forum_post.py` |
| R4 | Adjacent forum behavior remains green. | `tests/unit/test_forum_post.py` passed 84 tests, adjacent forum tests passed 252 tests, and full unit tests passed 1086 tests. | Regressing post-list acquisition, source acquisition, cached post collections, source cache assignment, parser diagnostics, forum thread reads, category reads, or forum post revision behavior rejects this local completion claim. | Forum post workflow | affected forum-post, forum-thread, forum-category, and forum-post-revision tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum source, private forum content, private comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-post tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7844351 fix(forum_post): validate post search ids`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_find_rejects_non_integer_ids` failed 4 parameterized cases before the fix: malformed IDs did not raise, and comparison was reached for every malformed value.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_find_rejects_non_integer_ids` passed 4 tests after adding ID search preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py` passed 84 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 252 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1086 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `.venv/bin/ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("5001")`, and `collection.find(5001.0)` raise `ValueError("id must be an integer")`.
- A well-formed integer ID matching an existing post still returns that post.
- A well-formed integer ID that is absent from the collection still returns `None`.
- Existing forum post-list acquisition, source acquisition, parser diagnostics, cached post collections, lazy `ForumThread.posts`, lazy `ForumPost.source`, forum thread reads, forum category reads, and forum post revision reads remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` tightens behavior for values that could previously compare equal to integer search keys. Mitigation: `bool` is not a meaningful forum post ID, and accepting it can hide caller payload bugs.
- Risk: Rejecting float or string search keys can expose upstream caller bugs. Mitigation: the documented API type is an integer; callers loading IDs from JSON, CLI flags, spreadsheets, or generated ledgers should normalize to non-boolean integers before calling `find(...)`.
- Risk: Diagnostics could expose private forum context. Mitigation: the new error message contains only the input-field name and expected type, not post text, source text, rendered content, site names, or account details.

## Dependencies

- Existing `ForumPostCollection` storage and iteration semantics remain authoritative for valid integer search keys.
- Existing post-list acquisition and source acquisition code remains unchanged.
- Existing forum post parser diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/forum_post.py` and does not affect forum thread acquisition, forum category acquisition, forum post revision behavior, page behavior, site search, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered forum post search-ID validation path.

## Upstream-Safe Motivation

Forum post lookup is often fed by generated forum inventories, moderation ledgers, translation tooling, migration scripts, archival indexes, or cached thread snapshots. Since `find(...)` compares supplied values against stored post IDs, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses or accidentally matching float values to integer post IDs.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post data as a practical workflow through post-list acquisition, source acquisition, retry behavior, duplicate fetch reduction, parser diagnostics, response-body diagnostics, parsed-field diagnostics, cache reuse, and lazy source reads.
- Existing forum-post drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, caller-provided thread inputs, stored collection-entry validation, write text inputs, and parsed post fields; they did not validate caller-provided search keys to `ForumPostCollection.find(id=...)`.
- This slice only validates `ForumPostCollection` search-ID inputs. It does not change post-list acquisition, forum post parser field extraction, cached post collections, source acquisition, lazy `ForumThread.posts`, lazy `ForumPost.source`, forum thread behavior, category behavior, forum post revision behavior, page behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum post source, raw rendered forum content, comments from private forums, source text from real sites, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search IDs instead of coercing them. Callers that load forum post search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into non-boolean integers before calling `ForumPostCollection.find(...)`.
