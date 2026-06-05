# PR Draft: Report Malformed QuickModule JSON Responses

## Summary

`QuickModule.member_lookup(...)`, `QuickModule.user_lookup(...)`, and `QuickModule.page_lookup(...)` fetch `quickmodule.php` and then parse the HTTP body with `response.json()`. Earlier local slices made QuickModule lookup retry-aware and added contextual diagnostics for decoded response roots, missing response keys, malformed result fields, malformed rows, missing row fields, and malformed user IDs. One earlier response boundary remained before those decoded-shape guards could run: if Wikidot returned a non-JSON QuickModule body, the lookup leaked the raw JSON decode `ValueError` without the QuickModule name or site ID.

This change catches JSON decode failures at `QuickModule._request(...)` and raises `ValueError("QuickModule response JSON is malformed for module: ..., site_id=...")`. The diagnostic intentionally omits the user-supplied lookup query and raw response body.

## Outcome

QuickModule callers now get a stable module/site diagnostic for non-JSON lookup responses before decoded response-shape parsing begins.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using QuickModule for browser-free member, user, or page selection in moderation, membership, publishing, attribution, or migration tooling.

## Current Evidence

Local QuickModule drafts already show this helper is a practical browser-free lookup surface: Issue 048 added transient retry behavior, Issues 313-320 hardened decoded response and row parsing, and site/member/publish workflows use the same user/page lookup capabilities. Those prior slices covered malformed JSON objects after decoding, but not a failed JSON decode itself.

## Related Issue

Builds on [048-pr-retry-quickmodule-lookups.md](048-pr-retry-quickmodule-lookups.md), [313-pr-quickmodule-user-id-context.md](313-pr-quickmodule-user-id-context.md), [314-pr-quickmodule-response-key-context.md](314-pr-quickmodule-response-key-context.md), [315-pr-quickmodule-row-field-context.md](315-pr-quickmodule-row-field-context.md), [318-pr-quickmodule-row-shape-context.md](318-pr-quickmodule-row-shape-context.md), [319-pr-quickmodule-response-field-context.md](319-pr-quickmodule-response-field-context.md), and [320-pr-quickmodule-response-body-context.md](320-pr-quickmodule-response-body-context.md). Those drafts established QuickModule lookup as a practical retry-aware parser surface and covered decoded JSON shapes while leaving non-JSON response decoding as a separate boundary.

No upstream issue was filed from this local workspace.

## Changes

- Wrap `response.json()` failures in `QuickModule._request(...)` with module and site ID context.
- Preserve invalid-module validation, URL encoding, transient retry behavior, site-not-found handling, and decoded response-shape diagnostics.
- Add focused coverage proving the diagnostic omits lookup query text and raw response body text.

## Type Of Change

- Parser-boundary diagnostics fix
- Privacy-preserving error-message improvement
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A non-JSON QuickModule response must fail at the QuickModule request boundary with a contextual `ValueError`. |
| R2 | The malformed JSON diagnostic must identify the QuickModule name and site ID. |
| R3 | The malformed JSON diagnostic must omit lookup query text and raw response body text. |
| R4 | Existing decoded QuickModule response-shape diagnostics, valid lookup behavior, retry behavior, and site-not-found behavior must remain unchanged. |
| R5 | Focused, adjacent, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `QuickModule.member_lookup(...)` raises the contextual malformed-JSON `ValueError` when the HTTP response cannot be decoded as JSON. | `TestQuickModuleRequest.test_request_non_json_response_includes_module_site_context` sets `response.json.side_effect = ValueError("not json")` and calls the public member lookup. | Leaking raw `not json`, returning an empty list, or entering decoded response-shape parsing rejects this local completion claim. | QuickModule request boundary | `tests/unit/test_quick_module.py` |
| R2 | The error names `MemberLookupQModule` and `site_id=123456`. | The focused regression asserts the exact message string. | Omitting module or site ID makes the failure ambiguous and rejects this local completion claim. | QuickModule diagnostics | `src/wikidot/util/quick_module.py` |
| R3 | The error does not include the lookup query or raw response body. | The focused regression asserts both private query text and raw body text are absent. | Including user-supplied lookup text, raw HTTP response body, credentials, cookies, local rollout paths, or private account material rejects this local completion claim. | Diagnostic privacy | `tests/unit/test_quick_module.py` |
| R4 | Existing QuickModule and adjacent helpers remain green. | `tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_requestutil.py` passed 133 tests; full unit passed 914 tests. | Regressing URL encoding, transient retry, invalid-module checks, site-not-found handling, response-root/key/field/row diagnostics, malformed user-ID diagnostics, or site workflows rejects this local completion claim. | QuickModule and adjacent workflows | `tests/unit/test_quick_module.py`, `tests/unit/test_site.py`, `tests/unit/test_requestutil.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit passed 914 tests; ruff, format check, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `bf545d4 fix(quick_module): report malformed JSON responses`.

- RED: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleRequest::test_request_non_json_response_includes_module_site_context -q` failed before the fix because the raw message was `not json`.
- GREEN: `uv run --extra test pytest tests/unit/test_quick_module.py::TestQuickModuleRequest::test_request_non_json_response_includes_module_site_context -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_quick_module.py -q` passed 30 tests.
- `uv run --extra test pytest tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_requestutil.py -q` passed 133 tests.
- `uv run --extra test pytest tests/unit -q` passed 914 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- Non-JSON QuickModule HTTP responses raise `ValueError` with QuickModule name and site ID.
- Valid QuickModule JSON responses continue through the existing decoded response-shape parser.
- `INTERNAL_SERVER_ERROR` site-not-found handling remains unchanged.
- Invalid module name validation remains unchanged and still happens before any HTTP request.
- The malformed-JSON message does not include lookup query text, raw response body, local rollout paths, credentials, cookies, auth JSON, private user/member/page data, or account material.
- No live Wikidot action, upstream Issue, upstream PR, push, raw QuickModule response body, account material, credentials, cookies, auth JSON, or private query data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

QuickModule lookup is useful because it resolves users, members, and pages without browser automation. If the HTTP response is not JSON at all, wikidot.py should report which lookup module and site failed before decoded response-shape checks can run. Keeping query text and raw body text out of the error gives operators actionable context without exposing unnecessary private lookup data.

## Local Evidence, Not For Upstream Paste

- Earlier local QuickModule slices repeatedly selected this helper from practical lookup and site workflow evidence.
- The focused RED failure showed the current non-JSON response path leaking only the raw decode error text.
- This slice only wraps JSON decoding and does not alter decoded response parsing, request URL construction, retry policy, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, real QuickModule response bodies, raw lookup query text, and private user/member/page data out of upstream discussion.

## Additional Notes

This slice intentionally does not add new QuickModule result fields, change `QMCUser` or `QMCPage`, retry JSON decode failures separately, alter response-root validation, or log raw response bodies. It only gives the existing JSON decode boundary the same compact module/site context as the decoded-shape diagnostics.
