# PR Draft: Validate Forum Thread List Post-Count ASCII Shape

## Summary

`ForumThreadCollection.acquire_all_in_category(...)`, exposed through `ForumCategory.threads`, parses generated category thread-list rows from `forum/ForumViewCategoryModule` into `ForumThread` records. Issue 234 converted malformed list post-count cells such as `not-a-number` into contextual `NoElementException`, and Issue 635 rejects parseable negative generated counts such as `-1`. One accepted-value gap remained: `_parse_thread_list_count(...)` still passed the generated `posts` cell text directly to Python `int(...)`, so a non-ASCII digit glyph such as `\uff15` was accepted and normalized into ordinary `post_count=5`.

This change accepts generated forum thread-list post counts only when the cell text matches ASCII digits, with the existing optional leading minus retained so negative ASCII values continue through the established non-negative diagnostic. Valid generated count cells such as `5` and `3` continue to parse normally, malformed text keeps the contextual `Posts count is malformed ...` path, negative ASCII cells keep the contextual non-negative path, and non-ASCII digit-like cells now fail before any `ForumThread` record is returned.

## Outcome

Category thread-list parsing no longer fabricates thread post counts by normalizing malformed generated count metadata. A `forum/ForumViewCategoryModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like count text now fails at the thread-list parser boundary with site, category, page, row, field, and observed value context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free category thread-list reads, forum inventories, discussion migration ledgers, moderation exports, cached category scans, lazy `ForumCategory.threads`, `ForumThread.posts`, reply-side category/thread count synchronization, local fixtures, or generated review records where `ForumThread.post_count` must reflect structurally valid Wikidot category thread-list metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify category thread-list acquisition as a practical read-heavy forum workflow. Existing drafts cover retry-aware category thread fetches, nested-table scoping, list title/description text fidelity, response-body diagnostics, malformed list post-count diagnostics, non-negative direct and generated thread post-count validation, generated thread href route validation, generated thread href ID ASCII-shape validation, generated thread-list pager page ASCII-shape validation, direct thread-detail count ASCII-shape validation, direct `ForumThread.post_count` validation, collection validation, cached category thread reuse, post traversal, and reply behavior.

This slice is not a duplicate of [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md). Issue 234 covers malformed count text that `int(...)` rejects, such as `not-a-number`; it did not cover Unicode digit glyphs that `int(...)` accepts.

This slice is not a duplicate of [635-pr-validate-non-negative-forum-thread-post-counts.md](635-pr-validate-non-negative-forum-thread-post-counts.md). Issue 635 covers negative direct constructor counts and generated negative count cells such as `-1`. The new ASCII-shape check deliberately preserves the existing negative-value path for ASCII `-1`.

This slice is also not a duplicate of [760-pr-validate-forum-thread-detail-post-count-ascii-shape.md](760-pr-validate-forum-thread-detail-post-count-ascii-shape.md), which covers direct thread-detail `ForumViewThreadModule` statistics, not category thread-list `ForumViewCategoryModule` post-count cells.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [034-pr-retry-category-thread-list-fetches.md](034-pr-retry-category-thread-list-fetches.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [158-pr-forum-thread-list-parse-context.md](158-pr-forum-thread-list-parse-context.md), [169-pr-forum-thread-list-fetch-failure-context.md](169-pr-forum-thread-list-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [234-pr-forum-thread-list-count-parse-context.md](234-pr-forum-thread-list-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [635-pr-validate-non-negative-forum-thread-post-counts.md](635-pr-validate-non-negative-forum-thread-post-counts.md), [681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md](681-pr-validate-category-thread-list-acquisition-retained-category-id-state.md), [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md), [753-pr-validate-forum-thread-pager-page-ascii-shape.md](753-pr-validate-forum-thread-pager-page-ascii-shape.md), [760-pr-validate-forum-thread-detail-post-count-ascii-shape.md](760-pr-validate-forum-thread-detail-post-count-ascii-shape.md), and adjacent generated-scalar ASCII-shape draft [762-pr-validate-forum-category-count-ascii-shape.md](762-pr-validate-forum-category-count-ascii-shape.md).

## Changes

- Require ASCII `-?[0-9]+` before integer conversion when parsing generated category thread-list `posts` count cells.
- Preserve successful parsing for valid generated post-count cells such as `5` and `3`.
- Preserve the existing contextual malformed-count diagnostic for non-integer text.
- Preserve the existing contextual non-negative diagnostic for negative ASCII cells such as `-1`.
- Add regression coverage for generated post-count text `\uff15`.

## Type Of Change

- Bug fix
- Forum thread-list generated scalar validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Generated category thread-list `posts` count cells containing non-ASCII digit glyphs must fail before a `ForumThreadCollection` is returned. |
| R2 | The malformed count diagnostic must identify the site, category, page, row, affected field, and observed raw value. |
| R3 | Valid generated ASCII count cells such as `5` and `3` must continue to parse into the same counts. |
| R4 | Existing malformed text and negative ASCII count paths must keep their established diagnostics. |
| R5 | Existing category thread-list response validation, pagination, nested-table filtering, title/description parsing, href parsing, collection/search behavior, cached category thread behavior, direct thread detail behavior, post/revision traversal, and reply behavior must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real forum HTML, raw forum content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, forum thread tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `\uff15` in a generated category thread-list `posts` cell raises before a collection is returned. | `test_acquire_all_rejects_non_ascii_digit_post_count` failed RED with `DID NOT RAISE`, then passed after ASCII-only count parsing. | Returning a `ForumThread`, normalizing `"\uff15"` into `post_count=5`, or silently skipping the row rejects this local completion claim. | Category thread-list parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | The exception reports `Posts count is malformed for site: test-site (category=1001, page=1, row=1, field=posts, value=\uff15)`. | The focused regression asserts the diagnostic family, structural location, field, and observed value. | A raw `ValueError`, omitted site/category/page/row context, omitted field/value, or unrelated parser diagnostic rejects this local completion claim. | Thread-list diagnostics | focused test |
| R3 | Valid ASCII count cells still parse successfully. | Focused GREEN included `test_acquire_all_single_page` and `TestForumThreadCollectionParseListInCategory::test_parse_fields`; `tests/unit/test_forum_thread.py` passed 236 tests. | Rejecting `5` or `3`, changing parsed counts, changing parsed thread fields, or changing list order rejects this local completion claim. | Valid thread-list parsing | `tests/unit/test_forum_thread.py` |
| R4 | Existing malformed and negative paths stay stable. | Focused GREEN included `test_acquire_all_malformed_post_count_includes_category_context` and `test_acquire_all_negative_post_count_includes_category_context`. | Accepting malformed text, reclassifying `-1` as malformed text, dropping context, or changing the non-negative diagnostic rejects this local completion claim. | Parser compatibility | `tests/unit/test_forum_thread.py` |
| R5 | Adjacent forum workflows remain green. | Adjacent forum category/thread/post/revision coverage passed 910 tests, and full unit passed 3765 tests. | Regressing response-body diagnostics, pagination, nested-table filtering, title/description parsing, href parsing, collection/search behavior, cached category thread behavior, direct thread detail behavior, forum post/revision behavior, reply behavior, or any unit test rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression mutates the synthetic `forum_threads_in_category` fixture and uses mocked AMC responses only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML from real sites, real thread titles/descriptions, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum thread module, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e7f85be fix(forum_thread): validate list count ascii shape`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_post_count -q` failed before the fix with `DID NOT RAISE` because generated category thread-list post-count text `\uff15` was accepted and normalized as `post_count=5`.
- GREEN focused category thread-list count slice: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_post_count tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_malformed_post_count_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_negative_post_count_includes_category_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireAll::test_acquire_all_single_page tests/unit/test_forum_thread.py::TestForumThreadCollectionParseListInCategory::test_parse_fields -q` passed 5 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 236 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 910 tests.
- `uv run pytest tests/unit -q` passed 3765 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no parser boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `ForumThreadCollection.acquire_all_in_category(...)` raises `NoElementException("Posts count is malformed ...")` for a generated category thread-list `posts` cell whose text is `\uff15`.
- The malformed post-count diagnostic includes `site: test-site`, `category=1001`, `page=1`, `row=1`, `field=posts`, and the observed generated cell value.
- The parser does not create or return `ForumThread(post_count=5, ...)` from non-ASCII digit post-count metadata.
- Valid ASCII generated count cells such as `5` and `3` still parse successfully.
- Existing malformed text such as `not-a-number` still raises the contextual malformed count diagnostic.
- Existing negative ASCII text such as `-1` still raises the contextual non-negative count diagnostic.
- Existing response-body diagnostics, pagination, nested-table filtering, title/description parsing, href parsing, collection/search behavior, cached category thread behavior, direct thread detail behavior, forum post/revision behavior, reply behavior, adjacent forum workflows, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, private forum content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 234. Mitigation: Issue 234 covers malformed text that `int(...)` rejects; this slice covers Unicode digit glyphs that `int(...)` accepts.
- Risk: This could be confused with Issue 635. Mitigation: Issue 635 covers negative thread counts; this slice keeps ASCII negative text valid for parser classification so the existing non-negative diagnostic remains intact.
- Risk: This could be confused with Issue 760. Mitigation: Issue 760 covers direct thread-detail generated statistics; this slice covers generated category thread-list count cells.
- Risk: This could alter valid category thread-list parsing. Mitigation: ASCII `[0-9]+` generated count cells still convert to integers, and successful acquisition plus adjacent forum tests remain green.
- Risk: Diagnostics could expose forum content. Mitigation: the diagnostic includes only site, category, page, row, field, and the compact count scalar; tests use synthetic fixture HTML and do not include real forum content.

