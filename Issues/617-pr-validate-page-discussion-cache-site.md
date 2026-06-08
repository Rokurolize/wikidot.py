# PR Draft: Validate Page Discussion Cache Site

## Summary

`Page._discussion` is the optional cached `ForumThread` behind `Page.discussion`. Issue 512 validates that the direct cache slot contains either `None` or a `ForumThread`, and Issue 567 validates a mutated `Page.site` before uncached discussion reads. One retained-cache ownership gap remained: direct `Page(...)` construction could combine `site=site_a` with a valid cached `ForumThread(site=site_b, ...)`, so `page.discussion` could return a thread whose retained site did not match the page that exposed it.

This change validates cached discussion site ownership during `Page.__post_init__`, after existing site and `_discussion` type checks and before storing the checked discussion state. A non-null cached discussion must retain the same `Site` object as the owning page. Mismatches raise `ValueError("page.discussion must belong to the page site")`. Valid cached same-site discussions, `_discussion=None`, checked no-discussion state, lazy discussion acquisition, discussion response diagnostics, and adjacent forum-thread workflows remain unchanged.

## Outcome

Directly constructed `Page` records can no longer expose cached discussion threads from a different retained site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct browser-free page inventories, generated page-to-discussion ledgers, discussion migration tooling, fixtures, adapters, or serialized and rehydrated page records before traversing forum discussions.

## Current Evidence

Local rollout-backed drafts repeatedly identify page discussion reads, forum-thread records, and cached object reuse as practical workflow surfaces. Existing drafts [045-pr-retry-page-discussion-fetch.md](045-pr-retry-page-discussion-fetch.md), [192-pr-page-auxiliary-fetch-site-context.md](192-pr-page-auxiliary-fetch-site-context.md), [219-pr-page-auxiliary-response-body-context.md](219-pr-page-auxiliary-response-body-context.md), [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md), [335-pr-page-auxiliary-response-body-type-context.md](335-pr-page-auxiliary-response-body-type-context.md), [512-pr-validate-page-constructor-discussion-cache.md](512-pr-validate-page-constructor-discussion-cache.md), [567-pr-validate-page-discussion-site.md](567-pr-validate-page-discussion-site.md), [590-pr-validate-forum-thread-collection-site-ownership.md](590-pr-validate-forum-thread-collection-site-ownership.md), and adjacent page cache ownership drafts [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md), [598-pr-validate-page-votes-cache-ownership.md](598-pr-validate-page-votes-cache-ownership.md), [599-pr-validate-page-files-cache-ownership.md](599-pr-validate-page-files-cache-ownership.md), and [600-pr-validate-page-source-cache-ownership.md](600-pr-validate-page-source-cache-ownership.md) establish discussion cache state, read-time site preflights, forum-thread site ownership, and retained cache-owner validation as active operational boundaries.

This is not a duplicate of Issue 512. Issue 512 validates `_discussion` object shape and `_discussion_checked` boolean shape. It does not validate that a valid cached `ForumThread` belongs to the same retained site as the page.

This is not a duplicate of Issue 567. Issue 567 validates a mutated malformed `Page.site` before uncached discussion reads. This slice validates constructor-seeded cached discussion ownership while the page and thread both retain valid `Site` objects.

This is not a duplicate of Issue 590. Issue 590 validates `ForumThreadCollection` entries against the collection site. This slice covers the separate `Page._discussion` cache slot, which stores one `ForumThread` and has no collection wrapper.

