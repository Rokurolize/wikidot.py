# PR Draft: Validate Non-Negative Site Change Revision Numbers

## Summary

`SiteChange.revision_no` is the recent-change revision identity stored by `Site.get_recent_changes(...)` rows and by direct local ledger construction. Existing local drafts validate malformed direct `SiteChange.revision_no` types, parser-side malformed recent-change revision cells, and non-negative page/forum revision objects, but direct `SiteChange(revision_no=-1)` still stored an impossible negative recent-change revision number.

This change validates direct `SiteChange.revision_no` values as non-negative integers. Malformed types still raise `ValueError("revision_no must be an integer")`, negative integers now raise `ValueError("revision_no must be non-negative")`, and `revision_no=0` remains accepted because this slice avoids a stronger positive-only invariant without separate rollout evidence.

## Outcome

Direct recent-change records can no longer carry negative revision metadata, while valid zero and positive values, generated recent-change parsing, existing malformed-type diagnostics, flags/text/actor/site validation precedence, pagination, retry handling, and adjacent site workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, browser-free change monitoring, serialized recent-change rows, or generated recent-change reports.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent changes and revision metadata as practical workflow surfaces. Existing recent-change drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md), [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [604-pr-validate-site-change-actor-client.md](604-pr-validate-site-change-actor-client.md), and [631-pr-validate-blank-site-change-page-fullnames.md](631-pr-validate-blank-site-change-page-fullnames.md) establish this row shape as an active local boundary.

This slice is not a duplicate of those drafts. Issue 436 validates malformed direct `SiteChange.revision_no` types but preserves ordinary integers and did not reject negative values. Issue 281 validates parser-side generated revision cells that contain no digits; generated parser values remain digit-only and therefore non-negative. Issue 637 validates `PageRevision.rev_no` and `ForumPostRevision.rev_no`, not `SiteChange.revision_no`. Issue 631 validates direct blank page identities, and Issue 604 validates actor/site client coherence.

## Related Issue / Non-Duplicate Analysis

Builds directly on [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [604-pr-validate-site-change-actor-client.md](604-pr-validate-site-change-actor-client.md), [631-pr-validate-blank-site-change-page-fullnames.md](631-pr-validate-blank-site-change-page-fullnames.md), and [637-pr-validate-non-negative-revision-numbers.md](637-pr-validate-non-negative-revision-numbers.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject direct `SiteChange(revision_no=-1)` and other negative integer revision numbers with `ValueError("revision_no must be non-negative")`.
- Preserve existing malformed-type diagnostics for `None`, booleans, strings, floats, lists, and other non-integers.
- Preserve `revision_no=0` as a valid non-negative value.
- Preserve generated recent-change parser behavior, which already parses digit-only revision cells before constructing `SiteChange`.
- Preserve existing `flags`, text-field, actor/time, site, and actor-client validation precedence.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Recent-change ledger state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(revision_no=-1)` and `revision_no=-100` must raise `ValueError("revision_no must be non-negative")` before storing record state. |
| R2 | Existing malformed direct revision-number type diagnostics must remain `ValueError("revision_no must be an integer")`. |
| R3 | `SiteChange(revision_no=0)` and positive integer values must remain valid. |
| R4 | Existing parser-created recent-change rows and direct `SiteChange` validators for flags, text fields, actor/time, site, and actor-client coherence must remain unchanged. |
| R5 | Existing recent-change fetching, pagination, limit handling, response-body validation, parser diagnostics, title/comment spacing, revision extraction, user/timestamp parsing, and adjacent site workflows must remain green. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, recent-change tests, site tests, adjacent workflow tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative direct recent-change revision numbers fail at construction. | `test_init_rejects_negative_revision_numbers` failed RED for `-1` and `-100` with `DID NOT RAISE`, then passed GREEN after the range check. | Accepting negative values, coercing them to `0`, or raising the malformed-type diagnostic for integers rejects this local completion claim. | `SiteChange` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Existing malformed-type diagnostics remain stable. | `test_init_rejects_malformed_revision_numbers` passed in RED and GREEN for `None`, booleans, strings, floats, and lists. | Changing `revision_no must be an integer`, accepting booleans, or coercing strings/floats rejects this local completion claim. | `SiteChange` constructor type validation | `tests/unit/test_site.py` |
| R3 | Zero remains valid. | `test_init_accepts_zero_revision_number` passed in RED and GREEN and stores `revision_no == 0`. | Requiring positive-only revision numbers without separate evidence rejects this local completion claim. | Constructor compatibility | `tests/unit/test_site.py` |
| R4 | Existing constructor validation order stays intact. | `TestSiteChangeDataclass` passed 55 tests after the fix, covering flags, malformed site, text fields, blank page fullname, optional comments, actor/time, and actor-client checks. | Weakening prior constructor validators or changing their diagnostics rejects this local completion claim. | Direct recent-change records | `tests/unit/test_site.py` |
| R5 | Existing recent-change and adjacent workflows remain green. | `TestSiteChangeDataclass` plus `TestSiteGetRecentChanges` passed 82 tests, `tests/unit/test_site.py` passed 304 tests, adjacent site/page/member/application/user suites passed 883 tests, and full unit passed 2992 tests. | Regressing parser-created rows, revision extraction, page title/fullname parsing, flags, timestamp/user parsing, response-body diagnostics, pagination, retry behavior, page workflows, member workflows, application workflows, user workflows, or any unit test rejects this local completion claim. | Recent changes and adjacent workflows | `tests/unit/test_site.py`, `tests/unit/test_page.py`, `tests/unit/test_site_member.py`, `tests/unit/test_site_application.py`, `tests/unit/test_user.py`, `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use synthetic constructors or mocked recent-change responses only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user data, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, targeted tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d05c7ce fix(site): validate site change revision ranges`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_malformed_revision_numbers tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_negative_revision_numbers tests/unit/test_site.py::TestSiteChangeDataclass::test_init_accepts_zero_revision_number tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success -q` failed 2 negative direct `SiteChange.revision_no` cases before the fix; 6 malformed-type guards, the zero-value guard, and the parser-created recent-change guard passed.
- GREEN: the same focused command passed 10 tests after adding the non-negative range check.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 82 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 304 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py -q` passed 883 tests.
- `uv run pytest tests/unit -q` passed 2992 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteChange(revision_no=-1)` and `SiteChange(revision_no=-100)` raise `ValueError("revision_no must be non-negative")`.
- Malformed direct values such as `None`, booleans, strings, floats, and lists still raise `ValueError("revision_no must be an integer")`.
- `SiteChange(revision_no=0)` remains valid and stores `0`.
- Existing valid parser-created recent-change rows still construct `SiteChange` objects.
- Existing `flags`, text-field, actor/time, site, and actor-client validators remain unchanged.
- Existing recent-change fetching, pagination, parser diagnostics, response-body validation, title/comment spacing, and adjacent site workflows remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private user data, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteChange.revision_no` is revision identity for recent-change monitoring, moderation dashboards, audit exports, migration checks, and generated ledgers. Negative revision numbers are invalid row state but previously passed direct constructor validation because they are ordinary integers. Non-negative validation keeps direct ledger construction aligned with parser-created recent-change rows without adding stronger positive-only or contiguous-sequence assumptions.

## Local Evidence

- Local rollout-backed drafts repeatedly used recent-change fetching, recent-change pagination, parser diagnostics, response-body validation, page/title/comment/user/timestamp/revision extraction, and tests that construct `SiteChange` directly.
- Issue 436 covered direct `revision_no` type validation but did not cover integer range semantics.
- Issue 281 covered malformed generated revision-cell text and kept parser-created revision numbers digit-only.
- Issue 637 covered page/forum revision object range semantics, not recent-change ledger rows.
- The focused RED failure showed direct negative `SiteChange.revision_no` values were accepted as dataclass state. The GREEN regressions cover negative rejection, malformed-type compatibility, zero compatibility, parser-created row compatibility, and adjacent site workflows.
- This slice only validates direct recent-change revision-number range. It does not change request payloads, parser selectors, generated revision parsing, positive-only requirements, `limit` behavior, pagination, retry policy, title/comment extraction, page fullname parsing, timestamp/user parsing, flag semantics, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, private user data, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change intentionally validates non-negative range only. It does not require positive revision numbers and does not reinterpret `0`, keeping the direct constructor conservative and consistent with the broader local range-validation pattern.
