# PR Draft: Validate ForumThread Creator And Time Fields

## Summary

`ForumThread` records store generated creator and creation-time metadata in `created_by` and `created_at`. Earlier local slices validated parser-side thread-list and thread-detail user/timestamp diagnostics, direct thread IDs, direct thread text fields, direct post counts, parent-category state, collection entries, public lookup IDs, loaded-collection search IDs, and adjacent category fields. The public `ForumThread(..., created_by=..., created_at=...)` dataclass constructor still accepted malformed direct metadata values such as `None`, booleans, integers, strings, dictionaries, and lists, letting callers create fixture, ledger, or rehydrated thread records whose creator was not an `AbstractUser` or whose creation time was not a `datetime`.

This change validates `ForumThread.created_by` and `ForumThread.created_at` at initialization. `created_by` now accepts only `AbstractUser` instances, preserving regular, deleted, anonymous, guest, and Wikidot system users that can be returned by the shared user parser. `created_at` now accepts only `datetime` instances. Malformed values raise stable `ValueError` diagnostics: `created_by must be an AbstractUser` and `created_at must be a datetime`. Valid category thread-list parsing, direct thread-detail parsing, parser-side ID/user/timestamp/count diagnostics, direct ID/text/post-count/category validation, collection validation, lazy post access, replies, and adjacent forum category/post/revision workflows remain unchanged.

## Outcome

Callers cannot silently construct forum-thread records with non-user creators or non-datetime creation timestamps, while parser-created threads and valid direct `ForumThread(...)` construction remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, direct thread-detail reads, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, `ForumThread.posts`, forum replies, local fixtures, or serialized/rehydrated thread records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-thread reads and stored thread records as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), and [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md) establish forum thread acquisition, retry behavior, parser scoping, text fidelity, parser diagnostics, response diagnostics, reply cache synchronization, public lookup validation, loaded-collection lookup validation, returned create-result validation, collection constructor state integrity, parent-category validation, adjacent category constructor validation, direct ID validation, direct text validation, and direct post-count validation as active operational boundaries.

