# PR Draft: Recursively Mask Sensitive AMC Log Data

## Summary

The Ajax module already masks sensitive request fields before writing retry and error logs, but the helper only handled top-level keys. If a caller passed nested AMC request data containing sensitive keys such as `password`, `login`, `WIKIDOT_SESSION_ID`, or `wikidot_token7`, the existing helper could leave those values visible in diagnostic logs.

The fix makes `_mask_sensitive_data(...)` recursively copy dictionaries and lists while masking the same sensitive key set at any nesting level. It preserves the current top-level behavior and continues not to mutate caller-owned request bodies.

## Related Issue

Drafted from the practical AMC and browser-free publishing evidence in [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), plus the retry/logging hardening area covered by [006-pr-retry-batched-source-fetches.md](006-pr-retry-batched-source-fetches.md), [010-pr-retry-batched-file-fetches.md](010-pr-retry-batched-file-fetches.md), [015-pr-retry-revision-source-html-fetches.md](015-pr-retry-revision-source-html-fetches.md), and [016-pr-retry-listpages-pagination.md](016-pr-retry-listpages-pagination.md). No upstream issue filed yet.

## Changes

- Make `_mask_sensitive_data(...)` recursively handle nested dictionaries.
- Make `_mask_sensitive_data(...)` recursively handle lists that contain dictionaries or other nested values.
- Preserve non-sensitive data.
- Preserve the existing sensitive key set: `password`, `login`, `WIKIDOT_SESSION_ID`, and `wikidot_token7`.
- Preserve caller-owned input data by returning a masked copy.
- Add a focused unit test for nested sensitive fields and original-body immutability.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Security/privacy hardening
- [x] Test addition/modification
- [ ] CI/CD or build related

## Testing

Local implementation commit: `070e858 fix(ajax): recursively mask sensitive log data`

- [x] `uv run --extra test pytest tests/unit/test_ajax.py::TestMaskSensitiveData::test_masks_nested_sensitive_data_without_mutating_original -q` failed before the fix because nested sensitive values were still visible and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_ajax.py tests/unit/test_amc_client.py -q` passed with 44 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 556 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` inspected current complexity leads.

## Acceptance Criteria

- Top-level sensitive fields remain masked.
- Nested sensitive fields inside dictionaries are masked.
- Nested sensitive fields inside lists are masked.
- Non-sensitive fields are preserved.
- The original request body is not mutated.
- Existing AMC retry, status-code, non-JSON, empty-response, and request-body immutability tests continue to pass.

## Upstream-Safe Motivation

wikidot.py uses retry and error logs to diagnose unreliable AMC requests. Those logs should be useful without risking accidental disclosure of credentials or tokens when callers pass structured request data. Recursive masking is a small hardening change that preserves current behavior while making diagnostics safer.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence repeatedly used wikidot.py's AMC path for browser-free page publishing, source fetching, and page metadata workflows.
- Several local retry improvements increased the importance of safe diagnostic logs because failed AMC requests can now be retried or surfaced with more context.
- Local operational rules prohibit writing secrets, auth JSON, tokens, cookies, or raw private payloads into reports or packets; this helper hardening supports the same privacy boundary inside library logs.

## Additional Notes

This slice does not mask arbitrary content fields such as page source text. It only extends the existing explicit sensitive-key policy to nested dictionaries and lists.
