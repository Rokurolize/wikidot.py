# PR Draft: Include Context In Private Message List Row Errors

## Summary

`PrivateMessageCollection._acquire(...)` parses inbox and sent-box list pages, extracts message IDs from structural `tr.message` rows, and then delegates detail fetching to `PrivateMessageCollection.from_ids(...)`. The parser already rejects structural rows whose `data-href` attribute is missing or whose `data-href` does not contain a message ID, but those failures only named the malformed field.

This follow-up keeps the existing `NoElementException` failure behavior and successful message-ID output shape, but includes the module name, page number, and structural message-row position in those list-row parser failures. That makes malformed private-message list responses diagnosable from logs without saving raw dashboard HTML or private message content.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), and [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), because those drafts established inbox/sent-box list acquisition as a practical read-heavy workflow and hardened the private-message list parser boundary.

No upstream issue was filed from this local workspace.

## Changes

- Add a small private-message list parse-context helper for module name, page number, and structural row position.
- Include that context in missing `data-href` and malformed `data-href` `NoElementException` messages.
- Count only structural message rows after existing nested-row filtering, so nested row-like markup does not skew the reported row position.
- Strengthen existing missing/malformed `data-href` tests to assert module/page/row context.
- Preserve first-page body reuse, pager filtering, nested-row filtering, duplicate message ID handling, retry-aware list acquisition, detail fetching, inbox/sent-box wrappers, and send behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Private-message list parser error-context ergonomics
- Test expectation strengthening

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Structural private-message rows missing `data-href` still fail. | `TestPrivateMessageCollection.test_acquire_missing_message_href_raises` raises `NoElementException`. | A change that silently skips or accepts the malformed structural row rejects this local completion claim. |
| Structural private-message rows with malformed `data-href` still fail. | `TestPrivateMessageCollection.test_acquire_malformed_message_href_raises` raises `NoElementException`. | A change that fabricates a message ID or silently skips the malformed structural row rejects this local completion claim. |
| The malformed list-row failures identify module, page, and structural row position. | The focused tests assert `for module: dashboard/messages/DMInboxModule (page=1, row=1)`. | The RED tests failed before the fix because the messages only named `data-href` or the malformed value. |
| Nested row-like markup does not distort reported structural row positions. | Source inspection shows `row_index` increments only after `_is_inside_message_row(...)` filtering. | A future change that counts nested rows before filtering could report misleading row positions when message rows contain row-like markup. |
| Private-message workflows remain green. | `uv run pytest tests/unit/test_private_message.py -q` passed 32 tests. | Regressions in detail parsing, inbox/sent-box acquisition, first-page reuse, pager filtering, nested-row filtering, retry behavior, duplicate IDs, or send behavior reject this local completion claim. |
| Adjacent client workflows remain green. | `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 51 tests. | Regressions in client private-message accessors reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `14bf330 fix(private_message): include context in list row errors`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_message_href_raises tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_message_href_raises -q` failed before the fix because the errors lacked module, page, and row context.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_missing_message_href_raises tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_malformed_message_href_raises -q`
- `uv run pytest tests/unit/test_private_message.py -q` passed 32 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 51 tests.
- `uv run pytest tests/unit -q` passed 720 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run successfully: `uv run pyright` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Missing and malformed `data-href` on structural private-message list rows still raise `NoElementException`.
- Those exceptions include the affected module name, page number, and structural row position.
- Nested message-row markup remains ignored before row positions are counted.
- Successful message ID extraction, non-numeric pager handling, row-pager filtering, nested-row filtering, duplicate ID handling, retry-aware pagination, detail fetching, inbox/sent-box wrappers, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message inbox and sent-box acquisition are dashboard read workflows where malformed generated list rows should still fail instead of inventing message IDs. The failure should identify which module, page, and structural row produced the malformed shape so maintainers can triage from logs without storing raw dashboard HTML or private message content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established private-message list acquisition as a retry-aware read path with pagination, duplicate-ID deduplication, row/pager parser boundaries, and first-page parse reuse.
- Recent parser-context slices showed that object- and row-specific failure messages improve resumable local ledgers without changing successful behavior.
- The refreshed complexity memo continues to list `src/wikidot/module/private_message.py` as an audit-worthy parser/acquisition surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw dashboard HTML, and private-message contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change request payloads, retry policy, pager parsing, message ID extraction rules, duplicate message ID handling, detail response parsing, inbox/sent-box wrappers, `PrivateMessage` fields, send behavior, or live Wikidot behavior. It only adds module/page/row context to existing malformed private-message list-row parser failures.
