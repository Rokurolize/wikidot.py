# PR Draft: Validate Forum Thread Category Site

## Summary

`ForumThread.category` is optional and Issue 447 already validates that the constructor field is either `None` or a `ForumCategory`. One retained-owner gap remained: direct `ForumThread(...)` construction could combine `site=site_a` with a valid `ForumCategory(site=site_b, ...)`, so thread records could retain one site while their parent category retained another.

This change validates optional category site ownership during `ForumThread.__post_init__`, after the existing category type check and before the optional posts-cache check. A non-null category must retain the same `Site` object as the owning thread. Mismatches raise `ValueError("category must belong to the thread site")`. Valid same-site categories, uncategorized direct thread records, category thread-list parsing, direct thread-detail parsing, thread post caches, post and revision batch guards, and adjacent forum workflows remain unchanged.

## Outcome

Directly constructed `ForumThread` records can no longer pair a thread with a parent category from another retained site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct browser-free forum inventories, generated forum migration ledgers, moderation audits, test fixtures, adapters, or serialized and rehydrated forum records before traversing category, thread, post, or revision state.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum category inventories, direct thread-detail reads, category-thread caches, retained-owner validation, and generated forum ledgers as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [136-pr-skip-cached-category-thread-list-fetches.md](136-pr-skip-cached-category-thread-list-fetches.md), [227-pr-cache-direct-category-thread-acquisition.md](227-pr-cache-direct-category-thread-acquisition.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md), [590-pr-validate-forum-thread-collection-site-ownership.md](590-pr-validate-forum-thread-collection-site-ownership.md), and [592-pr-validate-forum-category-collection-site-ownership.md](592-pr-validate-forum-category-collection-site-ownership.md) establish category thread-list acquisition, direct thread-detail acquisition, category field shape, direct thread site type validation, collection site ownership, and adjacent retained-state hardening as active operational boundaries.

This is not a duplicate of Issue 447. Issue 447 validates only the optional category field shape and explicitly leaves category/site identity consistency as a separate concern. This slice validates a well-typed `ForumCategory` whose retained `category.site` does not match the thread's retained `site`.

This is not a duplicate of Issue 590. Issue 590 validates `ForumThreadCollection` entries against the collection site. This slice validates a single `ForumThread` object's optional parent category, even when no collection wrapper is involved.

