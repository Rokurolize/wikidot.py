# PR Draft: Validate Forum Thread URL Site State

## Summary

`ForumThread.url` builds a canonical forum-thread URL from the retained parent `site` and thread ID. Existing local slices validate direct `ForumThread(site=...)` construction, direct thread acquisition inputs, forum-thread collection parent sites, and site URL metadata. One retained-state boundary still trusted `ForumThread.site` after construction: if a caller, fixture, or rehydrated thread object replaced `thread.site` with a malformed non-`Site` object, `thread.url` could fabricate a mock-derived URL instead of reporting the thread parent-state problem.

This change revalidates `self.site` inside `ForumThread.url` before reading `site.url`. Malformed URL-time thread parent state now raises `ValueError("site must be a Site")`. Valid thread URL generation, thread construction, thread acquisition, forum collection behavior, and adjacent forum workflows remain unchanged.

## Outcome

Forum-thread URL generation now has explicit retained-parent preflight before malformed local thread state can influence exported URLs or generated ledgers.

## Current Evidence

Existing drafts [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md), [571-pr-validate-site-url-metadata-state.md](571-pr-validate-site-url-metadata-state.md), and [572-pr-validate-page-collection-batch-site.md](572-pr-validate-page-collection-batch-site.md) establish forum-thread records, direct thread reads, URL-generating parent sites, and retained-state preflight as practical workflow surfaces.

This slice is not a duplicate of those issues. Issue 503 validates `ForumThread(site=...)` at construction time. Issue 543 validates the `site` argument to direct thread acquisition before request work. Issue 475 validates `ForumThreadCollection.site`, not the parent stored on an individual thread. Issue 571 validates the fields inside a valid `Site.url`, not whether `ForumThread.url` still has a `Site` parent. This slice covers mutated retained `ForumThread.site` at URL-generation time, not constructor input validation, direct acquisition arguments, thread ID validation, site URL metadata validation, or live Wikidot request behavior.

No upstream issue was filed from this local workspace.

## Changes

- Revalidate `self.site` inside `ForumThread.url`.
- Add a regression for a mutated non-`Site` thread parent that previously reached URL formatting.
- Preserve valid thread URL generation and adjacent forum workflows.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread.url` must reject a mutated non-`Site` `thread.site` with `ValueError("site must be a Site")` before reading `site.url`. |
| R2 | Valid `ForumThread.url` output must continue to include the parent site URL and `forum/t-<thread_id>/` path. |
| R3 | Direct `ForumThread(site=...)` constructor validation and `ForumThreadCollection(site=...)` validation must remain unchanged. |
| R4 | Valid category thread-list parsing, direct thread-detail parsing, lazy category/thread/post workflows, reply workflows, and adjacent forum behavior must remain stable. |
| R5 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Mutated retained thread parent state fails before URL generation accepts mock or non-site state. | `TestForumThreadBasic.test_url_rejects_mutated_site` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumThread.url` revalidated `self.site`. | Returning a mock-derived URL, coercing malformed parents, reading `site.url` from a non-`Site`, or deferring failure to later request/export work rejects this local completion claim. | `ForumThread.url` | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Valid URL output remains unchanged. | `TestForumThreadBasic.test_url_property` stayed green with URL text containing `test-site.wikidot.com` and `forum/t-3001`. | Changing valid URL scheme/host/path formatting or losing the thread ID path rejects this local completion claim. | Forum thread URL generation | `tests/unit/test_forum_thread.py` |
| R3 | Existing parent validation contracts stay green. | Focused constructor checks for malformed `ForumThread.site` and `ForumThreadCollection.site` passed 9 tests. | Weakening constructor validation, changing diagnostics, or accepting malformed explicit collection sites rejects this local completion claim. | ForumThread and ForumThreadCollection constructors | `tests/unit/test_forum_thread.py` |
| R4 | Adjacent workflows remain stable. | `tests/unit/test_forum_thread.py` passed 144 tests, adjacent forum workflow tests passed 510 tests, and the full unit suite passed 2671 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, response diagnostics, collection initialization, loaded-collection lookup, lazy category thread reads, direct thread lookup, batched thread lookup, lazy post reads, reply behavior, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit` |
| R5 | Existing repository quality gates remain green. | Full ruff check and format check passed, full mypy passed with no issues in 87 source files, full pyright passed with 0 errors, 0 warnings, and 0 informations, and `git diff --check` passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic mutated thread state and local fixtures; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private messages, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `6a0673d fix(forum_thread): validate thread url site`.

- RED URL-site validation: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_url_rejects_mutated_site -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused URL checks: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_url_rejects_mutated_site tests/unit/test_forum_thread.py::TestForumThreadBasic::test_url_property -q` passed 2 tests.
- Focused parent validation checks: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_sites tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_malformed_sites -q` passed 9 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 144 tests.
- Adjacent forum: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 510 tests.
- `uv run pytest tests/unit -q` passed 2671 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread.url` rejects mutated malformed `thread.site` values with `ValueError("site must be a Site")` before reading `site.url`.
- Valid `ForumThread.url` output remains unchanged.
- Constructor-time `ForumThread.site` and `ForumThreadCollection.site` validation remains unchanged.
- Adjacent forum behavior remains intact.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed mutated retained `ForumThread.site` state was accepted by `ForumThread.url` instead of producing the existing parent-site diagnostic.
- This slice only validates retained forum-thread parent state before URL generation. It does not change thread construction, direct thread acquisition, thread-list parsing, direct thread-detail parsing, collection lookup semantics, forum category/post/revision behavior, reply behavior, live site behavior, site URL metadata validation, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private metadata values, private-message content, private forum content, and live Wikidot account details out of upstream discussion.
