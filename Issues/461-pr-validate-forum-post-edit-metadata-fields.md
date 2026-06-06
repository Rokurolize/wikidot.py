# PR Draft: Validate ForumPost Edit Metadata Fields

## Summary

`ForumPost` records store optional edit metadata in `edited_by` and `edited_at`. Earlier local slices validated parser-side forum-post edit-user and edit-timestamp diagnostics, direct parent-thread state, direct creator/time metadata, direct ID/title/text fields, collection entries, collection initialization, collection search IDs, acquisition inputs, source response diagnostics, and write-side edit inputs. The public `ForumPost(..., edited_by=..., edited_at=...)` dataclass constructor still accepted malformed non-`None` edit metadata such as booleans, integers, strings, dictionaries, lists, and epoch/date strings, letting callers create fixture, ledger, or rehydrated post records whose optional editor was not an `AbstractUser` or whose edit time was not a `datetime`.

This change validates `ForumPost.edited_by` and `ForumPost.edited_at` at initialization while preserving `None` for valid unedited posts. Non-`None` `edited_by` values must be `AbstractUser` instances, and non-`None` `edited_at` values must be `datetime` instances. Malformed values raise stable `ValueError` diagnostics: `edited_by must be an AbstractUser or None` and `edited_at must be a datetime or None`. Valid post-list parsing, parser-side post ID/user/timestamp/edit-metadata diagnostics, direct thread validation, direct creator/time validation, direct ID/title/text validation, collection validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows remain unchanged.

## Outcome