## Dependencies

- BeautifulSoup continues to expose generated category thread-list post-count cells as direct structural `td` text.
- Normal Wikidot category thread-list post-count cells are expected to use ASCII decimal digits.
- Existing thread-list parser context continues to identify site, category, page, structural row, field, and raw scalar value.
- Existing `ForumThread` constructor validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated scalar-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Category thread-list post counts are durable generated metadata for forum inventories, discussion migration ledgers, moderation exports, cached scans, lazy thread/post traversal, and downstream traversal decisions. Unicode digit normalization can silently turn malformed generated count text into a valid-looking thread post count. Requiring ASCII digits keeps generated count parsing strict while preserving valid Wikidot category thread-list rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated category thread-list post-count value was accepted and normalized into `post_count=5`.
- Existing local drafts covered category thread-list fetch retries, nested-table scoping, list text fidelity, response diagnostics, parser-side malformed count diagnostics, negative count validation, direct constructor state, thread href route validation, thread href ID ASCII-shape validation, thread-list pager page ASCII-shape validation, direct thread-detail count ASCII-shape validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in generated category thread-list post-count cells.
- This slice does not change request payloads, retry policy, response-body validation, title/description extraction, thread href parsing, created user/time parsing, collection/search behavior, cached category thread behavior, direct thread-detail parsing, lazy post reads, reply behavior, live Wikidot behavior, direct `ForumThread` constructors, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML from real accounts, private forum content, and private site data out of upstream discussion.
