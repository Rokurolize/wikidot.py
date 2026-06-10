# PR Draft: Validate Forum Thread Detail Post-Count ASCII Shape

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses direct thread detail HTML returned by `forum/ForumViewThreadModule`. Issue 729 tightened direct thread-detail post-count parsing from "any embedded digit run" to valid full-label or bare-integer shapes, but the accepted branch still used Unicode-aware `\d+` before `int(...)`. A generated statistic containing a non-ASCII digit glyph such as `Number of posts: \uff15` was therefore accepted and normalized into ordinary `post_count=5`.

This change accepts generated direct thread-detail post counts only when the numeric part matches ASCII digits. Valid generated labels such as `Number of posts: 5` and bare integer values continue to parse normally, existing no-digit malformed labels keep the contextual `Post count is malformed ...` path, existing digit-bearing malformed labels such as `Number of posts: 5 latest` stay rejected, existing negative ASCII labels keep the `Post count must be non-negative ...` diagnostic, and non-ASCII digit-like labels now fail before a `ForumThread` is constructed.

## Outcome

Direct thread-detail reads no longer fabricate thread post counts by normalizing malformed generated count metadata. A `ForumViewThreadModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like count text now fails at the direct thread-detail parser boundary with site, requested thread, field, and observed value context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free direct thread reads, forum inventories, discussion migration ledgers, moderation exports, cached category scans, duplicate direct-thread reads, `ForumThread.posts`, local fixtures, or generated review records where `ForumThread.post_count` must reflect structurally valid Wikidot thread-detail metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify direct forum thread detail acquisition as a practical read-heavy workflow. Existing drafts cover retry-aware direct thread fetches, duplicate direct-thread deduplication, structural statistics scoping, description text preservation, breadcrumb title separator preservation, site/thread parser context, missing and malformed response-body diagnostics, no-digit direct post-count diagnostics, non-negative post-count validation, digit-bearing extra-text post-count shape validation, direct thread ID parser diagnostics, created-by and created-at parser diagnostics, direct `ForumThread.id` and `ForumThread.post_count` validation, collection validation, cached category-thread reuse, and reply behavior.

This slice is not a duplicate of [729-pr-validate-forum-thread-detail-post-count-shape.md](729-pr-validate-forum-thread-detail-post-count-shape.md). Issue 729 rejects valid-looking labels with extra non-count suffix text such as `Number of posts: 5 latest`; it did not cover Unicode digit normalization inside an otherwise accepted label shape.

It is also not a duplicate of [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [635-pr-validate-non-negative-forum-thread-post-counts.md](635-pr-validate-non-negative-forum-thread-post-counts.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), or [747-pr-validate-forum-thread-href-id-ascii-shape.md](747-pr-validate-forum-thread-href-id-ascii-shape.md), which cover no-digit generated count diagnostics, negative counts, direct constructor state, generated script thread IDs, or generated/list href thread IDs rather than direct thread-detail generated post-count Unicode normalization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md), [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [326-pr-forum-thread-response-body-type-context.md](326-pr-forum-thread-response-body-type-context.md), [362-pr-validate-forum-thread-id-inputs.md](362-pr-validate-forum-thread-id-inputs.md), [457-pr-validate-forum-thread-post-count-field.md](457-pr-validate-forum-thread-post-count-field.md), [543-pr-validate-forum-thread-direct-site.md](543-pr-validate-forum-thread-direct-site.md), [635-pr-validate-non-negative-forum-thread-post-counts.md](635-pr-validate-non-negative-forum-thread-post-counts.md), [729-pr-validate-forum-thread-detail-post-count-shape.md](729-pr-validate-forum-thread-detail-post-count-shape.md), [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md), and adjacent generated-scalar ASCII-shape drafts [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md), [757-pr-validate-forum-post-id-ascii-shape.md](757-pr-validate-forum-post-id-ascii-shape.md), [758-pr-validate-forum-post-revision-id-ascii-shape.md](758-pr-validate-forum-post-revision-id-ascii-shape.md), and [759-pr-validate-recent-change-revision-cell-ascii-shape.md](759-pr-validate-recent-change-revision-cell-ascii-shape.md).

## Changes

- Require ASCII `[0-9]+` before integer conversion when parsing generated direct thread-detail post-count text.
- Preserve successful parsing for `Number of posts: 5`, bare ASCII integer values, and existing direct thread-detail records.
- Preserve the existing contextual `NoElementException` message family for no-digit malformed labels and digit-bearing labels with extra suffix text.
- Preserve the existing `Post count must be non-negative ...` diagnostic for negative ASCII labels such as `Number of posts: -1`.
- Add focused regression coverage for a generated direct thread-detail statistic containing fullwidth post count text `Number of posts: \uff15`.

## Type Of Change

- Bug fix
- Forum thread-detail generated scalar validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated direct thread-detail post-count label containing non-ASCII digit glyphs must fail before a `ForumThread` is returned. |
| R2 | The malformed post-count diagnostic must identify the site, requested thread ID, affected field, and observed raw value. |
| R3 | Valid generated ASCII post-count labels such as `Number of posts: 5` and bare integer values must continue to parse into the same counts. |
| R4 | Existing no-digit malformed labels, digit-bearing malformed labels with suffix text, and negative ASCII labels must keep their existing diagnostics. |
| R5 | Existing direct thread-detail acquisition, duplicate handling, response-body validation, requested/parsed thread ID mismatch handling, category association, post access, reply behavior, parser scoping, and adjacent forum workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw forum HTML from real sites, private thread content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, direct thread-detail class coverage, full forum-thread tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Number of posts: \uff15` raises before a direct thread detail collection is returned. | `test_acquire_from_ids_rejects_non_ascii_digit_post_count` failed RED with `DID NOT RAISE`, then passed after ASCII-only count parsing. | Returning a `ForumThread`, normalizing `"\uff15"` into `post_count=5`, or silently skipping the thread rejects this local completion claim. | Direct thread-detail parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | The exception reports `Post count is malformed for site: test-site (thread=3001, field=posts, value=Number of posts: \uff15)`. | The focused regression asserts the diagnostic family, structural location, field, and observed value. | A raw `ValueError`, omitted site/thread context, omitted field/value, or unrelated parser diagnostic rejects this local completion claim. | Direct thread-detail diagnostics | focused test |
| R3 | Valid ASCII labels still parse successfully. | Focused GREEN included `test_acquire_from_ids_success`; direct lookup class passed 32 tests and `tests/unit/test_forum_thread.py` passed 235 tests. | Rejecting `Number of posts: 5`, changing parsed post counts, or changing successful thread fields rejects this local completion claim. | Valid direct thread-detail parsing | `tests/unit/test_forum_thread.py` |
| R4 | Existing malformed and negative paths stay stable. | Focused GREEN included `test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context`, `test_acquire_from_ids_rejects_malformed_post_count_with_embedded_digits`, and `test_acquire_from_ids_negative_post_count_includes_thread_and_value_context`. | Accepting `Number of posts: 5 latest`, reclassifying `Number of posts: -1`, or changing context for no-digit malformed labels rejects this local completion claim. | Parser compatibility | `tests/unit/test_forum_thread.py` |
| R5 | Adjacent forum workflows remain green. | Adjacent forum coverage passed 907 tests, and full unit passed 3761 tests. | Regressing category thread-list parsing, direct thread-detail parsing, direct lookup, duplicate handling, lazy category/thread/post behavior, reply behavior, forum category behavior, forum post behavior, forum post revision behavior, or any unit test rejects this local completion claim. | Forum and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression mutates the synthetic `forum_thread_detail` fixture and uses mocked AMC responses only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum HTML from real sites, real thread titles/descriptions, private forum content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, class, module, adjacent forum, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `816aa82 fix(forum_thread): validate detail post count ascii shape`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_ascii_digit_post_count -q` failed before the fix with `DID NOT RAISE` because `Number of posts: \uff15` was accepted and normalized as `post_count=5`.
- GREEN focused direct thread-detail slice: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_non_ascii_digit_post_count tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_malformed_post_count_with_embedded_digits tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_negative_post_count_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success -q` passed 5 tests.
- `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds -q` passed 32 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 235 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 907 tests.
- `uv run pytest tests/unit -q` passed 3761 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no parser boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `ForumThreadCollection.acquire_from_thread_ids(...)` raises `NoElementException("Post count is malformed ...")` for a generated direct thread-detail statistic whose text is `Number of posts: \uff15`.
- The malformed post-count diagnostic includes `site: test-site`, `thread=3001`, `field=posts`, and the observed generated statistic text.
- The parser does not create or return a `ForumThread(post_count=5, ...)` from non-ASCII digit post-count metadata.
- Valid ASCII structural post-count labels such as `Number of posts: 5` and bare integer values still parse successfully.
- Existing malformed no-digit labels such as `Number of posts: not-a-number` still raise `Post count is malformed ...`.
- Existing malformed digit-bearing labels such as `Number of posts: 5 latest` still raise `Post count is malformed ...`.
- Existing negative ASCII labels such as `Number of posts: -1` still raise `Post count must be non-negative ...`.
- Existing successful direct thread detail reads, duplicate-ID handling, response-body validation, requested/parsed ID mismatch handling, category association, post access, reply behavior, parser scoping, adjacent forum suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, private forum content, or private site data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 729. Mitigation: Issue 729 covers malformed digit-bearing text outside the expected post-count label shape; this slice covers Unicode digit normalization inside an otherwise accepted shape.
- Risk: This could be confused with direct `ForumThread.post_count` validation. Mitigation: direct constructor type/range validation remains separate; this slice runs at the generated direct thread-detail parser boundary before object construction.
- Risk: This could alter negative count handling. Mitigation: the regex still accepts ASCII signed integer text, and the existing negative branch remains responsible for `Number of posts: -1`.
- Risk: This could break valid direct thread parsing. Mitigation: ASCII `[0-9]+` generated count labels still convert to integers, and successful direct thread plus adjacent forum tests remain green.
- Risk: Diagnostics could expose private thread content. Mitigation: the diagnostic includes only site/thread structural location, field name, and the compact post-count scalar; tests use synthetic fixture HTML and do not include real forum content.

