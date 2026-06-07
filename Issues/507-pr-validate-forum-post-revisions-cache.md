# PR Draft: Validate ForumPost Revisions Cache

## Summary

`ForumPost._revisions` is the optional cached `ForumPostRevisionCollection` behind the public `ForumPost.revisions` property. It is used by lazy forum edit-history reads, duplicate cached revision reuse, direct revision acquisition cache population, edit cache invalidation, generated forum migration ledgers, local fixtures, and rehydrated forum-post records. Earlier local slices validated revision acquisition inputs, revision-list response diagnostics, duplicate revision reuse, revision HTML acquisition, `ForumPostRevisionCollection` constructor inputs, collection parent posts, revision entries, direct `ForumPostRevision` fields, and direct `ForumPost` identity/text/metadata/thread/parent/source fields, but direct `ForumPost(..., _revisions=...)` construction still accepted malformed cached values such as booleans, integers, raw lists, dictionaries, arbitrary objects, and mutated revision collections containing non-revision entries.

This change validates the direct constructor's optional revisions cache during `ForumPost.__post_init__`. `_revisions=None` remains valid for posts that have not acquired revisions yet, real `ForumPostRevisionCollection` objects remain valid, and malformed non-null values now raise stable `ValueError` diagnostics before they can make `ForumPost.revisions` return malformed local cache state.

## Outcome

Directly constructed `ForumPost` objects now fail early when optional cached revision state is malformed, while preserving lazy revision acquisition for `_revisions=None` and preserving valid preloaded `ForumPostRevisionCollection` caches.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum edit-history inventories, generated discussion migration ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumPost` objects.

## Current Evidence

Forum-post revision drafts [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [135-pr-skip-cached-post-revision-list-fetches.md](135-pr-skip-cached-post-revision-list-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [172-pr-forum-post-revision-list-fetch-failure-context.md](172-pr-forum-post-revision-list-fetch-failure-context.md), [217-pr-forum-post-revision-response-body-context.md](217-pr-forum-post-revision-response-body-context.md), and [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md) establish forum edit-history reads, cached direct revision reuse, duplicate revision reuse, response diagnostics, and revision cache population as active operational surfaces.

Constructor and state-integrity drafts [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), and [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md) establish the local pattern for validating direct post, revision, and collection state instead of relying only on parser-created objects.

Adjacent constructor-cache drafts [491-pr-validate-page-constructor-revisions-cache.md](491-pr-validate-page-constructor-revisions-cache.md), [506-pr-validate-forum-post-source-cache.md](506-pr-validate-forum-post-source-cache.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), and [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md) establish the direct optional-cache validation pattern that accepts `None`, accepts the annotated cache object shape, and rejects malformed cache objects or mutated cache entries without changing parser or acquisition semantics.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 421. Issue 421 validates `ForumPostRevisionCollection(revisions=...)` construction, not whether a direct `ForumPost(_revisions=...)` value is a valid cached collection for `post.revisions`.

This is not a duplicate of Issue 473. Issue 473 validates the collection-level explicit `ForumPostRevisionCollection.post` parent, not the optional cached revision collection stored on a `ForumPost`.

This is not a duplicate of Issue 366. Issue 366 validates entries in an already-built `ForumPostRevisionCollection` before revision HTML acquisition inspects the collection. This slice rejects malformed cached revision state at `ForumPost` construction before the public `post.revisions` property can return it.

This is not a duplicate of Issue 506. Issue 506 validates the separate `_source` string cache. This slice validates the separate optional `_revisions` collection cache.

This follows the Page constructor revisions-cache pattern from Issue 491, but applies it to the forum-post cached revision collection instead of the page-level `PageRevisionCollection` object cache.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached revisions validation for direct `ForumPost(...)` construction.
- Preserve `_revisions=None` for posts that should lazily acquire revision history.
- Preserve valid `ForumPostRevisionCollection` caches without coercion.
- Reject booleans, integers, raw lists, dictionaries, and arbitrary non-collection objects using a stable `ValueError` diagnostic.
- Reject mutated cached revision collections that contain non-`ForumPostRevision` entries.
- Add constructor tests for malformed direct `_revisions` values, mutated cached collection entries, and valid cached revision collections.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached forum-post revision state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(_revisions=...)` must accept `None` and real `ForumPostRevisionCollection` objects. |
| R2 | `ForumPost(_revisions=...)` must reject non-`None` non-`ForumPostRevisionCollection` values with `ValueError("post.revisions must be ForumPostRevisionCollection or None")`. |
| R3 | `ForumPost(_revisions=...)` must reject `ForumPostRevisionCollection` objects containing non-`ForumPostRevision` entries with `ValueError("post.revisions list entries must be ForumPostRevision")`. |
| R4 | Valid cached revision collections must be returned by `post.revisions` without triggering revision acquisition. |
| R5 | Valid post construction, lazy `ForumPost.revisions`, direct and batched `ForumPostRevisionCollection` acquisition, cached duplicate revision reuse, revision HTML acquisition, `ForumPost.edit(...)` revision cache invalidation, source-cache behavior, parser-created posts, and forum category/thread/post/revision workflows must remain unchanged. |
| R6 | This slice must not change revision-list acquisition, revision HTML acquisition, post-source acquisition, edit-form parsing, post-list parsing, response diagnostics, edit request construction, cache invalidation semantics, live request behavior, or unrelated constructor fields. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid cached revision collections remain accepted. | `TestForumPostBasic.test_init_accepts_valid_revisions_cache` passed before and after validation was added, preserving a valid cached `ForumPostRevisionCollection` and returning it through `post.revisions`. Existing constructors continue to use `_revisions=None`. | Rejecting missing cached revisions, triggering revision lookup during construction, or coercing valid collection objects rejects this local completion claim. | `ForumPost` constructor cached-revision state | `tests/unit/test_forum_post.py` |
| R2 | Malformed optional cached revision values fail at the constructor boundary. | `TestForumPostBasic.test_init_rejects_malformed_revisions_cache` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, integers, raw lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `ForumPost` constructor cached-revision state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Mutated cached revision collections fail at the constructor boundary. | `TestForumPostBasic.test_init_rejects_malformed_revisions_cache_entries` failed RED because a mutated `ForumPostRevisionCollection` with a string entry was accepted, then passed GREEN after entry validation was added. | Returning a cached collection containing non-`ForumPostRevision` entries rejects this local completion claim. | `ForumPost` constructor cached-revision state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R4 | Valid cached revision access remains a cache hit. | The valid-cache test asserts `post.revisions is revisions` from the constructor-seeded cache. | Calling AMC, clearing `_revisions`, or replacing the cached collection rejects this local completion claim. | `ForumPost.revisions` cache access | `tests/unit/test_forum_post.py` |
| R5 | Existing post/source/edit/revision workflows remain green. | `tests/unit/test_forum_post.py` passed 150 tests, adjacent forum tests passed 484 tests, and the full unit suite passed 2259 tests. | Regressing lazy revision acquisition, direct revision acquisition, multi-post revision acquisition, cached direct revision reuse, duplicate revision reuse, revision HTML acquisition, source acquisition, source cache updates, edit revision cache invalidation, parser-created posts, forum thread behavior, forum category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R6 | Broader revision semantics remain outside scope. | Existing acquisition, parser, source, edit, cache invalidation, collection, and adjacent tests remain green; this slice only validates direct constructor cache type and entry integrity. | Changing request construction, parser conversion, response diagnostics, revision ordering, revision HTML content, edit payloads, source semantics, thread post-cache invalidation, or live request behavior rejects this local completion claim. | ForumPost constructor scope | `src/wikidot/module/forum_post.py`, adjacent tests |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, revision HTML, source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `7de11fd fix(forum_post): validate revisions cache`.