This is not a duplicate of forum thread direct-site, URL-site, reply-site, posts-cache, post/revision, or category collection ownership slices. Those validate other parent fields, call-site routing, cache wrappers, or collection entries. This slice validates the thread-to-category retained-site relationship at the public constructor boundary.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_thread_category_belongs_to_site(...)`.
- Validate non-null `ForumThread.category.site` against `ForumThread.site` during `ForumThread.__post_init__`.
- Add a focused constructor regression where a valid `ForumCategory` from a different `Site` object but the same client is rejected.
- Adjust three existing mixed-site post/revision batch tests so their synthetic other-site thread is uncategorized, preserving their intended prefetch guard without constructing an invalid thread/category pair.
- Preserve valid same-site categories, `category=None`, category thread-list parsing, direct thread-detail parsing, thread post caches, post-list batch guards, revision batch guards, and adjacent forum behavior.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(site=site_a, category=ForumCategory(site=site_b, ...))` must raise `ValueError("category must belong to the thread site")` before storing the cross-site category. |
| R2 | The mismatch check must compare retained `Site` object identity, not merely client identity, IDs, unix names, titles, domains, or login state. |
| R3 | `ForumThread(site=site_a, category=ForumCategory(site=site_a, ...))` must remain valid. |
| R4 | `ForumThread(category=None)` must remain valid for uncategorized direct thread records. |
| R5 | Existing malformed category diagnostics from Issue 447 must keep their current precedence. |
| R6 | Category thread-list parsing, direct thread-detail parsing, lazy `ForumCategory.threads`, direct and batched thread acquisition, lazy `ForumThread.posts`, reply workflows, post-list batch guards, revision batch guards, and adjacent forum workflows must remain unchanged. |
| R7 | Full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cross-site parent categories fail at forum-thread construction. | `TestForumThreadBasic.test_init_rejects_category_from_different_site` failed RED with `DID NOT RAISE`, then passed GREEN after `ForumThread.__post_init__` called the category site preflight. | Accepting the cross-site category, storing it for later traversal, or deferring the mismatch to category/thread/post APIs rejects this local completion claim. | `ForumThread.__post_init__` | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | The regression proves site ownership rather than client ownership. | The test builds `other_site` with the same `Client` object as the thread site but a different `Site` object, and the category is still rejected. | Only comparing `category.site.client`, site IDs, unix names, domains, titles, or login state rejects this local completion claim. | Thread category ownership rule | `tests/unit/test_forum_thread.py` |
| R3 | Valid same-site categorized threads remain accepted. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 151 tests with existing same-site forum-thread fixtures and parser-created thread records. | Rejecting valid same-site categories, copying or replacing the category, or changing parser-created category relationships rejects this local completion claim. | Forum thread constructor and parser-created records | `tests/unit/test_forum_thread.py` |
| R4 | Uncategorized direct thread records remain accepted. | Adjacent post and revision mixed-site tests passed after their synthetic other-site threads used `category=None`; direct-detail fixtures using uncategorized threads also remained green. | Rejecting `category=None` or requiring every direct thread-detail record to carry a category rejects this local completion claim. | Direct thread records | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | Existing malformed category diagnostics remain stable. | `uv run pytest tests/unit/test_forum_thread.py -q` passed 151 tests, including malformed category cases from Issue 447. | Raising the ownership message for non-`ForumCategory` values or changing `ValueError("category must be a ForumCategory or None")` rejects this local completion claim. | Constructor validation precedence | `tests/unit/test_forum_thread.py` |
| R6 | Adjacent forum workflows remain green. | Adjacent forum category/post/post-revision coverage passed 396 tests, and full unit coverage passed 2777 tests. | Regressing category thread-list acquisition, direct thread-detail acquisition, lazy category/thread/post behavior, reply behavior, post-list batching, revision batching, or forum category behavior rejects this local completion claim. | Adjacent forum workflows | `tests/unit` |
| R7 | Repository quality gates remain green. | Full unit coverage passed 2777 tests; full ruff check, full format check, mypy, pyright, and `git diff --check` passed. | Any unreported test, lint, format, type, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R8 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic `Site`, `Client`, `ForumCategory`, and `ForumThread` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page source, private forum content, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `96f66ae fix(forum_thread): validate category site`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_category_from_different_site -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: the same command passed after the category site preflight was added.
- Forum thread module coverage: `uv run pytest tests/unit/test_forum_thread.py -q` passed 151 tests.
- Adjacent forum category/post/post-revision coverage: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 396 tests.
- `uv run pytest tests/unit -q` passed 2777 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(site=site_a, category=ForumCategory(site=site_b, ...))` raises `ValueError("category must belong to the thread site")` when `site_a is not site_b`, even if both sites share the same client object.
- Valid same-site categories remain accepted.
- `category=None` remains accepted.
- Existing malformed category values still raise `ValueError("category must be a ForumCategory or None")`.
- Category thread-list parsing, direct thread-detail parsing, direct and batched thread acquisition, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply workflows, post-list batch guards, revision batch guards, and adjacent forum behavior remain green.
- The new tests use unit-level synthetic state only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread.category` is the optional parent-category context behind browser-free category inventories, cached category-thread reuse, generated moderation ledgers, forum migration audits, and downstream post/revision traversal. Parser paths already create categorized threads from the owning `ForumCategory`; constructor ownership validation keeps generated fixtures, adapters, ledgers, and rehydrated records from pairing a thread with another site's category. The check follows existing retained-owner patterns by using object identity for the retained `Site` and does not add network lookups or ambiguous cross-site equivalence rules.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid `ForumCategory` from another `Site` object could be stored as a thread's category without rejection.
- Existing local drafts covered category field shape, direct thread site type validation, collection thread ownership, category collection ownership, thread posts-cache ownership, and adjacent forum post/revision ownership, but did not cover direct `ForumThread.category` retained-site ownership.
- This slice only validates constructor-time optional category site ownership. It does not change category thread-list request construction, direct thread-detail requests, parser selectors, thread ID parsing, title/description parsing, created metadata parsing, post-count parsing, cached duplicate behavior, `find(...)`, `ForumCategory.threads`, `ForumCategory.reload_threads()`, `ForumThread.posts`, `ForumThread.reply(...)`, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, private forum content, and live Wikidot account details out of upstream discussion.

## Additional Notes

The check intentionally rejects a different `Site` object even when both sites share the same client, because neighboring retained-owner rules use object identity rather than remote equality guesses. Direct thread-detail records that do not have category context remain valid with `category=None`.