This is not a duplicate of adjacent page source/revision/vote/file cache ownership slices. Those validate page-owned cache wrappers with explicit page parents. This slice validates the discussion thread's retained site because a Wikidot discussion thread is site-scoped and the page cache does not carry a thread-to-page owner link.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_discussion_cache_belongs_to_page_site(...)`.
- Validate non-null `Page._discussion.site` against `Page.site` during `Page.__post_init__`.
- Add a focused constructor regression where a valid `ForumThread` from a different `Site` object but the same client is rejected.
- Preserve valid same-site cached discussions, missing discussion cache, checked no-discussion state, and adjacent page/forum behavior.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(site=site_a, _discussion=ForumThread(site=site_b, ...), _discussion_checked=True)` must raise `ValueError("page.discussion must belong to the page site")` before the cached thread can be exposed. |
| R2 | The mismatch check must compare retained `Site` object identity, not merely client identity, IDs, unix names, titles, domains, or login state. |
| R3 | `Page(site=site_a, _discussion=ForumThread(site=site_a, ...), _discussion_checked=True)` must remain valid and `page.discussion` must return the cached thread without fetching. |
| R4 | `_discussion=None` with `_discussion_checked=False` and `_discussion_checked=True` must remain valid. |
| R5 | Existing malformed `_discussion` and `_discussion_checked` diagnostics must keep their current precedence. |
| R6 | Lazy discussion reads, response diagnostics, generated thread-ID parsing, direct forum-thread acquisition, forum-thread collection behavior, page constructor behavior, and adjacent page/forum workflows must remain unchanged. |
| R7 | Full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Cross-site cached discussions fail at page construction. | `TestPageInit.test_init_rejects_discussion_cache_from_different_site` failed RED with `DID NOT RAISE`, then passed GREEN after `Page.__post_init__` called the discussion cache site preflight. | Accepting the cross-site cached thread, exposing it through `page.discussion`, or deferring the mismatch to later discussion traversal rejects this local completion claim. | `Page.__post_init__` | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | The regression proves site ownership rather than client ownership. | The test builds `other_site` with the same `Client` object as the page site but a different `Site` object, and the cache is still rejected. | Only comparing `discussion.site.client`, site IDs, unix names, domains, titles, or login state rejects this local completion claim. | Discussion cache ownership rule | `tests/unit/test_page_constructor.py` |
| R3 | Valid same-site cached discussions remain accepted. | `TestPageInit.test_init_accepts_valid_optional_discussion` passed in focused and constructor runs and asserts `page_with_discussion.discussion == discussion`. | Rejecting a valid same-site thread, copying/replacing the cached thread, or fetching despite checked cache state rejects this local completion claim. | Page discussion cache access | `tests/unit/test_page_constructor.py` |
| R4 | Missing and checked no-discussion cache states remain valid. | The same valid optional discussion test passed and asserts default unchecked `_discussion is None`, checked no-discussion `_discussion_checked is True`, and `discussion is None`. | Rejecting `_discussion=None`, treating checked no-discussion as malformed, or changing lazy availability rejects this local completion claim. | Page discussion cache state | `tests/unit/test_page_constructor.py` |
| R5 | Existing malformed cache diagnostics remain stable. | `uv run pytest tests/unit/test_page_constructor.py -q` passed 169 tests, including malformed `_discussion` and `_discussion_checked` cases. | Raising the ownership message for non-`ForumThread` values or changing checked-flag diagnostics rejects this local completion claim. | Constructor validation precedence | `tests/unit/test_page_constructor.py` |
| R6 | Adjacent page and forum workflows remain green. | Page constructor coverage passed 169 tests, page module coverage passed 301 tests, forum thread/category coverage passed 252 tests, and full unit coverage passed 2776 tests. | Regressing lazy discussion reads, response diagnostics, forum-thread parsing, forum-thread collections, page source/revision/vote/file caches, or site workflows rejects this local completion claim. | Adjacent workflows | `tests/unit` |
| R7 | Repository quality gates remain green. | Full unit coverage passed 2776 tests; full ruff check, full format check, mypy, pyright, and `git diff --check` passed. | Any unreported test, lint, format, type, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R8 | No live auth material or private state is needed to prove the behavior. | The regression uses synthetic `Site`, `Client`, `User`, and `ForumThread` objects; this draft contains no credentials, cookies, auth JSON, raw account data, raw response bodies, private usernames, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page source, private forum content, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `3920654 fix(page): validate discussion cache site`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_discussion_cache_from_different_site -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: the same command passed after the discussion cache site preflight was added.
- Page constructor coverage: `uv run pytest tests/unit/test_page_constructor.py -q` passed 169 tests.
- Page workflow coverage: `uv run pytest tests/unit/test_page.py -q` passed 301 tests.
- Adjacent forum workflow coverage: `uv run pytest tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q` passed 252 tests.
- `uv run pytest tests/unit -q` passed 2776 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(site=site_a, _discussion=ForumThread(site=site_b, ...), _discussion_checked=True)` raises `ValueError("page.discussion must belong to the page site")` when `site_a is not site_b`, even if both sites share the same client object.
- Valid same-site cached discussions remain accepted and `page.discussion` returns the cached `ForumThread`.
- `_discussion=None` remains valid for both unchecked lazy state and checked no-discussion state.
- Existing malformed `_discussion` values still raise `ValueError("page.discussion must be ForumThread or None")`.
- Existing malformed `_discussion_checked` values still raise `ValueError("page.discussion_checked must be a boolean")`.
- Lazy discussion reads, no-discussion checked-state behavior, page discussion retry and response diagnostics, direct forum-thread acquisition, forum-thread collection behavior, and adjacent page cache ownership checks remain green.
- The new tests use unit-level synthetic state only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`Page.discussion` is a page-owned cache surface even though the retained `ForumThread` is site-scoped. Parser and lazy acquisition paths already construct the thread from the page's site; constructor ownership validation keeps generated fixtures, adapters, ledgers, and rehydrated records from pairing a page with another site's cached discussion thread. The check follows existing retained-owner patterns by using object identity for the retained `Site` and does not add network lookups or ambiguous cross-site equivalence rules.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed a valid `ForumThread` from another `Site` object could be stored as a page discussion cache without rejection.
- Existing local drafts covered discussion cache shape, read-time page-site validation, forum-thread site validation, forum-thread collection site ownership, and page source/revision/vote/file cache ownership, but did not cover direct `Page._discussion` retained-site ownership.
- This slice only validates constructor-time cached discussion site ownership. It does not change page construction scalar fields, discussion response parsing, generated thread-ID parsing, direct forum-thread acquisition, forum-thread collection semantics, source/revision/file/vote behavior, live site behavior, or authentication semantics for valid sites.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private response data, private-message content, private forum content, and live Wikidot account details out of upstream discussion.

## Additional Notes

The check intentionally rejects a different `Site` object even when both sites share the same client, because the neighboring page cache and forum collection ownership rules use retained owner object identity rather than remote equality guesses.