- RED cache tests: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_revisions_cache tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_revisions_cache_entries tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_valid_revisions_cache -q` failed 6 malformed `_revisions` cases before the fix with `DID NOT RAISE`, while the valid cached collection case passed.
- GREEN cache tests: the same focused command passed 7 tests after optional revisions-cache validation was added.
- Constructor/property block: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic -q` passed 54 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 150 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 484 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `uv run mypy src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2259 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPost(_revisions=None)` remains valid and lazy revision acquisition remains available.
- `ForumPost(_revisions=ForumPostRevisionCollection(...))` remains valid and `post.revisions` returns the cached collection without a lookup.
- `ForumPost(_revisions=True)`, `ForumPost(_revisions=5001)`, `ForumPost(_revisions=[])`, `ForumPost(_revisions={"revisions": []})`, and `ForumPost(_revisions=object())` raise `ValueError("post.revisions must be ForumPostRevisionCollection or None")` when every other constructor field is valid.
- `ForumPost(_revisions=collection_mutated_with_non_revision)` raises `ValueError("post.revisions list entries must be ForumPostRevision")` when every other constructor field is valid.
- Existing parser-created posts, direct post fixtures, thread post-list reads, lazy `ForumPost.revisions`, direct and batched `ForumPostRevisionCollection` acquisition, cached direct revision acquisition, duplicate cached revision reuse, revision HTML acquisition, lazy `ForumPost.source`, direct `ForumPostCollection.get_post_sources()`, `ForumPost.edit(...)`, revision cache invalidation, forum post revision behavior, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not validate revision HTML contents, source contents, parser selectors, live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with revision-list parsing or revision-content validation. Mitigation: the validator checks cache object shape and entry types only, matching the direct cache boundary; revision ordering, HTML content, parser selectors, and acquisition behavior remain outside scope.
- Risk: Valid cached revision collections could accidentally trigger revision acquisition. Mitigation: the valid-cache test asserts `post.revisions is revisions`, and the constructor validator does not call acquisition helpers.
