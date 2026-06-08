# PR Draft: Validate Non-Negative ForumThread Post Counts

## Summary

`ForumThread` records store `post_count` values used by browser-free category thread-list reads, direct thread-detail reads, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, lazy post-list reads, reply workflows, local fixtures, and rehydrated records. Issue 457 validated that direct `ForumThread.post_count` values are non-boolean integers, but it did not cover the separate domain invariant that a thread cannot have a negative post count. Issues 234 and 238 validate malformed non-integer generated count text, but parseable negative count text still became stored thread state, and direct thread detail text such as `Number of posts: -1` was parsed as `1`.

This change validates forum thread post counts as non-negative integers. Direct negative constructor values now raise `ValueError("post_count must be non-negative")`. Generated category thread-list rows with negative `posts` cells now raise contextual `NoElementException` diagnostics with site, category, page, row, field, and value. Direct thread-detail generated statistics with negative post-count text now raise contextual `NoElementException` diagnostics with site, thread, field, and value. Zero counts remain valid because empty or newly created threads can exist as legitimate stored state.

## Outcome

Direct and parser-created `ForumThread` records can no longer store negative post counts, while valid zero counts, valid positive counts, existing malformed-type diagnostics, existing malformed-text parser diagnostics, category thread-list parsing, direct thread-detail parsing, and adjacent forum workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum indexing, generated discussion migration ledgers, moderation tooling, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, `ForumThread.posts`, forum replies, local fixtures, or serialized/rehydrated thread records.

## Current Evidence

