# PR Draft: Validate PrivateMessageCollection Search IDs

## Summary

`PrivateMessageCollection.find(id)` documents `id` as an integer, but malformed caller-provided search keys were not rejected at the public collection lookup boundary. Values such as `None` and strings were treated as ordinary misses, while floats could compare equal to stored integer message IDs and booleans remain a Python `int` subclass.

This change validates the search key before scanning stored private messages. Malformed `id` values now raise `ValueError("id must be an integer")`. Existing valid lookup behavior and valid not-found behavior remain unchanged for non-boolean integer message IDs.

## Outcome

Private message collection callers now get deterministic Python-side preflight validation for malformed message search IDs instead of misleading misses, accidental float equality matches, or boolean/int comparison surprises.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free private-message reads for moderation ledgers, account migration checks, archival jobs, local indexing, generated workflows, inbox/sent-box audits, or source-preserving message transformations.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message list and detail reads as practical read surfaces. Existing drafts [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md), [101-pr-ignore-private-message-row-pager-markup.md](101-pr-ignore-private-message-row-pager-markup.md), [102-pr-ignore-private-message-nested-row-markup.md](102-pr-ignore-private-message-nested-row-markup.md), [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [119-pr-preserve-private-message-subject-spacing.md](119-pr-preserve-private-message-subject-spacing.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), and [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md) cover list acquisition, direct detail acquisition, retries, duplicate response reduction, parser diagnostics, response diagnostics, row-scoping, body/subject text fidelity, timestamp/user parsing, empty direct reads, and direct acquisition ID validation. Adjacent collection search preflight drafts [375-pr-validate-page-file-find-id.md](375-pr-validate-page-file-find-id.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [377-pr-validate-forum-post-revision-search-keys.md](377-pr-validate-forum-post-revision-search-keys.md), [378-pr-validate-forum-post-find-id.md](378-pr-validate-forum-post-find-id.md), [379-pr-validate-forum-thread-find-id.md](379-pr-validate-forum-thread-find-id.md), and [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md) cover nearby loaded-collection lookup keys.

Those prior slices are not duplicates. They fetch, parse, cache, diagnose, or validate direct private-message acquisition inputs, but they do not validate the caller-provided search key to an already loaded `PrivateMessageCollection.find(...)` before scanning stored messages.

## Related Issue

Builds directly on the private-message read hardening line from [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), and the adjacent `find(...)` preflight pattern from [380-pr-validate-forum-category-find-id.md](380-pr-validate-forum-category-find-id.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PrivateMessageCollection.find(id=...)` accepts only non-boolean integer IDs before scanning stored messages.
- Preserve valid `collection.find(1)` behavior when a matching private message exists.
- Preserve valid unknown integer behavior: a well-formed absent ID still returns `None`.
- Preserve direct private-message acquisition, inbox/sent-box acquisition, parser diagnostics, response diagnostics, cached/duplicate handling, empty direct reads, client private-message accessors, and private-message sending semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Private-message lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessageCollection.find(id=...)` must reject `None`, booleans, strings, floats, and other non-integer values with `ValueError("id must be an integer")` before scanning messages. |
| R2 | Valid lookup must remain unchanged for well-formed non-boolean integer IDs that match stored private messages. |
| R3 | Valid not-found behavior must remain unchanged for well-formed non-boolean integer IDs that are absent from the collection. |
| R4 | Existing direct private-message acquisition, inbox/sent-box acquisition, parser diagnostics, response diagnostics, duplicate handling, empty direct reads, client private-message accessors, and private-message sending behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, private-message tests, adjacent client-accessor tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed message IDs fail before collection iteration can compare them with stored private-message IDs. | `TestPrivateMessageCollection.test_find_rejects_non_integer_ids` failed RED before the fix for `None`, `True`, `"1"`, and `1.0`, then passed GREEN after validation was added. | Treating malformed IDs as ordinary misses, coercing values, scanning messages, or matching floats/booleans as integer IDs rejects this local completion claim. | Private-message ID search preflight | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | Matching non-boolean integer search keys still return the stored `PrivateMessage`. | Existing `test_find_existing` passed after validation was added. | Changing returned message identity, rejecting valid integer IDs, or comparing unrelated fields rejects this local completion claim. | Private-message collection lookup | `tests/unit/test_private_message.py` |
| R3 | Missing non-boolean integer search keys still return `None`. | Existing `test_find_not_existing` passed after validation was added. | Raising for a valid but absent integer ID or changing not-found behavior rejects this local completion claim. | Private-message collection lookup | `tests/unit/test_private_message.py` |
| R4 | Adjacent private-message behavior remains green. | `tests/unit/test_private_message.py` passed 63 tests, private-message plus client-accessor tests passed 87 tests, and full unit tests passed 1098 tests. | Regressing direct detail acquisition, inbox acquisition, sent-box acquisition, duplicate handling, empty direct reads, parser diagnostics, response diagnostics, client private-message accessors, or message sending rejects this local completion claim. | Private-message workflow | affected private-message and client tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw private-message bodies, private comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, private-message tests passed, client-adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `826ae5f fix(private_message): validate message search ids`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_find_rejects_non_integer_ids` failed 4 parameterized cases before the fix: malformed IDs did not raise, and comparison was reachable for every malformed value.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_find_rejects_non_integer_ids` passed 4 tests after adding ID search preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_private_message.py` passed 63 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_private_message.py tests/unit/test_client.py` passed 87 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1098 tests.
- `.venv/bin/ruff check src/wikidot/module/private_message.py tests/unit/test_private_message.py` passed.
- `.venv/bin/ruff format src/wikidot/module/private_message.py tests/unit/test_private_message.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("1")`, and `collection.find(1.0)` raise `ValueError("id must be an integer")`.
- A well-formed integer ID matching an existing private message still returns that message.
- A well-formed integer ID that is absent from the collection still returns `None`.
- Existing direct private-message acquisition, inbox/sent-box acquisition, parser diagnostics, response diagnostics, duplicate handling, empty direct reads, client private-message accessors, and private-message sending behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message content, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `True` tightens behavior for values that could previously compare equal to integer search keys. Mitigation: `bool` is not a meaningful private-message ID, and accepting it can hide caller payload bugs.
- Risk: Rejecting float or string search keys can expose upstream caller bugs. Mitigation: the documented API type is an integer; callers loading IDs from JSON, CLI flags, spreadsheets, or generated ledgers should normalize to non-boolean integers before calling `find(...)`.
- Risk: Diagnostics could expose private message context. Mitigation: the new error message contains only the input-field name and expected type, not message subjects, message bodies, account names, or site details.

## Dependencies

- Existing `PrivateMessageCollection` storage and iteration semantics remain authoritative for valid integer search keys.
- Existing direct private-message acquisition and inbox/sent-box acquisition code remains unchanged.
- Existing private-message parser diagnostics remain unchanged.
- The validation is local to `src/wikidot/module/private_message.py` and does not affect direct message acquisition, client private-message accessors, message sending, user parsing, forum behavior, page behavior, site search, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered private-message search-ID validation path.

## Upstream-Safe Motivation

Private-message lookup is often fed by generated inbox/sent-box inventories, moderation ledgers, migration scripts, archival indexes, or cached message snapshots. Since `find(...)` compares supplied values against stored message IDs, malformed search keys should fail deterministically before collection scanning rather than producing misleading misses or accidentally matching float values to integer message IDs.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established private-message data as a practical workflow through list acquisition, direct detail acquisition, retry behavior, duplicate fetch reduction, parser diagnostics, response-body diagnostics, row-scoping, text fidelity, timestamp/user diagnostics, empty direct reads, and client private-message accessors.
- Existing private-message drafts covered fetching, parsing, response diagnostics, cached/direct acquisition, caller-provided acquisition IDs, message send inputs, and parsed message fields; they did not validate caller-provided search keys to `PrivateMessageCollection.find(id=...)`.
- This slice only validates `PrivateMessageCollection` search-ID inputs. It does not change direct private-message acquisition, inbox/sent-box acquisition, parser field extraction, cached or duplicate handling, empty direct reads, client accessors, private-message sending, forum behavior, page behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw private-message bodies, raw rendered private-message content, comments from private messages, source text from real sites, private forum content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search IDs instead of coercing them. Callers that load private-message search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into non-boolean integers before calling `PrivateMessageCollection.find(...)`.
