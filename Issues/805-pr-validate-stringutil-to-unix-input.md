# PR Draft: Validate StringUtil Unix Conversion Input

## Summary

`StringUtil.to_unix(...)` now rejects non-string values with `ValueError("target_str must be a string")` before calling string-only normalization methods such as `.translate(...)`. Valid Wikidot legacy slug normalization for strings remains unchanged.

The change is intentionally narrow: profile lookup callers, site-name validation, QuickModule lookup behavior, valid Unicode transliteration, empty-string handling, colon/underscore cleanup, and existing caller-side validators remain unchanged.

## Problem Statement

`StringUtil.to_unix(target_str)` is a public helper used by profile lookup and returned user records, but its direct boundary trusted the caller-provided value. Passing `None`, booleans, numbers, lists, or dictionaries reached `target_str.translate(...)` and leaked raw `AttributeError` messages such as `"'dict' object has no attribute 'translate'"` instead of the stable validation style used elsewhere in wikidot.py.

This mattered because `StringUtil.to_unix(...)` is the canonical helper behind Wikidot-style user/profile slug normalization. Caller-side fixes should not be the only protection for a reusable public utility.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify profile lookup, user lookup, QuickModule lookup, and Wikidot name normalization as practical surfaces: [120-pr-preserve-user-profile-title-spacing.md](120-pr-preserve-user-profile-title-spacing.md), [166-pr-user-profile-parse-context.md](166-pr-user-profile-parse-context.md), [312-pr-user-profile-id-href-context.md](312-pr-user-profile-id-href-context.md), [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [623-pr-validate-blank-user-profile-lookup-names.md](623-pr-validate-blank-user-profile-lookup-names.md), [625-pr-validate-quickmodule-blank-user-lookup-queries.md](625-pr-validate-quickmodule-blank-user-lookup-queries.md), and [709-pr-reject-blank-user-profile-titles.md](709-pr-reject-blank-user-profile-titles.md).

This slice is not a duplicate of [358-pr-validate-user-profile-lookup-usernames.md](358-pr-validate-user-profile-lookup-usernames.md). Issue 358 validates `User.from_name(...)` and `UserCollection.from_names(...)` caller inputs before profile request construction; this draft validates direct calls to the reusable `StringUtil.to_unix(...)` helper itself.

This slice is not a duplicate of [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md). Issue 359 validates `StringUtil.validate_site_unix_name(...)` for site host interpolation; this draft validates the separate normalization helper used for Wikidot-style slug conversion.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Direct utility calls to `StringUtil.to_unix(...)`.
- Profile-page user lookup and returned `User.unix_name` derivation, already protected by caller-side validators.
- Local tests, migration tools, generated ledgers, and downstream scripts that normalize Wikidot display names or page-like labels directly through `StringUtil.to_unix(...)`.

## Proposed Fix

- Add a runtime type guard at the start of `StringUtil.to_unix(...)`.
- Raise `ValueError("target_str must be a string")` for non-string inputs.
- Preserve the legacy Wikidot normalization sequence for valid strings.
- Add a focused regression covering representative non-string values before `.translate(...)` is reached.

## Implementation Notes

Implemented locally in commit `21d5427 fix(stringutil): validate unix conversion input`.

The implementation adds one guard in `src/wikidot/util/stringutil.py`:

```python
if not isinstance(target_str, str):
    raise ValueError("target_str must be a string")
```

The RED regression called `StringUtil.to_unix(...)` with `None`, `True`, `123`, `["page"]`, and `{"page": "name"}`. Before the fix, every case leaked `AttributeError` from `.translate(...)`; after the fix, every case raises the stable `ValueError`.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct non-string `StringUtil.to_unix(...)` calls fail with stable validation before string methods are used. | `TestStringUtilToUnix.test_rejects_non_string_values` failed RED with raw `.translate(...)` `AttributeError`, then passed GREEN after the guard. | Reaching `.translate(...)`, `.lower(...)`, regex normalization, coercing inputs with `str(...)`, or leaking raw attribute/type errors rejects this claim. |
| Valid legacy string normalization remains unchanged. | `tests/unit/test_stringutil.py` passed 35 tests. | Regressing lowercase conversion, Unicode transliteration, empty strings, colon handling, underscore behavior, or Japanese/non-ASCII cleanup rejects this claim. |
| Adjacent user/profile/site/QuickModule behavior remains stable. | Adjacent suites passed 344 tests. | Regressing `User.from_name(...)`, `UserCollection.from_names(...)`, client user accessors, site UNIX-name validation, or QuickModule lookup rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3898 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `21d5427 fix(stringutil): validate unix conversion input`.

- RED: `uv run pytest tests/unit/test_stringutil.py::TestStringUtilToUnix::test_rejects_non_string_values -q --tb=short` failed before the fix with raw `AttributeError` from `target_str.translate(...)` for 5 non-string values.
- GREEN focused: `uv run pytest tests/unit/test_stringutil.py::TestStringUtilToUnix::test_rejects_non_string_values -q --tb=short` passed 5 tests.
- Adjacent string/user/site/QuickModule coverage: `uv run pytest tests/unit/test_stringutil.py tests/unit/test_user.py tests/unit/test_client.py tests/unit/test_site.py::TestSiteFromUnixName tests/unit/test_quick_module.py -q --tb=short` passed 344 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3898 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `StringUtil.to_unix(None)`, `True`, `123`, `["page"]`, and `{"page": "name"}` raise `ValueError("target_str must be a string")`.
- The rejection happens before `.translate(...)`, `.lower(...)`, regex cleanup, or any string coercion.
- Valid string inputs keep the existing Wikidot-compatible normalization outputs.
- Existing profile lookup caller validators from Issue 358 and site UNIX-name validation from Issue 359 remain unchanged.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `AttributeError` from passing non-strings. Mitigation: the documented parameter is a string and repo validators consistently raise `ValueError` for malformed public inputs.
- Risk: This could be confused with profile lookup input validation. Mitigation: Issue 358 remains the caller-side username boundary; this slice protects the reusable utility for direct use and future callers.
- Risk: The helper still accepts blank strings and strings that normalize to blank output. Mitigation: blank-name policy belongs to caller-specific validators such as profile lookup and QuickModule user lookup; this slice only validates input type.

## Dependencies

- Existing legacy transliteration table in `wikidot.util.table.char_table` remains the normalization map.
- Existing caller-side username and site-name validators remain the owners of public workflow-specific blank/host-shape policy.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, result ergonomics, cache ownership checks, cross-owner batch checks, or complexity candidates outside this now-covered direct string normalization boundary.

## Rationale for Upstream Suitability

`StringUtil.to_unix(...)` is small but central utility code. A direct runtime guard gives callers deterministic feedback, aligns the helper with established wikidot.py validation style, and preserves every valid string-normalization behavior. The patch is low risk and makes future callers less likely to need duplicate preflight code solely to avoid raw Python attribute errors.

## Local Evidence

- Local rollout-backed work used browser-free profile lookup, returned user records, QuickModule lookup, and site/name normalization in migration and moderation-style workflows.
- Existing local drafts covered profile-title spacing, profile parser context, profile lookup input validation, blank profile lookup names, site UNIX-name validation, and QuickModule query validation. They did not cover direct `StringUtil.to_unix(...)` calls.
- This slice only validates the direct helper input type. It does not change valid normalization rules, profile lookup request construction, user ID extraction, avatar URL construction, QuickModule behavior, site lookup behavior, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page content, raw response bodies, private site data, and private source text out of upstream discussion.
