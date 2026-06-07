# PR Draft: Validate Coroutine Runner Input

## Summary

`run_coroutine(coro)` is the shared bridge that lets synchronous wikidot.py callers execute async request batches even when an event loop is already running. It backs raw AMC request execution and direct URL RequestUtil batches. The helper documents `coro` as a coroutine, but malformed runtime values were previously passed into `asyncio.run_until_complete(...)`. Outside an existing loop, values such as `None`, booleans, integers, lists, dictionaries, and arbitrary objects failed with lower-level `asyncio` `TypeError`. Inside an existing loop, the same invalid values crossed into the helper's worker thread before failing.

This change validates the input at the helper boundary. Non-coroutine values now raise `ValueError("coro must be a coroutine")` before event-loop detection, new loop creation, thread-pool execution, or `asyncio` scheduling. Valid coroutine execution, return-value preservation, exception propagation, existing-loop execution, and async batch callers remain unchanged.

## Outcome

Malformed coroutine-runner inputs now fail deterministically at the wikidot.py helper boundary instead of surfacing lower-level `asyncio` errors or crossing a thread boundary first.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free AMC calls, direct URL batches, generated fixtures, local tests, worker automation, notebooks, FastAPI-like environments, or other contexts where synchronous code may need to run an async request coroutine.

## Current Evidence

Local rollout-backed drafts repeatedly identify async batch execution as practical infrastructure. `AjaxModuleConnectorClient.request(...)` uses `run_coroutine(...)` for raw AMC batches, and `RequestUtil.request(...)` uses it for direct GET/POST URL batches. Existing drafts [138-pr-reuse-requestutil-async-client.md](138-pr-reuse-requestutil-async-client.md), [389-pr-validate-amc-client-return-exceptions-flag.md](389-pr-validate-amc-client-return-exceptions-flag.md), [392-pr-validate-amc-numeric-controls.md](392-pr-validate-amc-numeric-controls.md), [393-pr-validate-requestutil-numeric-controls.md](393-pr-validate-requestutil-numeric-controls.md), [515-pr-validate-amc-config-object.md](515-pr-validate-amc-config-object.md), and [517-pr-validate-requestutil-method-urls.md](517-pr-validate-requestutil-method-urls.md) harden the request inputs and configs around those async batches.

Those prior slices are not duplicates. They validate request method/URL/config/exception/numeric controls before batch execution, but none validates the helper's own `coro` boundary before event-loop or thread handling begins.

No upstream issue was filed from this local workspace.

## Changes

- Add a runtime coroutine check at the start of `run_coroutine(...)`.
- Reject non-coroutine inputs with `ValueError("coro must be a coroutine")`.
- Validate before `asyncio.get_running_loop()`, new event-loop creation, thread-pool dispatch, and `run_until_complete(...)`.
- Add focused unit tests for malformed values outside an event loop.
- Add focused unit tests for malformed values inside an existing event loop.

## Type Of Change