## Dependencies

- BeautifulSoup continues to expose generated direct thread-detail statistics as text adjacent to the structural statistics block's third `br`.
- Normal Wikidot direct thread-detail post-count statistics are expected to use ASCII decimal digits after `Number of posts:`.
- Existing direct thread-detail parser context continues to identify site, requested thread, optional category, field, and raw scalar value.
- Existing `ForumThread` constructor validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated scalar-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Direct thread-detail post counts are durable generated metadata for forum inventories, discussion migration ledgers, moderation exports, cached scans, duplicate direct-thread reads, and downstream traversal decisions. Unicode digit normalization can silently turn malformed generated count text into a valid-looking thread post count. Requiring ASCII digits keeps generated count parsing strict while preserving valid Wikidot direct thread detail rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated direct thread-detail post-count value was accepted and normalized into `post_count=5`.
- Existing local drafts covered direct thread retry behavior, duplicate direct-thread reduction, parser scoping, parser-side no-digit post-count diagnostics, negative post-count validation, digit-bearing extra-text post-count shape, response diagnostics, direct lookup input validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in generated direct thread-detail post-count labels.
- This slice does not change request payloads, retry policy, response-body validation, title/description extraction, created user/time parsing, thread ID parsing, category association, duplicate handling, lazy post reads, reply behavior, live Wikidot behavior, direct `ForumThread` constructors, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw generated HTML from real accounts, real thread titles/descriptions, private forum content, and private site data out of upstream discussion.
