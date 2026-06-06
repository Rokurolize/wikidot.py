# PR Draft: Validate Forum Post Revision Collection Post Field

## Summary

`ForumPostRevisionCollection` stores the optional explicit parent `ForumPost` used by browser-free forum edit-history reads, lazy `ForumPost.revisions`, duplicate cached post-revision list reuse, revision HTML acquisition, generated migration or audit ledgers, local fixtures, and rehydrated forum revision state. Earlier local slices validated revision acquisition inputs, loaded collection entries, lookup keys, optional HTML controls, collection revision containers and entries, direct `ForumPostRevision.post`, direct revision identity fields, direct revision creator/time fields, and direct revision HTML assignment, but `ForumPostRevisionCollection(post=..., revisions=...)` still accepted malformed explicit parent posts such as booleans, strings, dictionaries, and arbitrary objects.

This change validates non-`None` `ForumPostRevisionCollection.post` constructor arguments before storing collection state. Malformed explicit values now raise `ValueError("post must be a ForumPost")`. The existing `post=None` behavior remains valid: collections can still infer the parent from a valid first revision, and empty no-parent collections still expose `post is None`. Valid `ForumPost` parents, empty revision lists, valid `ForumPostRevision` lists, iteration, lookup, direct and batched revision acquisition, revision HTML acquisition, lazy `ForumPost.revisions`, duplicate cached revision reuse, parser diagnostics, direct revision field validation, and adjacent forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-post-revision collections with malformed explicit parent-post state, while parser-created, fixture-created, cached-duplicate, inferred-parent, and manually created valid revision collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision HTML capture, duplicate revision cache reuse, direct `ForumPostRevisionCollection.acquire_all(post)`, lazy `ForumPost.revisions`, multi-post `ForumPostRevisionCollection.acquire_all_for_posts(...)`, or local tests that construct `ForumPostRevisionCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revisions as a practical workflow surface. Existing drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [146-pr-surface-lazy-forum-post-revision-html-failures.md](146-pr-surface-lazy-forum-post-revision-html-failures.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [180-pr-forum-post-revision-lazy-html-context.md](180-pr-forum-post-revision-lazy-html-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [284-pr-forum-post-revision-timestamp-context.md](284-pr-forum-post-revision-timestamp-context.md), [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [300-pr-forum-post-revision-html-content-context.md](300-pr-forum-post-revision-html-content-context.md), [329-pr-forum-post-revision-response-body-type-context.md](329-pr-forum-post-revision-response-body-type-context.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), and [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md) establish revision acquisition, HTML acquisition, parser diagnostics, response diagnostics, duplicate cache reuse, collection entry validation, lookup validation, direct revision parent validation, and direct revision field validation as active operational boundaries.

Those prior slices are not duplicates. Issue 421 validates only the collection's `revisions` container and entries while preserving `ForumPostRevisionCollection(revisions=[valid_revision])` inference. Issue 445 validates the `post` field on individual `ForumPostRevision` records, not the collection parent. Issues 463 and 464 validate direct revision identity, creator, and timestamp fields. Issue 364 validates caller-provided `post` inputs for acquisition APIs, and Issue 366 validates mutated collection entries before source/HTML acquisition. None validates direct non-`None` `ForumPostRevisionCollection(post=...)` construction before malformed parent-post state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), and the adjacent optional collection parent validation pattern from [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md) and [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate non-`None` `ForumPostRevisionCollection.post` values at constructor initialization.
- Reject malformed explicit parent-post values with `ValueError("post must be a ForumPost")`.
- Preserve `post=None` inference, empty no-parent construction, valid empty revision collections, valid `ForumPostRevision` lists, iteration, lookup, parser-created collections, duplicate cached revision reuse, direct and batched acquisition, revision HTML acquisition, lazy `ForumPost.revisions`, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum post revision parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection(post=True)`, `"5001"`, `{"id": 5001}`, and `object()` must raise `ValueError("post must be a ForumPost")` when `revisions` is otherwise valid. |
| R2 | `ForumPostRevisionCollection(revisions=[valid_revision])` must still infer the post from the first revision, and `ForumPostRevisionCollection(post=None, revisions=[])` must remain constructible with `post is None`. |
| R3 | Valid `ForumPost` parent values, valid empty revision lists, valid `ForumPostRevision` lists, iteration, `find(...)`, `find_by_rev_no(...)`, direct and batched revision acquisition, revision HTML acquisition, lazy `ForumPost.revisions`, duplicate cached revision reuse, parser diagnostics, direct revision field validation, and adjacent forum workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-post-revision tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent posts fail at the public constructor boundary. | `TestForumPostRevisionCollectionInit.test_init_rejects_malformed_posts` failed RED for 4 malformed non-`None` values because the constructor did not raise, then passed GREEN after post validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting revision collections with malformed explicit parent state rejects this local completion claim. | ForumPostRevisionCollection constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Optional no-parent and inference semantics stay green. | Existing empty initialization and post-inference tests passed in the 112-test forum-post-revision module run. | Rejecting `post=None`, losing parent inference from the first valid revision, or changing empty no-parent collections away from `post is None` rejects this local completion claim. | ForumPostRevisionCollection constructor | `tests/unit/test_forum_post_revision.py` |
| R3 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 112 tests, adjacent forum workflow tests passed 432 tests, and full unit tests passed 1907 tests. | Regressing direct revision acquisition, lazy `ForumPost.revisions`, multi-post acquisition, cached direct acquisition, duplicate post-revision reuse, parser diagnostics, response diagnostics, search lookup, HTML acquisition, forum post source/edit workflows, forum category/thread behavior, or adjacent forum workflows rejects this local completion claim. | Forum revision and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, forum post source text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b373933 fix(forum_post_revision): validate revision collection post`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_malformed_posts -q` failed 4 tests before the fix; every malformed explicit `post` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `ForumPostRevisionCollection` explicit post validation was added.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 112 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 432 tests.
- `uv run pytest tests/unit -q` passed 1907 tests.
- `uv run ruff format src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `uv run mypy src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed forum-post-revision test file pass pyright together.

