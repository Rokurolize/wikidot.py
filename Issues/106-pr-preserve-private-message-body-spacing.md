# PR Draft: Preserve Private Message Body Spacing

## Summary

`PrivateMessageCollection.from_ids(...)`, used by direct private-message detail reads and the inbox/sent-box acquisition paths, parses private-message detail HTML returned by `dashboard/PMReadModule`.

Before this fix, the private-message body was extracted with `body_element.get_text()` and no separator. When a rendered message body contained adjacent paragraph or formatted child elements, visible text could be concatenated. The focused regression used `<div class="body"><p>First <span>message</span></p><p>Second message</p></div>`; before the fix, the parsed body became `First messageSecond message`.

This fix extracts message body text with a space separator and `strip=True`, preserving visible word boundaries while keeping direct private-message metadata, subject parsing, duplicate-ID output order, retry behavior, list acquisition, inbox/sent-box wrappers, and send actions unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), because those drafts established private-message detail reads as a practical local workflow and separated structural headers from user-authored body content.

The parser-boundary failure class is adjacent to [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md) and [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), because those fixes also protect private-message list/detail behavior from user-visible message content that resembles generated structure.

No upstream issue was filed from this local workspace.

## Changes

- Extract direct private-message body text with `get_text(" ", strip=True)` instead of the default empty separator.
- Add a public direct-detail regression where adjacent paragraphs and inline formatting keep a space between visible text chunks.
- Preserve sender, recipient, subject, creation time, permission mapping, retry-aware fetching, duplicate-ID detail reuse, inbox/sent-box list parsing, row/pager guards, and send behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Private-message body text should not concatenate adjacent rendered paragraphs or formatted child text. | `TestPrivateMessageCollection.test_from_ids_preserves_body_text_spacing` asserts `body == "First message Second message"` through `PrivateMessageCollection.from_ids(...)`. | The RED test failed before the fix because the parsed body was `First messageSecond message`. |
| Structural private-message header parsing should remain scoped and unchanged. | Neighboring direct-detail tests for successful detail parsing, body header markup, duplicate IDs, and retry remained green. | If body markup changes sender/recipient parsing or header count behavior, the focused neighboring tests reject the local completion claim. |
| Private-message collection and client wrappers should remain green. | `uv run pytest tests/unit/test_private_message.py -q` passed 30 tests, and `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 49 tests. | Regressions in direct detail reads, inbox/sent-box acquisition, row/pager filtering, duplicate ID handling, retry behavior, or client accessors reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `4f86438 fix(private_message): preserve body text spacing`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_preserves_body_text_spacing -q` failed before the fix because `body` was `First messageSecond message`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_preserves_body_text_spacing -q`
- `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_success tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_ignores_body_header_markup tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_preserves_body_text_spacing tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_deduplicates_duplicate_message_ids_preserving_order tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_retries_transient_detail_failures -q` passed 5 tests.
- `uv run pytest tests/unit/test_private_message.py -q` passed 30 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 49 tests.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run ruff format --check src/wikidot/module/private_message.py tests/unit/test_private_message.py`
- `uv run pytest tests/unit -q` passed 658 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Direct private-message body text preserves a separator between adjacent rendered paragraphs and formatted child text.
- Sender, recipient, subject, and creation-time parsing remain unchanged.
- Body-rendered header-like markup still cannot alter structural sender/recipient metadata.
- Existing direct message lookup, duplicate ID behavior, retry-aware fetching, exhausted retry handling, inbox acquisition, sent-box acquisition, row/pager filtering, nested-row filtering, client accessors, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message bodies are user-authored content and can render multiple paragraphs or formatted inline HTML. Detail parsing should preserve visible word boundaries instead of concatenating adjacent rendered text nodes. This keeps direct private-message reads faithful to the rendered body without changing request flow or public object shape.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md) established direct private-message detail parsing as a practical read-heavy target.
- Parser-boundary drafts [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md) and [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md) established private-message content as a recurring list/detail boundary risk.
- The refreshed complexity scan continues to flag private-message parsing/acquisition paths as audit-worthy.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and message bodies out of upstream discussion.

## Additional Notes

This slice does not change request payloads, retry policy, direct message batch deduplication, sender parsing, recipient parsing, subject parsing, date parsing, permission mapping, inbox/sent-box list parsing, row/pager filtering, nested-row filtering, client wrappers, or send behavior. It only changes how direct private-message detail body text is flattened from rendered HTML into `PrivateMessage.body`.
