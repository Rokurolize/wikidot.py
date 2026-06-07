# PR Draft: Validate Forum Thread Collection Site Ownership

## Summary

`ForumThreadCollection` validates explicit collection parent-site types, validates its `threads` container and entries, and each `ForumThread` validates its own retained `site`, but the public collection constructor did not ensure contained threads all belong to the effective collection site. A caller could construct `ForumThreadCollection(site_a, [thread_from_site_b])`; a caller could also rely on parent inference with `ForumThreadCollection(site=None, threads=[thread_from_site_a, thread_from_site_b])`, which inferred `site_a` from the first thread while retaining a valid thread from `site_b`.

This change validates thread entry ownership at the public `ForumThreadCollection.__init__` boundary after entry validation and effective site selection but before list state is stored. Threads whose retained `thread.site` is not the collection site now raise `ValueError("threads must belong to the collection site")`. Valid explicit same-site collections, valid inferred same-site collections, empty no-parent collections, lookup, category thread-list parsing, direct thread-detail acquisition, duplicate cached thread reuse, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply workflows, and adjacent forum category/post/revision workflows remain unchanged.

## Outcome

Forum thread collections reject different-site thread entries before local collection state can represent one site while storing another site's threads.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free category thread inventories, direct thread-detail reads, generated forum migration or moderation ledgers, cached category-thread reuse, duplicate direct-thread reuse, lazy `ForumCategory.threads`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, or local tests that construct `ForumThreadCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum thread lists, direct thread-detail reads, category-thread caches, and thread-owned post traversal as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [098-pr-ignore-thread-description-pager-markup.md](098-pr-ignore-thread-description-pager-markup.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [228-pr-cache-direct-thread-post-acquisition.md](228-pr-cache-direct-thread-post-acquisition.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), [539-pr-preserve-empty-forum-thread-parent.md](539-pr-preserve-empty-forum-thread-parent.md), [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md), [573-pr-validate-forum-thread-url-site.md](573-pr-validate-forum-thread-url-site.md), and [574-pr-validate-forum-thread-reply-site.md](574-pr-validate-forum-thread-reply-site.md) establish category thread-list acquisition, direct thread-detail acquisition, cache behavior, parser diagnostics, response diagnostics, collection constructor integrity, direct thread parent validation, and adjacent retained-state hardening as active operational boundaries.

This slice is not a duplicate of those issues. Issue 475 validates explicit non-`None` `ForumThreadCollection.site` field type while preserving inference and empty no-parent semantics. Issue 423 validates the collection's `threads` container and entries. Issue 503 validates each `ForumThread.site` field type. Issue 447 validates a thread's optional `category` field. Issue 504 validates a `ForumThread` object's optional `_posts` cache slot. Issue 539 preserves empty `site=None` collection readability. None validates a valid `ForumThread` entry whose retained `thread.site` is individually valid but does not match the collection site selected explicitly or inferred from the first thread.

No upstream issue was filed from this local workspace.

## Changes

- Add a forum-thread collection ownership preflight at `ForumThreadCollection.__init__`.
- Reject explicit different-site thread entries with `ValueError("threads must belong to the collection site")`.
- Reject inferred-parent mixed-site thread collections with the same diagnostic.
- Preserve explicit valid parents, inferred valid parents, empty no-parent collections, valid thread lists, lookup, category thread-list acquisition, direct thread-detail acquisition, duplicate cached thread reuse, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply workflows, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum thread parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThreadCollection(site_a, [thread_from_site_b])` must reject the different-site thread with `ValueError("threads must belong to the collection site")` before storing collection list state. |
| R2 | `ForumThreadCollection(site=None, threads=[thread_from_site_a, thread_from_site_b])` must infer `site_a` from the first thread and reject the second different-site thread with the same diagnostic before storing collection list state. |
| R3 | Valid explicit same-site thread collections, valid inferred same-site thread collections, and empty no-parent collections must remain valid. |
| R4 | Existing `find(...)`, category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, duplicate cached thread reuse, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, replies, and adjacent forum category/post/revision workflows must remain unchanged. |
| R5 | Focused RED/GREEN, forum-thread module coverage, adjacent forum module coverage, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit different-site thread entries fail at the public collection constructor boundary. | `TestForumThreadCollectionInit.test_init_rejects_thread_from_different_site` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("threads must belong to the collection site")`. | Accepting the different-site thread, storing a collection for `site_a` that contains a thread retained from `site_b`, or deferring failure to lookup/cache code rejects this local completion claim. | `ForumThreadCollection.__init__` | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Inferred-parent mixed-site thread entries fail at the same constructor boundary. | `TestForumThreadCollectionInit.test_init_rejects_mixed_site_threads_when_site_is_inferred` failed RED with `DID NOT RAISE`, then passed GREEN with the same diagnostic. | Inferring `site_a` from the first thread while storing a thread retained from `site_b`, accepting mixed inferred collections, or rejecting all inferred collections rejects this local completion claim. | `ForumThreadCollection.__init__` | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Valid thread collection construction semantics stay green. | `tests/unit/test_forum_thread.py` passed 147 tests after the ownership preflight. | Rejecting valid same-site explicit collections, valid same-site inferred collections, empty no-parent collections, or normal site inference rejects this local completion claim. | Forum thread collections | `tests/unit/test_forum_thread.py` |
| R4 | Existing forum thread and adjacent forum workflows remain green. | Adjacent forum category/thread/post/revision coverage passed 528 tests, and the full unit suite passed 2695 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, lookup, duplicate cached thread reuse, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, post-list acquisition, post revision acquisition, or forum category behavior rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, full `pyright`, and `git diff --check` passed. Full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted; full mypy found no issues in 87 source files. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic valid `Site` and `ForumThread` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page/forum content from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `03866d6 fix(forum_thread): validate thread collection site ownership`.