## Acceptance Criteria

- `ForumPostRevisionCollection(post=True)`, `"5001"`, `{"id": 5001}`, and `object()` raise `ValueError("post must be a ForumPost")`.
- `ForumPostRevisionCollection(revisions=[valid_revision])` still infers the post from the first valid revision.
- `ForumPostRevisionCollection(post=None, revisions=[])`, `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[])`, and `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[valid_revision])` remain valid.
- Existing valid `ForumPostRevision` lists, iteration, `find(...)`, `find_by_rev_no(...)`, direct and batched acquisition, revision HTML acquisition, lazy `ForumPost.revisions`, parser-side revision diagnostics, direct revision field validation, and duplicate cached revision reuse remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevisionCollection.post` is the collection-level parent used by browser-free forum edit-history reads, duplicate post revision-list reuse, lazy `ForumPost.revisions`, revision HTML capture, collection lookup, and generated moderation or migration ledgers. Parser paths already create collections with valid owning posts or infer the parent from valid revisions; direct constructor validation keeps malformed explicit collection parents out of generated ledgers, migration comparisons, publication audits, and downstream tooling while preserving parser and caller paths that intentionally use `post=None` for inference.

## Local Evidence

- Local rollout evidence used browser-free forum post revision acquisition, duplicate cached revision reuse, lazy revision HTML retrieval, cached direct acquisition, and tests that seed revision collections directly.
- Existing local drafts covered forum post revision fetch retry behavior, duplicate revision and revision-HTML reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct acquisition, acquisition post input validation, collection revisions/entry validation, loaded-collection mutation validation, search-key validation, optional HTML flag validation, direct revision post validation, direct revision identity validation, direct revision creator/time validation, and HTML assignment validation, but did not cover direct non-`None` `ForumPostRevisionCollection(post=...)` construction.
- The focused RED failures showed invalid explicit constructor parent posts were accepted as collection state. The GREEN regression covers boolean, string, dictionary, and arbitrary object values while preserving `None` as the inference/no-parent sentinel.
- This slice only validates forum-post-revision collection explicit parent-post constructor input. It does not change revision-list parsing, HTML parsing, collection lookup semantics, forum post source/edit behavior, duplicate page/file/vote/revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, forum post source text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only for explicit non-`None` parent values. It does not compare collection parent identity with each contained revision, coerce dictionaries into posts, reject `post=None`, verify thread or site membership, change the empty no-parent `post is None` state, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
