# PR Draft: Validate PrivateMessage ID Field

## Summary

`PrivateMessage` records are produced by direct private-message detail reads, inbox/sent-box acquisition, `Client.private_message` accessors, duplicate-detail reuse, generated PM ledgers, and local fixtures. Earlier local slices validated caller-provided message IDs before lookup, loaded-collection search IDs before scanning, private-message collection constructor entries before storage, and multiple private-message parser/detail boundaries. The public `PrivateMessage(..., id=...)` dataclass constructor still accepted malformed stored IDs such as `None`, booleans, strings, and floats.

This change validates `PrivateMessage.id` at initialization. Malformed non-integer values now raise `ValueError("message_id must be an integer")`. Valid integer IDs remain valid, and parsed messages already use integer IDs from the existing lookup/list parsing paths.

## Outcome

Callers cannot silently construct private-message records whose stored message ID is not an integer, while direct PM reads, inbox/sent-box acquisition, duplicate-detail reuse, parser diagnostics, collection behavior, `PrivateMessage.from_id(...)`, client accessors, and send behavior continue to work.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free private-message detail reads, inbox/sent-box acquisition, generated PM audit ledgers, private-message migration checks, `Client.private_message.get_message(...)`, `Client.private_message.get_messages(...)`, or local fixtures that construct `PrivateMessage` records directly.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads and stored PM records as practical workflow surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), [397-pr-validate-private-message-retry-controls.md](397-pr-validate-private-message-retry-controls.md), and [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md) establish direct PM reads, inbox/sent list reads, empty-batch behavior, retry behavior, duplicate detail reuse, parser scoping, text fidelity, response diagnostics, caller-provided message-ID validation, loaded-collection search-key validation, retry-control validation, and collection constructor state integrity as active operational boundaries.

Those prior slices are not duplicates. Issues 361 and 381 cover public lookup inputs and already-loaded collection search keys. Issue 425 validates the `PrivateMessageCollection(messages=...)` container and stored entry types. This slice validates the separate public dataclass `PrivateMessage.id` field so malformed message IDs cannot become stored record state in manually constructed messages, fixtures, generated ledgers, or rehydrated records.

## Related Issue

Builds directly on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md), [425-pr-validate-private-message-collection-initialization.md](425-pr-validate-private-message-collection-initialization.md), and the adjacent constructor-field validation pattern from [448-pr-validate-site-member-user-field.md](448-pr-validate-site-member-user-field.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), and [450-pr-validate-site-application-text-field.md](450-pr-validate-site-application-text-field.md).

No upstream issue was filed from this local workspace.

## Changes

