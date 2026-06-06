# PR Draft: Validate Forum Post Revision Post Field

## Summary

`ForumPostRevision` records carry the owning `ForumPost` used by browser-free edit-history reads, lazy `ForumPost.revisions`, duplicate post-revision reuse, direct revision acquisition, revision HTML capture, and generated forum migration or audit ledgers. Earlier local slices validated revision acquisition inputs, collection entries, search keys, collection initialization, `html` assignments, and parser diagnostics, but the public `ForumPostRevision(...)` constructor still accepted malformed `post` values such as `None`, booleans, strings, dictionaries, and arbitrary objects.

This change validates `ForumPostRevision.post` at initialization. Malformed values now raise `ValueError("post must be a ForumPost")`. Existing revision-list parsing, lazy `ForumPost.revisions`, duplicate cached revision reuse, direct and batched revision acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows remain unchanged for valid `ForumPost` objects.

## Outcome

Callers cannot silently construct forum post revision records whose parent post is not a `ForumPost`, while parser-created, fixture-created, and manually created valid revisions continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum edit-history reads, generated discussion migration ledgers, revision HTML capture, duplicate revision cache reuse, direct `ForumPostRevisionCollection.acquire_all(post)`, lazy `ForumPost.revisions`, multi-post `ForumPostRevisionCollection.acquire_all_for_posts(...)`, or local tests that construct `ForumPostRevision` objects directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum post revision ownership as a practical workflow surface. Existing drafts [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), and [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md) establish direct revision-list acquisition, duplicate post ownership, cache reuse, and lazy `ForumPost.revisions` as active boundaries. Adjacent drafts [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), and [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md) cover caller-provided acquisition inputs, stored collection entries, lookup keys, optional HTML controls, collection constructor integrity, and direct HTML assignment integrity.

Those prior slices are not duplicates. Issue364 validates `post` and `posts` values passed into revision acquisition APIs, but explicitly does not validate forum dataclass fields. Issue421 validates `ForumPostRevisionCollection(post, revisions=...)` constructor state, not the `ForumPostRevision.post` field. Issue433 validates `ForumPostRevision.html` assignment, not revision ownership. The remaining prior slices cover fetch, parse, cache, lookup, and response-diagnostic behavior after valid revision records exist.

## Related Issue

