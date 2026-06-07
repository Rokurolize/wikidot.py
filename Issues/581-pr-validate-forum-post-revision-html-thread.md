# PR Draft: Validate Forum Post Revision HTML Thread State

## Summary

`ForumPostRevisionCollection.get_htmls()` validated that the collection contained `ForumPostRevision` objects, but it still trusted the retained `self.post.thread` field before revision-HTML request work. If caller code, a fixture, or rehydrated state replaced a valid revision post's thread with a malformed object after construction, lazy `ForumPostRevision.html` and direct collection HTML acquisition could reach request plumbing and surface unrelated request or iterator diagnostics before reporting the invalid retained parent.

This change revalidates the retained revision post thread before uncached forum-post revision HTML acquisition. Malformed read-time parent-thread state now raises `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation. Valid lazy revision HTML reads, direct `get_htmls()` acquisition, cached HTML reuse, duplicate revision ID deduplication, exhausted-retry behavior, response-content diagnostics, revision-list acquisition, and adjacent forum workflows remain unchanged.

## Outcome

Forum post revision HTML acquisition now has explicit retained-thread preflight before malformed local parent-thread state can influence request routing, response parsing, or revision HTML cache mutation.

## Current Evidence

Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-list-body-type-context.md](329-pr-forum-post-revision-list-body-type-context.md), [366-pr-validate-forum-post-revisions-before-html-fetch.md](366-pr-validate-forum-post-revisions-before-html-fetch.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [535-pr-preserve-empty-forum-post-revision-collection-parent.md](535-pr-preserve-empty-forum-post-revision-collection-parent.md), and [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md) establish forum post revision acquisition, revision HTML reads, retained parent validation, and response diagnostics as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 366 validates revision collection entries before HTML acquisition. Issue 445 validates constructor-time `ForumPostRevision.post` input. Issue 473 validates constructor-time `ForumPostRevisionCollection.post` input. Issue 580 validates retained `post.thread` before revision-list acquisition and lazy `ForumPost.revisions`, not revision HTML acquisition. This slice covers a valid retained revision post whose `post.thread` was mutated before direct `get_htmls()` or lazy `ForumPostRevision.html` request work.

No upstream issue was filed from this local workspace.

## Changes

- Reuse the forum-post revision retained thread/site validators inside `ForumPostRevisionCollection.get_htmls()`.
- Use the validated site for revision-HTML request work.
- Add regressions for direct `get_htmls()` and lazy `ForumPostRevision.html` with a mutated retained post thread.
- Preserve cached HTML no-op behavior: fully acquired revisions still return without parent validation or request work.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection.get_htmls()` must reject a mutated non-`ForumThread` `collection.post.thread` with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation. |
| R2 | Lazy `ForumPostRevision.html` must reject a mutated non-`ForumThread` `revision.post.thread` with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation. |
| R3 | Valid direct revision HTML acquisition, valid lazy HTML reads, cached HTML reuse, duplicate revision ID handling, exhausted-retry behavior, response-content diagnostics, revision-list acquisition, and constructor validation must remain stable. |
| R4 | Adjacent forum category, forum thread, forum post, and forum post revision workflows must remain stable. |
| R5 | Focused RED/GREEN, relevant HTML acquisition tests, full revision module, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Direct revision HTML acquisition fails before side-effect surfaces. | `TestForumPostRevisionCollectionGetHtmls.test_get_htmls_rejects_mutated_post_thread_before_fetch` passed after the fix and asserts no request call and no HTML cache mutation. | Calling `amc_request_with_retry`, accepting dictionaries or mocks as threads, mutating `_html`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostRevisionCollection.get_htmls()` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Lazy revision HTML acquisition fails before side-effect surfaces. | `TestForumPostRevisionHtml.test_html_property_rejects_mutated_post_thread_before_fetch` failed RED by reaching mocked request plumbing and surfacing `zip() argument 2 is shorter than argument 1`, then passed GREEN with `ValueError("thread must be a ForumThread")`. | Calling `amc_request_with_retry`, accepting dictionaries or mocks as threads, mutating `_html`, or deferring failure to request/response diagnostics rejects this local completion claim. | `ForumPostRevision.html` through `ForumPostRevisionCollection.get_htmls()` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid revision HTML behavior remains unchanged. | Focused HTML acquisition coverage passed 19 tests, and full `tests/unit/test_forum_post_revision.py` passed 123 tests. | Regressing lazy HTML reads, direct `get_htmls()`, cached reuse, duplicate revision ID handling, exhausted-retry behavior, response-content diagnostics, revision-list acquisition, or constructor validation rejects this local completion claim. | Forum post revision workflows | `tests/unit/test_forum_post_revision.py` |
| R4 | Adjacent workflows remain stable. | Adjacent forum workflow tests passed 520 tests, and the full unit suite passed 2681 tests. | Regressing forum category, forum thread, forum post, or forum post revision behavior rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic mutated post state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, post source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `fa7875f fix(forum_post_revision): validate revision html post thread`.

- RED lazy revision HTML retained-thread validation: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_rejects_mutated_post_thread_before_fetch -q` failed before the fix because mutated retained `ForumPost.thread` state reached mocked request plumbing and surfaced `zip() argument 2 is shorter than argument 1` instead of `ValueError("thread must be a ForumThread")`.
- GREEN focused regressions: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_mutated_post_thread_before_fetch tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml::test_html_property_rejects_mutated_post_thread_before_fetch -q` passed 2 tests.
- Focused HTML acquisition coverage: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls tests/unit/test_forum_post_revision.py::TestForumPostRevisionHtml -q` passed 19 tests.
- Full revision module: `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 123 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 520 tests.
- `uv run pytest tests/unit -q` passed 2681 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevisionCollection.get_htmls()` rejects mutated malformed `collection.post.thread` values with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation.
- Lazy `ForumPostRevision.html` rejects mutated malformed `revision.post.thread` values with `ValueError("thread must be a ForumThread")` before AMC request work or revision HTML cache mutation.
- Valid direct revision HTML acquisition, valid lazy HTML reads, cached HTML reuse, duplicate revision ID handling, exhausted-retry behavior, response-content diagnostics, revision-list acquisition, and constructor validation remain unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `ForumPost.thread` state reached mocked revision HTML request handling and then raised an unrelated `zip()` length diagnostic instead of the existing thread diagnostic.
- This slice only validates retained forum-post revision parent-thread state before revision HTML acquisition work. It does not change revision-list acquisition, revision constructor validation, revision collection constructor validation, response parsing, revision-list retry behavior, cached collection reuse, source acquisition, edit behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, post source text from real sites, and live Wikidot account details out of upstream discussion.
