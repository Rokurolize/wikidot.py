# PR Draft: Validate Forum Thread Detail Post-Count Shape

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses direct thread detail HTML returned by `forum/ForumViewThreadModule`.
Earlier local slices made direct thread detail acquisition retry-aware, duplicate-aware, structurally scoped, response-body-aware, and context-rich for missing or malformed generated fields.
Issue 238 added site/thread/field/value context when the direct thread-detail post-count label had no digits, and Issue 635 made negative counts fail instead of being parsed as positive values.
One adjacent scalar-shape gap remained: because `_parse_thread_detail_post_count(...)` used a loose digit search, a digit-bearing malformed label such as `Number of posts: 5 latest` was accepted as post count `5`.

This change validates the generated direct thread-detail post-count label shape before constructing `ForumThread`.
Valid labels such as `Number of posts: 5` and bare integer values still parse, negative labels still raise the existing non-negative diagnostic, and digit-bearing malformed labels now raise contextual `NoElementException` instead of silently fabricating a count.

## Outcome

Direct thread-detail reads no longer accept extra text around the generated post-count value merely because it contains a digit.
Callers get a structured parser failure naming the affected site, requested thread, field, and observed value, while successful thread-detail parsing, duplicate-ID handling, response validation, and forum traversal behavior remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free thread detail reads, forum inventories, discussion migration ledgers, moderation exports, cached category scans, duplicate direct-thread reads, `ForumThread.posts`, or local fixtures where thread post counts must come from structurally valid generated detail statistics.

## Current Evidence

Local rollout-backed drafts repeatedly identify direct forum thread detail acquisition as a practical read-heavy workflow.
Existing drafts cover retry-aware direct thread fetches, duplicate direct-thread deduplication, structural statistics scoping, description text preservation, breadcrumb title separator preservation, site/thread parser context, missing response-body diagnostics, response-body type validation, post-count no-digit diagnostics, non-negative post-count validation, direct thread ID parser diagnostics, created-by and created-at parser diagnostics, direct `ForumThread.id` and `ForumThread.post_count` validation, collection validation, cached category-thread reuse, and reply behavior.

This slice is not a duplicate of [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), which covers count labels without digits and the missing field/value context, or [635-pr-validate-non-negative-forum-thread-post-counts.md](635-pr-validate-non-negative-forum-thread-post-counts.md), which covers negative generated and direct post counts.
It also does not duplicate [311-pr-forum-thread-detail-id-context.md](311-pr-forum-thread-detail-id-context.md), [727-pr-validate-forum-thread-href-id-shape.md](727-pr-validate-forum-thread-href-id-shape.md), or the direct constructor validation drafts, because this slice validates the generated direct thread-detail post-count label shape.

No upstream issue was filed from this local workspace.

## Changes

- Validate direct thread-detail post-count text with a full label-or-integer match instead of searching for any digit run.
- Preserve successful parsing for `Number of posts: 5` and bare integer values.
- Preserve the existing `Post count is malformed ...` diagnostic for non-numeric labels.
- Preserve the existing `Post count must be non-negative ...` diagnostic for negative labels such as `Number of posts: -1`.
- Reject digit-bearing malformed labels such as `Number of posts: 5 latest` with site, requested thread, field, and raw value context.
- Preserve direct thread request construction, retry behavior, duplicate-ID deduplication, response-body validation, requested/parsed thread ID mismatch checks, structural statistics scoping, title extraction, description extraction, created-by parsing, created-at parsing, category association, post access, reply behavior, and adjacent forum workflows.

## Type Of Change