- Input validation
- Async helper boundary hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `run_coroutine(...)` must reject non-coroutine values with `ValueError("coro must be a coroutine")` before creating or using an event loop. |
| R2 | The same validation must apply when `run_coroutine(...)` is called inside an existing event loop, before worker-thread dispatch. |
| R3 | Valid coroutine return values, including scalars, dictionaries, lists, and `None`, must remain unchanged. |
| R4 | Valid coroutine exceptions must still propagate unchanged. |
| R5 | Existing AMC and RequestUtil async batch behavior must remain unchanged. |
| R6 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, async helper tests, adjacent AMC/RequestUtil tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `None`, `True`, `1`, `object()`, `[]`, and `{}` fail with a stable helper-level `ValueError` outside an existing loop. | `TestRunCoroutine.test_rejects_non_coroutine_inputs` failed RED for 6 malformed values with lower-level `asyncio` `TypeError`, then passed GREEN after validation was added. | Creating a new event loop, reaching `run_until_complete(...)`, leaking `asyncio` `TypeError`, or coercing non-coroutines rejects this local completion claim. | Coroutine runner preflight | `src/wikidot/util/async_helper.py`, `tests/unit/test_async_helper.py` |
| R2 | The same malformed values fail before worker-thread dispatch when called from inside an existing loop. | `TestRunCoroutine.test_rejects_non_coroutine_inputs_in_existing_loop` failed RED for 6 malformed values after crossing into the thread path, then passed GREEN after validation was added. | Submitting a worker thread, creating a thread-local loop, or surfacing a thread-propagated `asyncio` error rejects this local completion claim. | Existing-loop bridge preflight | `tests/unit/test_async_helper.py` |
| R3 | Valid return-value preservation remains stable. | Existing async helper tests for scalar, dictionary, list, and `None` return values passed in the full async helper suite. | Changing return values, dropping results, or wrapping results rejects this local completion claim. | Valid coroutine execution | `tests/unit/test_async_helper.py` |
| R4 | Valid coroutine exceptions still propagate unchanged. | Existing async helper exception tests passed in the full async helper suite. | Swallowing, wrapping, or changing exception classes/messages rejects this local completion claim. | Valid coroutine error propagation | `tests/unit/test_async_helper.py` |
| R5 | Existing async batch callers remain green. | Adjacent async helper, AMC client, and RequestUtil tests passed 242 tests, and full unit passed 2357 tests. | Regressing raw AMC async execution, direct URL async execution, retry behavior, exception-returning behavior, or existing-loop execution rejects this local completion claim. | Async batch callers | `tests/unit/test_amc_client.py`, `tests/unit/test_requestutil.py` |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic malformed values and local coroutines; the draft contains no raw credentials, cookies, auth JSON, rollout paths, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, async helper and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d41e38c fix(async): validate coroutine runner input`.

- RED coroutine-runner tests: `uv run pytest tests/unit/test_async_helper.py::TestRunCoroutine::test_rejects_non_coroutine_inputs tests/unit/test_async_helper.py::TestRunCoroutine::test_rejects_non_coroutine_inputs_in_existing_loop -q` failed 12 malformed cases before the fix with lower-level `asyncio` `TypeError`.
- GREEN focused tests: the same focused command passed 12 tests after the coroutine preflight was added.
- `uv run ruff format src/wikidot/util/async_helper.py tests/unit/test_async_helper.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_async_helper.py -q` passed 22 tests.
- `uv run pytest tests/unit/test_async_helper.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py -q` passed 242 tests.
- `uv run ruff check src/wikidot/util/async_helper.py tests/unit/test_async_helper.py` passed.
- `uv run ruff format --check src/wikidot/util/async_helper.py tests/unit/test_async_helper.py` passed with 2 files already formatted.
- `uv run mypy src/wikidot/util/async_helper.py tests/unit/test_async_helper.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/util/async_helper.py tests/unit/test_async_helper.py` passed with 0 errors, 0 warnings, and 0 informations after the validation check was kept inline.
- `uv run pytest tests/unit -q` passed 2357 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `run_coroutine(None)`, `True`, `1`, `object()`, `[]`, and `{}` raise `ValueError("coro must be a coroutine")`.
- The same malformed inputs raise the same validation error when `run_coroutine(...)` is called from inside an existing event loop.
- Malformed values fail before new event-loop creation, thread-pool dispatch, or `asyncio.run_until_complete(...)`.
- Valid simple, awaited, gathered, dictionary, list, and `None`-returning coroutines keep their existing behavior.
- Valid coroutine exceptions keep propagating unchanged.
- Existing AMC and RequestUtil async batch behavior remains green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Risks And Mitigations

- Risk: This tightens behavior for callers passing generic awaitables rather than coroutine objects. Mitigation: the public helper and type signature document `Coroutine`; existing wikidot.py callers pass coroutine objects such as `_execute_requests()`.
- Risk: This could be confused with RequestUtil or AMC request validation. Mitigation: those slices validate request payloads and controls before they create a coroutine; this slice validates the shared runner's own input boundary.
- Risk: Existing-loop behavior is sensitive because the helper uses a separate thread. Mitigation: the regression covers both outside-loop and inside-loop malformed input paths and existing valid inside-loop execution remains green.

## Out Of Scope

Changing the thread-execution strategy, accepting arbitrary awaitables or futures, changing event-loop ownership policy, making async APIs public, changing retry behavior, changing AMC or RequestUtil request construction, altering exception-returning modes, and live Wikidot behavior are outside this slice.

## Why This Matters

`run_coroutine(...)` sits under the batch request machinery that makes browser-free wikidot.py workflows usable from synchronous code, notebooks, and services that already have event loops. A malformed helper input should fail before loop/thread orchestration begins so diagnostics stay local to wikidot.py.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used raw AMC batches and direct URL batches that depend on `run_coroutine(...)`.
- Existing drafts covered request configs, exception flags, direct URL method/URL inputs, raw AMC request bodies, and async client reuse, but did not validate the coroutine runner itself.
- The focused RED failures showed malformed values entering `asyncio.run_until_complete(...)`; in an existing loop they first crossed into the helper's thread path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