Those prior slices are not duplicates. Issues 291 and 293 validate parser-side generated creator metadata before parser-side `ForumThread` construction. Issues 292 and 294 validate parser-side generated timestamp metadata. Issue 447 validates the optional `ForumThread.category` parent field, Issue 455 validates the separate `ForumThread.id` field, Issue 456 validates the separate `ForumThread.title` and `ForumThread.description` fields, and Issue 457 validates the separate `ForumThread.post_count` field. This slice validates the separate public dataclass `ForumThread.created_by` and `ForumThread.created_at` fields so malformed actor/time values cannot become stored record state in manually constructed threads, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), and [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumThread.created_by` validation at dataclass initialization.
- Add `ForumThread.created_at` validation at dataclass initialization.
- Reject non-`AbstractUser` `created_by` values with `ValueError("created_by must be an AbstractUser")`.
- Reject non-`datetime` `created_at` values with `ValueError("created_at must be a datetime")`.
- Tighten the unit fixture `mock_forum_thread_no_http` to use a real `User` and `datetime` instead of malformed `None` placeholders.
- Preserve valid `AbstractUser` subclasses without requiring regular integer-ID `User` instances.
- Preserve valid `datetime` timestamps without timezone normalization or coercion.
- Preserve category thread-list parsing, direct thread-detail parsing, parser-side ID/user/timestamp/count diagnostics, direct ID/text/post-count/category validation, collection validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and forum category/post/revision behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-thread metadata state integrity
- Test fixture tightening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(created_by=None)`, `True`, `3001`, `"test_user"`, and `{"id": 12345}` must raise `ValueError("created_by must be an AbstractUser")` before storing record state. |
| R2 | `ForumThread(created_at=None)`, `True`, `1700000000`, `"2023-11-14"`, and `[]` must raise `ValueError("created_at must be a datetime")` before storing record state. |
| R3 | Valid `AbstractUser` instances and valid `datetime` timestamps must remain valid and preserve stored values. |
| R4 | Existing category thread-list parsing, direct thread-detail parsing, parser-side ID/user/timestamp/count diagnostics, direct lookup ID validation, collection search validation, collection initialization, direct ID/text/post-count/category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply behavior, and forum category/post/revision workflows must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor creators fail at the public dataclass boundary. | `TestForumThreadBasic.test_init_rejects_malformed_created_by` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after creator validation was added. | Accepting missing values, booleans, integers, strings, dictionaries, arbitrary objects, or emitting thread records with non-user creators rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Malformed constructor timestamps fail at the public dataclass boundary. | `TestForumThreadBasic.test_init_rejects_malformed_created_at` failed RED for 5 malformed values because the constructor did not raise, then passed GREEN after timestamp validation was added. | Accepting missing values, booleans, epoch integers, date strings, lists, arbitrary objects, or emitting thread records with non-datetime timestamps rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R3 | Valid creator/time semantics stay green. | The `mock_forum_thread_no_http` fixture now uses a real `User` and `datetime`; existing constructor, string, URL, parser, post access, and reply tests passed. | Rejecting valid `AbstractUser` subclasses, changing stored users, coercing timestamps, or rejecting valid `datetime` values rejects this local completion claim. | Parser-created and manually created threads | `tests/conftest.py`, `tests/unit/test_forum_thread.py` |
| R4 | Existing forum-thread and adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 116 tests, adjacent forum tests passed 376 tests, and full unit tests passed 1786 tests. | Regressing category thread-list parsing, direct thread-detail parsing, parser user/timestamp/count diagnostics, direct lookup ID validation, collection search validation, collection initialization, direct ID/text/post-count/category validation, lazy category/thread caches, reply behavior, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, thread titles from real sites, thread descriptions from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-thread tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `97f2d23 fix(forum_thread): validate thread creator metadata`.

- RED 1: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_by -q` failed 5 tests before the fix; every malformed `created_by` value reported `DID NOT RAISE`.
- GREEN 1: the same focused creator command passed 5 tests after creator validation and fixture tightening were added.
- RED 2: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_at -q` failed 5 tests before the timestamp fix; every malformed `created_at` value reported `DID NOT RAISE`.
- GREEN 2: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_by tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_malformed_created_at -q` passed 10 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py tests/conftest.py` passed.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 116 tests.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py tests/conftest.py` passed with no issues in 3 source files.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 376 tests.
- `uv run pytest tests/unit -q` passed 1786 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 64 existing full-tree typing errors outside this slice, including fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed forum-thread test file pass pyright together.

## Acceptance Criteria

- `ForumThread(created_by=None)`, `True`, `3001`, `"test_user"`, and `{"id": 12345}` raise `ValueError("created_by must be an AbstractUser")`.
- `ForumThread(created_at=None)`, `True`, `1700000000`, `"2023-11-14"`, and `[]` raise `ValueError("created_at must be a datetime")`.
- Valid `User` and other `AbstractUser` instances remain valid as `created_by`.
- Valid `datetime` values remain valid as `created_at`.
- Existing category thread-list parsing, direct thread-detail parsing, parser-side user/timestamp/count diagnostics, direct lookup ID validation, collection search validation, collection initialization, `ForumThread.id`, `ForumThread.title`, `ForumThread.description`, `ForumThread.post_count`, parent-category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and forum category/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread.created_by` and `ForumThread.created_at` are durable actor/time fields behind browser-free forum indexing, direct thread-detail reads, generated migration ledgers, moderation summaries, cached category scans, duplicate direct-thread reuse, lazy post-list reads, replies, and downstream forum post/revision traversal. Parser paths already produce real `AbstractUser` and `datetime` values and report malformed generated creator/timestamp metadata with context; the record constructor should apply the same invariant so fixture-created or rehydrated threads cannot carry malformed actor/time state into logs, generated ledgers, migration comparisons, display summaries, or downstream tools.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, direct thread-detail reads, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, lazy post-list reads, reply workflows, and tests that seed forum-thread records directly.
- Existing local drafts covered forum thread fetch retry behavior, duplicate direct-thread reduction, parser scoping, parser-side user/timestamp diagnostics, response diagnostics, public direct lookup ID validation, loaded-collection search-key validation, create-thread returned-ID validation, collection constructor validation, parent-category validation, direct thread-ID validation, direct thread text-field validation, and direct post-count validation, but did not cover direct `ForumThread(created_by=..., created_at=...)` construction.
- The focused RED failures showed invalid constructor thread creator/time values were accepted as dataclass state. The GREEN regressions cover missing, boolean, numeric, string, dictionary, and list actor/time values.
- This slice only validates stored forum-thread creator/time types at construction. It does not change category thread-list acquisition, direct thread-detail acquisition, parser selectors, title parsing, description parsing, created metadata parsing, post-count parsing, collection initialization, `find(...)`, direct ID/text/post-count/category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, forum category behavior, forum post behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, thread titles from real sites, thread descriptions from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates creator type only as `AbstractUser`, not as an integer-ID regular `User`, because the shared user parser can return deleted, anonymous, guest, or Wikidot system users for valid Wikidot markup. It also validates timestamp type only and does not add timezone normalization, epoch parsing, or date-string parsing.
