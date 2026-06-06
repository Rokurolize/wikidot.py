# PR Draft: Validate ForumPost Creator And Time Fields

## Summary

`ForumPost` records store generated creator and creation-time metadata in `created_by` and `created_at`. Earlier local slices validated parser-side forum-post creator and timestamp diagnostics, edit metadata diagnostics, post-list acquisition inputs, loaded-collection entries, collection initialization, collection search IDs, source acquisition behavior, source response bodies, edit inputs, and the owning `ForumPost.thread` constructor field. The public `ForumPost(..., created_by=..., created_at=...)` dataclass constructor still accepted malformed direct metadata values such as `None`, booleans, integers, strings, dictionaries, and lists, letting callers create fixture, ledger, or rehydrated post records whose creator was not an `AbstractUser` or whose creation time was not a `datetime`.

This change validates `ForumPost.created_by` and `ForumPost.created_at` at initialization. `created_by` now accepts only `AbstractUser` instances, preserving regular, deleted, anonymous, guest, and Wikidot system users that can be returned by the shared user parser. `created_at` now accepts only `datetime` instances. Malformed values raise stable `ValueError` diagnostics: `created_by must be an AbstractUser` and `created_at must be a datetime`. Valid post-list parsing, parser-side post ID/user/timestamp/edit-metadata diagnostics, direct thread validation, collection validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-post records with non-user creators or non-datetime creation timestamps, while parser-created posts and valid direct `ForumPost(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, `ForumThread.posts`, forum post source reads, forum post edit workflows, forum post revisions, local fixtures, or serialized/rehydrated post records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-post reads and stored post records as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), and [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md) establish forum post acquisition, retry behavior, duplicate handling, parser scoping, text fidelity, parser diagnostics, response diagnostics, source acquisition, edit preflight, public acquisition input validation, collection-entry validation, search-key validation, collection constructor integrity, and parent-thread constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issues 295 and 296 validate parser-side generated creator and timestamp metadata before parser-side `ForumPost` construction. Issues 297 and 298 validate parser-side generated edit metadata. Issue 446 validates the separate public `ForumPost.thread` parent field. Issues 363, 367, 378, and 422 validate acquisition inputs, stored collection entries, collection lookup IDs, and collection initialization. This slice validates the separate public dataclass `ForumPost.created_by` and `ForumPost.created_at` fields so malformed actor/time values cannot become stored record state in manually constructed posts, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), and the adjacent direct record-field pattern from [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumPost.created_by` validation at dataclass initialization.
- Add `ForumPost.created_at` validation at dataclass initialization.
- Reject non-`AbstractUser` `created_by` values with `ValueError("created_by must be an AbstractUser")`.
- Reject non-`datetime` `created_at` values with `ValueError("created_at must be a datetime")`.
- Tighten the unit fixture `mock_forum_post_no_http` to use a real `User`, a real `datetime`, and an asserted dummy `Tag` instead of malformed placeholders.
- Preserve valid `AbstractUser` subclasses without requiring regular integer-ID `User` instances.
- Preserve valid `datetime` timestamps without timezone normalization or coercion.
- Preserve post-list parsing, parser-side post ID/user/timestamp/edit-metadata diagnostics, direct thread validation, collection validation, lazy `ForumPost.source`, lazy `ForumPost.revisions`, edit behavior, and adjacent forum category/thread/revision behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-post metadata state integrity
- Test fixture tightening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(created_by=None)`, `True`, `5001`, `"test_user"`, and `{"id": 12345}` must raise `ValueError("created_by must be an AbstractUser")` before storing record state. |
| R2 | `ForumPost(created_at=None)`, `True`, `1700000000`, `"2023-11-14"`, and `[]` must raise `ValueError("created_at must be a datetime")` before storing record state. |
| R3 | Valid `AbstractUser` instances and valid `datetime` timestamps must remain valid and preserve stored values. |
| R4 | Existing post-list parsing, parser-side ID/user/timestamp/edit-metadata diagnostics, direct thread validation, collection initialization, collection search validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor creators fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_created_by` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after creator validation was added. | Accepting missing values, booleans, integers, strings, dictionaries, arbitrary objects, or emitting post records with non-user creators rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Malformed constructor timestamps fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_created_at` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after timestamp validation was added. | Accepting missing values, booleans, epoch integers, date strings, lists, arbitrary objects, or emitting post records with non-datetime timestamps rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Valid creator/time semantics stay green. | The `mock_forum_post_no_http` fixture now uses a real `User` and `datetime`; existing constructor, string, source, revision, parser, and edit tests passed. | Rejecting valid `AbstractUser` subclasses, changing stored users, coercing timestamps, or rejecting valid `datetime` values rejects this local completion claim. | Parser-created and manually created posts | `tests/conftest.py`, `tests/unit/test_forum_post.py` |
| R4 | Existing forum-post and adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 109 tests, adjacent forum tests passed 386 tests, and full unit tests passed 1796 tests. | Regressing post-list parsing, parser user/timestamp/edit-metadata diagnostics, source acquisition, lazy revision acquisition, edit behavior, parent-thread validation, collection validation, forum category behavior, forum thread behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, post titles from real sites, post bodies from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-post tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `ca0ce0a fix(forum_post): validate post creator metadata`.

- RED 1: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_created_by -q` failed 5 tests before the fix; every malformed `created_by` value reported `DID NOT RAISE`.
- GREEN 1: the same focused creator command passed 5 tests after creator validation and fixture tightening were added.
- RED 2: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_created_at -q` failed 5 tests before the timestamp fix; every malformed `created_at` value reported `DID NOT RAISE`.
- GREEN 2: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_created_by tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_created_at -q` passed 10 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 109 tests.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py tests/conftest.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py tests/conftest.py` passed with 3 files already formatted after applying the formatter once.
- `uv run mypy src/wikidot/module/forum_post.py tests/unit/test_forum_post.py tests/conftest.py` passed with no issues in 3 source files.
- `uv run pyright src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 386 tests.
- `uv run pytest tests/unit -q` passed 1796 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 61 existing full-tree typing errors outside this slice, including page fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed forum-post test file pass pyright together.

