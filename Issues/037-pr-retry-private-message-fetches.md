# PR Draft: Retry Private Message Fetches

## Summary

`PrivateMessageCollection.from_ids(...)`, `PrivateMessageInbox.acquire(...)`, `PrivateMessageSentBox.acquire(...)`, and the `Client.private_message` accessors retrieve private message detail and inbox/sent-box list pages with dashboard message AMC modules. These read paths used direct `client.amc_client.request(...)` calls, so a transient AMC failure could raise immediately, parse an exception object as a response, or return a partial list after a later paginated page failed.

The fix adds retry-aware private-message read requests for detail, inbox, and sent-box retrieval. It preserves the existing `no_message` to `ForbiddenException` mapping, keeps send-message action requests on the existing direct action path, raises explicit exhausted-retry errors for required detail/list pages, and avoids re-fetching page 1 when a message list has pagination.

## Related Issue

Drafted from the same read-heavy AMC retry area as [036-pr-retry-thread-post-fetches.md](036-pr-retry-thread-post-fetches.md), [035-pr-retry-thread-detail-fetches.md](035-pr-retry-thread-detail-fetches.md), [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), and [031-pr-retry-member-list-fetches.md](031-pr-retry-member-list-fetches.md). No upstream issue filed yet.

## Changes

- Add a private-message retry helper that retries transient AMC exceptions while preserving non-retryable `ForbiddenException` and `WikidotStatusCodeException(status_code="no_message")` responses.
- Route `PrivateMessageCollection.from_ids(...)` through the retry-aware helper.
- Route `PrivateMessageCollection._acquire(...)`, used by inbox and sent-box retrieval, through the retry-aware helper for the first list page and additional list pages.
- Raise `UnexpectedException("Cannot retrieve private message: ...")` when a required message detail request exhausts retries.
- Raise `UnexpectedException("Cannot retrieve private messages page: ...")` when a required inbox/sent-box list page exhausts retries.
- Preserve `PrivateMessage.send(...)` on the existing direct action request path.
- Avoid re-fetching page 1 during paginated inbox/sent-box acquisition.
- Add focused tests for transient detail retry, exhausted detail retry, transient first-page list retry, and exhausted additional-page list retry.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `3f0c9be fix(private_message): retry message fetches`

- [x] `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_retries_transient_detail_failures -q` failed before the fix because `from_ids(...)` raised the transient exception returned by `client.amc_client.request(..., return_exceptions=True)` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_raises_when_detail_retry_is_exhausted tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_retries_transient_first_page_failures tests/unit/test_private_message.py::TestPrivateMessageCollection::test_acquire_raises_when_paginated_retry_is_exhausted -q` passed after the list and exhausted-retry handling was added.
- [x] `uv run --extra test pytest tests/unit/test_private_message.py -q` passed with 23 tests.
- [x] `uv run --extra test pytest tests/unit/test_client.py tests/unit/test_private_message.py -q` passed with 42 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 575 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed the current complexity leads.

## Acceptance Criteria

- A transient AMC failure while fetching private message detail is retried before surfacing an error.
- A transient AMC failure while fetching the first inbox or sent-box page is retried before parsing the page.
- Exhausted retries for a required message detail request raise `UnexpectedException` with the affected message ID.
- Exhausted retries for a required inbox or sent-box page raise `UnexpectedException` with the affected page number instead of returning a partial list.
- `WikidotStatusCodeException(status_code="no_message")` still maps to `ForbiddenException`.
- `Client.private_message.get_message(...)`, `get_messages(...)`, `inbox`, and `sentbox` keep the same public API.
- `PrivateMessage.send(...)` remains unchanged on the direct send action path.
- Paginated inbox/sent-box acquisition does not re-fetch page 1 after it was already fetched for pager discovery.

## Upstream-Safe Motivation

Private message inspection is a logged-in dashboard read workflow. It should have the same transient-failure tolerance as other retry-aware collection paths, while exhausted required reads should fail explicitly because silently missing inbox/sent-box messages can hide user-visible communication.

## Local Evidence, Not For Upstream Paste

- The rollout evidence index includes a source scan of `src/wikidot/module/private_message.py` showing the old direct dashboard message AMC calls for `DMViewMessageModule`, inbox/sent-box list modules, and the send action path.
- The refreshed complexity scan flags `src/wikidot/module/private_message.py` as a remaining module with nested retry/list parsing control flow worth auditing.
- Local retry hardening across source collection, member/application inspection, recent-changes retrieval, forum category retrieval, thread retrieval, and post-list retrieval established the same read-heavy AMC failure pattern.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, command transcripts, or private message bodies into an upstream PR.

## Additional Notes

This slice does not add new private message features and does not change message parsing, user parsing, date parsing, or send behavior. It only adds retry-aware read requests and explicit exhausted-retry handling for existing private message retrieval APIs. Follow-up [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md) reduces redundant detail reads when paginated list markup repeats the same message ID, and follow-up [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md) applies the same request-deduplication principle to direct public `from_ids(...)` inputs.
