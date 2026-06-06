# PR Draft: Validate Forum Post Revision HTML Assignments

## Summary

`ForumPostRevision.html` is a public property that lazily acquires and caches the rendered HTML for one forum post revision. The setter documented `value` as `str`, but it accepted any object. A caller could assign `revision.html = None`, `revision.html = True`, `revision.html = 1`, or `revision.html = ["<p>New HTML</p>"]`, causing the public property to store malformed local revision-HTML state and defer failures to later code that expects rendered HTML text.

This change validates direct `ForumPostRevision.html` assignments as strings. Invalid assignments now raise `ValueError("revision.html must be a string")` before mutating `_html`, preserving the last valid cached revision HTML when one exists. Existing lazy forum post revision HTML acquisition, retry behavior, duplicate cached revision HTML reuse, `with_html` acquisition controls, revision collection initialization, direct revision source workflows, and adjacent forum post/thread/category workflows remain unchanged.

## Outcome

Manually constructed, fixture-created, duplicate-reused, or ledger-rehydrated `ForumPostRevision` objects can no longer silently corrupt their cached rendered revision HTML through the public property setter.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum post revision HTML reads, forum post source/HTML comparison, revision snapshot ledgers, translation audits, migration scripts, moderation review tooling, or local tests that construct `ForumPostRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision HTML state as a practical workflow surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), and [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md) establish revision HTML reads, retry behavior, deduplication, cache reuse, response diagnostics, collection-entry validation, search-key validation, and acquisition controls as active operational boundaries.

Those prior slices are not duplicates. Issues042, 057, 058, 131, 135, 142, 143, 146, 180, 217, 229, 300, and 329 improved revision list/HTML acquisition, failure visibility, context, retry, deduplication, cached reuse, and response diagnostics. Issue364 validates post inputs, Issue366 validates collection entries before source/HTML acquisition, Issue377 validates revision search keys, Issue386 validates the `with_html` flag, and Issue421 validates `ForumPostRevisionCollection(...)` initialization. None of them validates direct public `ForumPostRevision.html = ...` assignment before single-revision cache mutation.

## Related Issue

Builds directly on [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), and [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a `ForumPostRevision.html` value validator.
- Reject `None`, booleans, integers, lists, and other non-string values with `ValueError("revision.html must be a string")`.
- Validate before assigning `_html`, so invalid assignments preserve any previously cached valid revision HTML.
- Preserve valid string assignments, including empty strings.
- Preserve existing lazy revision HTML acquisition, `get_htmls()` behavior, `with_html` acquisition controls, duplicate cached revision HTML reuse, revision collection initialization, and adjacent forum post/thread/category workflows.

## Type Of Change

- Input validation
- Public property behavior hardening
- Local forum post revision HTML cache integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `revision.html = None`, `revision.html = True`, `revision.html = 1`, and `revision.html = ["<p>New HTML</p>"]` must raise `ValueError("revision.html must be a string")` before mutating `_html`. |
| R2 | Invalid assignments after already-cached valid HTML must preserve that previous string. |
| R3 | Valid string assignments must remain allowed. |
| R4 | Existing lazy forum post revision HTML acquisition, retry behavior, duplicate cached revision HTML reuse, `with_html` collection behavior, forum post workflows, forum thread workflows, and forum category workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent forum post revision tests, broader unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed revision HTML assignments fail before local HTML cache mutation. | `TestForumPostRevisionHtml.test_html_setter_rejects_invalid_html` failed RED for `None`, `True`, `1`, and `["<p>New HTML</p>"]` because the setter did not raise, then passed GREEN after validation was added. | Accepting missing values, booleans, numbers, lists, arbitrary objects, or deferring failure to later HTML consumers rejects this local completion claim. | Direct forum post revision HTML setter | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Invalid assignments preserve the previous valid cached revision HTML. | The focused GREEN asserts `revision.html == "<p>Cached HTML</p>"` after each rejected assignment. | Mutating `_html` before raising, clearing cached HTML, or triggering lazy lookup to recover the value rejects this local completion claim. | Local revision HTML cache | `tests/unit/test_forum_post_revision.py` |
| R3 | String assignments remain valid. | `TestForumPostRevisionHtml.test_html_setter` assigns `"<p>New HTML</p>"` and asserts it is stored unchanged. | Rejecting valid strings, coercing non-strings to strings, or changing direct cache setup behavior rejects this local completion claim. | ForumPostRevision fixtures and cache setup | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing adjacent forum post revision HTML workflows remain green. | Focused setter/property/collection checks passed 11 tests, forum post revision/post/thread/category tests passed 307 tests, and full unit tests passed 1632 tests. | Regressing lazy revision HTML reads, retry exhaustion behavior, response parsing, duplicate cached revision HTML reuse, `with_html` acquisition, revision list reads, forum post source reads, forum thread reads, or forum category reads rejects this local completion claim. | Forum post revision, forum post, forum thread, and forum category workflows | `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, source text from real sites, forum post content, revision comments, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c404c3e fix(forum_post_revision): validate html assignments`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_setter_rejects_invalid_html -q` failed 4 tests before the fix; every malformed HTML assignment reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after adding setter validation.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `uv run mypy src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_setter tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_setter_rejects_invalid_html tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_cached tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_raises_when_retry_is_exhausted tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_missing_response_content_includes_site_post_revision_and_field_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_reuses_cached_duplicate_revision_html tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_deduplicates_duplicate_revision_ids -q` passed 11 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q` passed 307 tests.
- `uv run pytest tests/unit -q` passed 1632 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `revision.html = None`, `revision.html = True`, `revision.html = 1`, and `revision.html = ["<p>New HTML</p>"]` raise `ValueError("revision.html must be a string")` without changing an existing cached valid HTML string.
- `revision.html = "<p>New HTML</p>"` remains valid and stores the same string.
- Existing lazy `ForumPostRevision.html` acquisition still runs when `_html` is missing and still reports site/post/revision context if acquisition leaves `_html` unset.
- Existing revision HTML response parsing, retry behavior, duplicate cached revision HTML reuse, `with_html` controls, revision collection behavior, forum post source reads, forum thread reads, and forum category reads remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevision.html` is shared by lazy revision HTML reads, duplicate cached revision reuse, forum post revision snapshot ledgers, source/HTML comparison, and tests that seed revision state directly. Direct assignment is useful for caller-created revision objects and data rehydrated from external ledgers, but malformed HTML cache objects should fail at the property boundary instead of silently poisoning later forum post revision HTML consumers.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used forum post revision HTML snapshots, source/HTML comparison, cached duplicate revision reuse, and tests that seed revision HTML caches directly.
- Existing local drafts covered forum post revision list/HTML acquisition, retry/fallback behavior, duplicate request deduplication, lazy failure context, response diagnostics, `ForumPostRevisionCollection` initialization validation, collection entry validation, search-key validation, `with_html` validation, and direct page revision HTML assignment validation, but did not cover direct `ForumPostRevision.html = ...` mutation.
- The focused RED failures showed invalid assignments were accepted by the property setter. The GREEN regression covers missing, boolean, integer, and list values and asserts the previous valid HTML string survives.
- This slice only validates direct forum post revision HTML assignment shape. It does not change lazy revision HTML acquisition, revision list acquisition, forum post source behavior, forum post/thread/category parsing, live site behavior, or parser behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, source text from real sites, forum post content, revision comments, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed revision HTML cache objects instead of coercing values. Callers that load rendered forum post revision HTML from files, generated structures, JSON, YAML, CLI flags, spreadsheets, databases, or ledgers should normalize the rendered HTML to `str` before assigning it to `ForumPostRevision.html`.
