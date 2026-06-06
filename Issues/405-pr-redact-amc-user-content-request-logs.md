# PR Draft: Redact AMC User Content Request Logs

## Summary

`AjaxModuleConnectorClient.request(...)` already masked explicit request-side secrets such as passwords, login names, session IDs, Wikidot tokens, and page lock secrets before writing request bodies to diagnostic logs. However, the same logs still preserved user-authored content fields. When an AMC request failed, a page save, forum write, private-message send, category edit, or invitation request could leave fields such as `source`, `body`, `text`, `subject`, `title`, `comment`, `comments`, or `description` in captured logs.

This change extends the existing recursive request-body masker to redact those user-authored content keys while preserving structural routing fields such as `moduleName`, `page_id`, `action`, and other non-content metadata. Request construction, outgoing payloads, retries, response classification, token handling, header validation, numeric controls, request-body validation, and higher-level module behavior are unchanged.

## Outcome

AMC diagnostics keep enough structural context to triage a failing request without retaining page source, private-message bodies, forum text, invitation text, descriptions, comments, or titles from the request payload.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page publishing, source verification, forum edits/replies, forum category maintenance, private messaging, invitations, archival jobs, moderation helpers, migration scripts, or generated AMC request batches.

## Current Evidence

Local rollout-backed drafts established raw AMC request execution and browser-free write workflows as practical surfaces. [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md) and [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md) hardened explicit request-side secret masking, while [404-pr-redact-amc-malformed-response-diagnostics.md](404-pr-redact-amc-malformed-response-diagnostics.md) removed raw malformed response content from terminal diagnostics. Source inspection also shows user-authored request fields in page saves, forum post/thread/category writes, private-message sends, and site invitation requests.

Those prior slices are not duplicates. Issues 029 and 071 explicitly scoped out arbitrary content fields such as page source text, titles, comments, tags, parent names, and meta values. Issue 404 covered raw malformed response content, not request-side authored content fields printed through the existing masked request-body log path.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md), [050-pr-preserve-caller-wikidot-token.md](050-pr-preserve-caller-wikidot-token.md), [071-pr-mask-page-lock-secrets.md](071-pr-mask-page-lock-secrets.md), [401-pr-validate-amc-request-bodies.md](401-pr-validate-amc-request-bodies.md), [402-pr-validate-amc-response-status.md](402-pr-validate-amc-response-status.md), [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md), and [404-pr-redact-amc-malformed-response-diagnostics.md](404-pr-redact-amc-malformed-response-diagnostics.md).

## Changes

- Extend `_mask_sensitive_data(...)` so `source`, `body`, `text`, `subject`, `title`, `comment`, `comments`, and `description` values become `***MASKED***` in log-only request-body representations.
- Preserve recursive masking across nested dictionaries and lists.
- Preserve structural request diagnostics such as `moduleName` and `page_id`.
- Keep outgoing request payloads unchanged; only the diagnostic representation is masked.
- Add a public `AjaxModuleConnectorClient.request(...)` error-log regression proving synthetic user-authored content fields do not appear in captured logs.
- Add a focused helper regression proving nested user-content fields are recursively masked without mutating the original request body.

## Type Of Change

