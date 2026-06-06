# PR Draft: Validate Forum Post Collection Thread Field

## Summary

`ForumPostCollection` stores the optional explicit parent `ForumThread` used by browser-free forum post-list reads, lazy `ForumThread.posts`, duplicate cached thread-post list reuse, post source acquisition, generated migration or audit ledgers, local fixtures, and rehydrated forum post state. Earlier local slices validated caller-provided thread inputs before acquisition, loaded collection entries, lookup IDs, collection `posts` containers and entries, direct `ForumPost.thread`, direct post identity/text fields, direct post creator/time fields, and optional post edit metadata, but `ForumPostCollection(thread=..., posts=...)` still accepted malformed explicit parent threads such as booleans, strings, dictionaries, and arbitrary objects.

This change validates non-`None` `ForumPostCollection.thread` constructor arguments before storing collection state. Malformed explicit values now raise `ValueError("thread must be a ForumThread")`. The existing `thread=None` inference behavior remains valid when a collection is built from a valid first post. Valid `ForumThread` parents, empty post lists, valid `ForumPost` lists, iteration, lookup, direct and batched post-list acquisition, post source acquisition, lazy `ForumThread.posts`, duplicate cached post reuse, parser diagnostics, direct `ForumPost` field validation, and adjacent forum workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-post collections with malformed explicit parent-thread state, while parser-created, fixture-created, cached-duplicate, inferred-parent, and manually created valid post collections continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum post reads, generated discussion migration ledgers, post source capture, duplicate thread-post cache reuse, direct `ForumPostCollection.acquire_all_in_thread(thread)`, lazy `ForumThread.posts`, multi-thread `ForumPostCollection.acquire_all_in_threads(...)`, or local tests that construct `ForumPostCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post lists and forum post source reads as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), and [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md) establish forum post acquisition, source acquisition, parser diagnostics, response diagnostics, caller-provided thread validation, loaded-collection mutation validation, lookup validation, collection entry validation, direct post parent validation, and direct post field validation as active operational boundaries.

Those prior slices are not duplicates. Issue 422 validates only the collection's `posts` container and entries while preserving `ForumPostCollection(thread=None, posts=[valid_post])` inference. Issue 446 validates the `thread` field on individual `ForumPost` records, not the collection parent. Issues 459-462 validate direct `ForumPost` creator/time, identity/text, edit metadata, and parent-ID fields. Issue 363 validates caller-provided `thread` values for acquisition APIs, and Issue 367 validates mutated collection entries before post source acquisition. None validates direct non-`None` `ForumPostCollection(thread=...)` construction before malformed parent-thread state becomes stored collection state in manually constructed collections, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), and the adjacent optional collection parent validation pattern from [471-pr-validate-page-file-collection-page-field.md](471-pr-validate-page-file-collection-page-field.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), and [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate non-`None` `ForumPostCollection.thread` values at constructor initialization.
- Reject malformed explicit parent-thread values with `ValueError("thread must be a ForumThread")`.
- Preserve `thread=None` inference from a valid first post, valid empty post collections, valid `ForumPost` lists, iteration, lookup, parser-created collections, duplicate cached post reuse, direct and batched post-list acquisition, post source acquisition, lazy `ForumThread.posts`, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public collection constructor behavior hardening
- Forum post parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection(thread=True)`, `"3001"`, `{"id": 3001}`, and `object()` must raise `ValueError("thread must be a ForumThread")` when `posts` is otherwise valid. |
| R2 | `ForumPostCollection(posts=[valid_post])` must still infer the thread from the first post, and `ForumPostCollection(thread=<valid ForumThread>, posts=[])` must remain constructible. |
| R3 | Valid `ForumThread` parent values, valid empty post lists, valid `ForumPost` lists, iteration, `find(...)`, direct and batched post-list acquisition, post source acquisition, lazy `ForumThread.posts`, duplicate cached post reuse, parser diagnostics, direct `ForumPost` field validation, and adjacent forum workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-post tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed explicit collection parent threads fail at the public constructor boundary. | `TestForumPostCollectionInit.test_init_rejects_malformed_threads` failed RED for 4 malformed non-`None` values because the constructor did not raise, then passed GREEN after thread validation was added. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting post collections with malformed explicit parent-thread state rejects this local completion claim. | ForumPostCollection constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Optional inference and valid empty collection semantics stay green. | Existing empty initialization and thread-inference tests passed in the 137-test forum-post module run. | Losing parent inference from the first valid post, rejecting empty valid collections with explicit valid threads, or changing stored thread identity rejects this local completion claim. | ForumPostCollection constructor | `tests/unit/test_forum_post.py` |
| R3 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 137 tests, adjacent forum workflow tests passed 436 tests, and full unit tests passed 1911 tests. | Regressing direct post-list acquisition, lazy `ForumThread.posts`, multi-thread acquisition, cached direct acquisition, duplicate thread-post reuse, parser diagnostics, response diagnostics, ID lookup, source acquisition, forum thread/category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, forum post source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8330e71 fix(forum_post): validate post collection thread`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_rejects_malformed_threads -q` failed 4 tests before the fix; every malformed explicit `thread` input reported `DID NOT RAISE`.
- GREEN: the same focused command passed 4 tests after `ForumPostCollection` explicit thread validation was added.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 137 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 436 tests.
- `uv run pytest tests/unit -q` passed 1911 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `uv run mypy src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test page fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client mock typing, invalid test cookie arguments, and site test mock typing issues. The changed source file and changed forum-post test file pass pyright together.

## Acceptance Criteria

- `ForumPostCollection(thread=True)`, `"3001"`, `{"id": 3001}`, and `object()` raise `ValueError("thread must be a ForumThread")`.
- `ForumPostCollection(posts=[valid_post])` still infers the thread from the first valid post.
- `ForumPostCollection(thread=<valid ForumThread>, posts=[])` and `ForumPostCollection(thread=<valid ForumThread>, posts=[valid_post])` remain valid.
- Existing valid `ForumPost` lists, iteration, `find(...)`, direct and batched acquisition, post source acquisition, lazy `ForumThread.posts`, parser-side post diagnostics, direct post field validation, and duplicate cached post reuse remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostCollection.thread` is the collection-level parent used by browser-free forum post-list reads, duplicate thread-post list reuse, lazy `ForumThread.posts`, post source capture, collection lookup, and generated moderation or migration ledgers. Parser paths already create collections with valid owning threads or infer the parent from valid posts; direct constructor validation keeps malformed explicit collection parents out of generated ledgers, migration comparisons, publication audits, and downstream tooling while preserving parser and caller paths that intentionally use thread inference.

## Local Evidence

- Local rollout evidence used browser-free forum post acquisition, duplicate cached post reuse, lazy forum thread post reads, post source acquisition, cached direct acquisition, and tests that seed post collections directly.
- Existing local drafts covered forum post fetch retry behavior, duplicate post and source fetch reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct acquisition, acquisition thread input validation, collection posts/entry validation, loaded-collection mutation validation, search-key validation, direct post thread validation, direct post identity/text validation, direct post creator/time validation, optional edit metadata validation, and parent-ID validation, but did not cover direct non-`None` `ForumPostCollection(thread=...)` construction.
- The focused RED failures showed invalid explicit constructor parent threads were accepted as collection state. The GREEN regression covers boolean, string, dictionary, and arbitrary object values while preserving inference from valid posts.
- This slice only validates forum-post collection explicit parent-thread constructor input. It does not change post-list parsing, source parsing, collection lookup semantics, forum post source/edit behavior, duplicate page/file/vote/revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, forum post source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates type only for explicit non-`None` parent values. It does not compare collection parent identity with each contained post, coerce dictionaries into threads, change thread inference from a valid first post, verify category or site membership, or change live client authentication; those are separate parser, collection-consistency, and workflow concerns.
