# PR Draft: Validate Site.get_recent_changes Limit Input

## Summary

`Site.get_recent_changes(limit=None)` documents `limit` as `int | None`, but malformed caller-provided values were not rejected at the public API boundary. Values such as `True`, `"2"`, `2.0`, or `{"limit": 2}` could reach range comparisons, request payload construction, or AMC lookup work and then fail with Python internals such as `TypeError`, silently return an empty result for `False`, or send malformed `perpage` values.

This change validates `limit` before non-positive fast-return checks, `perpage` calculation, pager trimming, or AMC request construction. Invalid values now raise `ValueError("limit must be an integer or None")`. Existing `limit=None`, positive integer limit behavior, `limit=0` fast return, negative-limit empty-result behavior, recent-changes retry behavior, paginated batching, response-body diagnostics, parser diagnostics, comment filtering, and `SiteChange` output shape remain unchanged.

## Outcome

Recent-changes callers now get deterministic Python-side preflight validation for malformed `limit` values instead of raw comparison errors, accidental boolean behavior, or malformed recent-changes request payloads.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using `Site.get_recent_changes(...)` for moderation ledgers, archival indexing, publication audits, migration tooling, activity monitoring, or generated recent-change exports.

## Current Evidence

Local rollout-backed drafts repeatedly identify `Site.get_recent_changes(...)` as a practical browser-free site inspection workflow. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), and [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md) cover retry, batching, parser scoping, response-body diagnostics, and row-field diagnostics for recent changes.

Those prior slices are not duplicates. They preserve or consume valid `limit` values but do not validate malformed caller-provided `limit` objects before comparison, request construction, or AMC work. This slice targets only the public pagination input boundary.

## Related Issue

