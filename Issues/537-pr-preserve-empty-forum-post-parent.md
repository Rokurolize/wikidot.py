# PR Draft: Preserve Empty Forum Post Collection Parent State

## Summary

`ForumPostCollection(thread=None, posts=[])` and the default `ForumPostCollection()` constructor were left with an incidental first-entry lookup after the earlier constructor-validation and explicit-parent-validation slices. Direct callers, fixture builders, generated forum ledgers, migration audits, cached post-list setup, and downstream rehydration paths could hit `IndexError: list index out of range` before receiving a usable empty collection.

This change makes the empty no-parent state explicit by storing `self.thread = None` and typing the collection parent as `ForumThread | None`. Valid explicit `ForumThread` parents, first-post parent inference, empty thread-supplied collections, ID lookup, post-list acquisition, lazy `ForumThread.posts`, source acquisition on empty collections, parser diagnostics, direct `ForumPost` validation, revision-cache behavior, and adjacent forum workflows remain unchanged.

## Outcome

Empty no-parent forum-post collections now expose the readable `thread is None` sentinel instead of leaking a constructor-time `IndexError`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum post inventories, generated forum migration ledgers, moderation or audit scripts, duplicate cached post-list reuse, lazy `ForumThread.posts`, direct `ForumPostCollection.acquire_all_in_thread(...)`, or local tests that construct `ForumPostCollection` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post inventories and post source reads as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [076-pr-skip-empty-thread-fetch-batches.md](076-pr-skip-empty-thread-fetch-batches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [291-pr-forum-post-list-user-context.md](291-pr-forum-post-list-user-context.md), [327-pr-forum-post-list-response-body-type-context.md](327-pr-forum-post-list-response-body-type-context.md), [367-pr-validate-forum-post-source-entries.md](367-pr-validate-forum-post-source-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [411-pr-validate-forum-post-source-cache.md](411-pr-validate-forum-post-source-cache.md), [412-pr-validate-forum-post-revisions-cache.md](412-pr-validate-forum-post-revisions-cache.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-metadata.md](459-pr-validate-forum-post-creator-metadata.md), [460-pr-validate-forum-post-identity-fields.md](460-pr-validate-forum-post-identity-fields.md), [461-pr-validate-forum-post-edit-metadata.md](461-pr-validate-forum-post-edit-metadata.md), [462-pr-validate-forum-post-parent-id.md](462-pr-validate-forum-post-parent-id.md), [474-pr-validate-forum-post-collection-thread-field.md](474-pr-validate-forum-post-collection-thread-field.md), and [504-pr-validate-forum-thread-posts-cache.md](504-pr-validate-forum-thread-posts-cache.md) establish post-list reads, parser diagnostics, response diagnostics, duplicate cache reuse, lookup validation, collection entry validation, source/revision cache validation, direct post field validation, explicit collection parent validation, and cached `ForumThread.posts` validation as active operational boundaries.

This is not a duplicate of Issue 474. Issue 474 validates non-`None` explicit collection parents and preserves `thread=None` inference plus explicit-thread empty construction, but it did not assert that an empty no-parent collection can be constructed and exposes a readable `thread is None` sentinel. This slice repairs that direct-state gap without changing explicit parent validation, post-entry validation, post lookup, direct acquisition, lazy cache behavior, or live Wikidot behavior.

No upstream issue was filed from this local workspace.

## Changes

- Assign `self.thread = None` when `ForumPostCollection` is constructed with no thread and no posts.
- Type the collection parent as `ForumThread | None` to match supported constructor semantics.
- Keep `get_post_sources()` a no-op for an empty parentless collection.
- Preserve valid explicit parents, first-post parent inference, empty thread-supplied collections, ID lookup, post-list acquisition, lazy posts, duplicate cached post reuse, source acquisition, parser diagnostics, revision-cache behavior, and adjacent forum workflows.

## Type Of Change

- Contract repair
- Public collection constructor state hardening
- Forum post parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostCollection(thread=None, posts=[])` and `ForumPostCollection()` must expose `thread is None` and length 0 instead of raising `IndexError`. |
| R2 | `ForumPostCollection(thread=<valid ForumThread>, posts=[])` and `ForumPostCollection(thread=<valid ForumThread>, posts=[valid_post])` must remain valid. |
| R3 | `ForumPostCollection(thread=None, posts=[valid_post])` must still infer the parent from the first post. |
| R4 | Existing malformed explicit parent validation from Issue 474 must continue to reject non-`ForumThread` values with `ValueError("thread must be a ForumThread")`. |
| R5 | Post-list acquisition, lazy `ForumThread.posts`, source reads, duplicate cached post reuse, parser diagnostics, lookup helpers, revision-cache behavior, and adjacent forum workflows must remain unchanged. |
| R6 | Forum-post tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Empty no-parent construction leaves a readable `thread is None` state. | `test_init_empty_without_thread_exposes_none_thread` failed RED before the fix with `IndexError: list index out of range`, then passed GREEN after the constructor assigned `None`. | Raising `IndexError`, rejecting omitted input, missing `thread`, or changing the empty collection length rejects this local completion claim. | ForumPostCollection constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Explicit valid parent paths remain stable. | The focused constructor GREEN command covered existing explicit-thread empty and populated construction tests. | Losing the explicit parent, changing valid empty-list behavior, or changing valid post-list construction rejects this local completion claim. | ForumPostCollection constructor | `tests/unit/test_forum_post.py` |
| R3 | First-post parent inference remains available. | The focused constructor GREEN command covered `test_init_infers_thread_from_posts`. | Rejecting omitted parents with non-empty posts or failing to preserve inferred parent state rejects this local completion claim. | ForumPostCollection constructor | `tests/unit/test_forum_post.py` |
| R4 | Existing malformed explicit parent preflight remains intact. | The focused constructor GREEN command covered 4 malformed explicit parent cases, all still raising `ValueError("thread must be a ForumThread")`. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting malformed explicit parent state rejects this local completion claim. | Constructor validation | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R5 | Existing forum-post and adjacent forum workflows remain stable. | `tests/unit/test_forum_post.py` passed 151 tests and adjacent forum workflow tests passed 492 tests. | Regressing post-list acquisition, lazy posts, source reads, duplicate cached post reuse, post lookup, parser diagnostics, revision cache behavior, forum thread/category behavior, or forum post revision workflows rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post_revision.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-post module passed, adjacent forum workflows passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state and local mocks; this draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, forum source text, private messages, page source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `7deab5c fix(forum_post): preserve empty collection parent`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit::test_init_empty_without_thread_exposes_none_thread -q` failed before the fix with `IndexError: list index out of range`.
- GREEN focused constructor coverage: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionInit -q` passed 23 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 151 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 492 tests.
- `uv run pytest tests/unit -q` passed 2555 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostCollection(thread=None, posts=[])` and `ForumPostCollection()` return an empty collection with `collection.thread is None`.
- `ForumPostCollection(thread=<valid ForumThread>, posts=[])` keeps that explicit parent.
- `ForumPostCollection(thread=<valid ForumThread>, posts=[valid_post])` remains valid.
- `ForumPostCollection(thread=None, posts=[valid_post])` still infers the parent from the first valid post.
- Malformed explicit parent values from Issue 474 still raise `ValueError("thread must be a ForumThread")`.
- Existing valid `ForumPost` lists, iteration, `find(...)`, post-list acquisition, lazy `ForumThread.posts`, source acquisition, parser-side post-list diagnostics, direct `ForumPost` field validation, revision-cache behavior, duplicate cached post reuse, and adjacent forum workflows remain green.
- The tests use local synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private forum data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be mistaken for a broader collection consistency change. Mitigation: this slice only makes the default empty no-parent constructor readable and leaves acquisition behavior unchanged.
- Risk: Optional parent typing could be read as permission to use a parentless collection for remote source acquisition. Mitigation: acquisition paths still construct collections with real threads, and this slice keeps only empty parentless source hydration as a no-op.
- Risk: This could be confused with Issue 474. Mitigation: Issue 474 validates malformed explicit non-`None` parent threads; this slice fixes the preserved empty no-parent branch.

## Out Of Scope

Changing post-list parsing, comparing collection parent identity with each contained post, coercing dictionaries into threads, rejecting `thread=None`, changing direct acquisition, changing lazy `ForumThread.posts`, changing live Wikidot behavior, changing forum revision/source contracts, and creating upstream Issues or PRs are outside this slice.

## Why This Matters

The empty no-parent state is useful for local fixtures, post ledgers, migration audits, and generated workflows that may construct a post collection before a concrete `ForumThread` owner is attached. A readable `thread is None` sentinel is easier to reason about than a default constructor that crashes before returning a collection.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free forum post acquisition, duplicate cached post reuse, lazy post state, source reads, post ledgers, and tests that seed post collections directly.
- Issue 474 preserved `thread=None` inference and explicit-thread empty construction, but the fully empty no-parent constructor branch was not covered by an assertion and still indexed `self[0]`.
- The focused RED failure reproduced the constructor crash without live Wikidot access. The GREEN regression now proves the empty collection exposes the documented sentinel while the broader forum and repository gates prove adjacent behavior remains stable.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, forum source text, private messages, page source text, private content, private site data, and source text from real sites out of upstream discussion.
