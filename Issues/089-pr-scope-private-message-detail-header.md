# PR Draft: Scope Private Message Detail Header Parsing

## Summary

`PrivateMessageCollection.from_ids(...)` parses private-message detail HTML returned by `dashboard/messages/DMViewMessageModule`.

Before this fix, message sender/recipient metadata was selected with response-wide descendants such as `div.pmessage div.header span.printuser`. If the user-authored message body rendered a `div.header` fragment with a `span.printuser`, the parser counted that body content as message header metadata and rejected an otherwise valid message with `NoElementException`.

This fix first locates the structural `div.pmessage` container, then parses direct sender, recipient, subject, and date metadata from the direct `div.header` child and the message body from the direct `div.body` child. Header-like markup inside the message body no longer changes the sender/recipient candidate set, while private-message detail retry behavior, duplicate-ID handling, no-message permission mapping, inbox/sent-box acquisition, and send actions remain unchanged.

## Related Issue

Builds on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), because direct private-message detail acquisition is the public fetch path affected by this parser. It also follows the same private-message acquisition line as [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md). The parser-boundary motivation matches the forum content-boundary fixes in [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), and [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse private-message detail metadata from the direct structural `div.pmessage > div.header` element.
- Read sender and recipient only from direct `span.printuser` children of that header.
- Read subject and timestamp from direct header children.
- Read body text from the direct `div.pmessage > div.body` element.
- Add a public `PrivateMessageCollection.from_ids(...)` regression test where the message body contains a header-like block with a fake `span.printuser`.
- Preserve retry handling, duplicate requested output positions, duplicate response parsing reuse, empty input behavior, `no_message` permission mapping, inbox/sent-box list acquisition, and send actions.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Message sender/recipient metadata should come from the structural detail header, not message body content. | `TestPrivateMessageCollection.test_from_ids_ignores_body_header_markup` asserts the parsed sender and recipient are the two structural header users and that `user_parser` is called exactly twice. | The RED test failed before the fix with `NoElementException: Expected sender and recipient elements for message: 1` because the body fake `span.printuser` was included. |
| Public direct private-message acquisition should preserve normal behavior. | `uv run pytest tests/unit/test_private_message.py -q` passed 27 tests. | Regressions in login handling, empty input, retry behavior, duplicate IDs, permission mapping, missing metadata errors, list acquisition, or send behavior reject the local completion claim. |
| Adjacent client/private-message behavior stays green. | `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 46 tests. | Client or private-message regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `5088b81 fix(private_message): scope detail header parsing`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_ignores_body_header_markup -q` failed before the fix with `NoElementException: Expected sender and recipient elements for message: 1`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_ignores_body_header_markup -q`
- `uv run pytest tests/unit/test_private_message.py -q` passed 27 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 46 tests.
- `uv run pytest tests/unit -q` passed 641 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Private-message detail parsing locates the direct `div.pmessage` container and direct structural `div.header`.
- Sender and recipient are parsed only from direct structural header `span.printuser` children.
- Subject and date are parsed only from direct structural header children.
- A body-rendered `div.header` block with fake `span.printuser` markup does not affect sender/recipient parsing or trigger a false missing-metadata error.
- Existing direct detail retry behavior, duplicate ID handling, duplicate parse reuse, empty input behavior, permission mapping, inbox/sent-box acquisition, and send behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Private-message bodies are user-authored content. The parser should treat the message detail module's direct header element as the metadata boundary instead of selecting every descendant `div.header span.printuser` inside the message container. Scoping detail metadata extraction to the structural header prevents body content from breaking valid message parsing while preserving the public API and acquisition flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including direct private-message reads as an already-hardened acquisition surface.
- Earlier private-message drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), and [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md) established direct private-message detail parsing as a practical local usage path.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), and [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md) established the concrete failure pattern: authored content can collide with structural parser selectors.
- The refreshed complexity scan continues to flag `src/wikidot/module/private_message.py` around detail/list parsing as an audit-worthy path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved message contents out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry behavior, duplicate ID preservation, duplicate response parsing reuse, inbox/sent-box list acquisition, permission mapping, or send actions. It only narrows private-message detail metadata parsing to the structural direct message header and body elements.
