# PR Draft: Validate Forum Post Revision Collection Post Ownership

## Summary

`ForumPostRevisionCollection` validates explicit collection parent-post types, validates its `revisions` container and entries, each `ForumPostRevision` validates its own retained `post`, and revision HTML acquisition revalidates mutated target revision post/thread state before requests. The public collection constructor still did not ensure contained revisions all belonged to the effective collection post. A caller could construct `ForumPostRevisionCollection(post_a, [revision_from_post_b])`; a caller could also rely on parent inference with `ForumPostRevisionCollection(post=None, revisions=[revision_from_post_a, revision_from_post_b])`, which inferred `post_a` from the first revision while retaining a valid revision from another post.

This change validates revision entry ownership at the public `ForumPostRevisionCollection.__init__` boundary after entry validation and effective post selection but before list state is stored. Revisions whose retained `revision.post` does not match the collection post, thread, and site now raise `ValueError("revisions must belong to the collection post")`. Valid explicit same-post collections, valid inferred same-post collections, empty no-parent collections, `find(...)`, `find_by_rev_no(...)`, direct and batched revision-list parsing, cached duplicate revision reuse, lazy `ForumPost.revisions`, revision HTML acquisition, and adjacent forum category/thread/post workflows remain unchanged.

## Outcome

Forum post revision collections reject different-post revision entries before local collection state can represent one post while storing another post's revisions.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration or moderation ledgers, cached post revision lists, lazy `ForumPost.revisions`, revision HTML capture, duplicate cached revision reuse, or local tests that construct `ForumPostRevisionCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision acquisition, duplicate revision reuse, revision HTML capture, lazy revision access, and generated forum ledgers as practical workflow surfaces. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [535-pr-preserve-empty-forum-post-revision-parent.md](535-pr-preserve-empty-forum-post-revision-parent.md), [580-pr-validate-forum-post-revision-thread.md](580-pr-validate-forum-post-revision-thread.md), [581-pr-validate-forum-post-revision-html-thread.md](581-pr-validate-forum-post-revision-html-thread.md), [582-pr-validate-forum-post-revision-html-target-post-thread.md](582-pr-validate-forum-post-revision-html-target-post-thread.md), and [583-pr-reject-mixed-site-forum-post-revision-batches.md](583-pr-reject-mixed-site-forum-post-revision-batches.md) establish revision acquisition, HTML acquisition, parser diagnostics, response diagnostics, duplicate cache reuse, collection shape, retained parent validation, and action/read-boundary target validation as active operational boundaries.

This slice is not a duplicate of those issues. Issue 421 validates only the collection's `revisions` container and entries. Issue 473 validates direct non-`None` `ForumPostRevisionCollection.post` type. Issue 535 preserves the empty `post=None` state and explicitly left comparing the collection parent identity with each contained revision out of scope. Issue 445 validates each individual `ForumPostRevision.post` field type. Issues 580, 581, and 582 validate later revision acquisition and HTML acquisition boundaries for mutated or mismatched target state. Issue 583 rejects mixed-site multi-post revision batches. None validates a valid `ForumPostRevision` entry whose retained `revision.post` is individually valid but does not match the collection post selected explicitly or inferred from the first revision.

No upstream issue was filed from this local workspace.

## Changes

