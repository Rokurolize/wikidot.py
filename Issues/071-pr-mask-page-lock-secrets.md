# PR Draft: Mask Page Lock Secrets In AMC Logs

## Summary

`Page.create_or_edit(...)` obtains a Wikidot page edit lock and then sends `lock_secret` in the later `savePage` AMC request. The Ajax retry/error log masker already hides passwords, login names, session IDs, and `wikidot_token7`, but it did not treat page lock secrets as sensitive. A failed `savePage` request could therefore expose the temporary edit-lock secret in diagnostic logs.

This change adds `lock_secret` to the recursive AMC request-body masking policy. The fix keeps existing recursive dictionary/list masking, preserves non-sensitive fields, and still returns a masked copy without mutating caller-owned request bodies.

## Related Issue

Builds on [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), and [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md). No upstream issue was filed from this local workspace.

## Changes

- Add `lock_secret` to `_mask_sensitive_data(...)` sensitive keys.
- Keep top-level and nested masking behavior for `password`, `login`, `WIKIDOT_SESSION_ID`, and `wikidot_token7`.
- Preserve non-sensitive `savePage` fields such as `action`, `event`, `wiki_page`, `title`, `source`, and `comments`.
- Preserve caller-owned request body immutability.
- Add a focused regression test covering top-level and nested `lock_secret` values.

## Type Of Change

- Bug fix
- Security/privacy hardening
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| AMC logs must not expose page edit-lock secrets. | `TestMaskSensitiveData.test_masks_page_lock_secret` asserts top-level and nested `lock_secret` values become `***MASKED***`. | The RED test failed before the fix because `result["lock_secret"]` remained `secret456`. |
| Existing sensitive-key masking remains intact. | `tests/unit/test_ajax.py` still covers `password`, `login`, `WIKIDOT_SESSION_ID`, `wikidot_token7`, nested structures, empty dicts, and non-sensitive fields. | A regression in earlier sensitive keys would fail the existing mask tests. |
| Page save behavior is unchanged. | `TestPageCreateOrEdit` and `TestPageEdit` pass after the mask-only change. | Changing `savePage` request construction or lock handling would fail page create/edit tests. |
| Static and broad unit gates remain green. | `tests/unit`; ruff; format; mypy; diff check. | Formatting, lint, type, whitespace, or broad unit failures reject the local completion claim. |

## Testing

Implemented locally in commit `a08bdd9 fix(ajax): mask page lock secrets`.

- RED: `uv run --extra test pytest tests/unit/test_ajax.py::TestMaskSensitiveData::test_masks_page_lock_secret -q` failed before the fix with `AssertionError: assert 'secret456' == '***MASKED***'`.
- GREEN: `uv run --extra test pytest tests/unit/test_ajax.py::TestMaskSensitiveData::test_masks_page_lock_secret -q`
- `uv run --extra test pytest tests/unit/test_ajax.py -q` passed 14 tests.
- `uv run --extra test pytest tests/unit/test_ajax.py tests/unit/test_amc_client.py -q` passed 47 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit -q` passed 10 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_new_page tests/unit/test_page.py::TestPageEdit::test_edit_existing_page -q` passed 2 tests.
- `uv run --extra test pytest tests/unit -q` passed 626 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`
- `python3 /home/roku/.codex/skills/complexity-optimizer/scripts/analyze_complexity.py /home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/worktrees/wikidot.py --format markdown` refreshed current complexity leads.

## Acceptance Criteria

- `_mask_sensitive_data({"lock_secret": ...})` returns `{"lock_secret": "***MASKED***"}`.
- Nested dictionaries and lists containing `lock_secret` are recursively masked.
- The input dictionary is not mutated.
- Existing sensitive keys remain masked.
- Non-sensitive request fields are preserved.
- `Page.create_or_edit(...)`, `Page.edit(...)`, and AMC request behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`lock_secret` is a temporary page edit credential used by Wikidot's `savePage` workflow. Since wikidot.py logs masked AMC request bodies on retry and error paths, the masking policy should cover the page lock secret just as it covers passwords, session IDs, and request tokens.

## Local Evidence, Not For Upstream Paste

- Local browser-free publishing evidence repeatedly used lock acquisition and `savePage` through wikidot.py's AMC path.
- The broad browser-free publish draft lists page edit lock acquisition and `savePage` as core workflow steps.
- Earlier local hardening in [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md) made the masker recursive; this slice closes the remaining page-lock secret key gap.
- Keep private rollout paths, account names, sandbox details, raw command transcripts, and saved page contents out of upstream discussion.

## Additional Notes

This slice does not mask arbitrary content fields such as page source text, title, comments, tags, parent names, or meta values. It only extends the explicit sensitive-key policy for AMC diagnostics.
