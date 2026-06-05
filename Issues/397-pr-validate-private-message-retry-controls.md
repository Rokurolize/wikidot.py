# PR Draft: Validate Private-Message Retry Controls

## Summary

`PrivateMessageCollection.from_ids(...)`, `PrivateMessageInbox.acquire(...)`, and `PrivateMessageSentBox.acquire(...)` route authenticated dashboard AMC reads through `PrivateMessageCollection._amc_request_with_retry(...)`. That client-scoped retry helper read `client.amc_client.config.retry_batch_size` and `retry_max_retries`, but malformed values were either silently replaced with defaults or accepted through Python's `bool` subclassing `int`.

This change validates `retry_batch_size` as a non-bool positive integer and `retry_max_retries` as a non-bool non-negative integer before any private-message AMC request is issued. Existing missing-attribute defaults, valid zero retry counts, valid positive retry counts, retry behavior, exhausted retry diagnostics, no-message permission mapping, list/detail parsing, inbox/sent wrappers, and send behavior remain unchanged.

## Outcome

Private-message read callers now get deterministic wikidot.py-side validation for malformed retry config instead of accidental bool coercion, silent fallback from malformed strings/floats/`None`, later parser failures, or request work against a malformed batch/retry policy.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free private-message reads for moderation inbox checks, notification verification, local audit ledgers, migration tooling, or generated scripts that may load retry settings from JSON, YAML, CLI flags, spreadsheets, generated structures, environment variables, or mock clients.

## Current Evidence