- Privacy/logging improvement
- Raw AMC connector hardening
- Request diagnostic policy update
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | AMC request diagnostic logs must redact user-authored content fields named `source`, `body`, `text`, `subject`, `title`, `comment`, `comments`, and `description`. |
| R2 | The redaction must be recursive for nested dictionaries and lists and must not mutate the caller's original request body. |
| R3 | Structural request fields must remain available in diagnostics so failing requests can still be routed and triaged. |
| R4 | Existing explicit secret masking must remain unchanged for `password`, `login`, `WIKIDOT_SESSION_ID`, `wikidot_token7`, and `lock_secret`. |
| R5 | Request construction, outgoing payloads, retry behavior, response classification, token defaults, explicit token preservation, headers, numeric controls, request-body validation, Site wrapper behavior, RequestUtil behavior, auth behavior, and module write/read behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not expose real page source, private messages, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, AMC/ajax tests, adjacent write-path tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A terminal HTTP error log for an AMC request containing all eight content fields omits every synthetic private value and still includes `***MASKED***`. | `TestAjaxModuleConnectorClientRequest.test_http_error_log_masks_user_content_fields` failed RED because `PRIVATE_AMC_SOURCE_SHOULD_NOT_LEAK` appeared in `caplog.text`, then passed GREEN after the masking policy was extended. | Any raw content-field sentinel in `caplog.text` rejects this local completion claim. | Public raw AMC request error path | `src/wikidot/connector/ajax.py`, `tests/unit/test_amc_client.py` |
| R2 | Nested content fields under dictionaries and lists are masked, and the original request dictionary still contains the original values after masking. | `TestMaskSensitiveData.test_masks_nested_user_content_fields_without_mutating_original` passed after the implementation and covers nested `source`, `body`, `text`, `subject`, `title`, `comment`, `comments`, and `description`. | Mutating the caller body, leaving nested content unmasked, or collapsing list/dict shape rejects this local completion claim. | Request log masking helper | `src/wikidot/connector/ajax.py`, `tests/unit/test_ajax.py` |
| R3 | Structural routing fields remain visible in the public log regression. | The public log regression asserts `moduleName` and `page_id` remain in captured log text. | Masking all request data, hiding routing fields, or removing masked request-body context rejects this local completion claim. | AMC diagnostic usability | `tests/unit/test_amc_client.py` |
| R4 | Existing explicit secret masking and recursive secret behavior remain green. | `tests/unit/test_ajax.py` passed 33 tests and `tests/unit/test_amc_client.py tests/unit/test_ajax.py` passed 145 tests. | Regressing password, login, session ID, token, or lock-secret masking rejects this local completion claim. | Secret masking compatibility | `tests/unit/test_ajax.py` |
| R5 | Existing adjacent behavior remains stable. | Adjacent write/request suites passed 722 tests, and the full unit suite passed 1439 tests. | Regressing request sending, retries, response validation, Site wrapper behavior, RequestUtil, auth, page writes, forum writes, private-message sends, invitations, or parser/read workflows rejects this local completion claim. | wikidot.py request and module workflows | affected unit suites |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic values and mocked HTTP responses only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private site data, or source text from real sites rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED evidence was recorded, focused GREEN passed, AMC/ajax and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0aabffa fix(amc): redact user content from request logs`.

- RED tracer: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_http_error_log_masks_user_content_fields -q` failed before the fix because the captured terminal HTTP error log included `PRIVATE_AMC_SOURCE_SHOULD_NOT_LEAK` and the other synthetic user-content request values.
- GREEN tracer: `uv run pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_http_error_log_masks_user_content_fields -q` passed 1 test.
- Focused recursive helper: `uv run pytest tests/unit/test_ajax.py::TestMaskSensitiveData::test_masks_nested_user_content_fields_without_mutating_original -q` passed 1 test.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_ajax.py -q` passed 145 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_forum_post.py tests/unit/test_forum_thread.py tests/unit/test_forum_category.py tests/unit/test_private_message.py tests/unit/test_requestutil.py tests/unit/test_auth.py -q` passed 722 tests.
- `uv run pytest tests/unit -q` passed 1439 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 81 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files.
- `git diff --check` passed before the code commit.

Not run successfully: `command -v pyright` exited nonzero because no PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- AMC terminal diagnostics for failed requests redact `source`, `body`, `text`, `subject`, `title`, `comment`, `comments`, and `description`.
- The redaction is recursive and does not mutate the request body object supplied by the caller.
- Structural fields such as `moduleName` and `page_id` remain visible in masked diagnostic request bodies.
- Existing explicit secret keys remain masked.
- Outgoing request payloads and all retry/response behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Redacting titles or descriptions could remove useful one-line debugging clues. Mitigation: the log still keeps structural fields such as module/action/page identifiers, while user-authored text stays out of durable diagnostics.
- Risk: The key `body` can be a generic field name. Mitigation: `_mask_sensitive_data(...)` is used for request-body logging, not response parsing, and Wikidot module response `body` values are not passed through this request-log helper.
- Risk: Existing follow-up notes deliberately scoped out arbitrary content masking. Mitigation: this draft records the policy change as a separate follow-up, and the test proves structural fields remain available rather than replacing logs with opaque placeholders.

## Dependencies

- Existing `AjaxModuleConnectorClient.request(...)` remains the source of truth for raw Ajax Module Connector request execution.
- Existing `_mask_sensitive_data(...)` remains the source of truth for request-side diagnostic masking.
- Existing request-body merging remains the source of truth for outgoing payloads and explicit caller `wikidot_token7` preservation.
- Existing Site, RequestUtil, auth, page, forum, and private-message wrappers continue to own higher-level behavior and validation.
- The diagnostic change is local to `src/wikidot/connector/ajax.py` and does not alter URL routing, request body field semantics, retry control validation, module-specific action-status validators, module-specific response-body validators, or live Wikidot behavior.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-body field-type checks, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered AMC request-log content redaction path.

## Upstream-Safe Motivation

Browser-free Wikidot workflows often send page source, forum text, private-message content, invitation text, comments, and titles through the raw AMC connector. When a request fails, logs should help identify the route and operation without retaining user-authored content. Extending the existing recursive masker keeps diagnostics actionable while reducing accidental content retention.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established raw AMC request execution as shared infrastructure for token handling, site wrapper delegation, request utilities, login/session setup, source fetches, browser-free publishing, forum workflows, private messages, invitations, and generated request batches.
- Existing drafts covered recursive explicit-secret masking, caller token preservation, page lock-secret masking, return-exceptions validation, numeric request controls, request-body batch validation, response status validation, response status type validation, and malformed response diagnostic redaction. They did not redact request-side user-authored content fields.
- This slice only changes diagnostic request-body representations. It does not change outgoing request bodies, token defaults, token masking, login credentials, session-cookie validation, logout cleanup, retry control validation, URL routing, RequestUtil behavior, Site wrapper behavior, module-specific action-status diagnostics, module-specific response-body diagnostics, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, page source text from real sites, and private message contents out of upstream discussion.

## Additional Notes

This slice intentionally does not mask `module_body`, `tags`, parent names, meta values, IDs, action names, or routing fields. Those fields remain separate policy decisions because they can be structural diagnostics rather than directly authored prose.