Callers cannot silently construct edited forum-post records with malformed editor or edit-time metadata, while unedited posts with `edited_by=None` and `edited_at=None`, parser-created posts, and valid direct `ForumPost(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, `ForumThread.posts`, forum post source reads, forum post edit workflows, forum post revisions, local fixtures, or serialized/rehydrated post records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-post reads and stored post records as practical workflow surfaces. Existing drafts [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md), [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [097-pr-ignore-forum-content-pager-markup.md](097-pr-ignore-forum-content-pager-markup.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [125-pr-reuse-cached-duplicate-forum-post-sources.md](125-pr-reuse-cached-duplicate-forum-post-sources.md), [134-pr-skip-cached-thread-post-list-fetches.md](134-pr-skip-cached-thread-post-list-fetches.md), [141-pr-reuse-cached-duplicate-thread-posts.md](141-pr-reuse-cached-duplicate-thread-posts.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [161-pr-forum-post-source-error-context.md](161-pr-forum-post-source-error-context.md), [171-pr-forum-post-list-fetch-failure-context.md](171-pr-forum-post-list-fetch-failure-context.md), [174-pr-forum-post-lazy-source-failure-context.md](174-pr-forum-post-lazy-source-failure-context.md), [175-pr-forum-post-source-form-parse-context.md](175-pr-forum-post-source-form-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [209-pr-forum-post-source-response-body-context.md](209-pr-forum-post-source-response-body-context.md), [235-pr-forum-post-id-parse-context.md](235-pr-forum-post-id-parse-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [296-pr-forum-post-list-timestamp-context.md](296-pr-forum-post-list-timestamp-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [327-pr-forum-post-response-body-type-context.md](327-pr-forum-post-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), and [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md) establish forum post acquisition, retry behavior, duplicate handling, parser scoping, text fidelity, parser diagnostics, response diagnostics, source acquisition, edit preflight, public acquisition input validation, collection-entry validation, search-key validation, collection constructor integrity, parent-thread constructor validation, creator/time constructor validation, and identity/text constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issues 297 and 298 validate parser-side generated edit metadata before parser-side `ForumPost` construction. Issue 082 and Issue 123 validate selector scoping for generated edit metadata. Issue 354 validates write-side source/title text passed into forum mutations. Issue 446 validates the separate public `ForumPost.thread` parent field. Issue 459 validates required `ForumPost.created_by` and `ForumPost.created_at` fields. Issue 460 validates required `ForumPost.id`, `ForumPost.title`, and `ForumPost.text` fields. This slice validates the separate optional public dataclass `ForumPost.edited_by` and `ForumPost.edited_at` fields so malformed non-`None` edit metadata cannot become stored record state in manually constructed posts, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [059-pr-deduplicate-thread-post-fetches.md](059-pr-deduplicate-thread-post-fetches.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), [160-pr-forum-post-list-parse-context.md](160-pr-forum-post-list-parse-context.md), [208-pr-forum-post-list-response-body-context.md](208-pr-forum-post-list-response-body-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [298-pr-forum-post-list-edit-timestamp-context.md](298-pr-forum-post-list-edit-timestamp-context.md), [363-pr-validate-forum-post-thread-inputs.md](363-pr-validate-forum-post-thread-inputs.md), [367-pr-validate-forum-post-collection-entries.md](367-pr-validate-forum-post-collection-entries.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [446-pr-validate-forum-post-thread-field.md](446-pr-validate-forum-post-thread-field.md), [459-pr-validate-forum-post-creator-time-fields.md](459-pr-validate-forum-post-creator-time-fields.md), [460-pr-validate-forum-post-identity-text-fields.md](460-pr-validate-forum-post-identity-text-fields.md), and the adjacent direct record-field pattern from [458-pr-validate-forum-thread-creator-time-fields.md](458-pr-validate-forum-thread-creator-time-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add optional `ForumPost.edited_by` validation at dataclass initialization.
- Add optional `ForumPost.edited_at` validation at dataclass initialization.
- Preserve `edited_by=None` for valid unedited posts.
- Preserve `edited_at=None` for valid unedited posts.
- Reject non-`None`, non-`AbstractUser` `edited_by` values with `ValueError("edited_by must be an AbstractUser or None")`.
- Reject non-`None`, non-`datetime` `edited_at` values with `ValueError("edited_at must be a datetime or None")`.
- Preserve valid `AbstractUser` subclasses without requiring regular integer-ID `User` instances.
- Preserve valid `datetime` edit timestamps without timezone normalization or coercion.
- Preserve post-list parsing, parser-side post ID/user/timestamp/edit-metadata diagnostics, direct thread validation, direct creator/time validation, direct identity/text validation, collection validation, lazy `ForumPost.source`, lazy `ForumPost.revisions`, edit behavior, and adjacent forum category/thread/revision behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Optional forum-post edit metadata state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumPost(edited_by=True)`, `5001`, `"edit_user"`, and `{"id": 12345}` must raise `ValueError("edited_by must be an AbstractUser or None")` before storing record state. |
| R2 | `ForumPost(edited_at=True)`, `1700000000`, `"2023-11-14"`, and `[]` must raise `ValueError("edited_at must be a datetime or None")` before storing record state. |
| R3 | `edited_by=None` and `edited_at=None` must remain valid for unedited posts. |
| R4 | Valid non-`None` `AbstractUser` instances and valid non-`None` `datetime` timestamps must remain valid and preserve stored values. |
| R5 | Existing post-list parsing, parser-side ID/user/timestamp/edit-metadata diagnostics, direct thread validation, direct creator/time validation, direct identity/text validation, collection initialization, collection search validation, lazy source reads, lazy revision reads, edit behavior, and adjacent forum category/thread/revision workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed non-`None` constructor editors fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_edited_by` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after optional editor validation was added. | Accepting booleans, integers, strings, dictionaries, arbitrary objects, or emitting edited post records with non-user editors rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Malformed non-`None` constructor edit timestamps fail at the public dataclass boundary. | `TestForumPostBasic.test_init_rejects_malformed_edited_at` failed RED for 4 malformed values because the constructor did not raise, then passed GREEN after optional edit timestamp validation was added. | Accepting booleans, epoch integers, date strings, lists, arbitrary objects, or emitting edited post records with non-datetime edit timestamps rejects this local completion claim. | ForumPost constructor | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R3 | Unedited-post semantics stay valid. | The unchanged `mock_forum_post_no_http` fixture constructs posts with `edited_by=None` and `edited_at=None`, and existing constructor, string, source, revision, parser, and edit tests passed. | Rejecting `None`, fabricating an editor, fabricating an edit timestamp, or changing `ForumPost.has_revisions` for unedited posts rejects this local completion claim. | Parser-created and manually created posts | `tests/conftest.py`, `tests/unit/test_forum_post.py` |
| R4 | Valid edited-post metadata semantics stay valid. | Existing parser tests that preserve top-level edit metadata still pass and adjacent forum post revision tests still pass. | Rejecting valid `AbstractUser` subclasses, changing stored editor objects, coercing timestamps, rejecting valid `datetime` values, or dropping parsed edit metadata rejects this local completion claim. | Parser-created edited posts | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py` |
| R5 | Existing forum-post and adjacent forum workflows remain green. | `tests/unit/test_forum_post.py` passed 129 tests, adjacent forum tests passed 406 tests, and full unit tests passed 1816 tests. | Regressing post-list parsing, parser ID/user/timestamp/edit-metadata diagnostics, source acquisition, lazy revision acquisition, edit behavior, parent-thread validation, creator/time validation, identity/text validation, collection validation, forum category behavior, forum thread behavior, or forum post revision behavior rejects this local completion claim. | Forum post and adjacent forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, post titles from real sites, post bodies from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-post tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `3815031 fix(forum_post): validate post edit metadata`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_edited_by tests/unit/test_forum_post.py::TestForumPostBasic::test_init_rejects_malformed_edited_at -q` failed 8 tests before the fix; every malformed `edited_by` and `edited_at` value reported `DID NOT RAISE`.
- GREEN: the same focused command passed 8 tests after optional editor/edit-timestamp validation was added.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 129 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 406 tests.
- `uv run pytest tests/unit -q` passed 1816 tests.
- `uv run ruff check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed.
- `uv run ruff format --check src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 2 files already formatted.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with no issues in 2 source files.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `uv run pyright src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 61 existing full-tree typing errors outside this slice, including page fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed forum-post test file pass pyright together.