Local rollout-backed drafts repeatedly identify private-message reads as practical surfaces. [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [073-pr-reuse-private-message-detail-parsing.md](073-pr-reuse-private-message-detail-parsing.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [133-pr-reuse-private-message-list-first-page-body.md](133-pr-reuse-private-message-list-first-page-body.md), [163-pr-private-message-list-row-error-context.md](163-pr-private-message-list-row-error-context.md), [178-pr-private-message-list-fetch-failure-context.md](178-pr-private-message-list-fetch-failure-context.md), [184-pr-private-message-detail-fetch-context.md](184-pr-private-message-detail-fetch-context.md), [188-pr-private-message-detail-parse-context.md](188-pr-private-message-detail-parse-context.md), [206-pr-private-message-detail-response-body-context.md](206-pr-private-message-detail-response-body-context.md), [207-pr-private-message-list-response-body-context.md](207-pr-private-message-list-response-body-context.md), [272-pr-private-message-detail-timestamp-context.md](272-pr-private-message-detail-timestamp-context.md), [273-pr-private-message-detail-subject-body-context.md](273-pr-private-message-detail-subject-body-context.md), [287-pr-private-message-detail-timestamp-value-context.md](287-pr-private-message-detail-timestamp-value-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [321-pr-private-message-response-body-type-context.md](321-pr-private-message-response-body-type-context.md), [355-pr-validate-private-message-send-text-inputs.md](355-pr-validate-private-message-send-text-inputs.md), [360-pr-validate-private-message-send-recipients.md](360-pr-validate-private-message-send-recipients.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), and [381-pr-validate-private-message-find-id.md](381-pr-validate-private-message-find-id.md) show why private-message request setup should fail deterministically before remote work when caller configuration is malformed.

Those prior slices are not duplicates. Issue 037 made private-message reads retry-aware, but did not validate retry config. Issue 361 validates message IDs, not retry controls. Issues 392 and 393 validate raw AMC and RequestUtil numeric controls, not this higher-level client-scoped private-message retry helper. Issue 394 validates `Site.amc_request_with_retry(...)`, and Issue 396 validates the separate first-page ListPages retry helper; neither covers `PrivateMessageCollection._amc_request_with_retry(...)`.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [037-pr-retry-private-message-fetches.md](037-pr-retry-private-message-fetches.md), [054-pr-deduplicate-private-message-detail-fetches.md](054-pr-deduplicate-private-message-detail-fetches.md), [067-pr-deduplicate-direct-private-message-fetches.md](067-pr-deduplicate-direct-private-message-fetches.md), [077-pr-skip-empty-private-message-fetch-batches.md](077-pr-skip-empty-private-message-fetch-batches.md), [361-pr-validate-private-message-message-id-inputs.md](361-pr-validate-private-message-message-id-inputs.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md), and [396-pr-validate-listpages-retry-control.md](396-pr-validate-listpages-retry-control.md).

## Changes

- Validate `retry_batch_size` in `PrivateMessageCollection._amc_request_with_retry(...)` as a non-bool positive integer before private-message AMC request work.
- Validate `retry_max_retries` in the same helper as a non-bool non-negative integer before private-message AMC request work.
- Preserve the existing default values of `50` and `3` when the config object lacks those attributes.
- Preserve valid zero retry counts and valid positive retry counts.
- Preserve private-message detail/list retry behavior, exhausted retry diagnostics, forbidden/no-message mapping, list/detail parser diagnostics, inbox/sent wrappers, client accessors, and send behavior.

## Type Of Change

- Input validation
- Private-message request preflight hardening
- Retry-control boundary clarification
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PrivateMessageCollection.from_ids(...)` must reject malformed `retry_batch_size` values with `ValueError("batch_size must be a positive integer")` before issuing a private-message AMC request. |
| R2 | `PrivateMessageCollection.from_ids(...)` must reject malformed `retry_max_retries` values with `ValueError("max_retries must be a non-negative integer")` before issuing a private-message AMC request. |
| R3 | Missing retry config attributes, valid `retry_batch_size`, valid `retry_max_retries=0`, and positive retry counts must remain accepted. |
| R4 | Existing private-message retry behavior, exhausted retry diagnostics, forbidden/no-message mapping, list/detail parsing, inbox/sent wrappers, client accessors, and send behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private message bodies/subjects, private recipient data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, adjacent private-message/client/AMC/Site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `retry_batch_size=None`, `True`, `False`, `"2"`, `1.5`, `0`, and `-1` fail before private-message AMC request work. | `TestPrivateMessageCollection.test_from_ids_rejects_invalid_retry_batch_size_before_request` passed GREEN for all seven values and asserts `mock_client.amc_client.request.assert_not_called()`. | Issuing the private-message AMC request, accepting booleans or strings, silently defaulting malformed values, accepting non-positive sizes, or raising a later parser/remapping error rejects this local completion claim. | Private-message retry helper | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R2 | `retry_max_retries=None`, `True`, `False`, `"1"`, `-1`, and `1.5` fail before private-message AMC request work. | `TestPrivateMessageCollection.test_from_ids_rejects_invalid_retry_max_retries_before_request` passed GREEN for all six values and asserts `mock_client.amc_client.request.assert_not_called()`. | Issuing the private-message AMC request, accepting booleans or strings, silently defaulting malformed values, accepting negative counts, accepting floats, or raising a later parser/remapping error rejects this local completion claim. | Private-message retry helper | `src/wikidot/module/private_message.py`, `tests/unit/test_private_message.py` |
| R3 | Missing config attributes still use defaults and a valid read can proceed. | `TestPrivateMessageCollection.test_from_ids_uses_retry_defaults_when_config_attrs_are_missing` passed GREEN and returned one parsed message with a single AMC request. | Requiring config attributes that were previously optional, rejecting a config object without those attributes, or changing valid request flow rejects this local completion claim. | Private-message retry defaults | `tests/unit/test_private_message.py` |
| R4 | Valid adjacent behavior remains stable. | `tests/unit/test_private_message.py` plus adjacent client accessor, raw AMC, and Site AMC retry tests passed 185 tests; full unit passed 1393 tests. | Regressing direct detail reads, inbox/sent acquisition, retry exhaustion, no-message mapping, parser diagnostics, client accessors, raw AMC behavior, or Site AMC retry behavior rejects this local completion claim. | Private-message and request workflows | affected unit suites |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic config values, mocks, synthetic IDs, and local assertions. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private message bodies, private message subjects, private recipients, private site data, or raw HTTP bodies rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `095f0ab fix(private_message): validate retry controls`.

- RED tracer: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_invalid_retry_batch_size_before_request` failed 7 tests before the fix. `None`, `True`, `"2"`, and `1.5` reached request/response work and leaked `KeyError: 1` from later response remapping; `False`, `0`, and `-1` raised the old weaker `ValueError("batch_size must be positive, got ...")` shape.
- GREEN tracer: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_invalid_retry_batch_size_before_request` passed 7 tests after adding `retry_batch_size` validation.
- RED tracer: `timeout 8s .venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_invalid_retry_max_retries_before_request` failed 6 tests before the fix. `None`, `True`, `False`, `"1"`, and `1.5` reached request/response work and leaked `KeyError: 1`; `-1` raised the old weaker `ValueError("max_retries must be non-negative, got -1")` shape.
- GREEN tracer: `.venv/bin/python -m pytest -q tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_invalid_retry_batch_size_before_request tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_rejects_invalid_retry_max_retries_before_request tests/unit/test_private_message.py::TestPrivateMessageCollection::test_from_ids_uses_retry_defaults_when_config_attrs_are_missing` passed 14 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_private_message.py tests/unit/test_client.py::TestClientPrivateMessageAccessor tests/unit/test_amc_client.py tests/unit/test_site.py::TestSiteAmcRequest` passed 185 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1393 tests.
- `.venv/bin/ruff check src tests` passed.
- `.venv/bin/ruff format --check src tests` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `pyright src tests` was unavailable because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `PrivateMessageCollection.from_ids(client, [1])` rejects `client.amc_client.config.retry_batch_size=None`, `True`, `False`, `"2"`, `1.5`, `0`, and `-1` with `ValueError("batch_size must be a positive integer")` before issuing an AMC request.
- `PrivateMessageCollection.from_ids(client, [1])` rejects `client.amc_client.config.retry_max_retries=None`, `True`, `False`, `"1"`, `-1`, and `1.5` with `ValueError("max_retries must be a non-negative integer")` before issuing an AMC request.
- A config object without `retry_batch_size` or `retry_max_retries` attributes still uses the existing defaults.
- Valid zero retry counts and positive integer retry counts remain accepted.
- Existing private-message detail/list retry behavior, exhausted retry diagnostics, forbidden/no-message mapping, list/detail parsing, inbox/sent wrappers, client accessors, raw AMC behavior, Site AMC retry behavior, and send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private message bodies/subjects, private recipient data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting booleans tightens behavior for callers that accidentally relied on Python's `bool` subclassing `int`. Mitigation: `True` and `False` are configuration mistakes for batch size or retry count and should not become size one, one retry, or zero retries.
- Risk: Rejecting strings can expose CLI, environment, JSON, YAML, spreadsheet, or generated-structure parsing bugs. Mitigation: textual configuration should parse retry controls into real integers before calling private-message read helpers.
- Risk: Rejecting floats tightens behavior for callers that accidentally used decimal config values. Mitigation: batch sizes and retry counts are discrete integer controls; fractional values cannot be executed meaningfully.
- Risk: This change could be confused with Issue 037. Mitigation: Issue 037 made private-message reads retry-aware; this slice validates the retry controls that now drive that helper.
- Risk: This change could be confused with Issue 361. Mitigation: Issue 361 validates private-message IDs before request construction; this slice validates retry config after valid non-empty ID input and login checks.
- Risk: This change could be confused with Issue 394. Mitigation: Issue 394 validates `Site.amc_request_with_retry(...)`; this slice covers the separate client-scoped helper used by private-message reads.
- Risk: This change could be confused with Issue 396. Mitigation: Issue 396 validates the first-page ListPages retry count; this slice covers private-message detail/list requests.

## Dependencies

- Existing `PrivateMessageCollection._amc_request_with_retry(...)` remains the source of truth for private-message detail/list retry behavior.
- Existing private-message ID validation remains the source of truth for direct message ID preflight.
- Existing raw AMC, RequestUtil, Site AMC retry, and ListPages retry validations remain separate helper boundaries.
- The validation is local to `src/wikidot/module/private_message.py` and does not affect URL construction, response parsing, raw AMC request execution, direct URL RequestUtil execution, site-level AMC retry helper behavior, ListPages request behavior, send behavior, or live Wikidot actions.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered private-message retry-control path.

## Upstream-Safe Motivation

Private-message reads are authenticated dashboard workflows that already use retry-aware AMC batching. Since retry settings determine whether request work starts, how batches are split, and how many times transient failures repeat, malformed `None`, strings, booleans, non-positive batch sizes, negative retry counts, and floats should fail deterministically before private-message AMC request setup.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established private-message reads as practical surfaces through retry-aware list/detail fetching, direct/list deduplication, duplicate parse reuse, empty lookup handling, list first-page body reuse, parser scoping, fetch/parser diagnostics, response-body validation, timestamp/user diagnostics, send validation, message-ID validation, and find-ID validation.
- Existing drafts covered private-message retry behavior, message ID validation, raw AMC numeric controls, RequestUtil numeric controls, Site AMC retry controls, and ListPages retry controls; they did not validate the client-scoped private-message retry helper's config values before request work.
- This slice only validates private-message retry controls. It does not change retry policy, status classification, response parsing, inbox/sent wrappers, private-message send behavior, RequestUtil behavior, raw AMC request behavior, site-level AMC retry behavior, first-page ListPages behavior, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, recipient names from real messages, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private message bodies, private message subjects, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed retry controls instead of coercing them. Callers that load retry values from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should resolve them into real integers before calling private-message read helpers.