## Acceptance Criteria

- `ForumPost(created_by=None)`, `True`, `5001`, `"test_user"`, and `{"id": 12345}` raise `ValueError("created_by must be an AbstractUser")`.
- `ForumPost(created_at=None)`, `True`, `1700000000`, `"2023-11-14"`, and `[]` raise `ValueError("created_at must be a datetime")`.
- Valid `User` and other `AbstractUser` instances remain valid as `created_by`.
- Valid `datetime` values remain valid as `created_at`.
- Existing post-list parsing, parser-side creator/timestamp/edit-metadata diagnostics, direct parent-thread validation, collection search validation, collection initialization, `ForumPost.source`, `ForumPost.revisions`, `ForumPost.edit(...)`, and adjacent forum category/thread/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost.created_by` and `ForumPost.created_at` are durable actor/time fields behind browser-free forum indexing, post-list reads, generated migration ledgers, moderation summaries, cached thread-post scans, duplicate thread-post reuse, source reads, edit workflows, revision traversal, and downstream forum audit tooling. Parser paths already produce real `AbstractUser` and `datetime` values and report malformed generated creator/timestamp metadata with context; the record constructor should apply the same invariant so fixture-created or rehydrated posts cannot carry malformed actor/time state into logs, generated ledgers, migration comparisons, display summaries, or downstream tools.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, generated moderation ledgers, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, lazy source reads, edit workflows, revision traversal, and tests that seed forum-post records directly.
- Existing local drafts covered forum post fetch retry behavior, duplicate thread-post reduction, parser scoping, parser-side user/timestamp/edit-metadata diagnostics, response diagnostics, public acquisition input validation, collection entry validation, collection search-key validation, collection constructor validation, and direct parent-thread validation, but did not cover direct `ForumPost(created_by=..., created_at=...)` construction.
- The focused RED failures showed invalid constructor post creator/time values were accepted as dataclass state. The GREEN regressions cover missing, boolean, numeric, string, dictionary, and list actor/time values.
- This slice only validates stored forum-post creator/time types at construction. It does not change post-list acquisition, parser selectors, title parsing, body parsing, created metadata parsing, edit metadata parsing, collection initialization, `find(...)`, source acquisition, revision acquisition, edit behavior, forum category behavior, forum thread behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, post titles from real sites, post bodies from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates creator type only as `AbstractUser`, not as an integer-ID regular `User`, because the shared user parser can return deleted, anonymous, guest, or Wikidot system users for valid Wikidot markup. It also validates timestamp type only and does not add timezone normalization, epoch parsing, or date-string parsing. Optional edit metadata remains a separate surface because valid unedited posts store `edited_by=None` and `edited_at=None`.