## Acceptance Criteria

- `ForumPost(edited_by=True)`, `5001`, `"edit_user"`, and `{"id": 12345}` raise `ValueError("edited_by must be an AbstractUser or None")`.
- `ForumPost(edited_at=True)`, `1700000000`, `"2023-11-14"`, and `[]` raise `ValueError("edited_at must be a datetime or None")`.
- `ForumPost(edited_by=None)` remains valid for unedited posts.
- `ForumPost(edited_at=None)` remains valid for unedited posts.
- Valid `AbstractUser` instances remain valid as non-`None` `edited_by`.
- Valid `datetime` values remain valid as non-`None` `edited_at`.
- Existing post-list parsing, parser-side edit-user/edit-timestamp diagnostics, direct parent-thread validation, direct creator/time validation, direct identity/text validation, collection search validation, collection initialization, `ForumPost.source`, `ForumPost.revisions`, `ForumPost.edit(...)`, and adjacent forum category/thread/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost.edited_by` and `ForumPost.edited_at` are durable optional edit metadata fields behind browser-free forum indexing, post-list reads, generated migration ledgers, moderation summaries, cached thread-post scans, duplicate thread-post reuse, source reads, edit workflows, revision traversal, and downstream forum audit tooling. Parser paths already produce either `None` for unedited posts or real `AbstractUser` and `datetime` values for edited posts, and they report malformed generated edit metadata with context; the record constructor should apply the same invariant so fixture-created or rehydrated posts cannot carry malformed edit metadata into logs, generated ledgers, migration comparisons, display summaries, or downstream tools.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, generated moderation ledgers, translation review tooling, forum migration checks, cached thread-post scans, duplicate thread-post reads, lazy source reads, edit workflows, revision traversal, and tests that seed forum-post records directly.
- Existing local drafts covered forum post fetch retry behavior, duplicate thread-post reduction, parser scoping, parser-side user/timestamp/edit-metadata diagnostics, response diagnostics, public acquisition input validation, collection entry validation, collection search-key validation, collection constructor validation, direct parent-thread validation, direct creator/time validation, and direct identity/text validation, but did not cover direct `ForumPost(edited_by=..., edited_at=...)` construction.
- The focused RED failures showed invalid non-`None` constructor post edit metadata values were accepted as dataclass state. The GREEN regressions cover boolean, numeric, string, dictionary, and list actor/time values while preserving `None`.
- This slice only validates stored optional forum-post edit metadata types at construction. It does not change post-list acquisition, parser selectors, title parsing, body parsing, created metadata parsing, edit metadata parsing, collection initialization, `find(...)`, source acquisition, revision acquisition, edit behavior, forum category behavior, forum thread behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, post titles from real sites, post bodies from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates optional metadata type only. It does not require edited posts to set both `edited_by` and `edited_at` together, add timezone normalization, parse epoch integers, parse date strings, infer revisions, or change `ForumPost.has_revisions`; those would be separate behavior changes with separate parser or workflow evidence.