Builds directly on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), and the input-validation pattern from [344-pr-validate-search-pagination-types.md](344-pr-validate-search-pagination-types.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `Site.get_recent_changes(limit=...)` accepts only `None` or a non-boolean integer before non-positive checks, `perpage` calculation, or AMC request construction.
- Preserve `limit=None` first-page behavior.
- Preserve `limit=0` and negative integer empty-result behavior.
- Preserve positive integer limit behavior, batched page trimming, retry handling, response-body diagnostics, row parser diagnostics, comment filtering, and `SiteChange` field semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Recent-changes pagination preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site.get_recent_changes(limit=...)` must reject non-integer and boolean values with `ValueError("limit must be an integer or None")` before AMC request work. |
| R2 | `limit=None`, positive integer limits, `limit=0`, and negative integer limits must keep existing behavior. |
| R3 | Existing recent-changes retry, batched pagination, response-body diagnostics, parser diagnostics, comment filtering, and `SiteChange` output shape must remain unchanged. |
| R4 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private recent-change content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R5 | Focused RED/GREEN, recent-changes tests, site tests, adjacent site/page/member/application/user tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed recent-changes limits fail before AMC request calls. | `TestSiteGetRecentChanges.test_get_recent_changes_rejects_invalid_limit_before_request` failed RED before the fix for `True`, `False`, `"2"`, `2.0`, and a dict, then passed GREEN after validation was added. | Comparing a dict/string/float to zero, accepting `False` as zero, sending `perpage=True`, coercing strings/floats/dicts, or calling AMC rejects this local completion claim. | Recent-changes input preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Valid and documented limit semantics stay compatible. | Existing `test_get_recent_changes_with_limit`, `test_get_recent_changes_zero_limit_returns_empty`, `test_get_recent_changes_batches_only_pages_needed_for_limit`, and the full recent-changes class passed. | Rejecting `None`, changing positive limit clipping, making `limit=0` request AMC, changing negative integer empty results, or changing return ordering rejects this local completion claim. | Recent-changes pagination | `tests/unit/test_site.py` |
| R3 | Recent-changes behavior beyond input validation remains green. | `TestSiteGetRecentChanges` passed 30 tests, `tests/unit/test_site.py` passed 117 tests, adjacent `test_site.py::TestSiteGetRecentChanges test_page.py test_site_member.py test_site_application.py test_user.py` passed 317 tests, and full unit passed 1059 tests. | Regressing retry exhaustion, transient retry success, response-body missing/type diagnostics, parser context, comment markup filtering, pager filtering, batched pagination, user parsing, title/revision/timestamp diagnostics, or `SiteChange` fields rejects this local completion claim. | Recent-changes workflow | affected site/page/member/application/user tests |
| R4 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, generated recent-change HTML from real sites, private page names, private edit comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, recent-changes tests passed, site and adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `deaadb7 fix(site): validate recent changes limit`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_invalid_limit_before_request` failed before the fix with 5 failures: `True` and `2.0` reached request work and hit `IndexError`, `False` returned without `ValueError`, `"2"` leaked `TypeError`, and the dict leaked comparison `TypeError`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_invalid_limit_before_request` passed 5 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteGetRecentChanges` passed 30 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py` passed 117 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_site.py::TestSiteGetRecentChanges tests/unit/test_page.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py` passed 317 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1059 tests.
- `.venv/bin/ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `.venv/bin/ruff format --check src/wikidot/module/site.py tests/unit/test_site.py` passed with 2 files already formatted.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `site.get_recent_changes(limit=True)` and `limit=False` raise `ValueError("limit must be an integer or None")` before AMC request work.
- `site.get_recent_changes(limit="2")`, `limit=2.0`, and `limit={"limit": 2}` raise the same `ValueError` before comparison, `perpage` calculation, or AMC request work.
- `site.get_recent_changes()` still requests the first recent-changes page with `perpage` based on the default path.
- `site.get_recent_changes(limit=1)` still clips returned results to one item.
- `site.get_recent_changes(limit=0)` still returns `[]` without calling AMC.
- Negative integer limits still follow the existing non-positive empty-result behavior.
- Limit-bounded paginated reads still request only needed pages.
- Existing retry, missing-body diagnostics, malformed-body diagnostics, parser context, comment filtering, pager filtering, user/timestamp/revision diagnostics, and `SiteChange` field semantics remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting booleans tightens behavior for `False`, which previously behaved like `0`. Mitigation: the public type is `int | None`; bool is an `int` subclass but not a meaningful recent-changes count, and `False` can hide config parsing mistakes.
- Risk: Limit validation could alter non-positive integer behavior. Mitigation: the helper returns valid integers unchanged, so the existing `limit <= 0` fast-return path remains intact.
- Risk: Diagnostics could expose private recent-change content. Mitigation: the new error message contains only the input-field name and expected type, not generated HTML, page names, edit comments, or response bodies.

## Dependencies

- Existing recent-changes request, retry, parser, and response-body diagnostics remain the authoritative behavior for valid `limit` values.
- The validation helper is local to `src/wikidot/module/site.py` and does not change `SearchPagesQuery` or other pagination APIs.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, action/read boundaries, parser diagnostics, result ergonomics, or complexity candidates outside this now-covered recent-changes limit validation path.

## Upstream-Safe Motivation

Recent-changes reads are often driven by generated configs, CLI payloads, JSON/YAML values, ledgers, and automation. Since `limit` controls remote request sizing and pagination trimming, malformed values should fail deterministically before request work rather than leaking Python internals or creating malformed `perpage` payloads.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established recent changes as a practical workflow for site inspection, activity monitoring, and moderation/audit ledgers.
- The focused RED failure showed malformed `limit` values crossing the public call boundary without stable validation.
- Existing recent-changes drafts covered retry, batching, parser scoping, response-body diagnostics, row diagnostics, and preservation of valid limit handling. They did not validate malformed caller-provided `limit` values.
- This slice only validates `Site.get_recent_changes(limit=...)`. It does not change request module names, retry policy, response-body validation, row parsing, pager discovery, comment extraction, user parsing, timestamp parsing, revision parsing, title/fullname parsing, `SiteChange` fields, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, generated recent-change HTML, real page names, private edit comments, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed values instead of coercing them. Callers that load recent-changes limits from text sources should parse and validate those values as integers before calling `Site.get_recent_changes(...)`.
