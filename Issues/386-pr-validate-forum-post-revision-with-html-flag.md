# PR Draft: Validate Forum Post Revision With-HTML Flag

## Summary

`ForumPostRevisionCollection.acquire_all_for_posts(posts, with_html=...)` documents `with_html` as a boolean, but malformed caller-provided values were accepted at the public batch revision acquisition boundary. Falsy malformed values such as `None` and `0` silently skipped optional HTML acquisition, while truthy malformed values such as `"false"` and `1` triggered the optional `ForumPostRevisionModule` HTML request path.

This change validates `with_html` after `posts` validation and before empty-batch handling, cache inspection, revision-list acquisition, or optional revision HTML work. Malformed values now raise `ValueError("with_html must be a boolean")`. Existing valid `False` revision-list behavior and valid `True` revision HTML acquisition remain unchanged.

## Outcome

Forum post revision callers now get deterministic Python-side preflight validation for malformed optional-HTML controls instead of silent coercion, unexpected HTML request work, or later failures caused by truthy configuration strings and integer stand-ins.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using forum post revision history for browser-free moderation workflows, archival indexing, diff tooling, generated evidence ledgers, audit exports, cache-aware batch reads, or migration scripts that optionally need rendered revision HTML.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision history and revision HTML as practical read-heavy surfaces. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), and [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md) cover retry-aware revision-list and HTML acquisition, duplicate request deduplication, cache reuse, contextual response diagnostics, lazy HTML failure visibility, and cached direct acquisition.

Those prior slices are not duplicates. They covered request retry behavior, duplicate post and revision ID batching, cache-aware list reuse, cached duplicate HTML reuse, response-body diagnostics, missing-content diagnostics, lazy HTML diagnostics, and parser context. [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md) validated caller-provided `post` and `posts` objects, [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md) validated collection entries for HTML acquisition, and [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md) validated loaded collection search keys. None of those drafts validates the boolean `with_html` control before batch acquisition branches on it.

## Related Issue