Builds directly on [056-pr-deduplicate-forum-post-revision-fetches.md](056-pr-deduplicate-forum-post-revision-fetches.md), [142-pr-reuse-cached-duplicate-post-revisions.md](142-pr-reuse-cached-duplicate-post-revisions.md), [143-pr-skip-cached-direct-post-revisions.md](143-pr-skip-cached-direct-post-revisions.md), [229-pr-cache-direct-post-revision-acquisition.md](229-pr-cache-direct-post-revision-acquisition.md), [364-pr-validate-forum-post-revision-post-inputs.md](364-pr-validate-forum-post-revision-post-inputs.md), [366-pr-validate-forum-post-revision-collection-entries.md](366-pr-validate-forum-post-revision-collection-entries.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [386-pr-validate-forum-post-revision-with-html-flag.md](386-pr-validate-forum-post-revision-with-html-flag.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [433-pr-validate-forum-post-revision-html-assignments.md](433-pr-validate-forum-post-revision-html-assignments.md), and the adjacent constructor parent-field validation pattern from [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [443-pr-validate-page-file-page-field.md](443-pr-validate-page-file-page-field.md), and [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPostRevision.post` validation at dataclass initialization.
- Reject non-`ForumPost` values with `ValueError("post must be a ForumPost")`.
- Update forum-post-revision unit fixtures to use real `User` objects for `created_by` so the touched test file is target-pyright-clean.
- Keep negative test fixtures pyright-clean by typing intentionally malformed values through `Any`.
- Preserve existing revision-list parsing, lazy `ForumPost.revisions`, duplicate cached revision reuse, direct and batched acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum post revision parent-post state integrity
- Test fixture tightening

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPostRevision(post=None)`, `True`, `"5001"`, `{"id": 5001}`, and `object()` must raise `ValueError("post must be a ForumPost")` when every other revision field is valid. |
| R2 | Valid `ForumPost` instances must remain valid and preserve existing revision fields. |
| R3 | Existing revision-list parsing, lazy `ForumPost.revisions`, duplicate cached revision reuse, direct and batched acquisition, revision HTML behavior, collection lookup, and adjacent forum workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-post-revision/forum-post tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor posts fail at the public dataclass boundary. | `TestForumPostRevisionBasic.test_init_rejects_malformed_posts` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after post validation was added. | Accepting missing values, booleans, strings, dictionaries, arbitrary objects, or emitting revision rows with non-`ForumPost` parent state rejects this local completion claim. | ForumPostRevision constructor | `src/wikidot/module/forum_post_revision.py`, `tests/unit/test_forum_post_revision.py` |
| R2 | Valid post semantics stay green. | Existing forum-post-revision unit tests passed after valid constructor fixtures used real `User` values for `created_by`. | Rejecting valid `ForumPost` instances, coercing post-like mocks, or changing stored revision fields rejects this local completion claim. | Parser-created and manually created revisions | `tests/unit/test_forum_post_revision.py` |
| R3 | Existing adjacent forum workflows remain green. | `tests/unit/test_forum_post_revision.py` passed 90 tests, `tests/unit/test_forum_post.py` passed 94 tests, and full unit tests passed 1712 tests. | Regressing direct revision acquisition, lazy `ForumPost.revisions`, multi-post acquisition, cached direct acquisition, duplicate post-revision reuse, parser diagnostics, response diagnostics, search lookup, HTML acquisition, forum post source/edit workflows, or adjacent forum workflows rejects this local completion claim. | Forum revision and adjacent forum workflows | `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum post text, revision HTML, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `dcea670 fix(forum_post_revision): validate revision post`.

- RED: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_posts -q` failed 5 tests before the fix; every malformed `post` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionBasic::test_init_rejects_malformed_posts -q` passed 5 tests.
- `uv run pytest tests/unit/test_forum_post_revision.py -q` passed 90 tests.
- `uv run ruff check src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed.
- `uv run pyright src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_post_revision.py tests/unit/test_forum_post_revision.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 94 tests.
- `uv run pytest tests/unit -q` passed 1712 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 80 existing full-tree typing errors, including intentional invalid-input test fixtures, fixture `None` mismatches, invalid `test_search_pages_query` parameter calls, requestutil response narrowing issues, and one unrelated BeautifulSoup narrowing warning in `src/wikidot/module/forum_post.py`. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumPostRevision(post=None)`, `True`, `"5001"`, `{"id": 5001}`, and `object()` raise `ValueError("post must be a ForumPost")`.
- Valid `ForumPost` instances remain valid as `post`.
- Existing revision-list parsing, lazy `ForumPost.revisions`, duplicate cached revision reuse, `ForumPostRevisionCollection.find(...)`, `find_by_rev_no(...)`, direct and batched acquisition, cached direct acquisition, and revision HTML behavior remain green.
- Existing forum post source/edit behavior and adjacent forum workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPostRevision.post` is the parent context behind browser-free forum edit-history reads, duplicate post revision-list reuse, lazy `ForumPost.revisions`, revision HTML capture, collection lookup, and generated moderation or migration ledgers. Constructor validation keeps malformed local parent-post state out of revision rows while preserving parser and caller paths that construct revisions from real `ForumPost` objects.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free forum post revision reads, duplicate revision list reuse, revision HTML fetches, lazy forum post revision reads, and tests that seed revision objects directly.
- Existing local drafts covered forum post revision fetch retry behavior, duplicate revision and revision-HTML reduction, parse reuse, response diagnostics, parser field diagnostics, cached direct acquisition, acquisition post input validation, collection initialization validation, loaded-collection mutation validation, search-key validation, optional HTML flag validation, and HTML assignment validation, but did not cover direct `ForumPostRevision(post=...)` construction.
- The focused RED failures showed invalid constructor post fields were accepted as dataclass state. The GREEN regression covers missing, boolean, string, dictionary, and arbitrary object post values.
- This slice only validates forum post revision parent-post constructor input. It does not change revision-list parsing, optional HTML parsing, parser selectors, revision ID parsing, revision timestamp parsing, revision user parsing, revision HTML content parsing, cached duplicate behavior, collection lookup semantics, source/edit behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum post text, revision HTML, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates only that `post` is a `ForumPost` instance. It does not validate post IDs, thread identity, site identity, revision IDs, revision numbers, user shape, timestamp shape, HTML cache content, or live client authentication at `ForumPostRevision` construction time; those are separate post object, parser, cache, and workflow concerns.
