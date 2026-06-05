# PR Draft: Report Malformed Forum Thread Detail IDs

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses direct thread detail HTML returned by `forum/ForumViewThreadModule`. Earlier local slices made direct thread detail acquisition retry-aware, deduplicated duplicate thread IDs, scoped thread detail statistics to the structural block, preserved formatted description text and breadcrumb separators, added site/thread parser context, validated missing detail response bodies, converted malformed direct thread-detail post-count values into contextual `NoElementException`, and added contextual diagnostics for malformed direct thread-detail user and timestamp metadata. One adjacent scalar boundary remained: the generated `WIKIDOT.forumThreadId` script assignment was matched with a digit-only regex, so a present malformed assignment such as `WIKIDOT.forumThreadId = latest;` was treated as a missing script element and lost the observed value.

This local slice keeps successful direct thread parsing, missing script diagnostics, response-body validation, retry handling, duplicate-ID deduplication, requested/parsed thread ID mismatch checks, category association, thread-list parsing, post access, and reply behavior unchanged. It captures present direct `forumThreadId` assignments before integer conversion and raises `NoElementException` with site unix name, requested thread ID, optional category ID, `field=thread_id`, and the observed value when the assignment is malformed.

## Outcome

Malformed direct forum-thread detail IDs now fail with value-aware thread-detail context instead of being reported as a missing script element.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who retrieve forum thread details directly for browser-free archival, moderation, migration, indexing, or publishing-adjacent workflows.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), and [294-pr-forum-thread-detail-timestamp-context.md](294-pr-forum-thread-detail-timestamp-context.md). Those drafts established direct thread detail acquisition as a practical read-heavy workflow with explicit site/thread diagnostics for adjacent malformed response and parser values.