- Add `PrivateMessage.id` validation at dataclass initialization.
- Reuse the existing private-message ID validator so constructor IDs reject non-integers and booleans with `ValueError("message_id must be an integer")`.
- Preserve valid integer IDs, parsed direct-detail messages, inbox/sent-box records, collections, `from_id(...)`, client accessors, duplicate reuse, parser diagnostics, and send behavior.
- Make two existing invalid-input test fixtures explicit `Any` values so targeted pyright can type-check the changed private-message test file without weakening runtime coverage.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Private-message record state integrity
- Test addition
- Test fixture typing cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessage(id=None)`, `True`, `"1"`, and `1.25` must raise `ValueError("message_id must be an integer")` when other constructor fields are valid. |
| R2 | Valid integer message IDs must remain valid constructor input. |
| R3 | Existing direct PM reads, inbox/sent-box acquisition, collection initialization, loaded-collection lookup, `PrivateMessage.from_id(...)`, client private-message accessors, parser diagnostics, retry behavior, duplicate reuse, and send behavior must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, private-message tests, adjacent client/private-message tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed constructor ID values fail at the public dataclass boundary. | `TestPrivateMessage.test_init_rejects_non_integer_message_id` failed RED for `None`, `True`, `"1"`, and `1.25` because the constructor did not raise, then passed GREEN after constructor validation was added. | Accepting missing values, booleans, strings, floats, serialized IDs, or emitting `PrivateMessage` records with non-integer IDs rejects this local completion claim. | PrivateMessage constructor | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Valid integer ID semantics stay green. | Existing `sample_message`, `str(...)`, direct `from_ids(...)` success, inbox/sent-box wrapper, and `PrivateMessage.from_id(...)` tests passed. | Rejecting ordinary integer IDs, coercing strings to integers, or changing stored IDs rejects this local completion claim. | Parser-created and manually created messages | `tests/unit/test_private_message.py` |
| R3 | Existing private-message workflows remain green. | `tests/unit/test_private_message.py` passed 90 tests, adjacent private-message/client tests passed 114 tests, and full unit tests passed 1740 tests. | Regressing direct message reads, empty direct reads, inbox acquisition, sent-box acquisition, duplicate detail behavior, parser diagnostics, collection initialization, loaded-collection lookup, `PrivateMessage.from_id(...)`, client accessors, send behavior, or adjacent client behavior rejects this local completion claim. | Private-message and client workflows | `tests/unit/test_private_message.py`, `tests/unit/test_client.py`, `tests/unit` |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private message bodies, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, private-message tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues unrelated to this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `54578e7 fix(private_message): validate message id`.

- RED: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_non_integer_message_id -q` failed 4 tests before the fix; every malformed `id` value reported `DID NOT RAISE`.
- GREEN: `uv run pytest tests/unit/test_private_message.py::TestPrivateMessage::test_init_rejects_non_integer_message_id -q` passed 4 tests.
- `uv run ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed.
- `uv run pytest tests/unit/test_private_message.py -q` passed 90 tests.
- `uv run pyright src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed with 0 errors, 0 warnings, and 0 informations after making existing invalid-input fixtures explicit `Any`.
- `uv run mypy src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed with no issues in 2 source files.
- `uv run pytest tests/unit/test_private_message.py tests/unit/test_client.py -q` passed 114 tests.
- `uv run pytest tests/unit -q` passed 1740 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 82 files already formatted.
- `uv run mypy src tests` passed with no issues in 82 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 68 existing full-tree typing errors outside this slice, including fixture `None` mismatches, intentional invalid-input test calls, invalid `SearchPagesQuery` parameter calls, requestutil response narrowing issues, and site test mock typing issues. The changed source file and changed test file pass pyright together.

## Acceptance Criteria

- `PrivateMessage(id=None)`, `True`, `"1"`, and `1.25` raise `ValueError("message_id must be an integer")`.
- Valid integer IDs remain valid.
- Existing direct PM reads, inbox/sent-box acquisition, collection initialization, loaded-collection lookup, `PrivateMessage.from_id(...)`, client private-message accessors, parser diagnostics, retry behavior, duplicate reuse, and send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PrivateMessage` is the record shape behind browser-free PM reads, inbox/sent-box acquisition, client accessors, duplicate-detail reuse, and generated PM ledgers. Lookup APIs already validate caller-provided message IDs; the record constructor should apply the same invariant so fixture-created or rehydrated messages cannot carry non-integer IDs into logs, comparisons, searches, or downstream ledgers.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence used browser-free private-message detail reads, inbox/sent-box acquisition, duplicate detail reuse, empty direct lookup handling, client accessors, and tests that seed private-message records directly.
- Existing local drafts covered private-message fetch retry behavior, duplicate detail reduction, parse reuse, response diagnostics, parser field diagnostics, message ID input validation, loaded collection search validation, collection constructor validation, and retry-control validation, but did not cover the `PrivateMessage(id=...)` field itself.
- The focused RED failures showed invalid constructor IDs were accepted as dataclass state. The GREEN regression covers missing, boolean, string, and float ID values.
- This slice only validates stored private-message ID type at construction. It does not change direct PM acquisition, inbox/sent-box acquisition, parser selectors, sender/recipient parsing, subject/body parsing, timestamp parsing, cached duplicate behavior, collection initialization, `find(...)`, `PrivateMessage.from_id(...)`, `PrivateMessage.send(...)`, live site behavior, or parsing.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private message bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load message IDs from JSON, YAML, CLI flags, generated structures, spreadsheets, or environment variables should normalize them to integers before constructing `PrivateMessage` records.
