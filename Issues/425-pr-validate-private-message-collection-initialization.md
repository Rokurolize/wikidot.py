# PR Draft: Validate Private Message Collection Initialization

## Summary

`PrivateMessageCollection` documents and behaves as a collection of `PrivateMessage` objects, but it inherited the raw `list` constructor. A caller could construct `PrivateMessageCollection("1")`, `PrivateMessageCollection(("1",))`, or `PrivateMessageCollection([None])`; the malformed collection then failed later in `str(...)`, iteration, `find(...)`, inbox/sent-box wrappers, direct `PrivateMessage.from_id(...)` helper tests, or downstream generated ledgers with unstable attribute errors or silently poisoned local state.

This change validates constructor input before storing entries. Non-list non-`None` `messages` values now raise `ValueError("messages must be a list or None")`; list entries that are not `PrivateMessage` now raise `ValueError("messages list entries must be PrivateMessage")`. `messages=None`, empty collections, valid `PrivateMessage` lists, `str(...)`, iteration, `find(...)`, direct `from_ids(...)` reads, empty direct reads, inbox and sent-box wrappers, `PrivateMessage.from_id(...)`, client private-message accessors, retry-aware acquisition, duplicate-detail reuse, and parser diagnostics remain unchanged.

## Outcome

Callers cannot silently create malformed `PrivateMessageCollection` instances through the public constructor, while existing private-message read, inbox, sent-box, lookup, retry, cache, parser, and client workflows remain intact.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free private-message detail reads, inbox/sent-box acquisition, generated PM audit ledgers, private-message migration checks, duplicate-detail reuse, `Client.private_message.get_messages(...)`, `Client.private_message.get_message(...)`, `PrivateMessage.from_id(...)`, or local fixtures that construct private-message collections directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads as a practical workflow surface. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), and [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md) establish direct PM reads, inbox/sent list reads, empty-batch no-op behavior, retry behavior, duplicate detail reuse, parser scoping, text fidelity, response diagnostics, caller-provided message-ID validation, loaded-collection search-key validation, and retry-control validation as active operational boundaries. Adjacent constructor-hardening drafts [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), and [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md) establish the local state-integrity pattern for collection constructors.

Those prior slices are not duplicates. The private-message drafts covered fetching, retry behavior, empty direct reads, duplicate reuse, parser scope, parser diagnostics, response diagnostics, caller-provided message ID validation, search-key validation after a collection already exists, and retry config validation. None of them validates the `PrivateMessageCollection(messages=...)` constructor itself before malformed message entries become stored list state.

## Related Issue