- Parser hardening
- Forum thread-detail scalar validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated direct thread-detail post-count label containing digits plus extra non-count text, such as `Number of posts: 5 latest`, must fail before a `ForumThread` is returned. |
| R2 | The malformed post-count diagnostic must identify the site, requested thread ID, affected field, and observed raw value. |
| R3 | Valid generated post-count labels such as `Number of posts: 5` must still parse to the same integer count. |
| R4 | Existing no-digit malformed labels and negative labels must keep their existing diagnostics. |
| R5 | Direct thread-detail acquisition, category association, post access, reply behavior, duplicate handling, response diagnostics, and adjacent forum workflows must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw forum HTML from real sites, upstream Issues, upstream PRs, or pushes. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Number of posts: 5 latest` fails instead of becoming `post_count=5`. | `test_acquire_from_ids_rejects_malformed_post_count_with_embedded_digits` failed RED with `DID NOT RAISE`, then passed GREEN after full label-or-integer matching was added. | Returning a `ForumThread`, extracting the embedded digit run, silently dropping `latest`, or deferring failure to unrelated code rejects this local completion claim. | Direct thread-detail parser | `src/wikidot/module/forum_thread.py`, `tests/unit/test_forum_thread.py` |
| R2 | The malformed diagnostic includes site, requested thread, `field=posts`, and the raw value. | The regression matches `Post count is malformed for site: test-site (thread=3001, field=posts, value=Number of posts: 5 latest)`. | Omitting site, thread, field, or raw value rejects this local completion claim. | Parser diagnostics | `tests/unit/test_forum_thread.py` |
| R3 | The normal generated label remains valid. | Focused GREEN included `test_acquire_from_ids_success`; `tests/unit/test_forum_thread.py` passed 225 tests. | Rejecting valid `Number of posts: 5`, changing the parsed count, or changing successful thread fields rejects this local completion claim. | Successful direct thread detail parsing | `tests/unit/test_forum_thread.py` |
| R4 | Existing no-digit and negative behavior stays stable. | Focused GREEN included `test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context` and `test_acquire_from_ids_negative_post_count_includes_thread_and_value_context`. | Reclassifying negative counts as generic malformed labels, accepting negatives, or changing no-digit messages rejects this local completion claim. | Parser compatibility | `tests/unit/test_forum_thread.py` |
| R5 | Adjacent behavior stays green. | Adjacent forum coverage, full unit, ruff, ruff format, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R6 | No private or live-site material is needed. | The regression mutates the synthetic `forum_thread_detail` fixture and uses mocks only. | Using credentials, cookies, auth JSON, live Wikidot actions, raw generated forum HTML from a real site, private thread content, upstream Issues, upstream PRs, or pushes rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `38e8f7a fix(forum_thread): validate detail post count shape`.

- RED: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_malformed_post_count_with_embedded_digits -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_rejects_malformed_post_count_with_embedded_digits tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_negative_post_count_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success -q` passed 4 tests.
- `uv run pytest tests/unit/test_forum_thread.py -q` passed 225 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 887 tests.
- `uv run pytest tests/unit -q` passed 3602 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `ForumThreadCollection.acquire_from_thread_ids(...)` raises `NoElementException` for a direct thread-detail statistic such as `Number of posts: 5 latest`.
- The exception includes the site `unix_name`, requested thread ID, `field=posts`, and the raw observed value.
- Valid direct thread-detail post-count labels still parse the same count.
- Existing no-digit malformed labels and negative labels keep their established diagnostics.
- Successful direct thread detail reads, duplicate-ID handling, response-body validation, requested/parsed ID mismatch handling, category association, post access, reply behavior, parser scoping, and adjacent forum workflows remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A future generated detail response could contain only a bare integer. Mitigation: the parser still accepts bare signed integer text for compatibility while rejecting labels with extra suffixes.
- Risk: The stricter parser could be confused with direct `ForumThread.post_count` constructor validation. Mitigation: constructor validation remains responsible for stored record state; this slice only validates generated direct detail text before object construction.
- Risk: The fix could alter negative count handling. Mitigation: the fullmatch still captures signed integers, and the existing negative branch remains the owner for `Number of posts: -1`.

## Dependencies

- Existing `ForumThreadCollection.acquire_from_thread_ids(...)` request construction, retry helper usage, response-body validation, duplicate handling, parser scoping, and mismatch checks remain unchanged.
- Existing `NoElementException` remains the generated-parser exception for malformed direct thread-detail fields.
- Existing `ForumThread` constructor validation remains responsible for direct local object state.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice.
Future work should continue with fresh duplicate-checked parser boundaries, response-shape validation, direct input validation, result ergonomics, or measured complexity candidates outside this direct thread-detail post-count shape path.

## Upstream-Safe Motivation

Direct thread-detail post counts are used in browser-free forum inventories, migration ledgers, moderation exports, cached scans, and downstream traversal decisions.
If generated Wikidot statistics contain extra text around the count, wikidot.py should not silently accept the embedded digit run as authoritative thread state.
Full label-or-integer validation keeps malformed generated detail output visible while preserving valid thread detail reads.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established direct thread detail acquisition as a practical workflow through retry-aware fetching, duplicate-ID handling, structural parser scoping, response-body diagnostics, parser context, and adjacent category/thread/post/revision traversal.
- Existing local drafts covered no-digit direct detail post-count diagnostics and negative generated/direct counts; they did not reject digit-bearing malformed detail labels such as `Number of posts: 5 latest`.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw generated forum HTML from real sites, private forum content, and live account details out of upstream discussion.