- Add a forum-post-revision collection ownership preflight at `ForumPostRevisionCollection.__init__`.
- Reject explicit different-post revision entries with `ValueError("revisions must belong to the collection post")`.
- Reject inferred-parent mixed-post revision collections with the same diagnostic.
- Keep the later HTML/read-time mutation guards by updating their tests to append mismatched revisions after constructing valid empty collections.
- Preserve explicit valid parents, inferred valid parents, empty no-parent collections, valid revision lists, lookup, revision-list parsing, revision HTML acquisition, lazy `ForumPost.revisions`, duplicate cached revision reuse, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum post revision parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection(post_a, [revision_from_post_b])` must reject the different-post revision with `ValueError("revisions must belong to the collection post")` before storing collection list state. |
| R2 | `ForumPostRevisionCollection(post=None, revisions=[revision_from_post_a, revision_from_post_b])` must infer `post_a` from the first revision and reject the second different-post revision with the same diagnostic before storing collection list state. |
| R3 | Valid explicit same-post revision collections, valid inferred same-post revision collections, and empty no-parent collections must remain valid. |
| R4 | Existing HTML/source-time mutation validation, `find(...)`, `find_by_rev_no(...)`, direct and batched revision-list acquisition, parser diagnostics, cached duplicate revision reuse, lazy `ForumPost.revisions`, revision HTML acquisition, and adjacent forum category/thread/post workflows must remain unchanged. |
| R5 | Focused RED/GREEN, forum-post-revision module coverage, adjacent forum module coverage, full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Explicit different-post revision entries fail at the public collection constructor boundary. | `TestForumPostRevisionCollectionInit.test_init_rejects_revision_from_different_post` failed RED with `DID NOT RAISE`, then passed GREEN with `ValueError("revisions must belong to the collection post")`. | Accepting the different-post revision, storing a collection for `post_a` that contains a revision retained from `post_b`, or deferring failure to HTML/cache code rejects this local completion claim. | `ForumPostRevisionCollection.__init__` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Inferred-parent mixed-post revision entries fail at the same constructor boundary. | `TestForumPostRevisionCollectionInit.test_init_rejects_mixed_post_revisions_when_post_is_inferred` failed RED with `DID NOT RAISE`, then passed GREEN with the same diagnostic. | Inferring `post_a` from the first revision while storing a revision retained from `post_b`, accepting mixed inferred collections, or rejecting all inferred collections rejects this local completion claim. | `ForumPostRevisionCollection.__init__` | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R3 | Valid revision collection construction semantics stay green. | `TestForumPostRevisionCollectionInit` passed 18 tests and `tests/unit/test_forum_post_revision.py` passed 129 tests after the ownership preflight. | Rejecting valid same-post explicit collections, valid same-post inferred collections, empty no-parent collections, or normal post inference rejects this local completion claim. | Forum post revision collections | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing later mutation validation and adjacent forum workflows remain green. | The two older read-boundary tests now construct valid empty collections and append mismatched revisions after construction; adjacent forum category/thread/post/revision coverage passed 534 tests, and the full unit suite passed 2701 tests. | Losing later mutation guards, regressing revision-list acquisition, parser diagnostics, cached duplicate revision reuse, lazy `ForumPost.revisions`, revision HTML acquisition, forum post source/edit workflows, forum thread/category behavior, or forum post behavior rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | Repository quality gates pass in the local dependency environment. | Full `ruff check`, `ruff format --check`, `mypy`, full `pyright`, and `git diff --check` passed. Full pyright reported 0 errors, 0 warnings, and 0 informations; full format saw 87 files already formatted; full mypy found no issues in 87 source files. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No live auth material or private state is needed to prove the behavior. | The regressions use synthetic valid `ForumPost` and `ForumPostRevision` objects; this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page/forum content from real sites, forum post source text from real sites, revision HTML from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `395d504 fix(forum_post_revision): validate revision collection post ownership`.

- RED explicit target-post ownership: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_revision_from_different_post -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused explicit ownership regression: the same focused command passed 1 test after the explicit branch fix.
- RED inferred target-post ownership: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_mixed_post_revisions_when_post_is_inferred -q` failed before the inferred-branch fix with `DID NOT RAISE`.
- GREEN focused ownership coverage: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_revision_from_different_post tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_mixed_post_revisions_when_post_is_inferred -q` passed 2 tests.
- Constructor coverage: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit -q` passed 18 tests.
- Forum post revision module coverage: `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 129 tests.
- Adjacent forum category/thread/post/revision tests: `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 534 tests.
- `uv run pytest tests/unit -q` passed 2701 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevisionCollection(post_a, [revision_from_post_b])` raises `ValueError("revisions must belong to the collection post")` before storing collection list state.
- `ForumPostRevisionCollection(post=None, revisions=[revision_from_post_a, revision_from_post_b])` raises the same diagnostic after inferring the first revision's post and before storing collection list state.
- `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[])`, `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[same_post_revision])`, `ForumPostRevisionCollection(post=None, revisions=[same_post_revision])`, and `ForumPostRevisionCollection(post=None, revisions=[])` remain valid.
- Existing later mutation validation, `find(...)`, `find_by_rev_no(...)`, direct and batched revision-list acquisition, parser diagnostics, cached duplicate revision reuse, lazy `ForumPost.revisions`, revision HTML acquisition, and adjacent forum category/thread/post behavior remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevisionCollection.post` and each retained `ForumPostRevision.post` should describe the same owning post for browser-free forum edit-history reads, generated moderation ledgers, migration audits, cached post revision lists, lazy revision access, revision HTML capture, and duplicate cached revision reuse. Parser paths already create revisions from the owning post, and same-post duplicate cache helpers replace revision parents when copying cached revisions; constructor ownership validation keeps mismatched rehydrated records, fixtures, or generated ledgers from silently carrying another post's revisions under the collection post.

## Local Evidence, Not For Upstream Paste

- The explicit RED failure showed a valid revision from another post could be accepted by `ForumPostRevisionCollection(post, [revision])` without ownership rejection.
- The inferred RED failure showed `ForumPostRevisionCollection(post=None, revisions=[revision_from_post_a, revision_from_post_b])` could infer a collection post from the first revision while retaining another post's revision.
- Existing local drafts covered revision-list acquisition, parser diagnostics, response-body diagnostics, lookup validation, collection revisions/entry validation, direct revision post validation, explicit collection-post validation, empty no-parent handling, later HTML/read-time retained parent validation, later target ownership validation, and mixed-site revision batching, but did not compare each valid `ForumPostRevision.post` to the effective collection post during construction.
- This slice only validates forum-post-revision collection target-post ownership at collection initialization. It does not change revision-list parsing, collection lookup semantics, lazy revision cache invalidation, HTML response parsing, forum post source/edit behavior, live site behavior, authentication semantics, or parser selectors.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page/forum source text from real sites, revision HTML from real sites, and private site data out of upstream discussion.

## Additional Notes

The ownership check intentionally requires matching post ID, matching thread ID, and the same retained site object. This matches the adjacent forum ownership preflight style and allows duplicate post objects representing the same post on the same thread/site, while still rejecting different-post, different-thread, and different-site revisions. It does not coerce post-like objects, compare by title, infer a collection post from a later revision, validate a post's cached revision collection ownership, verify remote post membership, or change live client authentication; those are separate parser, lookup, cache, and workflow concerns.
