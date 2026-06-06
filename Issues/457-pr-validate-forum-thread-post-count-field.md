# PR Draft: Validate ForumThread Post Count Field

## Summary

`ForumThread` records carry `post_count` values used by browser-free category thread-list reads, direct thread-detail reads, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, lazy post-list reads, reply workflows, local fixtures, and rehydrated records. Earlier local slices validated parser-side malformed post-count diagnostics, forum reply count updates, adjacent `ForumCategory` count fields, direct lookup IDs, loaded-collection search IDs, parser-extracted thread IDs, create-thread returned IDs, collection constructor entries, parent-category state, direct stored thread IDs, and thread title/description fields. The public `ForumThread(..., post_count=...)` dataclass constructor still accepted malformed stored count values such as `None`, booleans, strings, and floats.

This change validates `ForumThread.post_count` at initialization. Malformed non-integer values now raise `ValueError("post_count must be an integer")`. Valid integers, including zero, remain valid, and parsed threads already produce integers from the existing category thread-list and direct thread-detail parsers.

## Outcome

Callers cannot silently construct forum-thread records whose stored post count is not an integer, while category thread-list parsing, direct thread-detail parsing, parser-side count diagnostics, parser text-fidelity behavior, parser-side ID/user/timestamp diagnostics, public lookup ID validation, collection lookup validation, collection initialization, `ForumThread.id` validation, title/description validation, parent-category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and adjacent forum category/post/revision workflows continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, `ForumThread.posts`, forum replies, local fixtures, or serialized/rehydrated thread records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-thread reads and stored thread records as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [354-pr-validate-forum-write-text-inputs.md](354-pr-validate-forum-write-text-inputs.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), and [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md) establish forum thread acquisition, retry behavior, parser scoping, text fidelity, parser diagnostics, response diagnostics, reply cache synchronization, public lookup validation, loaded-collection lookup validation, returned create-result validation, collection constructor state integrity, parent-category validation, adjacent category constructor validation, direct ID validation, and direct text validation as active operational boundaries.

Those prior slices are not duplicates. Issues 234 and 238 validate parser failures when generated thread-list or thread-detail markup contains malformed post-count text. Issue 268 validates reply-side count/cache updates after a confirmed mutation. Issue 453 validates the separate `ForumCategory.threads_count` and `ForumCategory.posts_count` fields. Issue 379 validates loaded-collection search keys, Issue 423 validates collection entries, Issue 447 validates the optional `ForumThread.category` parent field, Issue 455 validates the separate `ForumThread.id` field, and Issue 456 validates the separate `ForumThread.title` and `ForumThread.description` fields. This slice validates the separate public dataclass `ForumThread.post_count` field so malformed count values cannot become stored record state in manually constructed threads, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), and [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumThread.post_count` validation at dataclass initialization.
- Reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("post_count must be an integer")`.
- Preserve valid integers without coercion.
- Preserve category thread-list parsing, direct thread-detail parsing, parser-side count diagnostics, parser text-fidelity behavior, parser-side ID/user/timestamp diagnostics, public lookup ID validation, collection lookup validation, collection initialization, `ForumThread.id` validation, title/description validation, parent-category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and forum category/post/revision behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-thread record state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(post_count=None)`, `True`, `"5"`, and `5.0` must raise `ValueError("post_count must be an integer")` when every other constructor field is valid. |
| R2 | Valid integer post counts must remain valid constructor input. |
| R3 | Existing category thread-list parsing, direct thread-detail parsing, parser-side count diagnostics, parser text-fidelity behavior, parser-side ID/user/timestamp diagnostics, direct lookup ID validation, collection search validation, collection initialization, direct ID/text/category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply behavior, and forum category/post/revision workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor post-count values fail at the public dataclass boundary. | `TestForumThreadBasic.test_init_rejects_non_integer_post_count` failed RED for `None`, `True`, `"5"`, and `5.0` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, numeric strings, floats, serialized structures, or emitting `ForumThread` records with non-integer post counts rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Valid integer post-count semantics stay green. | Existing `mock_forum_thread_no_http`, `str(...)`, URL generation, category thread-list acquisition, direct thread acquisition, parser count diagnostics, collection lookup, post access, and reply tests passed. | Rejecting ordinary integers, coercing non-integers to integers, fabricating zero, or changing parsed count values rejects this local completion claim. | Parser-created and manually created threads | `tests/unit/test_forum_thread.py` |
| R3 | Existing forum-thread and adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 106 tests, adjacent forum tests passed 366 tests, and full unit tests passed 1776 tests. | Regressing category thread-list parsing, direct thread-detail parsing, parser count diagnostics, parser text fidelity, parser ID/user/timestamp diagnostics, direct lookup ID validation, collection search validation, collection initialization, direct ID/text/category validation, lazy category/thread caches, reply behavior, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, thread titles from real sites, thread descriptions from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-thread tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1062d4b fix(forum_thread): validate thread post counts`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_post_count -q` failed 4 tests before the fix; every malformed `post_count` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_post_count -q` passed 4 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 106 tests.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 366 tests.
- `uv run pytest tests/unit -q` passed 1776 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 66 existing full-tree typing errors outside this slice, including fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumThread(post_count=None)`, `True`, `"5"`, and `5.0` raise `ValueError("post_count must be an integer")`.
- Valid integer post counts remain valid.
- Existing category thread-list parsing, direct thread-detail parsing, parser-side count diagnostics, parser text-fidelity behavior, parser-side ID/user/timestamp diagnostics, direct lookup ID validation, collection search validation, collection initialization, `ForumThread.id` validation, `ForumThread.title` and `ForumThread.description` validation, parent-category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and forum category/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread` is the record shape behind browser-free category thread-list reads, direct thread-detail reads, generated discussion migration ledgers, cached category scans, duplicate direct-thread reuse, lazy post-list reads, replies, and downstream forum post/revision traversal. Parser paths already parse post counts into integers and raise contextual exceptions for malformed generated count text; the record constructor should apply the same invariant so fixture-created or rehydrated threads cannot carry non-integer counts into logs, generated ledgers, migration comparisons, display summaries, reply count updates, or downstream tools.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, direct thread-detail reads, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, lazy post-list reads, reply workflows, and tests that seed forum-thread records directly.
- Existing local drafts covered forum thread fetch retry behavior, duplicate direct-thread reduction, parser scoping, parser-side post-count diagnostics, response diagnostics, public direct lookup ID validation, loaded-collection search-key validation, create-thread returned-ID validation, collection constructor validation, parent-category validation, direct thread-ID validation, and direct thread text-field validation, but did not cover the `ForumThread(post_count=...)` field itself.
- The focused RED failures showed invalid constructor thread post-count values were accepted as dataclass state. The GREEN regression covers missing, boolean, numeric-string, and float values.
- This slice only validates stored forum-thread post-count type at construction. It does not change category thread-list acquisition, direct thread-detail acquisition, parser selectors, title parsing, description parsing, created metadata parsing, post-count parsing, collection initialization, `find(...)`, direct ID/text/category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, forum category behavior, forum post behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, thread titles from real sites, thread descriptions from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them with `int(...)`. Callers that load forum thread post counts from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to integers before constructing `ForumThread` records.
