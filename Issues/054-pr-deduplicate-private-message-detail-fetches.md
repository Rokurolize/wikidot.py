# PR Draft: Deduplicate Private Message Detail Fetch IDs

## Summary

`PrivateMessageInbox.acquire(...)` and `PrivateMessageSentBox.acquire(...)` collect message IDs from each dashboard list page, then call `PrivateMessageCollection.from_ids(...)` to fetch message details. If Wikidot repeats a row across pages or renders a duplicate message row, the acquisition path would pass duplicate IDs into the detail fetch step and request the same message detail more than once.

The fix keeps list-page parsing and result ordering stable while deduplicating message IDs before detail acquisition. The first occurrence of each ID is retained, later duplicates are skipped, and existing retry/error handling stays unchanged.

## Related Issue

Builds on the retry-aware private-message read work in [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md). No upstream issue filed yet.

## Changes

- Track seen message IDs while parsing inbox/sent-box list pages.
- Preserve first-seen message ordering before calling `PrivateMessageCollection.from_ids(...)`.
- Avoid redundant detail fetches for duplicate message IDs.
- Add a focused regression test covering duplicates across paginated list pages.

## Type Of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Performance/reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification |
| --- | --- | --- |
| R1: Duplicate list rows do not trigger duplicate detail fetches | `_acquire(...)` calls `from_ids(...)` with each message ID once | `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order -q` |
| R2: Ordering remains stable | The first occurrence order is retained when duplicates are skipped | Same focused test |
| R3: Existing private-message retry and access behavior is preserved | Private-message and client tests plus full unit suite pass | Commands listed below |

## Testing

Local implementation commit: `a1c9e35 perf(private_message): deduplicate message detail fetch ids`

- [x] `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_deduplicates_message_ids_preserving_order -q` failed before the fix because `from_ids(...)` received `[123, 123, 456]`, then passed after the fix with `[123, 456]`.
- [x] `uv run --extra test pytest tests/unit/test_private_message.py -q` passed with 24 tests.
- [x] `uv run --extra test pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed with 43 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 608 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- Duplicate private-message IDs collected from paginated inbox or sent-box rows are removed before detail fetching.
- First-seen list order is preserved.
- Missing or malformed `data-href` rows still raise the existing `NoElementException` errors.
- Transient list/detail AMC failures still use the existing retry-aware behavior.
- Exhausted required list/detail reads still raise the existing explicit `UnexpectedException` errors.
- `PrivateMessage.send(...)` remains unchanged on the direct send action path.

## Upstream-Safe Motivation

Private-message list acquisition should not spend dashboard requests fetching the same detail record twice. A small ordered deduplication pass keeps the public API stable while reducing redundant AMC work when Wikidot list markup repeats a row across paginated results.

## Local Evidence, Not For Upstream Paste

- Local retry hardening in [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md) established private-message list/detail acquisition as an active read-heavy workflow.
- The refreshed complexity scan continues to flag `src/wikidot/module/private_message.py` as a module worth auditing for list/retry parsing overhead.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, command transcripts, or private message bodies into an upstream PR.

## Additional Notes

This slice does not change private-message parsing, detail response parsing, pagination request construction, retry policy, no-message permission mapping, or send behavior. It only removes duplicate IDs before the existing detail fetch step for inbox/sent-box list acquisition. Follow-up [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md) handles duplicate IDs passed directly to the public `from_ids(...)` API while preserving duplicate output positions.
