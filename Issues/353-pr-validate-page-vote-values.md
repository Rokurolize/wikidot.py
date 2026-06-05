# PR Draft: Validate Page Vote Values Before Requests

## Summary

`Page.vote(value=...)` documents the vote value as integer `1` or `-1`, but the preflight check used membership equality against `(1, -1)`. In Python, `True == 1`, `1.0 == 1`, and `-1.0 == -1`, so malformed boolean or float values could pass validation, reach the login check, and be sent as the rating action `points` payload.

This change validates the public vote argument as an actual non-boolean integer equal to `1` or `-1` before login checks, `RateAction` request construction, AMC submission, rating action status parsing, local rating mutation, or vote-cache invalidation. Invalid values continue to raise `ValueError("Vote value must be 1 or -1")`.

## Outcome

Page voting callers now get deterministic preflight rejection for malformed bool/float vote values instead of partial write-side progress or non-integer rating payloads.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page voting, rating audits, moderation tooling, cleanup scripts, or publish-adjacent workflows that keep local `Page.rating` and `Page.votes` state coherent after rating actions.

## Current Evidence

Local rollout evidence repeatedly treats page voting and page rating data as practical read/write surfaces. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), and [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md) establish retry-aware vote reads, contextual vote parser errors, returned rating diagnostics, cache invalidation after successful mutations, and rating action status validation. Those slices did not cover malformed public `Page.vote(value=...)` inputs that Python equality treats as `1` or `-1`.

Adjacent input-boundary drafts [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [349-pr-validate-page-source-inputs.md](349-pr-validate-page-source-inputs.md), [350-pr-validate-page-text-inputs.md](350-pr-validate-page-text-inputs.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), and [352-pr-validate-page-rename-fullname-input.md](352-pr-validate-page-rename-fullname-input.md) establish the current local pattern: documented page-write inputs should fail before login checks, request construction, remote writes, response parsing, result creation, or local cache mutation.

## Related Issue

Builds directly on [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), and [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small `Page.vote(...)` value validator for documented vote values.
- Reject `bool` values even though `bool` is an `int` subclass.
- Reject float values such as `1.0` and `-1.0` instead of accepting equality with `1` and `-1`.
- Keep the existing `ValueError("Vote value must be 1 or -1")` message for malformed values.
- Run validation before login checks, AMC requests, action status handling, local rating updates, or vote-cache invalidation.
- Preserve successful positive and negative integer votes, malformed action-response diagnostics, login enforcement, returned rating updates, and successful vote-cache invalidation.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page rating write safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.vote(True)` must raise `ValueError("Vote value must be 1 or -1")` before login checks, AMC requests, rating response parsing, local rating mutation, or vote-cache invalidation. |
| R2 | `Page.vote(1.0)` and `Page.vote(-1.0)` must raise the same `ValueError` before write-side progress even though they compare equal to valid integer values. |
| R3 | Valid integer `Page.vote(1)` and `Page.vote(-1)` behavior must remain unchanged, including request construction, returned rating parsing, local rating updates, and vote-cache invalidation after successful action responses. |
| R4 | Existing invalid value `Page.vote(0)`, login-required behavior, malformed `points` diagnostics, missing action-status diagnostics, and `Page.cancel_vote()` behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page write tests, adjacent page/vote/site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Boolean vote values fail at the public input boundary. | `TestPageWriteMethods.test_vote_rejects_non_integer_vote_values_before_request[True]` failed RED before the fix because `True` reached a successful mocked rating response, then passed GREEN after the validator was added. | Calling login, sending `RateAction`, updating `rating`, clearing `_votes`, leaking downstream status errors, or treating `True` as `1` rejects this local completion claim. | Page vote preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Float vote values fail at the public input boundary. | The same parameterized regression covers `1.0` and `-1.0`; both failed RED before the fix with `DID NOT RAISE`, then passed GREEN after the validator was added. | Accepting floats, coercing floats to integers, sending float `points`, or mutating local state rejects this local completion claim. | Page vote preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Valid positive and negative integer vote paths remain unchanged. | `TestPageWriteMethods.test_vote_positive` and `TestPageWriteMethods.test_vote_negative` passed after the fix. | Changing valid request payloads, returned ratings, local `rating` assignment, or successful `_votes` invalidation rejects this local completion claim. | Page rating mutation | `tests/unit/test_page.py` |
| R4 | Existing adjacent vote behavior remains unchanged. | `TestPageWriteMethods` passed 45 tests after the fix. | Regressing invalid `0` handling, login checks, missing `points`, malformed action status, cancel-vote, rename, metadata, or other page write behavior rejects this local completion claim. | Page write methods | `tests/unit/test_page.py` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw action responses, or private page content rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, `TestPageWriteMethods` passed, adjacent page/vote/site tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `0122ae4 fix(page): validate vote values`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_rejects_non_integer_vote_values_before_request -q` failed 3 parameterized cases before the fix because `True`, `1.0`, and `-1.0` were accepted and no `ValueError` was raised.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_rejects_non_integer_vote_values_before_request tests/unit/test_page.py::TestPageWriteMethods::test_vote_invalid_value_raises tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_vote_negative -q` passed 6 tests after adding vote-value preflight.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 45 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 295 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run --extra test pytest tests/unit -q` passed 954 tests.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `page.vote(True)` raises `ValueError("Vote value must be 1 or -1")` before calling `login_check()` or `amc_request(...)`.
- `page.vote(1.0)` and `page.vote(-1.0)` raise the same `ValueError` before calling `login_check()` or `amc_request(...)`.
- Rejected malformed values do not mutate `page.rating` or clear cached votes.
- `page.vote(1)` and `page.vote(-1)` keep the existing successful behavior.
- `page.vote(0)` keeps the existing invalid-value behavior.
- Existing malformed rating action responses and login-required behavior remain unchanged.
- The new test uses unit-level code only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Vote values are small but stateful write inputs. Runtime validation should match the documented `int` contract and reject values that only pass because of Python equality rules. The change is narrow: it rejects malformed bool/float values before side effects and does not change valid integer voting semantics, rating response handling, or live Wikidot request shape for valid calls.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence established page voting as a practical surface through vote-list acquisition, WhoRated parser diagnostics, rating action result parsing, rating action status validation, and vote-cache invalidation after successful mutations.
- Existing rating drafts covered response-side `points` and `status` validation, but not malformed public `Page.vote(value=...)` inputs.
- Adjacent input-boundary drafts covered page source, title/comment, metadata, boolean controls, parent fullnames, and rename fullnames; vote values were the remaining small public page write input whose Python type semantics could bypass the intended guard.
- This slice only validates the `Page.vote(...)` input value. It does not change `Page.cancel_vote()`, WhoRated parsing, returned rating parsing, action status validation, vote-cache invalidation after successful votes, page source/revision/file caches, publish helpers, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw action response bodies, vote data, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them with `int(...)`. Callers that load vote directions from JSON, YAML, CLI flags, spreadsheets, generated structures, or environment variables should parse them into integer `1` or `-1` before calling `Page.vote(...)`.
