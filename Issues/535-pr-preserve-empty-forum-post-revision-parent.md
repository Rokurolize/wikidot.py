# PR Draft: Preserve Empty Forum Post Revision Collection Parent State

## Summary

`ForumPostRevisionCollection(post=None, revisions=[])` was documented by the prior local explicit-parent validation draft as a valid empty no-parent state, but the constructor did not assign `self.post` for that branch. Direct callers, fixture builders, generated migration ledgers, audit code, and downstream rehydration paths could construct the collection successfully and then hit `AttributeError: 'ForumPostRevisionCollection' object has no attribute 'post'` when inspecting the advertised parent state.

This change makes the no-parent empty state explicit by storing `self.post = None`, updates the collection annotation to `ForumPost | None`, and validates `self.post` before revision HTML acquisition needs a real request parent. Valid explicit `ForumPost` parents, valid revision-list parent inference, empty collections, `find(...)`, `find_by_rev_no(...)`, direct and batched revision acquisition, cached duplicate revision reuse, lazy `ForumPost.revisions`, revision HTML acquisition, parser diagnostics, and adjacent forum workflows remain unchanged.

## Outcome

Empty no-parent forum-post-revision collections now expose the documented `post is None` state instead of leaking a missing-attribute error.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct forum post revision collections directly for browser-free forum edit-history reads, generated discussion migration ledgers, fixture rehydration, duplicate cached revision reuse, lazy revision testing, or local audit tooling.

## Current Evidence

