# PR Draft: Validate ForumPost Source Cache

## Summary

`ForumPost._source` is the optional cached source string behind the public `ForumPost.source` property. It is used by lazy post-source reads, direct source acquisition cache population, cached duplicate source reuse, edit workflows, generated forum migration ledgers, local fixtures, and rehydrated forum-post records. Earlier local slices validated forum post-list fetching, source fetching, response-body diagnostics, source collection entries, write-side edit source inputs, `ForumPostCollection` constructor inputs, collection parent threads, and direct `ForumPost` identity/text/metadata/thread/parent fields, but direct `ForumPost(..., _source=...)` construction still accepted malformed cached values such as booleans, integers, lists, dictionaries, and arbitrary objects.

This change validates the direct constructor's optional source cache during `ForumPost.__post_init__`. `_source=None` remains valid for posts that have not acquired source yet, cached strings remain valid, and malformed non-null values now raise `ValueError("post.source must be a string or None")` before they can make `ForumPost.source` return malformed local cache state.

## Outcome

Directly constructed `ForumPost` objects now fail early when optional cached source state is malformed, while preserving lazy source acquisition for `_source=None` and preserving valid preloaded source strings.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who build browser-free forum inventories, generated discussion migration ledgers, moderation tooling, translation review tooling, cached forum records, local fixtures, generated adapters, or serialized and rehydrated `ForumPost` objects.

## Current Evidence

Forum-post source and edit drafts [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), and [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md) establish post-source reads, cached source reuse, edit-form reads, source diagnostics, and source acquisition preflight as active operational surfaces.

Constructor and state-integrity drafts [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), [461-pr-validate-forum-post-edit-metadata-fields.md](461-pr-validate-forum-post-edit-metadata-fields.md), [462-pr-validate-forum-post-parent-id-field.md](462-pr-validate-forum-post-parent-id-field.md), and [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md) establish the local pattern for validating direct post and collection state instead of relying only on parser-created objects.

Adjacent constructor-cache drafts [490-pr-validate-page-constructor-source-field.md](490-pr-validate-page-constructor-source-field.md), [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md), and [505-pr-validate-forum-category-threads-cache.md](505-pr-validate-forum-category-threads-cache.md) establish the direct optional-cache validation pattern that accepts `None`, accepts the annotated cache object shape, and rejects malformed cache objects without adding unrelated parser or ownership checks.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 460. Issue 460 validates `ForumPost.id`, `ForumPost.title`, and `ForumPost.text` and explicitly leaves `_source` source-level validation as a separate concern. This slice validates the separate optional cached source field.

This is not a duplicate of Issue 367. Issue 367 validates entries in `ForumPostCollection.get_post_sources()` before source acquisition inspects cache state or builds requests. This slice rejects malformed cached source state at `ForumPost` construction before the public `post.source` property can return it.

This is not a duplicate of Issue 327. Issue 327 validates present non-string AMC response bodies before post-list, source-form, or edit-form parsing. This slice validates local constructor cache input, not remote response payload shape.

This is not a duplicate of Issue 354. Issue 354 validates write-side public source arguments for forum mutations. This slice validates already cached read-side local source state.

This follows the Page constructor-source pattern from Issue 490, but applies it to the forum-post cached source string instead of the page-level `PageSource` object cache.

No upstream issue was filed from this local workspace.

## Changes

