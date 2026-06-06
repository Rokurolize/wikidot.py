# PR Draft: Validate ForumThread ID Field

## Summary

`ForumThread` records carry an integer `id` used by browser-free category thread-list reads, direct thread-detail reads, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, duplicate thread-detail reuse, cached category scans, lazy post-list reads, reply workflows, local fixtures, and rehydrated records. Earlier local slices validated direct lookup ID inputs, loaded-collection search IDs, parser-extracted thread IDs, create-thread returned IDs, collection constructor entries, parent-category state, category-side fields, parser diagnostics, and response-body diagnostics. The public `ForumThread(..., id=...)` dataclass constructor still accepted malformed stored IDs such as `None`, booleans, strings, and floats.

This change validates `ForumThread.id` at initialization. Malformed non-integer values now raise `ValueError("thread_id must be an integer")`. Valid non-boolean integer IDs remain valid, and parsed threads already use integer IDs from the existing thread-list and thread-detail parsers.

## Outcome

Callers cannot silently construct forum-thread records whose stored thread ID is not an integer, while category thread-list parsing, direct thread-detail parsing, parser-side ID diagnostics, public lookup ID validation, collection lookup validation, `ForumThread.category` validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and adjacent forum category/post/revision workflows continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, `ForumThread.posts`, forum replies, local fixtures, or serialized/rehydrated thread records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-thread reads and stored thread records as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), and [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md) establish forum thread acquisition, retry behavior, parser scoping, text fidelity, parser diagnostics, response diagnostics, public lookup validation, loaded-collection lookup validation, returned create-result validation, collection constructor state integrity, parent-category validation, and adjacent category constructor validation as active operational boundaries.

Those prior slices are not duplicates. Issue 311 validates malformed generated thread IDs while parsing direct thread-detail HTML. Issue 362 validates caller-provided `thread_id` and `thread_ids` inputs before direct lookup request construction. Issue 379 validates `ForumThreadCollection.find(id=...)` search keys after a collection already exists. Issue 407 validates Wikidot's returned `newThread` result ID before cache mutation or created-thread lookup. Issue 423 validates the `ForumThreadCollection(site, threads=...)` container and stored entry types. Issue 447 validates the optional `ForumThread.category` parent field. Issues 452 through 454 validate adjacent `ForumCategory` constructor fields. This slice validates the separate public dataclass `ForumThread.id` field so malformed thread IDs cannot become stored record state in manually constructed threads, fixtures, generated ledgers, or rehydrated records.

## Related Issue / Non-Duplicate Analysis

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [407-pr-reject-boolean-create-thread-ids.md](407-pr-reject-boolean-create-thread-ids.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [452-pr-validate-forum-category-id-field.md](452-pr-validate-forum-category-id-field.md), [453-pr-validate-forum-category-count-fields.md](453-pr-validate-forum-category-count-fields.md), and [454-pr-validate-forum-category-text-fields.md](454-pr-validate-forum-category-text-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `ForumThread.id` validation at dataclass initialization.
- Reuse the existing thread-ID validator so constructor IDs reject non-integers and booleans with `ValueError("thread_id must be an integer")`.
- Preserve valid non-boolean integer IDs.
- Preserve category thread-list parsing, direct thread-detail parsing, parser-side ID diagnostics, public lookup ID validation, collection lookup validation, collection initialization, `ForumThread.category` validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and forum category/post/revision behavior.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Forum-thread record state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `ForumThread(id=None)`, `True`, `"3001"`, and `3001.0` must raise `ValueError("thread_id must be an integer")` when every other constructor field is valid. |
| R2 | Valid non-boolean integer thread IDs must remain valid constructor input. |
| R3 | Existing category thread-list parsing, direct thread-detail parsing, parser-side ID diagnostics, direct lookup ID validation, collection search validation, collection initialization, parent-category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply behavior, and forum category/post/revision workflows must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, forum-thread tests, adjacent forum tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor ID values fail at the public dataclass boundary. | `TestForumThreadBasic.test_init_rejects_non_integer_thread_id` failed RED for `None`, `True`, `"3001"`, and `3001.0` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, floats, serialized IDs, or emitting `ForumThread` records with non-integer IDs rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Valid integer ID semantics stay green. | Existing `mock_forum_thread_no_http`, `str(...)`, URL generation, category thread-list acquisition, direct thread acquisition, collection lookup, post access, and reply tests passed. | Rejecting ordinary integer IDs, coercing strings to integers, or changing stored IDs rejects this local completion claim. | Parser-created and manually created threads | `tests/unit/test_forum_thread.py` |
| R3 | Existing forum-thread and adjacent forum workflows remain green. | `tests/unit/test_forum_thread.py` passed 94 tests, adjacent forum tests passed 354 tests, and full unit tests passed 1764 tests. | Regressing category thread-list parsing, direct thread-detail parsing, parser-side ID diagnostics, direct lookup ID validation, collection search validation, collection initialization, parent-category validation, lazy category/thread caches, reply behavior, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | Forum thread and adjacent forum workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, forum-thread tests passed, adjacent forum tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `9055db8 fix(forum_thread): validate thread id field`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_thread_id -q` failed 4 tests before the fix; every malformed `id` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_thread_id -q` passed 4 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 94 tests.
- `uv run pyright src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run mypy src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 354 tests.
- `uv run pytest tests/unit -q` passed 1764 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 66 existing full-tree typing errors outside this slice, including fixture `None` mismatches, intentional invalid-input test calls, requestutil response narrowing issues, invalid `SearchPagesQuery` parameter calls, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `ForumThread(id=None)`, `True`, `"3001"`, and `3001.0` raise `ValueError("thread_id must be an integer")`.
- Valid non-boolean integer IDs remain valid.
- Existing category thread-list parsing, direct thread-detail parsing, parser-side ID diagnostics, direct lookup ID validation, collection search validation, collection initialization, parent-category validation, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, and forum category/post/revision workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumThread` is the record shape behind browser-free category thread-list reads, direct thread-detail reads, generated discussion migration ledgers, cached category scans, duplicate direct-thread reuse, lazy post-list reads, replies, and downstream forum post/revision traversal. Public direct lookup and collection search APIs already validate caller-provided thread IDs; the record constructor should apply the same invariant so fixture-created or rehydrated threads cannot carry non-integer IDs into URLs, maps, cache keys, comparisons, request payloads, logs, or downstream ledgers.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, direct thread-detail reads, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, lazy post-list reads, and tests that seed forum-thread records directly.
- Existing local drafts covered forum thread fetch retry behavior, duplicate direct-thread reduction, parser scoping, response diagnostics, parser field diagnostics, public direct lookup ID validation, loaded-collection search-key validation, create-thread returned-ID validation, collection constructor validation, and parent-category validation, but did not cover the `ForumThread(id=...)` field itself.
- The focused RED failures showed invalid constructor thread IDs were accepted as dataclass state. The GREEN regression covers missing, boolean, string, and float ID values.
- This slice only validates stored forum-thread ID type at construction. It does not change category thread-list acquisition, direct thread-detail acquisition, parser selectors, title parsing, description parsing, created metadata parsing, post-count parsing, collection initialization, `find(...)`, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, forum category behavior, forum post behavior, forum post revision behavior, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load forum thread IDs from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to integers before constructing `ForumThread` records.
