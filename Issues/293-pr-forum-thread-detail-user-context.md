# PR Draft: Report Malformed Forum Thread Detail Users

## Summary

`ForumThreadCollection.acquire_from_thread_ids(...)`, exposed through `Site.get_thread(...)`, `Site.get_threads(...)`, and `ForumThread.get_from_id(...)`, parses direct thread detail HTML returned by `forum/ForumViewThreadModule`. Earlier local slices made direct thread detail acquisition retry-aware, deduplicated duplicate thread IDs, scoped thread detail statistics to the structural block, preserved formatted description text and breadcrumb separators, added site/thread parser context, validated missing detail response bodies, and converted malformed direct thread-detail post-count values into contextual `NoElementException`. One adjacent parser-value gap remained in the direct thread detail parser: when the generated statistics block contained a present direct `span.printuser` whose `userInfo(...)` metadata was malformed, the shared `user_parse(...)` utility raised raw `ValueError("user id is not found")` without identifying the site, requested thread, affected field, or observed `onclick` value.

This follow-up keeps the shared `user_parse(...)` utility unchanged and catches malformed direct thread-detail created-by metadata at the thread-detail parser boundary. It raises `NoElementException` with site unix name, requested thread ID, optional category ID, `field=created_by`, and the offending direct `onclick` value. Valid direct thread parsing, valid user parsing, timestamp parsing, malformed post-count diagnostics, retry behavior, missing response-body diagnostics, duplicate-ID deduplication, category thread lists, post access, and thread mutation actions remain unchanged.

## Outcome

