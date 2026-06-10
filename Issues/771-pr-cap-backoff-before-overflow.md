# PR Draft: Cap Exponential Backoff Before Overflow Escapes

## Summary

`wikidot.util.http.calculate_backoff(...)` and the raw Ajax Module Connector `_calculate_backoff(...)` both clamp retry sleeps to `max_backoff`, but they computed `backoff_factor ** (retry_count - 1)` before the clamp. Very large finite retry counts or factors could therefore raise `OverflowError` before the existing maximum-backoff cap was applied.

This change keeps the existing direct arithmetic path for ordinary finite values, including the existing jitter behavior when a finite computed backoff exceeds `max_backoff`. Only when Python raises `OverflowError` during exponentiation does the shared helper fall back to log-space calculation. If the mathematical value reaches or exceeds the cap, callers receive `max_backoff`; if the exponent alone overflows but a tiny base interval keeps the final value below the cap, callers receive the finite jittered backoff. The raw AMC helper now delegates to the shared HTTP helper so both retry surfaces use one canonical calculation.

## Outcome

Retry backoff calculation no longer leaks `OverflowError` for huge finite retry controls when a deterministic capped or finite backoff can be produced. Shared HTTP helpers and raw AMC retry handling now agree on the same overflow-safe calculation.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using retry-aware HTTP helpers, raw AMC requests, direct URL reads, site probing, QuickModule lookup, auth login, publishing, migration jobs, archival workflows, generated audits, or tests that load retry controls from Python objects, generated structures, JSON/YAML adapters, CLI parsing, spreadsheets, or fixtures.

## Current Evidence

Local rollout-backed drafts repeatedly identify retry-aware request behavior as practical infrastructure beneath browser-free Wikidot automation. Existing drafts already hardened retry controls for ordinary malformed values, boolean confusion, and non-finite floats.

This slice is not a duplicate of [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md). Issue 391 validates ordinary low-level HTTP retry numeric controls before request execution and before jitter calculation; it does not cover huge finite exponent overflow after validation.

This slice is not a duplicate of [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md). Issue 392 validates raw AMC numeric controls and its local backoff helper for ordinary malformed values; it does not make the raw AMC backoff calculation overflow-safe.

