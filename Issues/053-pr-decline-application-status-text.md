# PR Draft: Spell Decline Application Status Text Correctly

## Summary

`SiteApplication.decline()` processes a pending join application through the same `_process(...)` helper as `accept()`. The helper built the applicant notification text with `f"{action}ed"`, which produced the misspelled decline message `your application has been declineed`.

The fix keeps the existing application action payload, `type` field, login checks, and exception mapping, but maps the two supported actions to explicit status words: `accepted` and `declined`.

## Related Issue

Complements the pending-application management work in [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md). No upstream issue filed yet.

## Changes

- Map `accept` to `accepted` and `decline` to `declined` before constructing the application notification text.
- Preserve the existing `ManageSiteMembershipAction`, `acceptApplication` event, `type` field, and `user_id` payload.
- Add a focused regression assertion for the decline notification text.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [ ] Security/privacy hardening
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification |
| --- | --- | --- |
| R1: Decline notifications use the correct English status word | `SiteApplication.decline()` sends `text="your application has been declined"` | `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_decline_success -q` |
| R2: Application action semantics are unchanged | Decline still sends `type="decline"` through the existing action payload | `tests/unit/test_site_application.py::TestSiteApplicationProcess::test_decline_success` |
| R3: Existing application list and process behavior is preserved | Full `test_site_application.py` and full unit suite pass | Commands listed below |

## Testing

Local implementation commit: `d081ef5 fix(site_application): spell decline notification status`

- [x] `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationProcess::test_decline_success -q` failed before the fix because the payload text was `your application has been declineed`, then passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_site_application.py -q` passed with 17 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 607 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- `SiteApplication.accept()` still sends an accepted application payload.
- `SiteApplication.decline()` sends a decline payload with `type="decline"`.
- `SiteApplication.decline()` sends `text="your application has been declined"`.
- Invalid action strings still raise `ValueError`.
- Existing application list parsing, retry behavior, login checks, and not-found mapping remain unchanged.

## Upstream-Safe Motivation

Join-application processing is an administrative user-facing action. The applicant notification text should not contain a spelling error, and the fix should be narrow enough to avoid changing Wikidot action semantics.

## Local Evidence, Not For Upstream Paste

- The local application-list draft [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md) preserved `accept()` and `decline()` mutation behavior while hardening the read side. Reviewing that action boundary exposed this typo in the write payload.
- The test fixture for pending applications includes both accept and decline actions, so application processing is a real exposed workflow rather than dead code.

## Additional Notes

This slice does not retry application mutation actions, rename the Wikidot `acceptApplication` event, or alter exception mapping. It only fixes the status word inserted into the existing notification text.