Malformed present created-by metadata in a generated direct thread-detail statistics block is now reported as a forum-thread detail parser failure instead of a raw shared-parser failure.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_thread(...)`, `Site.get_threads(...)`, `ForumThread.get_from_id(...)`, or `ForumThreadCollection.acquire_from_thread_ids(...)` for browser-free forum inspection, indexing, migration, or moderation workflows.

## Related Issue

Builds on [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [060-pr-deduplicate-thread-detail-fetches.md](060-pr-deduplicate-thread-detail-fetches.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), [104-pr-preserve-thread-detail-description-text.md](104-pr-preserve-thread-detail-description-text.md), [105-pr-preserve-thread-title-separators.md](105-pr-preserve-thread-title-separators.md), [159-pr-forum-thread-detail-parse-context.md](159-pr-forum-thread-detail-parse-context.md), [170-pr-forum-thread-detail-fetch-failure-context.md](170-pr-forum-thread-detail-fetch-failure-context.md), [214-pr-forum-thread-response-body-context.md](214-pr-forum-thread-response-body-context.md), [238-pr-forum-thread-detail-count-parse-context.md](238-pr-forum-thread-detail-count-parse-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), and [292-pr-forum-thread-list-timestamp-context.md](292-pr-forum-thread-list-timestamp-context.md). Those drafts established direct thread detail acquisition as a retry-aware, duplicate-aware, structurally scoped, diagnosable read path and established adjacent parser-boundary diagnostics for forum thread lists and detail count values. This slice also follows the shared printuser parser-boundary pattern from [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), and [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present direct thread-detail `span.printuser` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site unix name, requested thread ID, optional category ID, `field=created_by`, and the observed direct `onclick` value in the parser error.
- Preserve the shared `user_parse(...)` utility behavior and parser tests.
- Preserve successful `ForumThreadCollection.acquire_from_thread_ids(...)` parsing, direct `_parse_thread_page(...)` parsing, and valid direct thread-detail user handling.
- Preserve existing direct thread-detail response-body validation, retry-exhausted behavior, duplicate-ID deduplication, requested/parsed thread ID mismatch checks, structural statistics scoping, title separator preservation, description text preservation, malformed post-count diagnostics, category thread-list acquisition, post access, and reply behavior.
- Add a focused public `ForumThreadCollection.acquire_from_thread_ids(...)` regression for a malformed created-by `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Forum thread-detail parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A structural direct thread-detail statistics block with malformed present created-by `userInfo(...)` metadata must fail at the forum-thread detail parser boundary. |
| R2 | The malformed user error must identify the affected site, requested thread, field, and observed direct `onclick` value. |
| R3 | Existing valid direct thread-detail parsing and direct parser callers must remain compatible. |
| R4 | Existing direct thread-detail response handling, retries, duplicate-ID behavior, parser scoping, title/description fidelity, and malformed post-count diagnostics must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `ForumThreadCollection.acquire_from_thread_ids(site, [thread_id])` raises `NoElementException` for `userInfo(latest)` in the structural thread-detail statistics block. | `TestForumThreadCollectionAcquireFromIds.test_acquire_from_ids_malformed_user_includes_thread_and_value_context` returns the direct thread detail page and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, silently skipping the field, returning `created_by=None`, or returning a malformed `ForumThread` rejects this local completion claim. | `src/wikidot/module/forum_thread.py` | `tests/unit/test_forum_thread.py` |
| R2 | The error names site, requested thread, `field=created_by`, and the bad direct `onclick` value. | The focused regression asserts `Forum thread detail user is malformed for site: test-site (thread=3001, field=created_by, value=WIKIDOT.page.listeners.userInfo(latest); return false;)`. | Omitting site, requested thread, field, or observed value makes the failure ambiguous and rejects this local completion claim. | Thread-detail diagnostics | `tests/unit/test_forum_thread.py` |
| R3 | Valid direct thread-detail rows still parse through the existing public acquisition API and direct parser helper. | Focused GREEN includes public direct thread acquisition and direct `_parse_thread_page(...)` success. | Regressing parsed thread ID, title, description, created-by user, created-at timestamp, post count, category association, or collection order rejects this local completion claim. | `ForumThreadCollection.acquire_from_thread_ids(...)` and `_parse_thread_page(...)` | `tests/unit/test_forum_thread.py` |
| R4 | Adjacent direct thread-detail behaviors stay green. | Focused GREEN includes malformed post-count context and description-statistics scoping; the whole `test_forum_thread.py` file passed 53 tests. | Regressing missing response-body context, retry behavior, duplicate-ID handling, requested/parsed thread ID mismatch handling, structural statistics scoping, title separator preservation, description text preservation, malformed post-count diagnostics, post access, or reply behavior rejects this local completion claim. | Direct thread-detail workflows | `tests/unit/test_forum_thread.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `43852b0 fix(forum_thread): report malformed detail users`.

- RED: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_user_includes_thread_and_value_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run --extra test pytest tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_user_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_malformed_post_count_includes_thread_and_value_context tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_success tests/unit/test_forum_thread.py::TestForumThreadCollectionAcquireFromIds::test_acquire_from_ids_ignores_description_statistics_markup tests/unit/test_forum_thread.py::TestForumThreadCollectionParseThreadPage::test_parse_success -q` passed 5 tests.
- `uv run --extra test pytest tests/unit/test_forum_thread.py -q` passed 53 tests.
- `uv run --extra test pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 184 tests.
- `uv run --extra test pytest tests/unit -q` passed 850 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `ForumThreadCollection.acquire_from_thread_ids(site, [thread_id])` raises `NoElementException` when a direct thread-detail response has a structural statistics block with a direct `span.printuser` element whose `userInfo(...)` metadata cannot be parsed by the shared user parser.
- The malformed created-by error includes the site unix name, requested thread ID, `field=created_by`, and observed direct `onclick` value.
- Valid direct thread-detail rows still parse created-by users through `user_parser(...)`.
- Direct `_parse_thread_page(site, html, category=None, thread_id=None)` callers remain compatible.
- Existing missing response-body diagnostics, retry-exhausted handling, duplicate-ID deduplication, requested/parsed thread ID mismatch checks, structural statistics scoping, title separator preservation, description text preservation, malformed post-count diagnostics, category thread-list acquisition, post access, and reply action payloads remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated thread-detail HTML, forum titles from real sites, or private forum content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected created-by parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only thread-detail location metadata.
- Risk: Changing the shared user parser could affect unrelated modules. Mitigation: this slice intentionally leaves `user_parse(...)` unchanged and validates parser and adjacent forum behavior through the full unit suite.
- Risk: Description content containing `statistics`-like markup could be mistaken for the structural author. Mitigation: the existing structural statistics scoping remains unchanged, and the focused GREEN run includes the description metadata isolation test.

## Dependencies

- BeautifulSoup continues to expose direct thread-detail `span.printuser` elements and direct child user links in the generated statistics block.
- The shared `user_parse(...)` utility remains the source of truth for valid Wikidot user metadata extraction.
- Direct thread-detail pages still identify created-by users through direct `span.printuser` metadata in the structural `div.statistics` block.

## Open Questions

None for this local slice. A direct thread-detail created-at value-context wrapper remains an adjacent parser-boundary candidate and should be evaluated separately with its own red/green proof.

## Upstream-Safe Motivation

Direct thread lookup is a read-heavy prerequisite for discussion inspection, post collection, indexing, migration, and moderation-oriented tooling. If Wikidot emits a structural thread-detail statistics block with malformed direct created-by metadata, wikidot.py should return a structured parser failure naming the affected site, requested thread, field, and observed value instead of forcing operators to infer context from a raw shared helper exception. That keeps forum diagnostics actionable without retaining generated forum HTML, raw response JSON, forum content, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established direct thread detail acquisition as a practical read-heavy workflow, including retry-aware direct thread fetches, duplicate-ID deduplication, structural statistics scoping, visible description text preservation, breadcrumb title separator handling, site/thread parser context, response-body validation, and malformed post-count diagnostics.
- Recent forum workflow drafts validated parser-boundary diagnostics for category thread-list created-by and created-at metadata. Direct thread-detail parsing uses the same shared user parser but needs site/thread context at its own parser boundary.
- Shared printuser work has already covered parser-boundary diagnostics in forum post revisions, private-message details, site members, and category thread lists. Direct thread details use the same parser utility but need direct thread-detail context.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated forum HTML, thread titles from real sites, page names from real sites, and private forum content out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding direct thread-detail response and forum diagnostics.
