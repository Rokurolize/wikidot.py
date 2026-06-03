# PR Draft: Preserve Private Message Subject Spacing

## Summary

`PrivateMessageCollection.from_ids(...)` parses Wikidot private message details and exposes the visible message subject through `PrivateMessage.subject`.

Before this fix, the subject was extracted with raw `subject_element.get_text()`. When a rendered subject contained adjacent formatted child elements, visible text chunks could be concatenated. The focused regression changed the subject to `<span class="subject"><span>First <em>Part</em></span><span>Subject</span></span>`; before the fix, `PrivateMessage.subject` became `First PartSubject`.

This fix extracts private-message subjects with a space separator and `strip=True`, matching the already-normalized body parsing path and preserving visible word boundaries while keeping sender parsing, recipient parsing, message body parsing, date parsing, retry handling, duplicate ID reuse, inbox/sent-box factories, and message ordering unchanged.

## Related Issue

Builds on private-message parser drafts [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), and [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), because those drafts established message detail parsing and private-message acquisition as practical rollout-backed read paths.

The text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [116-pr-preserve-listpages-field-spacing.md](116-pr-preserve-listpages-field-spacing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), and [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental structural-parser changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract private-message subjects with `get_text(" ", strip=True)` instead of raw `get_text()`.
- Add a public `PrivateMessageCollection.from_ids(...)` regression where adjacent formatted subject chunks keep a space between visible text chunks.
- Preserve message detail batching, duplicate message ID handling, sender/recipient parsing, body parsing, created-at parsing, inbox/sent-box wrappers, and forbidden/no-message handling.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Private-message subjects should not concatenate adjacent rendered subject chunks or formatted child text. | `TestPrivateMessageCollection.test_from_ids_preserves_subject_text_spacing` asserts `result[0].subject == "First Part Subject"` through `PrivateMessageCollection.from_ids(...)`. | The RED test failed before the fix because the parsed subject was `First PartSubject`. |
| Existing private-message detail behavior should remain unchanged. | `uv run pytest tests/unit/test_private_message.py -q` passed 31 private-message tests covering empty input, login checks, header scoping, body spacing, detail retries, duplicate detail reuse, forbidden messages, missing sender/recipient handling, row parsing, pager scoping, inbox wrappers, sent-box wrappers, direct message retrieval, and send requests. | If subject normalization breaks message detail acquisition, retries, duplicate mapping, metadata parsing, or wrappers, the private-message suite rejects the local completion claim. |
| Adjacent message/account/read workflows should remain green. | `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_page.py tests/unit/test_site.py -q` passed 314 tests. | Regressions in client access, user parsing, forum/page/site read paths, or private-message consumers reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `a766e64 fix(private_message): preserve subject text spacing`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_preserves_subject_text_spacing -q` failed before the fix because `result[0].subject` was `First PartSubject`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_preserves_subject_text_spacing -q`
- `uv run pytest tests/unit/test_private_message.py -q` passed 31 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py tests/unit/test_user.py tests/unit/parsers/test_user_parser.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_page.py tests/unit/test_site.py -q` passed 314 tests.
- `uv run pytest tests/unit -q` passed 671 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- `PrivateMessage.subject` preserves a separator between adjacent rendered subject chunks and formatted child text.
- Incidental wrapper whitespace around the subject element is stripped.
- `PrivateMessage.body` keeps its existing spacing-preserving behavior.
- Sender, recipient, and created-at parsing remain scoped to the message detail header.
- Duplicate message IDs still reuse parsed details while preserving requested output order.
- Inbox and sent-box factories continue to delegate to the shared private-message parser.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message subjects are user-visible fields returned by the message detail API. They should preserve visible word boundaries from rendered HTML the same way private-message bodies already do, without changing message acquisition, sender/recipient metadata, retry behavior, or wrappers.

## Local Evidence, Not For Upstream Paste

- Earlier private-message drafts [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), and [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md) established private messages as a recurring local read path.
- Text-fidelity drafts [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md) through [118-pr-preserve-printuser-name-spacing.md](118-pr-preserve-printuser-name-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag parser-heavy collection modules as audit-worthy; this slice keeps the change localized to the message detail parser rather than broad refactoring.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and message content out of upstream discussion.

## Additional Notes

This slice does not change private-message element selection, sender/recipient parsing, body flattening, `odate` parsing, retry policy, duplicate detail reuse, forbidden-message behavior, or inbox/sent-box wrapper behavior. It only changes how subject element text is flattened into `PrivateMessage.subject`.