Local rollout-backed drafts repeatedly identify forum-thread reads and stored thread records as practical workflow surfaces. Existing drafts [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [268-pr-forum-thread-reply-category-cache-sync.md](268-pr-forum-thread-reply-category-cache-sync.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [447-pr-validate-forum-thread-category-field.md](447-pr-validate-forum-thread-category-field.md), [455-pr-validate-forum-thread-id-field.md](455-pr-validate-forum-thread-id-field.md), [456-pr-validate-forum-thread-text-fields.md](456-pr-validate-forum-thread-text-fields.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [607-pr-validate-forum-thread-creator-client.md](607-pr-validate-forum-thread-creator-client.md), [618-pr-validate-forum-thread-category-site.md](618-pr-validate-forum-thread-category-site.md), and [634-pr-validate-non-negative-forum-category-counts.md](634-pr-validate-non-negative-forum-category-counts.md) establish forum thread acquisition, retry behavior, parser scoping, text fidelity, parser diagnostics, response diagnostics, reply cache synchronization, public lookup validation, collection constructor state integrity, direct scalar validation, retained client/site validation, and adjacent non-negative forum count validation as active operational boundaries.

This slice is not a duplicate of Issue 457. Issue 457 validated integer type and boolean rejection for direct thread post counts; this follow-up covers the separate non-negative count invariant while preserving zero counts. This slice is also not a duplicate of Issues 234 or 238, which validate malformed non-integer parser text such as `not-a-number`; this follow-up covers parseable but impossible negative generated count values, including direct thread-detail text that previously matched the positive digits inside a negative value. This slice is adjacent to, but separate from, Issue 634 because `ForumCategory.threads_count` and `posts_count` are category summary fields, while `ForumThread.post_count` is per-thread state.

## Related Issue / Non-Duplicate Analysis

Builds directly on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [607-pr-validate-forum-thread-creator-client.md](607-pr-validate-forum-thread-creator-client.md), [618-pr-validate-forum-thread-category-site.md](618-pr-validate-forum-thread-category-site.md), and [634-pr-validate-non-negative-forum-category-counts.md](634-pr-validate-non-negative-forum-category-counts.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a non-negative check to `ForumThread.post_count` validation after the existing non-boolean integer check.
- Reject direct negative thread post counts with `ValueError("post_count must be non-negative")`.
- Add parser-side non-negative checks for generated category thread-list `posts` cells.
- Parse direct thread-detail post-count labels as signed numeric values so `Number of posts: -1` fails instead of becoming `1`.
- Preserve zero counts for empty or newly created thread records.
- Preserve existing malformed count-type diagnostics, malformed count-text parser diagnostics, successful category thread-list parsing, direct thread-detail parsing, thread ID parsing, title/description parsing, creator/timestamp parsing, lazy category/thread/post reads, reply behavior, and adjacent forum category/post/revision workflows.

## Type Of Change

- Input validation
- Parser diagnostics
- Public dataclass constructor behavior hardening
- Forum-thread count state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Direct `ForumThread(post_count=-1)` must raise `ValueError("post_count must be non-negative")`. |
| R2 | Direct `ForumThread(post_count=0)` must remain valid. |
| R3 | Existing malformed type diagnostics must remain `ValueError("post_count must be an integer")`. |
| R4 | Generated category thread-list rows with negative `posts` cells must raise contextual `NoElementException` with site, category, page, row, field, and raw value. |
| R5 | Generated direct thread-detail statistics with negative post-count text must raise contextual `NoElementException` with site, thread, field, and raw value. |
| R6 | Existing malformed non-integer parser diagnostics for thread-list and thread-detail post-count text must remain unchanged. |
| R7 | Successful category thread-list parsing, direct thread-detail parsing, thread ID parsing, title/description parsing, creator/timestamp parsing, collection initialization, direct lookup, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, reply behavior, and adjacent forum category/post/revision workflows must remain unchanged. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, forum-thread tests, adjacent forum workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative direct thread post counts fail at the public constructor boundary. | `TestForumThreadBasic.test_init_rejects_negative_post_count` failed RED with `DID NOT RAISE`, then passed GREEN after `_validate_thread_post_count(...)` rejected negative integers. | Accepting negative thread counts, coercing them to zero, or deferring failure to later forum workflows rejects this local completion claim. | ForumThread constructor | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | Zero thread post counts remain valid. | `TestForumThreadBasic.test_init_accepts_zero_post_count` passed in RED and GREEN and asserts the field stores `0`. | Rejecting empty threads or requiring positive counts rejects this local completion claim. | ForumThread constructor compatibility | `tests/unit/test_forum_thread.py` |
| R3 | Existing malformed-type diagnostics remain stable. | `test_init_rejects_non_integer_post_count` passed in the focused RED and GREEN commands. | Changing type diagnostics, accepting booleans as integers, or coercing strings/floats rejects this local completion claim. | ForumThread constructor type validation | `tests/unit/test_forum_thread.py` |
| R4 | Negative generated category thread-list counts fail with parser context. | `TestForumThreadCollectionAcquireAll.test_acquire_all_negative_post_count_includes_category_context` failed RED with `DID NOT RAISE`, then passed GREEN with contextual `NoElementException` diagnostics. | Returning a `ForumThread` with a negative generated list count, raising a raw constructor `ValueError`, omitting category/page/row/field/value context, or silently clamping the value rejects this local completion claim. | Category thread-list parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R5 | Negative generated direct thread-detail counts fail with parser context. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_negative_post_count_includes_thread_and_value_context` failed RED with `DID NOT RAISE`, then passed GREEN with contextual `NoElementException` diagnostics. | Parsing `Number of posts: -1` as `1`, returning a negative count, raising a raw constructor `ValueError`, omitting thread/field/value context, or silently clamping the value rejects this local completion claim. | Direct thread-detail parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R6 | Existing malformed non-integer parser diagnostics remain stable. | `test_acquire_all_malformed_post_count_includes_category_context` and `test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context` passed in the focused RED and GREEN commands. | Treating malformed strings as negative, changing `Posts count is malformed` / `Post count is malformed`, or dropping context rejects this local completion claim. | ForumThread parser compatibility | `tests/unit/test_forum_thread.py` |
| R7 | Existing forum-thread and adjacent forum workflows remain green. | Forum-thread coverage passed 155 tests, adjacent forum coverage passed 556 tests, and full unit coverage passed 2865 tests. | Regressing valid category thread-list parsing, direct thread-detail parsing, direct lookup, duplicate handling, lazy category/thread/post behavior, reply behavior, forum category behavior, forum post behavior, or forum post revision behavior rejects this local completion claim. | ForumThread and adjacent workflows | `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_post.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R8 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic `ForumThread` or generated fixture data only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML from real sites, forum source text, thread titles/descriptions from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, module and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c685f2f fix(forum_thread): validate non-negative post counts`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_post_count_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_negative_post_count_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_negative_post_count_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_non_integer_post_count tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_rejects_negative_post_count tests/unit/test_forum_thread.py::TestForumThreadBasic::test_init_accepts_zero_post_count -q` failed 3 new negative-count cases before the fix with `DID NOT RAISE`; malformed count-type, malformed count-text parser, and zero-count guards stayed green.
- GREEN: the same focused command passed 10 tests after constructor and parser non-negative validation was added.
- `uv run ruff format src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 155 tests.
- `uv run ruff check src/wikidot/module/forum_thread.py tests/unit/test_forum_thread.py` passed.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 556 tests.
- `uv run pytest tests/unit -q` passed 2865 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThread(post_count=-1)` raises `ValueError("post_count must be non-negative")`.
- `ForumThread(post_count=0)` remains valid.
- Existing malformed type inputs still raise `ValueError("post_count must be an integer")`.
- A generated category thread-list `posts=-1` cell raises `NoElementException("Posts count must be non-negative for site: test-site (category=1001, page=1, row=1, field=posts, value=-1)")`.
- A generated direct thread-detail statistic `Number of posts: -1` raises `NoElementException("Post count must be non-negative for site: test-site (thread=3001, field=posts, value=Number of posts: -1)")`.
- Existing malformed non-integer category thread-list and direct thread-detail post-count diagnostics remain unchanged.
- Existing category thread-list parsing, direct thread-detail parsing, direct lookup, duplicate handling, lazy category/thread/post behavior, reply behavior, forum category behavior, forum post behavior, and forum post revision behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Forum thread post counts cannot be negative. Parser-side integer conversion already makes malformed textual values visible; this follow-up catches parseable but impossible negatives while preserving zero-count compatibility. Direct constructor validation keeps generated ledgers, local fixtures, rehydrated records, moderation summaries, and downstream audit tooling from carrying impossible per-thread metrics.

## Local Evidence

- Local rollout evidence used browser-free forum indexing, direct thread-detail reads, generated moderation ledgers, translation review tooling, forum migration checks, cached category scans, duplicate direct-thread reads, lazy post-list reads, reply workflows, and tests that seed forum-thread records directly.
- Existing local drafts covered forum thread fetch retry behavior, duplicate direct-thread reduction, parser scoping, parser-side malformed post-count diagnostics, response diagnostics, public direct lookup ID validation, loaded-collection search-key validation, collection constructor validation, parent-category validation, direct scalar validation, retained owner validation, and adjacent non-negative category counts, but did not cover negative `ForumThread.post_count` values.
- The focused RED failures showed negative direct thread post counts, negative generated category thread-list post counts, and negative direct thread-detail post counts were accepted as stored thread state. The GREEN regressions cover negative values, zero compatibility, pre-existing malformed type validation, existing malformed parser text validation, and contextual parser diagnostics.
- This slice only validates non-negative forum thread post counts. It does not change category thread-list acquisition, direct thread-detail acquisition, parser selectors, thread ID parsing, title parsing, description parsing, created metadata parsing, collection initialization, `find(...)`, lazy `ForumCategory.threads`, lazy `ForumThread.posts`, `ForumThread.reply(...)`, forum category behavior, forum post behavior, forum post revision behavior, live site behavior, or parsing beyond negative count values.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, raw forum HTML from real sites, page source text, forum source text, thread titles/descriptions from real sites, and private site data out of upstream discussion.

## Additional Notes

This change intentionally validates thread post counts only. Forum post IDs, revision IDs, and other numeric identifier ranges have separate compatibility histories and should be considered only in duplicate-checked follow-up slices.