- RED explicit target-site ownership: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_thread_from_different_site -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused explicit ownership regression: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_thread_from_different_site -q` passed 1 test.
- RED inferred target-site ownership: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_mixed_site_threads_when_site_is_inferred -q` failed before the inferred-branch fix with `DID NOT RAISE`.
- GREEN focused ownership coverage: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_thread_from_different_site tests/unit/test_forum_thread.py::TestForumThreadCollectionInit::test_init_rejects_mixed_site_threads_when_site_is_inferred -q` passed 2 tests.
- Forum thread module coverage: `uv run pytest tests/unit/test_forum_thread.py -q` passed 147 tests.
- Adjacent forum category/thread/post/revision tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 528 tests.
- `uv run pytest tests/unit -q` passed 2695 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThreadCollection(site_a, [thread_from_site_b])` raises `ValueError("threads must belong to the collection site")` before storing collection list state.
- `ForumThreadCollection(site=None, threads=[thread_from_site_a, thread_from_site_b])` raises the same diagnostic after inferring the first thread's site and before storing collection list state.
- `ForumThreadCollection(site=<valid Site>, threads=[])`, `ForumThreadCollection(site=<valid Site>, threads=[same_site_thread])`, `ForumThreadCollection(site=None, threads=[same_site_thread])`, and `ForumThreadCollection(site=None, threads=[])` remain valid.
- Existing `find(...)`, category thread-list acquisition, direct thread-detail acquisition, parser diagnostics, duplicate cached thread reuse, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply workflows, and adjacent forum category/post/revision behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThreadCollection.site` and each retained `ForumThread.site` should describe the same owning site for browser-free category thread inventories, duplicate cached thread reuse, lazy category-thread state, thread lookup, generated moderation ledgers, migration audits, and downstream post/revision traversal. Parser paths already create threads from the owning site, and same-site direct/detail helpers already preserve thread ownership; constructor ownership validation keeps mismatched rehydrated records, fixtures, or generated ledgers from silently carrying another site's threads under the collection site.

## Local Evidence, Not For Upstream Paste

- The explicit RED failure showed a valid thread from another site could be accepted by `ForumThreadCollection(site, [thread])` without ownership rejection.
- The inferred RED failure showed `ForumThreadCollection(site=None, threads=[thread_from_site_a, thread_from_site_b])` could infer a collection site from the first thread while retaining another site's thread.
- Existing local drafts covered category thread-list acquisition, direct thread-detail acquisition, duplicate direct-thread and post-list reuse, parser diagnostics, response-body diagnostics, lookup validation, collection threads/entry validation, direct thread site validation, explicit collection-site validation, empty no-parent handling, and direct thread posts-cache validation, but did not compare each valid `ForumThread.site` to the effective collection site.
- This slice only validates forum-thread collection target-site ownership at collection initialization. It does not change thread-list parsing, direct thread-detail parsing, collection lookup semantics, category thread-list cache invalidation, lazy post acquisition, reply behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page/forum source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally uses object identity. A site-owned thread collection should contain `ForumThread` objects retained from the exact owning `Site` object, matching parser-created threads and direct helper results. It does not infer a collection site from a later thread, coerce site-like objects, compare by unix name alone, verify remote site membership, validate a thread's optional category ownership, or change live client authentication; those are separate parser, lookup, and workflow concerns.
