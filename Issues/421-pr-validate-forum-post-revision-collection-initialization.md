# PR Draft: Validate Forum Post Revision Collection Initialization

## Summary

`ForumPostRevisionCollection` documents `revisions` as `list[ForumPostRevision] | None`, but its constructor accepted malformed containers and arbitrary list entries. A caller could construct `ForumPostRevisionCollection(post, revisions=False)`, which silently became an empty collection, or `ForumPostRevisionCollection(post, revisions="9001")`, `ForumPostRevisionCollection(post, revisions=("9001",))`, and `ForumPostRevisionCollection(post, revisions=[None])`, which could store malformed collection entries or raise incidental low-level exceptions.

This change validates constructor input before storing entries. Non-list non-`None` `revisions` values now raise `ValueError("revisions must be a list or None")`; list entries that are not `ForumPostRevision` now raise `ValueError("revisions list entries must be ForumPostRevision")`. `revisions=None`, empty collections, valid `ForumPostRevision` lists, post inference from a valid first revision, iteration, `find(...)`, `find_by_rev_no(...)`, direct revision acquisition, lazy `ForumPost.revisions`, multi-post revision acquisition, cached direct revision reuse, duplicate post-revision reuse, and `get_htmls()` mutation guarding remain unchanged.

## Outcome

Callers cannot silently create malformed `ForumPostRevisionCollection` instances through the public constructor, while existing forum post revision fetch, parser, cache, search, and HTML acquisition behavior remains intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision HTML capture, duplicate revision cache reuse, direct `ForumPostRevisionCollection.acquire_all(post)`, lazy `ForumPost.revisions`, multi-post `ForumPostRevisionCollection.acquire_all_for_posts(...)`, or local fixtures that construct revision collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision history and revision HTML as practical workflow surfaces. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), and [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md) establish forum post revision acquisition, HTML acquisition, cache reuse, duplicate reuse, response diagnostics, parser diagnostics, caller-provided post validation, loaded-collection mutation validation, and search-key validation as active operational boundaries. Adjacent constructor-hardening drafts [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), and [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md) establish the local state-integrity pattern for collection constructors.

Those prior slices are not duplicates. Issues042, 056, 057, 058, 131, 135, 142, 143, 146, 172, 180, 217, 229, 263, 283, 284, 285, 300, and 329 covered fetching, retry behavior, cache reuse, duplicate revision reuse, lazy HTML failure visibility, parser diagnostics, response diagnostics, and edit-cache invalidation; Issue364 validated caller-provided post inputs before revision acquisition; Issue366 validated loaded collection entries before `get_htmls()` performs network work; Issue377 validated search keys after a collection already exists. None of them validates the `ForumPostRevisionCollection(post, revisions=...)` constructor itself before malformed revision entries become stored list state.

## Related Issue