- Add optional cached source validation for direct `ForumPost(...)` construction.
- Preserve `_source=None` for posts that should lazily acquire source.
- Preserve valid cached source strings without coercion.
- Reject booleans, integers, lists, dictionaries, and arbitrary non-string objects using a stable `ValueError` diagnostic.
- Add constructor tests for malformed direct `_source` values and valid cached source strings.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Cached forum-post source state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(_source=...)` must accept `None` and real strings. |
| R2 | `ForumPost(_source=...)` must reject non-`None` non-string values with `ValueError("post.source must be a string or None")`. |
| R3 | Valid cached source strings must be returned by `post.source` without triggering source acquisition. |
| R4 | Valid post construction, lazy `ForumPost.source`, `ForumPostCollection.get_post_sources()`, cached duplicate source reuse, `ForumPost.edit(...)`, source cache updates, revision cache invalidation, parser-created posts, and forum category/thread/post/revision workflows must remain unchanged. |
| R5 | This slice must not change source acquisition, edit-form parsing, post-list parsing, response diagnostics, edit request construction, source normalization, cache invalidation semantics, live request behavior, or unrelated constructor fields. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None` and valid string cached source values remain accepted. | `TestForumPostBasic.test_init_accepts_valid_source_cache` passed after validation was added, preserving a valid cached string and returning it through `post.source`. Existing constructors continue to use `_source=None`. | Rejecting missing cached source, triggering source lookup during construction, or coercing valid strings rejects this local completion claim. | `ForumPost` constructor cached-source state | `tests/unit/test_forum_post.py` |
| R2 | Malformed optional cached source values fail at the constructor boundary. | `TestForumPostBasic.test_init_rejects_malformed_source_cache` failed RED for 5 malformed values because constructors did not raise, then passed GREEN after validation was added. | Accepting booleans, integers, lists, dictionaries, arbitrary objects, or silently coercing malformed values rejects this local completion claim. | `ForumPost` constructor cached-source state | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Valid cached source access remains a cache hit. | The valid-cache test asserts `post.source == "cached source"` from the constructor-seeded cache. | Calling AMC, clearing `_source`, or changing returned source text rejects this local completion claim. | `ForumPost.source` cache access | `tests/unit/test_forum_post.py` |
| R4 | Existing post/source/edit workflows remain green. | `tests/unit/test_forum_post.py` passed 143 tests, adjacent forum tests passed 477 tests, and the full unit suite passed 2252 tests. | Regressing lazy source acquisition, source collection acquisition, duplicate cached source reuse, source response diagnostics, edit-form preflight, source cache update, revision cache invalidation, parser-created posts, forum thread behavior, forum category behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit` |
| R5 | Broader source semantics remain outside scope. | Existing acquisition, parser, edit, cache invalidation, collection, and adjacent tests remain green; this slice only validates direct constructor cache type integrity. | Changing request construction, parser conversion, response diagnostics, source content normalization, edit payloads, title handling, revision invalidation, thread post-cache invalidation, or live request behavior rejects this local completion claim. | ForumPost constructor scope | `src/wikidot/module/forum_post.py`, adjacent tests |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML, forum source text, private messages, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1d2c74c fix(forum_post): validate source cache`.

- RED type guard: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_source_cache -q` failed 5 tests before the fix; every malformed `_source` value reported `DID NOT RAISE`.
- GREEN cache tests: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_source_cache tests/unit/test_forum_post.py::TestForumPostBasic::test_init_accepts_valid_source_cache -q` passed 6 tests after optional source-cache validation was added.
- Constructor/property block: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic -q` passed 47 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 143 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 477 tests.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `uv run mypy src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2252 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPost(_source=None)` remains valid and lazy source acquisition remains available.
- `ForumPost(_source="cached source")` remains valid and `post.source` returns the cached string without a lookup.
- `ForumPost(_source=True)`, `ForumPost(_source=5001)`, `ForumPost(_source=["cached source"])`, `ForumPost(_source={"source": "cached source"})`, and `ForumPost(_source=object())` raise `ValueError("post.source must be a string or None")` when every other constructor field is valid.
- Existing parser-created posts, direct post fixtures, thread post-list reads, lazy `ForumPost.source`, direct `ForumPostCollection.get_post_sources()`, duplicate cached source reuse, source response diagnostics, `ForumPost.edit(...)`, source cache updates, revision cache invalidation, forum post revision behavior, and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not validate source contents, parser selectors, live Wikidot, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: Constructor validation could be confused with source normalization or content validation. Mitigation: the validator checks type only, matching the direct cache boundary; source contents, trimming, and normalization remain outside scope.
- Risk: Valid cached strings could accidentally trigger source acquisition. Mitigation: the valid-cache test asserts `post.source == "cached source"`, and the constructor validator does not call acquisition helpers.