Builds directly on [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), and [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `with_html` in `ForumPostRevisionCollection.acquire_all_for_posts(...)` before empty-batch handling, cache inspection, revision-list acquisition, or optional revision HTML work.
- Reject malformed optional-HTML controls with `ValueError("with_html must be a boolean")`.
- Preserve valid default/`False` revision-list acquisition and cached-list behavior.
- Preserve valid `True` optional revision HTML acquisition, cached revision-list HTML fill, duplicate revision-ID HTML deduplication, cached duplicate HTML reuse, retry handling, missing-content diagnostics, lazy `ForumPostRevision.html`, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public API behavior hardening
- Forum post revision optional-HTML control preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=...)` must reject `None`, strings, integers, and other non-bool values with `ValueError("with_html must be a boolean")` before cache inspection, revision-list fetches, or optional revision HTML fetches. |
| R2 | Existing malformed `posts` validation precedence must remain unchanged. |
| R3 | Valid default/`with_html=False` behavior must remain unchanged for empty batches, cached revision lists, duplicate post IDs, and ordinary revision-list acquisition. |
| R4 | Valid `with_html=True` behavior must remain unchanged for cached-list HTML fill, duplicate revision-ID HTML deduplication, retry-aware HTML acquisition, and missing-content diagnostics. |
| R5 | Adjacent forum post, thread, and category workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private post data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, affected forum-post-revision tests, adjacent forum tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed optional-HTML controls fail before request work. | `TestForumPostRevisionCollectionAcquireAllForPosts.test_acquire_all_for_posts_rejects_non_bool_with_html_before_fetch` failed RED for `None`, `"false"`, `0`, and `1`, then passed GREEN after validation was added. | Treating `"false"` or `1` as truthy, treating `None` or `0` as false controls, touching either AMC request path, returning a result, or raising an unrelated later error rejects this local completion claim. | Forum post revision batch preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Malformed `posts` errors still occur before `with_html` validation. | Validation remains ordered as `posts = _validate_forum_posts(posts)` followed by `with_html = _validate_with_html(with_html)`, and the existing non-list and bad-entry tests passed in the affected file. | Changing the documented malformed `posts` error messages or accepting malformed `posts` rejects this local completion claim. | Forum post revision batch preflight | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid false controls still perform revision-list acquisition and cache-aware skips. | `tests/unit/test_forum_post_revision.py` passed 72 tests after validation was added. | Fetching cached revision lists, losing duplicate post-ID behavior, changing empty-batch handling, or changing ordinary revision-list acquisition rejects this local completion claim. | Forum post revision list reads | `tests/unit/test_forum_post_revision.py` |
| R4 | Valid true controls still perform optional revision HTML acquisition correctly. | The affected file includes the cached-list `with_html=True`, retry-aware HTML, missing-content diagnostics, and duplicate revision-ID HTML dedupe tests, all green in the 72-test run. | Skipping valid HTML fills, refetching revision lists unnecessarily, losing duplicate revision-ID grouping, hiding missing content, or changing retry behavior rejects this local completion claim. | Forum post revision HTML reads | `tests/unit/test_forum_post_revision.py` |
| R5 | Adjacent forum behavior remains green. | `tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py` passed 264 tests, and full unit tests passed 1122 tests. | Regressing forum post source reads, post edits, replies, thread acquisition, category acquisition, cached lazy properties, or adjacent parser diagnostics rejects this local completion claim. | Forum workflow | affected forum tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic local objects and mocks. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private post content, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `58579ff fix(forum_post_revision): validate with-html flag`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_non_bool_with_html_before_fetch` failed 4 selected tests before the fix because malformed controls were accepted; falsy values did not raise, while truthy values reached the optional HTML path and failed later.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAllForPosts::test_acquire_all_for_posts_rejects_non_bool_with_html_before_fetch` passed 4 tests after adding boolean preflight.
- `.venv/bin/ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py` passed 72 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py` passed 264 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1122 tests.
- `.venv/bin/ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `ForumPostRevisionCollection.acquire_all_for_posts([post], with_html=None)`, `with_html="false"`, `with_html=0`, and `with_html=1` raise `ValueError("with_html must be a boolean")` before cache inspection or AMC requests.
- `ForumPostRevisionCollection.acquire_all_for_posts([])` still returns `{}` with the default valid `False` control.
- Valid default/`False` acquisition still fetches and caches revision lists as before.
- Valid `True` acquisition still fetches missing revision HTML and populates cached revision lists without refetching their list data.
- Duplicate post IDs, cached duplicate revision lists, duplicate revision IDs, retry-aware list/HTML acquisition, missing response diagnostics, lazy revision HTML, and adjacent forum workflows remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private post data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `0` or `1` tightens behavior for callers that previously used integers as booleans. Mitigation: the documented API type is `bool`; accepting integer controls can hide configuration parsing mistakes and accidentally change optional request behavior.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, or spreadsheet parsing bugs. Mitigation: text configuration should parse `"true"`/`"false"` into real booleans before calling wikidot.py.
- Risk: The change could be confused with forum post revision entry validation. Mitigation: collection-entry validation was already covered separately; this slice only validates the batch optional-HTML flag.
- Risk: The change could be confused with revision-list or HTML response diagnostics. Mitigation: parser and response validation remain unchanged; this slice only rejects malformed caller controls before those paths.

## Dependencies

- Existing `ForumPostRevisionCollection.acquire_all_for_posts(...)` remains the source of truth for multi-post revision-list acquisition.
- Existing `ForumPostRevisionCollection.get_htmls()` remains the collection-level source of truth for loaded revision HTML acquisition.
- Existing retry-aware AMC behavior remains unchanged for valid controls.
- Existing `post`/`posts` preflight validation remains the first validation step.
- The validation is local to `src/wikidot/module/forum_post_revision.py` and does not affect forum post source reads, post edits, thread replies, page revisions, page files, user lookup, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered forum post revision `with_html` flag validation path.

## Upstream-Safe Motivation

Forum post revision history is a common read-heavy surface for moderation, archive, diff, and audit tooling. Since `with_html` controls whether the helper performs additional rendered revision HTML requests, malformed truthy strings and integer stand-ins should fail deterministically before request work rather than silently changing optional network behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established forum post revision lists and revision HTML as practical workflows through retry-aware list reads, retry-aware HTML reads, duplicate request deduplication, cached direct acquisition, cached duplicate reuse, optional `with_html=True` acquisition, parser context, response diagnostics, and lazy HTML failure visibility.
- Existing forum post revision drafts covered request retry behavior, deduplication, cache behavior, response diagnostics, post input validation, collection entry validation, and loaded collection search-key validation; they did not validate the caller-provided `with_html` control.
- This slice only validates `with_html` inputs for `ForumPostRevisionCollection.acquire_all_for_posts(...)`. It does not change post object validation, revision-list parsing, revision HTML parsing, cached collection ownership, duplicate request grouping, retry behavior, lazy HTML behavior, forum post source reads, post edits, thread replies, category reads, page behavior, user lookup, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, post or page names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private post content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed optional-HTML controls instead of coercing them. Callers that load this flag from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve it into a real boolean before calling `ForumPostRevisionCollection.acquire_all_for_posts(...)`.
