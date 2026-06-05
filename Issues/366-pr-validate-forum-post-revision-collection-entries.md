# PR Draft: Validate Forum Post Revision Collection Entries

## Summary

`ForumPostRevisionCollection.get_htmls()` documents collection entries as `ForumPostRevision` objects, but malformed collection entries were not rejected at the public HTML acquisition boundary. A malformed entry such as `None`, `True`, or `"9001"` reached the cached-HTML map and leaked an unstable `AttributeError` on `_html` before request construction.

This change validates forum-post-revision collection entries before cached HTML checks, cached duplicate reuse, duplicate request grouping, retry-aware AMC request construction, response parsing, HTML cache assignment, or lazy revision HTML completion. Invalid entries now raise `ValueError("revisions list entries must be ForumPostRevision")`. Empty valid collections, valid HTML reads, retry partial-success behavior, duplicate request deduplication, cached duplicate HTML reuse, missing response content diagnostics, lazy `ForumPostRevision.html` behavior, direct revision-list acquisition, batched revision-list acquisition, and optional `with_html=True` acquisition remain unchanged.

## Outcome

Forum post revision HTML callers now get deterministic Python-side preflight validation for malformed collection entries instead of accidental attribute failures from later cache or acquisition stages.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free forum post revision HTML for moderation ledgers, translation review tooling, edit-history audits, forum migration checks, archival jobs, local indexing, or generated workflows that compare historical forum post content.

## Current Evidence

Local rollout-backed drafts repeatedly treat forum post revision HTML acquisition as a practical read surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), and [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md) establish forum post revision-list and revision-HTML retrieval as active practical workflows.

Those prior slices are not duplicates. They covered retry behavior, revision-list request deduplication, direct revision HTML request deduplication, optional `with_html=True` HTML deduplication, cached duplicate HTML reuse, lazy HTML failure visibility, lazy failure context, missing revision-list response body diagnostics, missing HTML response content diagnostics, and malformed revision-list response body type diagnostics. [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md) validated caller-provided `post` and `posts` objects before revision-list acquisition, but it did not validate malformed `ForumPostRevisionCollection` entries before public `get_htmls()` cache inspection, duplicate grouping, request construction, or response parsing. This slice follows the recent collection-entry boundary pattern from [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), but applies it to forum post revision HTML entries.

## Related Issue

Builds directly on [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), and [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate every `ForumPostRevisionCollection.get_htmls()` entry is a `ForumPostRevision` before cached HTML checks or request construction.
- Preserve empty valid collection behavior, valid HTML reads, duplicate request deduplication, cached duplicate HTML reuse, retry partial-success behavior, missing response content diagnostics, lazy `ForumPostRevision.html` behavior, direct revision-list acquisition, batched revision-list acquisition, and optional `with_html=True` HTML acquisition.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum-post-revision HTML read preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.get_htmls()` must reject entries that are not `ForumPostRevision` objects with `ValueError("revisions list entries must be ForumPostRevision")` before cache or request work. |
| R2 | Valid empty collections and valid revision HTML reads must remain unchanged. |
| R3 | Existing retry behavior, duplicate request handling, cached duplicate HTML reuse, missing response content diagnostics, lazy HTML behavior, direct revision-list acquisition, batched revision-list acquisition, and optional `with_html=True` behavior must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, affected forum-post-revision tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | HTML acquisition collection entries without `ForumPostRevision` objects fail before cache or request work. | `TestForumPostRevisionCollectionGetHtmls.test_get_htmls_rejects_non_revision_entries_before_fetch` failed RED for `None`, `True`, and `"9001"` by leaking `AttributeError` through the cached-HTML map, then passed GREEN after validation was added. | Accepting missing values, booleans, or strings as revisions, inspecting invalid entry caches, grouping invalid revision IDs, calling AMC, or surfacing `AttributeError` rejects this local completion claim. | Forum post revision HTML preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Valid empty collections and valid revision HTML reads remain unchanged. | `tests/unit/test_forum_post_revision.py` passed 60 tests, the adjacent forum-post/forum-thread/forum-category/forum-post-revision set passed 233 tests, and the full unit suite passed 1020 tests. | Regressing `ForumPostRevisionCollection(post, [])`, valid HTML acquisition, or HTML cache assignment rejects this local completion claim. | Forum post revision HTML workflow | `tests/unit/test_forum_post_revision.py`, adjacent forum tests |
| R3 | Existing forum post revision acquisition behavior remains unchanged. | The adjacent 233-test forum set and full 1020-test unit suite covered retry partial-success behavior, duplicate request handling, cached duplicate HTML reuse, missing response content diagnostics, lazy HTML behavior, direct revision-list acquisition, batched revision-list acquisition, and optional `with_html=True` behavior. | Regressing retry behavior, duplicate request handling, cached duplicate reuse, missing content diagnostics, lazy HTML failures, revision-list parsing, direct/batched acquisition, optional HTML fetching, source, edit, or reply behavior rejects this local completion claim. | Forum post revision workflow | `tests/unit/test_forum_post_revision.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic forum post and revision objects plus malformed local values. | Using credentials, cookies, auth JSON, live Wikidot actions, raw rollout paths, sandbox details, upstream Issues, upstream PRs, forum post text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c1d0e4e fix(forum_post_revision): validate collection entries`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_non_revision_entries_before_fetch` failed before the fix with 3 failures; malformed collection entries leaked `AttributeError` through the cached-HTML map.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_non_revision_entries_before_fetch` passed 3 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py` passed 60 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py` passed 233 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1020 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumPostRevisionCollection(post=post, revisions=[valid_revision, None]).get_htmls()`, `[valid_revision, True]`, and `[valid_revision, "9001"]` raise `ValueError("revisions list entries must be ForumPostRevision")` before cache inspection or AMC work.
- `ForumPostRevisionCollection(post=post, revisions=[])` remains a valid empty collection.
- Valid revision HTML acquisition still submits `forum/sub/ForumPostRevisionModule` request bodies with integer revision IDs.
- Existing retry partial-success behavior, duplicate request handling, cached duplicate HTML reuse, missing response content diagnostics, lazy HTML behavior, direct revision-list acquisition, batched revision-list acquisition, and optional `with_html=True` behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum post revision HTML acquisition depends on real `ForumPostRevision` objects because the implementation reads revision HTML cache state, revision IDs, and post/site context before it builds revision HTML module requests. Generated workflows can accidentally pass revision IDs, serialized records, booleans, or missing values into this surface. Those malformed values should fail deterministically at the public API boundary, especially because the valid path contains cache reuse, deduplication, retry-aware request construction, response parsing, and cache assignment. The change is narrow: it rejects malformed values instead of coercing them and leaves valid read behavior unchanged.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established forum post revision HTML retrieval as a practical workflow.
- The focused RED failures showed malformed public collection entries crossing into HTML cache checks and leaking unstable attribute failures instead of failing at the public call boundary.
- Existing forum-post-revision drafts covered retry behavior, duplicate request handling, optional `with_html=True` deduplication, cached duplicate HTML reuse, lazy failure context, missing response content diagnostics, response body context, and malformed response body type context, but not malformed public collection entry preflight.
- This slice only validates forum post revision collection entries for HTML acquisition. It does not change forum post revision-list parsing, revision HTML parsing, optional `with_html=True` acquisition, post source fetching, post editing, replies, retry semantics, response diagnostics, site authentication, live Wikidot behavior, or forum post revision dataclass fields.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw action responses, forum post text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects IDs, strings, booleans, and missing values instead of treating them as revision objects. Callers that receive revision IDs from text sources should resolve them to `ForumPostRevision` instances before requesting revision HTML.