Local rollout-backed drafts repeatedly use forum post revision acquisition, duplicate revision reuse, revision HTML capture, and direct revision collection fixtures as practical workflows. Related drafts include [042-pr-retry-forum-post-revision-fetches.md](042-pr-retry-forum-post-revision-fetches.md), [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [057-pr-deduplicate-forum-post-revision-html-fetches.md](057-pr-deduplicate-forum-post-revision-html-fetches.md), [058-pr-deduplicate-forum-post-revision-with-html-fetches.md](058-pr-deduplicate-forum-post-revision-with-html-fetches.md), [131-pr-reuse-cached-duplicate-forum-post-revision-html.md](131-pr-reuse-cached-duplicate-forum-post-revision-html.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [445-pr-validate-forum-post-revision-post-field.md](445-pr-validate-forum-post-revision-post-field.md), [463-pr-validate-forum-post-revision-identity-fields.md](463-pr-validate-forum-post-revision-identity-fields.md), [464-pr-validate-forum-post-revision-creator-time-fields.md](464-pr-validate-forum-post-revision-creator-time-fields.md), and [473-pr-validate-forum-post-revision-collection-post-field.md](473-pr-validate-forum-post-revision-collection-post-field.md).

This is not a duplicate of Issue 473. Issue 473 validates non-`None` explicit collection parents and says empty no-parent construction remains valid with `post is None`, but its regression tests did not assert the empty no-parent attribute state. This slice repairs that preserved contract. It is also separate from Issue 421, which validates the `revisions` container and entries, and Issue 366, which validates mutated collection entries before HTML acquisition.

No upstream issue was filed from this local workspace.

## Changes

- Assign `self.post = None` when `ForumPostRevisionCollection` is constructed with `post=None` and no revisions.
- Type the collection parent as `ForumPost | None` to match actual supported constructor semantics.
- Validate the collection parent before `get_htmls()` starts request work for non-empty target revisions.
- Preserve valid explicit parents, first-revision parent inference, empty collection chaining, collection lookup, direct and batched acquisition, duplicate cache reuse, lazy revisions, parser diagnostics, and adjacent forum behavior.

## Type Of Change

- Contract repair
- Public collection constructor state hardening
- Forum post revision parent-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevisionCollection(post=None, revisions=[])` must expose `post is None` and length 0 instead of raising `AttributeError` on `collection.post`. |
| R2 | `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[])` and `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[valid_revision])` must remain valid. |
| R3 | `ForumPostRevisionCollection(revisions=[valid_revision])` must still infer the parent from the first revision. |
| R4 | Existing malformed explicit parent validation from Issue 473 must continue to reject non-`ForumPost` values with `ValueError("post must be a ForumPost")`. |
| R5 | `get_htmls()` must still return an empty collection before request work when no target revisions need HTML, and non-empty HTML acquisition must still use a validated `ForumPost` parent. |
| R6 | Forum post revision tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Empty no-parent construction leaves a readable `post is None` state. | `test_init_empty_without_post_exposes_none_post` failed RED before the fix with `AttributeError: 'ForumPostRevisionCollection' object has no attribute 'post'`, then passed GREEN after the constructor assigned `None`. | Missing `post`, raising `AttributeError`, rejecting `post=None`, or changing the empty collection length rejects this local completion claim. | ForumPostRevisionCollection constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Explicit valid parent paths remain stable. | The focused constructor GREEN command covered `test_init_with_post_and_empty_revisions` and `test_init_with_post_and_revisions`; the module and adjacent forum suites also passed. | Losing the explicit parent, changing valid empty-list behavior, or changing valid revision-list construction rejects this local completion claim. | ForumPostRevisionCollection constructor | `tests/unit/test_forum_post_revision.py` |
| R3 | First-revision parent inference remains available. | Existing module tests passed, including constructor and acquisition paths that depend on valid revision parent state. | Rejecting omitted parents with non-empty revisions or failing to preserve inferred parent state rejects this local completion claim. | ForumPostRevisionCollection constructor | `tests/unit/test_forum_post_revision.py` |
| R4 | Existing malformed explicit parent preflight remains intact. | The focused constructor GREEN command covered 4 malformed explicit parent cases, all still raising `ValueError("post must be a ForumPost")`. | Accepting booleans, strings, dictionaries, arbitrary objects, or emitting malformed explicit parent state rejects this local completion claim. | Constructor validation | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | HTML acquisition still uses a concrete post parent only when needed. | `tests/unit/test_forum_post_revision.py` passed 119 tests and adjacent forum workflow tests passed 491 tests after `get_htmls()` validated `self.post` before request work. | Regressing empty HTML no-op behavior, request construction, duplicate HTML reuse, failed response handling, cached HTML reuse, lazy HTML acquisition, or parser diagnostics rejects this local completion claim. | Forum revision HTML acquisition | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum revision module passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic state and local mocks; this draft contains no credentials, cookies, auth JSON, raw response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, revision HTML, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `fb64580 fix(forum_post_revision): preserve empty collection parent`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_empty_without_post_exposes_none_post -q` failed before the fix with `AttributeError: 'ForumPostRevisionCollection' object has no attribute 'post'`.
- GREEN focused constructor coverage: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_empty_without_post_exposes_none_post tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_with_post_and_empty_revisions tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_with_post_and_revisions tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionInit::test_init_rejects_malformed_posts -q` passed 7 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 119 tests.
- `uv run pytest tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_forum_post_revision.py -q` passed 491 tests.
- `uv run pytest tests/unit -q` passed 2553 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumPostRevisionCollection(post=None, revisions=[])` returns an empty collection with `collection.post is None`.
- `ForumPostRevisionCollection(revisions=[])` uses the same empty no-parent state.
- `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[])` keeps that explicit parent.
- `ForumPostRevisionCollection(post=<valid ForumPost>, revisions=[valid_revision])` remains valid.
- `ForumPostRevisionCollection(revisions=[valid_revision])` still infers the parent from the first valid revision.
- Malformed explicit parent values from Issue 473 still raise `ValueError("post must be a ForumPost")`.
- Empty `get_htmls()` no-op behavior, non-empty HTML acquisition, duplicate revision HTML reuse, lazy revisions, direct and batched revision acquisition, and adjacent forum workflows remain green.
- The tests use local synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be mistaken for a broader collection consistency change. Mitigation: this slice only makes the already documented empty no-parent state readable and validates the parent before HTML request work.
- Risk: Optional parent typing could mask a bad non-empty collection. Mitigation: non-empty HTML acquisition validates `self.post` with the existing `ForumPost` validator before accessing request state.
- Risk: The Issue 473 draft already claimed `post is None`. Mitigation: this slice explicitly records the missing regression and fixes the preserved contract without changing Issue 473's explicit-parent validation scope.

## Out Of Scope

Changing revision parsing, comparing collection parent identity with each contained revision, coercing dictionaries into posts, rejecting `post=None`, changing forum post source/edit behavior, changing live Wikidot behavior, changing page/file/vote revision collection contracts, and creating upstream Issues or PRs are outside this slice.

## Why This Matters

The empty no-parent state is useful for local fixtures, migration ledgers, and generated audits that may construct a collection before a concrete `ForumPost` owner is attached. A readable `post is None` sentinel is easier to reason about than a constructor that succeeds but leaves the public parent attribute missing.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free forum post revision acquisition, duplicate cached revision reuse, lazy revision HTML retrieval, cached direct acquisition, and tests that seed revision collections directly.
- Issue 473 explicitly preserved empty no-parent construction with `post is None`, but the constructor branch was not covered by an assertion and left the attribute unset.
- The focused RED failure reproduced the missing public state without live Wikidot access. The GREEN regression now proves the empty collection exposes the documented sentinel while the broader forum and repository gates prove adjacent behavior remains stable.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, forum source text, revision HTML, private content, private site data, and source text from real sites out of upstream discussion.