Builds directly on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), and the adjacent constructor validation pattern from [417-pr-validate-page-collection-initialization.md](417-pr-validate-page-collection-initialization.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [420-pr-validate-page-file-collection-initialization.md](420-pr-validate-page-file-collection-initialization.md), [421-pr-validate-forum-post-revision-collection-initialization.md](421-pr-validate-forum-post-revision-collection-initialization.md), [422-pr-validate-forum-post-collection-initialization.md](422-pr-validate-forum-post-collection-initialization.md), [423-pr-validate-forum-thread-collection-initialization.md](423-pr-validate-forum-thread-collection-initialization.md), and [424-pr-validate-forum-category-collection-initialization.md](424-pr-validate-forum-category-collection-initialization.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PrivateMessageCollection.__init__(messages=...)` validation.
- Preserve omitted `messages` and `messages=None` as empty collections.
- Reject non-list non-`None` `messages` with `ValueError("messages must be a list or None")`.
- Reject non-`PrivateMessage` list entries with `ValueError("messages list entries must be PrivateMessage")`.
- Update one existing unit fixture from a generic `MagicMock` entry to a real `PrivateMessage` fixture because constructor validation now rejects non-message stand-ins.
- Preserve valid empty collections, valid `PrivateMessage` entries, `str(...)`, iteration, `find(...)`, direct `from_ids(...)`, inbox and sent-box wrappers, `PrivateMessage.from_id(...)`, client accessors, retry-aware acquisition, duplicate-detail reuse, parser diagnostics, and private-message send behavior.

## Type Of Change

- Input validation
- Public constructor behavior hardening
- Private-message collection state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessageCollection(messages=True)`, `False`, `"1"`, `("1",)`, and `1` must raise `ValueError("messages must be a list or None")` before storing collection entries. |
| R2 | `PrivateMessageCollection(messages=[None])`, `[True]`, `["1"]`, and `[{"id": 1}]` must raise `ValueError("messages list entries must be PrivateMessage")` before storing collection entries. |
| R3 | `PrivateMessageCollection()`, `PrivateMessageCollection(None)`, `PrivateMessageCollection([])`, and `PrivateMessageCollection([valid_message])` must remain valid. |
| R4 | Existing `str(...)`, iteration, `find(...)`, `from_ids(...)`, empty direct reads, inbox and sent-box wrappers, `PrivateMessage.from_id(...)`, client private-message accessors, retry behavior, duplicate reuse, parser diagnostics, and send behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, private-message wrapper tests, adjacent client tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list constructor input fails at the public constructor boundary, while `None` remains valid. | `TestPrivateMessageCollection.test_init_rejects_non_list_messages` failed RED for `True`, `False`, `"1"`, `("1",)`, and `1`, then passed GREEN after constructor validation was added. | Treating strings or tuples as message entries, surfacing incidental `TypeError`, or deferring failure to iteration rejects this local completion claim. | PrivateMessageCollection constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Non-`PrivateMessage` constructor list entries fail at the public constructor boundary. | `TestPrivateMessageCollection.test_init_rejects_non_message_entries` failed RED for `None`, `True`, `"1"`, and `{"id": 1}` because the constructor did not raise, then passed GREEN after entry validation was added. | Accepting missing values, booleans, strings, dictionaries, serialized PM records, or fixture stand-ins as stored messages rejects this local completion claim. | PrivateMessageCollection constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Valid constructor inputs remain green. | Existing `str(...)`, iteration, valid-message lookup, and valid not-found lookup tests plus the focused constructor regressions passed in the 13-test focused run. | Rejecting omitted input, `None`, empty valid lists, valid message lists, string representation, iteration, or normal ID lookup rejects this local completion claim. | PrivateMessageCollection constructor and methods | `tests/unit/test_private_message.py` |
| R4 | Existing private-message workflows remain green. | Focused private-message collection, inbox, sent-box, and `PrivateMessage.from_id(...)` tests passed 72 tests, private-message plus client tests passed 110 tests, and full unit tests passed 1567 tests. | Regressing direct message reads, empty direct reads, inbox acquisition, sent-box acquisition, client accessors, parser diagnostics, retry behavior, duplicate reuse, ID validation, search validation, send behavior, or adjacent client behavior rejects this local completion claim. | Private-message and client workflows | `tests/unit/test_private_message.py`, `tests/unit/test_client.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private message bodies, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, targeted private-message tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a923c9b fix(private_message): validate message collection initialization`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_init_rejects_non_list_messages -q` failed 5 tests before the container fix; strings and tuples were accepted, while booleans and integers leaked incidental `TypeError`.
- GREEN: the same focused command passed 5 tests after adding non-list validation.
- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_init_rejects_non_message_entries -q` failed 4 tests before the entry fix because malformed list entries were accepted and stored.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection::test_init_rejects_non_list_messages tests/unit/test_private_message.py::TestPrivateMessageCollection::test_init_rejects_non_message_entries tests/unit/test_private_message.py::TestPrivateMessageCollection::test_str_representation tests/unit/test_private_message.py::TestPrivateMessageCollection::test_iter tests/unit/test_private_message.py::TestPrivateMessageCollection::test_find_existing tests/unit/test_private_message.py::TestPrivateMessageCollection::test_find_not_existing -q` passed 13 tests after adding entry validation and preserving existing collection behavior.
- `uv run ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_private_message.py::TestPrivateMessageCollection tests/unit/test_private_message.py::TestPrivateMessageInbox tests/unit/test_private_message.py::TestPrivateMessageSentBox tests/unit/test_private_message.py::TestPrivateMessage::test_from_id -q` passed 72 tests.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 110 tests.
- `uv run pytest tests/unit -q` passed 1567 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 81 files already formatted.
- `uv run mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `PrivateMessageCollection(messages=True)`, `False`, `"1"`, `("1",)`, and `1` raise `ValueError("messages must be a list or None")`.
- `PrivateMessageCollection(messages=[None])`, `[True]`, `["1"]`, and `[{"id": 1}]` raise `ValueError("messages list entries must be PrivateMessage")`.
- `PrivateMessageCollection()`, `PrivateMessageCollection(None)`, `PrivateMessageCollection([])`, and `PrivateMessageCollection([valid_message])` continue to work.
- Existing `str(...)`, iteration, `find(...)`, `from_ids(...)`, empty direct reads, inbox and sent-box wrappers, `PrivateMessage.from_id(...)`, client private-message accessors, retry behavior, duplicate reuse, parser diagnostics, and send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PrivateMessageCollection` is the stored object shape behind browser-free direct PM detail reads, inbox/sent-box acquisition, `PrivateMessage.from_id(...)`, client private-message accessors, duplicate-detail reuse, and generated PM ledgers. Constructor validation keeps malformed local state out of the collection while preserving existing read, parser, retry, cache, lookup, wrapper, and send behavior.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free private-message detail reads, inbox/sent-box acquisition, duplicate detail reuse, empty direct lookup handling, and tests that seed private-message collections directly.
- Existing local drafts covered private-message fetch retry behavior, duplicate detail reduction, parse reuse, response diagnostics, parser field diagnostics, message ID input validation, loaded collection search validation, and retry-control validation, but did not cover the `PrivateMessageCollection(messages=...)` constructor itself.
- The focused RED failures showed invalid constructor input either raised incidental exceptions, was accepted as an iterable, or stored invalid entries. The GREEN regressions cover non-list input, malformed list entries, valid constructor input preservation, inbox/sent-box wrappers, and adjacent client workflows.
- This slice only validates private-message collection constructor input and updates one test fixture to use a real `PrivateMessage`. It does not change direct PM acquisition, inbox/sent-box acquisition, parser selectors, message ID parsing, sender/recipient parsing, subject/body parsing, timestamp parsing, cached duplicate behavior, `find(...)`, `PrivateMessage.from_id(...)`, `PrivateMessage.send(...)`, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private message bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects duck-typed message-like objects and test mocks in `PrivateMessageCollection`. Callers should construct real `PrivateMessage` entries before storing them in a private-message collection.
