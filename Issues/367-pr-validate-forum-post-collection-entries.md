# PR Draft: Validate Forum Post Collection Entries

## Summary

`ForumPostCollection.get_post_sources()` documents collection entries as `ForumPost` objects, but malformed collection entries were not rejected before source acquisition. A malformed entry such as `None`, `True`, or `"5001"` reached cached-source inspection and leaked an unstable `AttributeError` on `_source` before request construction.

This change validates forum post collection entries before cached source checks, cached duplicate source reuse, duplicate request grouping, retry-aware AMC request construction, response-body validation, edit-form/source textarea parsing, source cache assignment, or lazy post source completion. Invalid entries now raise `ValueError("posts list entries must be ForumPost")`. Empty valid collections, valid source reads, retry behavior, duplicate request deduplication, cached duplicate source reuse, response-body diagnostics, edit-form textarea scoping, lazy `ForumPost.source` behavior, post edit preflight, and reply behavior remain unchanged.

## Outcome

Forum post source callers now get deterministic Python-side preflight validation for malformed collection entries instead of accidental attribute failures from later cache or acquisition stages.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum post source reads for moderation ledgers, translation review tooling, edit-history audits, forum migration checks, archival jobs, local indexing, generated workflows, or source-preserving forum transformations.

## Current Evidence

Local rollout-backed drafts repeatedly treat forum post source acquisition as a practical read surface. Existing drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), and [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md) establish forum post source retrieval as an active practical workflow.

Those prior slices are not duplicates. They covered retry behavior, source request deduplication, edit-form control scoping, cached duplicate source reuse, lazy failure visibility, lazy failure context, missing source textarea context, missing response body diagnostics, and malformed response body type diagnostics. [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md) validated caller-provided thread inputs before post-list acquisition, but it did not validate malformed `ForumPostCollection` entries before public `get_post_sources()` cache inspection, duplicate grouping, request construction, or response parsing. This slice follows the recent collection-entry boundary pattern from [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md) and [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), but applies it to forum post source entries.

## Related Issue

Builds directly on [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), and [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate every `ForumPostCollection.get_post_sources()` entry is a `ForumPost` before cached source checks or request construction.
- Preserve empty valid collection behavior, valid source reads, retry behavior, duplicate request deduplication, cached duplicate source reuse, missing response body diagnostics, malformed response body type diagnostics, edit-form textarea scoping, lazy `ForumPost.source` behavior, post edit preflight, and reply behavior.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum post source read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection.get_post_sources()` must reject entries that are not `ForumPost` objects with `ValueError("posts list entries must be ForumPost")` before cache or request work. |
| R2 | Valid empty collections and valid source reads must remain unchanged. |
| R3 | Existing retry behavior, duplicate request handling, cached duplicate source reuse, response diagnostics, edit-form textarea scoping, lazy source behavior, post edit preflight, and reply behavior must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, affected forum-post tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Source acquisition collection entries without `ForumPost` objects fail before cache or request work. | `TestForumPostCollectionGetSources.test_get_post_sources_rejects_non_post_entries_before_fetch` failed RED for `None`, `True`, and `"5001"` by leaking `AttributeError` through cached-source inspection, then passed GREEN after validation was added. | Accepting missing values, booleans, or strings as posts, inspecting invalid entry caches, grouping invalid post IDs, calling AMC, or surfacing `AttributeError` rejects this local completion claim. | Forum post source preflight | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Valid empty collections and valid source reads remain unchanged. | `tests/unit/test_forum_post.py` passed 80 tests, the adjacent forum-post/forum-thread/forum-category/forum-post-revision set passed 236 tests, and the full unit suite passed 1023 tests. | Regressing `ForumPostCollection(thread, [])`, valid source acquisition, or source cache assignment rejects this local completion claim. | Forum post source workflow | `tests/unit/test_forum_post.py`, adjacent forum tests |
| R3 | Existing forum post source behavior remains unchanged. | The adjacent 236-test forum set and full 1023-test unit suite covered retry behavior, duplicate request handling, cached duplicate source reuse, missing response body diagnostics, malformed response body type diagnostics, edit-form textarea scoping, lazy source behavior, post edit preflight, and reply behavior. | Regressing retry behavior, duplicate request handling, cached duplicate reuse, response diagnostics, parser scoping, lazy source failures, edit preflight, replies, post-list parsing, source, edit, or reply behavior rejects this local completion claim. | Forum post workflow | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post_revision.py` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic forum post objects plus malformed local values. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, forum post text, source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7c06574 fix(forum_post): validate collection entries`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_non_post_entries_before_fetch` failed before the fix with 3 failures; malformed collection entries leaked `AttributeError` through cached-source inspection.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_rejects_non_post_entries_before_fetch` passed 3 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py` passed 80 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 236 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1023 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumPostCollection(thread=thread, posts=[valid_post, None]).get_post_sources()`, `[valid_post, True]`, and `[valid_post, "5001"]` raise `ValueError("posts list entries must be ForumPost")` before cache inspection or AMC work.
- `ForumPostCollection(thread=thread, posts=[])` remains a valid empty collection.
- Valid source acquisition still submits `forum/sub/ForumEditPostFormModule` request bodies with integer post IDs.
- Existing retry behavior, duplicate request handling, cached duplicate source reuse, missing response body diagnostics, malformed response body type diagnostics, edit-form textarea scoping, lazy source behavior, post edit preflight, and reply behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum post source acquisition depends on real `ForumPost` objects because the implementation reads source cache state, post IDs, and thread/site context before it builds edit-form module requests. Generated workflows can accidentally pass post IDs, serialized records, booleans, or missing values into this surface. Those malformed values should fail deterministically at the public API boundary, especially because the valid path contains cache reuse, deduplication, retry-aware request construction, response parsing, and cache assignment. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established forum post source retrieval as a practical workflow.
- The focused RED failures showed malformed public collection entries crossing into source cache checks and leaking unstable attribute failures instead of failing at the public call boundary.
- Existing forum-post source drafts covered retry behavior, duplicate request handling, cached duplicate source reuse, edit-form control scoping, lazy failure context, missing response body diagnostics, response body type diagnostics, and source textarea context, but not malformed public collection entry preflight.
- This slice only validates forum post collection entries for source acquisition. It does not change forum post-list parsing, source parsing, post editing, replies, retry semantics, response diagnostics, site authentication, live Wikidot behavior, or forum post dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, forum post text, source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects IDs, strings, booleans, and missing values instead of treating them as post objects. Callers that receive post IDs from text sources should resolve them to `ForumPost` instances before requesting source text.
