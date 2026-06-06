# PR Draft: Clean Broad Pyright Test Typing

## Summary

The repository’s full `uv run pyright src tests` gate was repeatedly failing with 44 errors after otherwise-green local slices. The failures were confined to tests that intentionally pass malformed values across typed public boundaries, plus one public typing mismatch where `SearchPagesQuery` documented and implemented `None` for query fields but `SearchPagesQueryParams` did not type those fields as nullable.

This change makes the full pyright gate usable again. `SearchPagesQueryParams.tags` and `SearchPagesQueryParams.limit` now match the documented runtime behavior by allowing `None`. Tests that deliberately pass invalid values now mark those values as `Any`, and `RequestUtil` success tests narrow `httpx.Response | Exception` before asserting response status codes.

## Outcome

`uv run pyright src tests` now passes with 0 errors, 0 warnings, and 0 informations, while the malformed-input tests continue to exercise runtime validation paths.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream contributors who rely on pyright, editor type checking, or typed tests as part of local development. It is also useful for maintainers reviewing later validation slices because broad pyright failures no longer mask new type regressions.

## Current Evidence

Recent local validation slices repeatedly passed focused tests, full unit tests, ruff, format, mypy, target pyright, and whitespace checks while the broad `uv run pyright src tests` command still failed with the same 44 full-tree test typing errors. Those residual errors were not source behavior failures, but they made broad pyright unusable as a completion gate.

The fresh RED baseline for this slice showed the 44 errors were confined to `tests/unit/test_amc_client.py`, `tests/unit/test_requestutil.py`, `tests/unit/test_search_pages_query.py`, and `tests/unit/test_site.py`.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of the earlier validation slices. Those slices hardened runtime parsing, constructor, accessor, action, and collection behavior. This slice fixes the static typing surface around already-existing malformed-input tests and corrects `SearchPagesQueryParams` typing for documented `None` behavior.

No upstream issue was filed from this local workspace.

## Changes

- Update `SearchPagesQueryParams.tags` from `str | list[str]` to `str | list[str] | None`.
- Update `SearchPagesQueryParams.limit` from `int` to `int | None`.
- Align the `SearchPagesQueryParams` docstring for `tags` and `limit`.
- Add explicit `Any` values in tests that intentionally pass malformed arguments to typed public APIs.
- Add a `_assert_response(...)` helper in `tests/unit/test_requestutil.py` to narrow `httpx.Response | Exception` before checking `status_code`.

## Type Of Change

- Public type contract correction
- Test typing maintenance
- Static-analysis gate cleanup

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SearchPagesQueryParams` must type documented `tags=None` and `limit=None` calls as valid. |
| R2 | Tests that intentionally pass malformed cookie, query, site, or request arguments must remain runtime validation tests without causing pyright call-site errors. |
| R3 | `RequestUtil` success tests must narrow response results before accessing `status_code`. |
| R4 | The touched tests must continue to pass and still cover the same malformed-input behavior. |
| R5 | The final tree must pass full pyright, ruff, format, mypy, full unit tests, and whitespace checks before the slice is considered locally complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `SearchPagesQuery(tags=None, limit=None)` remains valid at runtime and type-checks through the public params contract. | Targeted pyright and full pyright passed after `SearchPagesQueryParams` was updated. | Hiding valid `None` calls behind `Any` instead of correcting the source type contract rejects this local completion claim. | Page search query typing | `src/wikidot/module/page.py`, `tests/unit/test_search_pages_query.py` |
| R2 | Invalid test inputs are explicitly typed as intentional boundary crossings. | Targeted pyright over the four reported test files passed with 0 errors. | Removing malformed-input tests or weakening production signatures to accept invalid types rejects this local completion claim. | Test validation boundaries | `tests/unit/test_amc_client.py`, `tests/unit/test_search_pages_query.py`, `tests/unit/test_site.py` |
| R3 | Response status assertions happen only after a runtime response assertion. | `tests/unit/test_requestutil.py` and full pyright passed. | Accessing `status_code` directly on `httpx.Response | Exception` rejects this local completion claim. | RequestUtil tests | `tests/unit/test_requestutil.py` |
| R4 | Touched tests keep passing. | `.venv/bin/python -m pytest -q tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_search_pages_query.py tests/unit/test_site.py` passed 472 tests. | Any touched test regression rejects this local completion claim. | Unit tests | `tests/unit` |
| R5 | Full repository gates pass. | Full unit, full pyright, ruff, format, mypy, and whitespace checks passed. | Any failed required gate or hidden broad-pyright limitation rejects this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `52a55cf test: clean broad pyright typing`.

- RED: `uv run pyright src tests` failed with 44 errors before the fix, all confined to `tests/unit/test_amc_client.py`, `tests/unit/test_requestutil.py`, `tests/unit/test_search_pages_query.py`, and `tests/unit/test_site.py`.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_search_pages_query.py tests/unit/test_site.py` passed with 0 errors, 0 warnings, and 0 informations.
- `.venv/bin/python -m pytest -q tests/unit/test_amc_client.py tests/unit/test_requestutil.py tests/unit/test_search_pages_query.py tests/unit/test_site.py` passed 472 tests.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `.venv/bin/python -m pytest -q tests/unit` passed 2156 tests.
- `git diff --check` passed.

## Acceptance Criteria

- Full `uv run pyright src tests` is green.
- `SearchPagesQuery(tags=None, limit=None).as_dict()` still excludes `tags` and `limit`.
- Invalid query parameters, invalid pagination values, invalid cookie names, invalid site method arguments, and malformed request client tests remain present and pass.
- `RequestUtil` response status assertions narrow the response type before accessing `status_code`.
- This slice does not add live Wikidot calls, upstream Issues, upstream PRs, pushes, credential handling, runtime compatibility shims, or behavior changes outside the documented type contract correction.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: `Any` annotations could hide real source typing bugs. Mitigation: use `Any` only where a test deliberately crosses the typed API boundary to exercise runtime validation.
- Risk: Fixing tests only could leave a source type contract mismatch in place. Mitigation: correct `SearchPagesQueryParams.tags` and `limit` directly because the class already documents and implements `None` for those fields.
- Risk: Response narrowing could reduce assertion coverage. Mitigation: `_assert_response(...)` asserts the runtime response type before returning the narrowed value.

## Dependencies

- `RequestUtil.request(...)` retains its `list[httpx.Response | Exception]` return type.
- `SearchPagesQuery` continues to exclude `None` values from `as_dict()`.
- The invalid-input tests remain intentionally dynamic at the call boundary.

## Open Questions

None for this local slice. Future work can separately evaluate whether other `SearchPagesQueryParams` fields should allow explicit `None` in the public type contract, because this slice only corrects the fields already covered by existing tests and documented optional behavior.

## Upstream-Safe Motivation

A full-repo static type gate is useful only when existing intentional negative tests do not produce unrelated noise. This change keeps those tests intact while making broad pyright failures meaningful for future validation work.

## Local Evidence

- Multiple previous local slices reported the same broad pyright limitation after their focused gates passed.
- The fresh baseline showed a bounded, test-only typing failure set plus the `SearchPagesQueryParams` optional-field mismatch.
- This slice avoids weakening production runtime validation, does not alter network behavior, and does not expose sensitive data.