This slice also follows the scalar parser-boundary pattern from [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [240-pr-listpages-rating-parse-context.md](240-pr-listpages-rating-parse-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md), and [310-pr-site-id-context.md](310-pr-site-id-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse present direct `WIKIDOT.forumThreadId` assignments with a value-capturing regex instead of a digit-only regex.
- Reject present non-numeric or empty direct thread ID values with contextual `NoElementException`.
- Include site unix name, requested thread ID, optional category ID, `field=thread_id`, and observed value in the parser error.
- Preserve the existing missing-script diagnostic when no `forumThreadId` assignment is present.
- Preserve successful direct thread parsing, requested/parsed thread ID mismatch detection, response-body validation, retry-aware direct fetching, duplicate-ID deduplication, title and description parsing, metadata parsing, category association, post access, and reply behavior.
- Add a focused public `ForumThreadCollection.acquire_from_thread_ids(...)` regression for `WIKIDOT.forumThreadId = latest;`.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-detail parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated direct thread-detail response with a present non-numeric `WIKIDOT.forumThreadId` assignment must fail at the direct thread-detail parser boundary. |
| R2 | The malformed direct thread ID error must identify the affected site, requested thread ID, field, and observed value. |
| R3 | A direct thread-detail response without any `forumThreadId` assignment must still use the existing missing-script diagnostic. |
| R4 | Valid direct thread IDs, response-body validation, retry-aware acquisition, duplicate-ID deduplication, requested/parsed mismatch detection, title/description parsing, metadata parsing, category association, post access, and reply behavior must remain compatible. |
| R5 | Focused, direct-thread, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumThreadCollection.acquire_from_thread_ids(...)` raises `NoElementException` for `WIKIDOT.forumThreadId = latest;`. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_malformed_script_thread_id_includes_thread_and_value_context` expects `NoElementException`. | Treating the malformed assignment as missing, leaking a raw scalar parse error, fabricating a thread ID, or returning a `ForumThread` rejects this local completion claim. | `src/wikidot/module/forum_thread.py` | `tests/unit/test_forum_thread.py` |
| R2 | The error names `site: test-site`, `thread=3001`, `field=thread_id`, and `value=latest`. | The focused regression matches all fields. | Omitting the site, requested thread ID, field, or observed value makes the failure ambiguous and rejects this local completion claim. | Direct thread-detail diagnostics | `tests/unit/test_forum_thread.py` |
| R3 | Responses with no direct `forumThreadId` assignment continue to raise the existing missing-script `NoElementException`. | Source inspection shows the missing-assignment branch still raises `Script element is not found ...`; adjacent direct parser tests remained green. | Treating absent script metadata as a malformed value would blur distinct failure modes and rejects this local completion claim. | Direct thread-detail missing-field handling | `src/wikidot/module/forum_thread.py` |
| R4 | Valid direct thread details still parse and adjacent failure modes remain green. | The direct parser/acquire group passed 17 tests and the full forum-thread suite passed 55 tests. | Regressing valid thread ID parsing, requested/parsed mismatch detection, retry exhaustion, duplicate-ID handling, response-body diagnostics, title/description parsing, post-count diagnostics, user diagnostics, timestamp diagnostics, post access, or reply behavior rejects this local completion claim. | Direct forum-thread workflow | `tests/unit/test_forum_thread.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `8372943 fix(forum_thread): report malformed detail thread ids`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_script_thread_id_includes_thread_and_value_context -q` failed before the fix with `NoElementException: Script element is not found for site: test-site (thread=3001)`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_script_thread_id_includes_thread_and_value_context -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionParseThreadPage tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds -q` passed 17 tests.
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 55 tests.
- `uv run --extra test pytest tests/unit -q` passed 869 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- A generated direct thread-detail response whose present `WIKIDOT.forumThreadId` value is non-numeric raises `NoElementException`.
- The malformed direct thread ID message includes site unix name, requested thread ID, `field=thread_id`, and observed value.
- Valid numeric direct thread IDs still construct the parsed `ForumThread.id`.
- Responses without a direct `forumThreadId` assignment still use the existing missing-script failure path.
- Missing response-body diagnostics, retry-exhausted behavior, duplicate-ID deduplication, requested/parsed mismatch detection, title and description parsing, metadata parsing, category association, post access, and reply behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, generated thread HTML from real sites, forum content, page content, credentials, cookies, auth JSON, or private site data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Treating absent script metadata as malformed could change the existing missing-field contract. Mitigation: this slice raises the new malformed-value error only when a `WIKIDOT.forumThreadId` assignment is present.
- Risk: The wider regex could alter valid direct thread parsing. Mitigation: valid direct thread acquisition and direct parser tests remained green, and valid numeric values still require digit-only content before integer conversion.
- Risk: Diagnostics could expose thread content. Mitigation: the error reports only site/thread identifiers, field name, and the scalar value, not raw thread HTML, descriptions, post bodies, credentials, or local rollout paths.

## Dependencies

- `forum/ForumViewThreadModule` continues to expose direct thread identity through a generated `WIKIDOT.forumThreadId = <id>;` assignment.
- `ForumThreadCollection.acquire_from_thread_ids(...)` remains the source of truth for direct thread detail acquisition.
- Existing direct thread-detail responses without a `forumThreadId` assignment continue to represent missing script metadata rather than a malformed scalar value.

## Open Questions

None for this local slice. A future cleanup could centralize small scalar context wrappers only if it removes duplication without hiding parser-specific diagnostics.

## Upstream-Safe Motivation

Direct forum-thread lookup is a read-heavy path for archival, moderation, migration, and indexing tools. If Wikidot emits a malformed generated thread ID, wikidot.py should fail with structured thread-local diagnostics instead of reporting the value as missing script metadata. That keeps logs actionable without retaining raw generated thread HTML, forum content, credentials, local rollout paths, or private site data.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established direct thread detail reads as retry-aware, duplicate-aware, and context-rich.
- Issue 159 added site/thread context to direct thread-detail parser failures but preserved the digit-only script-ID search, making the present malformed assignment a separate adjacent boundary.
- Issue 309 covered generated page discussion `forumThreadId` parsing; this slice covers direct `forum/ForumViewThreadModule` detail parsing and does not alter `Page.discussion`.
- The immediate RED failure showed the existing digit-only regex skipped `WIKIDOT.forumThreadId = latest;` and raised the missing-script `NoElementException`.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated thread HTML, forum contents, page source text, thread titles from real sites, and private site data out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It preserves valid direct thread lookup while preventing a malformed present direct thread ID from losing the raw scalar value that operators need for diagnosis.