This slice is not a duplicate of [731-pr-validate-finite-http-numeric-controls.md](731-pr-validate-finite-http-numeric-controls.md) or [732-pr-validate-finite-amc-and-requestutil-numeric-controls.md](732-pr-validate-finite-amc-and-requestutil-numeric-controls.md). Those issues reject `NaN` and infinities; this issue covers finite values that pass validation but overflow during exponentiation.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [391-pr-validate-http-retry-numeric-controls.md](391-pr-validate-http-retry-numeric-controls.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [731-pr-validate-finite-http-numeric-controls.md](731-pr-validate-finite-http-numeric-controls.md), and [732-pr-validate-finite-amc-and-requestutil-numeric-controls.md](732-pr-validate-finite-amc-and-requestutil-numeric-controls.md).

## Changes

- Add an overflow-safe exponential backoff helper under `wikidot.util.http`.
- Preserve the original direct arithmetic path when exponentiation succeeds.
- Fall back to log-space calculation when exponentiation raises `OverflowError`.
- Return `max_backoff` when the mathematical overflow fallback reaches the cap.
- Preserve below-cap finite values when only the exponent term overflows but a tiny base interval keeps the product below `max_backoff`.
- Route raw AMC `_calculate_backoff(...)` through the shared HTTP helper.
- Add regression tests for capped huge finite backoff values and tiny-base below-cap overflow cases.

## Type Of Change

- Retry-control correctness
- Overflow handling
- Shared helper consolidation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `calculate_backoff(1025, 1.0, 2.0, 60.0)` must return `60.0` instead of raising `OverflowError`. |
| R2 | Raw AMC `_calculate_backoff(1025, 1.0, 2.0, 60.0)` must return `60.0` instead of raising `OverflowError`. |
| R3 | If exponentiation overflows but the mathematical product remains below `max_backoff`, the shared helper must return the finite jittered value rather than prematurely capping. |
| R4 | Ordinary finite capped values must preserve the existing jitter path before clamping. |
| R5 | Existing malformed-value, non-finite-value, zero-control, and normal retry behavior must remain unchanged. |
| R6 | Adjacent raw AMC, auth, QuickModule, Site, and RequestUtil callers must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | RED/GREEN, affected retry tests, adjacent retry-caller tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Shared HTTP backoff caps huge finite growth at `max_backoff`. | The first focused RED failed with `OverflowError`; focused GREEN passed after overflow fallback. | Raising `OverflowError`, returning infinity, or returning an uncapped huge value rejects this local completion claim. | Shared HTTP retry helper | `src/wikidot/util/http.py`, `tests/unit/test_http.py` |
| R2 | Raw AMC backoff uses the same capped result. | The first focused RED failed with `OverflowError`; focused GREEN passed after raw AMC delegated to the shared helper. | Keeping a duplicate raw AMC exponentiation path or raising `OverflowError` rejects this local completion claim. | Raw AMC retry helper | `src/wikidot/connector/ajax.py`, `tests/unit/test_ajax.py` |
| R3 | Tiny-base below-cap overflow returns a finite jittered value. | A second focused RED failed for `calculate_backoff(1025, 1e-308, 2.0, 60.0)`; focused GREEN passed after log-space fallback computed the finite product. | Returning `60.0`, returning infinity, or raising `OverflowError` rejects this local completion claim. | Shared HTTP retry helper | `tests/unit/test_http.py` |
| R4 | Ordinary finite capped values keep the existing jitter path. | A follow-up compatibility commit restored the finite capped path so only non-finite fallback values bypass jitter; full retry tests remained green. | Skipping jitter for normal finite capped values rejects this local completion claim. | Shared HTTP retry compatibility | `src/wikidot/util/http.py` |
| R5 | Existing retry validation and normal behavior remain stable. | Affected HTTP/Ajax suites passed 211 tests and full unit passed 3780 tests. | Changing validation diagnostics, zero retry controls, first/second/third retry ranges, finite caps, status handling, or request behavior rejects this local completion claim. | Retry behavior | affected and full unit tests |
| R6 | Adjacent retry callers remain compatible. | AMC/Auth/QuickModule/Site/RequestUtil tests passed 917 tests. | Regressing raw AMC requests, auth login retry settings, QuickModule lookup, Site probing/publishing, or direct URL request retries rejects this local completion claim. | Higher-level retry callers | adjacent unit suites |
| R7 | No live site state or private material is needed. | All regressions use unit-level synthetic numeric inputs and local mocks. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | RED/GREEN, affected tests, adjacent tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commits `f54cbcf fix(http): cap backoff after overflow` and `a496a64 fix(http): preserve capped backoff jitter`.

- RED: `uv run pytest tests/unit/test_http.py::TestCalculateBackoff::test_caps_large_exponential_backoff_before_overflow tests/unit/test_ajax.py::TestCalculateBackoff::test_caps_large_exponential_backoff_before_overflow -q --tb=short` failed before the fix with `OverflowError` in both helpers.
- RED follow-up: `uv run pytest tests/unit/test_http.py::TestCalculateBackoff::test_large_exponential_backoff_preserves_tiny_base_below_cap -q --tb=short` failed before the log-space fallback with `OverflowError`.
- GREEN focused: `uv run pytest tests/unit/test_http.py::TestCalculateBackoff tests/unit/test_ajax.py::TestCalculateBackoff -q --tb=short` passed 58 tests.
- `uv run pytest tests/unit/test_http.py tests/unit/test_ajax.py -q --tb=short` passed 211 tests.
- `uv run pytest tests/unit/test_amc_client.py tests/unit/test_auth.py tests/unit/test_quick_module.py tests/unit/test_site.py tests/unit/test_requestutil.py -q --tb=short` passed 917 tests.
- `uv run pytest tests/unit -q --tb=short` passed 3780 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no blocking change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Evidence reported CLI `0.5.0`, branch `roku-local-codex-goal`, commit `d89ca91`, `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `calculate_backoff(1025, 1.0, 2.0, 60.0)` returns `60.0`.
- Raw AMC `_calculate_backoff(1025, 1.0, 2.0, 60.0)` returns `60.0`.
- `calculate_backoff(1025, 1e-308, 2.0, 60.0)` returns a finite value in the expected jitter range below `60.0`.
- Ordinary finite capped values still follow the existing jitter calculation before `min(..., max_backoff)` clamps the result.
- Existing validation messages and normal retry behavior remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commits.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Log-space fallback could subtly change ordinary retry behavior. Mitigation: ordinary successful exponentiation still uses the original direct arithmetic path, and the compatibility follow-up preserves finite capped jitter behavior.
- Risk: Returning a capped value for huge retry counts hides a caller configuration bug. Mitigation: these values are already valid finite positive controls; once accepted, `max_backoff` is the documented cap for retry sleeps.
- Risk: Very tiny base intervals with huge exponents could be incorrectly capped. Mitigation: the below-cap regression verifies that the log-space fallback returns the finite product with jitter instead of blindly returning `max_backoff`.
- Risk: Raw AMC and shared HTTP helpers could drift again. Mitigation: raw AMC `_calculate_backoff(...)` now delegates to `wikidot.util.http.calculate_backoff(...)` while keeping the private wrapper available.

## Dependencies

- `wikidot.util.http.calculate_backoff(...)` remains the source of truth for shared low-level HTTP backoff.
- Raw AMC retry handling keeps its private `_calculate_backoff(...)` wrapper but delegates calculation to the shared helper.
- Existing retry callers, request setup, status handling, response parsing, and live Wikidot behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-shape validation, result ergonomics, action/read boundaries, or measured complexity candidates outside this now-covered retry backoff overflow handling.

## Upstream-Safe Motivation

Retry helpers already expose `max_backoff` as the cap for retry sleeps. Huge finite retry controls should not escape as `OverflowError` before the cap can apply, and raw AMC should not maintain a separate exponentiation path that can drift from the shared HTTP retry helper.

## Local Evidence, Not For Upstream Paste

- The focused RED tests demonstrated prior behavior: both shared HTTP and raw AMC backoff helpers raised `OverflowError` before `max_backoff` could clamp huge finite exponential growth.
- Existing local drafts covered ordinary retry numeric validation, raw AMC numeric validation, and non-finite numeric controls; they did not cover finite exponent overflow after validation.
- This slice only changes retry backoff calculation and raw AMC delegation. It does not change request URLs, headers, form data, response parsing, retry classification, status handling, auth behavior, publish behavior, RequestUtil batching, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

This is a retry helper correctness fix. It preserves normal finite behavior while preventing Python float exponent overflow from bypassing the existing `max_backoff` contract.