Builds directly on [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), and the adjacent constructor validation pattern from [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), and [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPostRevisionCollection.__init__(..., revisions=...)` validation.
- Preserve `revisions=None` as an empty collection.
- Reject non-list non-`None` `revisions` with `ValueError("revisions must be a list or None")`.
- Reject non-`ForumPostRevision` list entries with `ValueError("revisions list entries must be ForumPostRevision")`.
- Preserve valid empty collections, valid `ForumPostRevision` entries, post inference, iteration, `find(...)`, `find_by_rev_no(...)`, direct revision acquisition, lazy `ForumPost.revisions`, multi-post acquisition, cached direct acquisition, duplicate post-revision reuse, and `get_htmls()` mutated-entry validation behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Forum post revision collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection(post, revisions=True)`, `False`, `"9001"`, `("9001",)`, and `9001` must raise `ValueError("revisions must be a list or None")` before storing collection entries. |
| R2 | `ForumPostRevisionCollection(post, revisions=[None])`, `[True]`, `["9001"]`, and `[{"id": 9001}]` must raise `ValueError("revisions list entries must be ForumPostRevision")` before storing collection entries. |
| R3 | `ForumPostRevisionCollection(post, revisions=None)`, `ForumPostRevisionCollection(post, revisions=[])`, and `ForumPostRevisionCollection(post, revisions=[valid_revision])` must remain valid, and `ForumPostRevisionCollection(post=None, revisions=[valid_revision])` must still infer the post from that revision. |
| R4 | Existing iteration, `find(...)`, `find_by_rev_no(...)`, direct revision acquisition, lazy `ForumPost.revisions`, multi-post revision acquisition, cached direct acquisition, duplicate post-revision reuse, revision HTML acquisition, forum post workflows, thread workflows, and category workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent forum revision/post/thread/category tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestForumPostRevisionCollectionInit.test_init_rejects_non_list_revisions` failed RED for `True`, `False`, `"9001"`, `("9001",)`, and `9001`, then passed GREEN after constructor validation was added. | Treating `False` as empty, accepting strings or tuples as revision lists, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | ForumPostRevisionCollection constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Non-`ForumPostRevision` constructor list entries fail at the public constructor boundary. | `TestForumPostRevisionCollectionInit.test_init_rejects_non_revision_entries` failed RED for `None`, `True`, `"9001"`, and `{"id": 9001}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized revision records, or fixture stand-ins as stored revisions rejects this local completion claim. | ForumPostRevisionCollection constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid constructor inputs remain green. | Existing empty-list and valid-revision initialization tests passed in the focused 14-test run and the 81-test forum post revision module run. | Rejecting `None`, empty valid lists, valid revision lists, normal post inference, iteration, ID lookup, or revision-number lookup rejects this local completion claim. | ForumPostRevisionCollection constructor and methods | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing forum revision and adjacent workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 81 tests, forum revision/post/thread/category tests passed 274 tests, and full unit tests passed 1529 tests. | Regressing direct revision acquisition, lazy `ForumPost.revisions`, multi-post acquisition, cached direct acquisition, duplicate post-revision reuse, parser diagnostics, response diagnostics, ID/revision-number lookup, HTML acquisition, forum post source/edit workflows, thread workflows, or category workflows rejects this local completion claim. | Forum revision and adjacent forum workflows | `tests/unit/test_forum_post_revision.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d20566a fix(forum_post_revision): validate revision collection initialization`.

- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_non_list_revisions -q` failed 5 tests before the container fix; `False`, strings, and tuples were accepted, while `True` and `9001` leaked incidental `TypeError`.
- GREEN: the same focused command passed 5 tests after adding non-list validation.
- RED: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_non_revision_entries -q` failed 4 tests before the entry fix because malformed list entries were accepted and stored.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_non_list_revisions tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_non_revision_entries tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_with_post_and_empty_revisions tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_with_post_and_revisions tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionGetHtmls::test_get_htmls_rejects_non_revision_entries_before_fetch -q` passed 14 tests after adding entry validation and preserving mutated-entry `get_htmls()` validation.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py -q` passed 81 tests.
- `uv run --extra test pytest tests/unit/test_forum_post_revision.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py -q` passed 274 tests.
- `uv run --extra test pytest tests/unit -q` passed 1529 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `ForumPostRevisionCollection(post, revisions=True)`, `False`, `"9001"`, `("9001",)`, and `9001` raise `ValueError("revisions must be a list or None")`.
- `ForumPostRevisionCollection(post, revisions=[None])`, `[True]`, `["9001"]`, and `[{"id": 9001}]` raise `ValueError("revisions list entries must be ForumPostRevision")`.
- `ForumPostRevisionCollection(post, revisions=None)`, `ForumPostRevisionCollection(post, revisions=[])`, and `ForumPostRevisionCollection(post, revisions=[valid_revision])` continue to work.
- `ForumPostRevisionCollection(post=None, revisions=[valid_revision])` still infers the post from that revision.
- Existing iteration, `find(...)`, `find_by_rev_no(...)`, direct revision acquisition, lazy `ForumPost.revisions`, multi-post revision acquisition, cached direct acquisition, duplicate post-revision reuse, `get_htmls()`, forum post source/edit behavior, thread behavior, and category behavior remains green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevisionCollection` is the stored object shape behind browser-free forum edit-history reads, direct revision-list acquisition, lazy `ForumPost.revisions`, multi-post revision acquisition, revision HTML capture, duplicate post-revision cache reuse, and revision ID/revision-number lookup. Constructor validation keeps malformed local state out of the collection while preserving existing fetch, parser, cache, search, and HTML acquisition behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free forum post revision reads, duplicate revision list reuse, revision HTML fetches, lazy forum post revision reads, and tests that seed revision collections directly.
- Existing local drafts covered forum post revision fetch retry behavior, duplicate revision and revision-HTML reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct acquisition, post input validation, loaded-collection mutation validation, and ID/revision-number search validation, but did not cover the `ForumPostRevisionCollection(post, revisions=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was treated as empty, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, post inference, and adjacent forum workflows.
- This slice only validates forum post revision collection constructor input. It does not change direct revision acquisition, multi-post revision acquisition, parser selectors, revision ID parsing, revision timestamp parsing, revision user parsing, revision HTML content parsing, cached duplicate behavior, `find(...)`, `find_by_rev_no(...)`, `get_htmls()` behavior beyond preserving its mutated-entry guard, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed revision-like objects and test mocks in `ForumPostRevisionCollection`. Callers should construct real `ForumPostRevision` entries before storing them in a revision collection.
