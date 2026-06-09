# PR Draft: Validate Recent Change Revision Cell Shape

## Summary

`Site.get_recent_changes()` parses each generated recent-change row's `td.revision-no` cell into `SiteChange.revision_no`. Issue [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md) made cells with no digits, such as `rev. latest`, fail with site/page/change/field/value context. One adjacent parser gap remained: any embedded digit run was accepted, so malformed generated text such as `rev. 3 latest` silently became revision `3`.

This change accepts the expected recent-change revision shapes, such as `(rev. 3)` and `rev. 3`, and rejects digit-bearing trailing or surrounding text with `NoElementException` before constructing `SiteChange`.

## Outcome

Recent-change revision parsing no longer fabricates a revision number from malformed generated text. Valid rows still parse the same revision numbers, and existing no-digit malformed cells keep the `Revision number is not found ...` diagnostic.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free recent-change monitoring, moderation dashboards, migration checks, publication audits, generated ledgers, or local fixtures where `revision_no` must reflect a structurally valid Wikidot recent-change cell.

## Current Evidence

Local rollout-backed drafts already identify `Site.get_recent_changes()` as a practical read-heavy workflow. Existing drafts cover retry-aware fetching, paginated batching, parser scoping, title/comment text preservation, page title/fullname diagnostics, timestamp/user diagnostics, response-body validation, limit validation, and direct `SiteChange` constructor validation.

This slice is not a duplicate of [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), or [657-pr-validate-non-negative-site-change-revision-numbers.md](657-pr-validate-non-negative-site-change-revision-numbers.md). Issue 281 covers generated revision cells with no parseable digits. Issues 436 and 657 cover direct `SiteChange(revision_no=...)` construction. This slice covers a generated parser cell that contains digits but does not match the expected recent-change revision shape.

No upstream issue was filed from this local workspace.

## Changes

- Add a helper for recent-change revision-number cell parsing.
- Accept `rev. <digits>` with optional surrounding parentheses and whitespace.
- Reject digit-bearing malformed revision cells, such as `rev. 3 latest`, with `NoElementException` containing site, recent-changes page, change index, field, and normalized cell value.
- Preserve the existing no-digit `Revision number is not found ...` diagnostic.
- Preserve successful recent-change parsing, request payloads, retry/pagination behavior, title/comment parsing, timestamp/user parsing, flags, `limit`, and `SiteChange` constructor semantics.
- Add a focused `Site.get_recent_changes()` regression for a malformed revision cell with trailing text.

## Type Of Change

- Parser hardening
- Recent-changes data validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated recent-change revision cell containing digits plus extra text, such as `rev. 3 latest`, must fail before constructing `SiteChange`. |
| R2 | The malformed revision-cell error must identify site, recent-changes page, structural change index, `field=revision_no`, and the normalized cell value. |
| R3 | Existing no-digit malformed cells, such as `rev. latest`, must keep the prior `Revision number is not found ...` diagnostic. |
| R4 | Valid fixture revision cells must continue to parse into the same `SiteChange.revision_no` values. |
| R5 | Existing recent-change parser behavior, pagination, retry handling, title/comment extraction, timestamp/user parsing, flags, and direct `SiteChange` validators must remain unchanged. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page names, private edit comments, raw generated HTML, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `rev. 3 latest` fails instead of becoming revision `3`. | `test_get_recent_changes_rejects_revision_number_with_trailing_text` failed RED with `DID NOT RAISE`, then passed GREEN after the helper was added. | Returning a `SiteChange`, extracting the first digit run, or silently dropping the malformed text rejects this local completion claim. | Recent-change generated parser | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | The new malformed-cell diagnostic includes the structural context and observed value. | The regression matches `Revision number is malformed for site: test (page=1, change=1, field=revision_no, value=rev. 3 latest)`. | Omitting site, page, change index, field, or observed value rejects this local completion claim. | Recent-change revision diagnostics | `tests/unit/test_site.py` |
| R3 | `rev. latest` keeps the no-digit diagnostic from Issue 281. | `test_get_recent_changes_malformed_revision_number_includes_raw_value_context` passed in focused and full site coverage. | Reclassifying no-digit cells as the new malformed-digit case rejects this local completion claim. | Existing parser diagnostic compatibility | `tests/unit/test_site.py` |
| R4 | Valid recent-change rows still parse. | `test_get_recent_changes_success`, `TestSiteGetRecentChanges`, `tests/unit/test_site.py`, and full unit coverage passed. | Regressing valid revision numbers, page identity, title, flags, actor, timestamp, or comments rejects this local completion claim. | Recent-change row parsing | `tests/unit/test_site.py` |
| R5 | Adjacent repository behavior stays green. | Full unit, ruff, ruff format, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R6 | No private or live-site material is needed. | The regression uses synthetic fixture mutation and mocks only. | Using credentials, cookies, auth JSON, live Wikidot actions, raw private generated HTML, private page names, private comments, upstream Issues, upstream PRs, or pushes rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `9e3b3a4 fix(site): validate recent change revision cells`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_revision_number_with_trailing_text -q` failed before the fix with `DID NOT RAISE`.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_revision_number_includes_raw_value_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_revision_number_with_trailing_text tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success -q` passed 3 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 31 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass -q` passed 61 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 352 tests.
- `uv run pytest tests/unit -q` passed 3598 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Site.get_recent_changes()` raises `NoElementException` for a recent-change revision cell such as `rev. 3 latest`.
- The exception includes site `unix_name`, recent-changes page number, structural change-item position, `field=revision_no`, and the normalized cell value.
- No-digit malformed revision cells keep the existing `Revision number is not found ...` message.
- Valid recent-change rows still parse `revision_no` from `(rev. <digits>)` / `rev. <digits>` cells.
- Successful recent-change parsing, retry behavior, paginated batching, limit handling, zero-limit behavior, empty-result behavior, structural pager parsing, comment-pager filtering, title/comment text spacing, page title/fullname validation, flags, modifier users, timestamps, and `SiteChange` output fields remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Live Wikidot might emit a revision cell without parentheses. Mitigation: the helper accepts both `(rev. 3)` and `rev. 3`.
- Risk: Overly loose parsing could continue accepting malformed text. Mitigation: the helper uses full-cell matching instead of searching for any digit run.
- Risk: This could be confused with Issue 281. Mitigation: Issue 281 covers no-digit malformed cells; this slice covers digit-bearing cells that do not match the expected cell shape.
- Risk: This could be confused with direct `SiteChange` validation. Mitigation: Issues 436 and 657 cover constructor inputs after parsing; this slice validates generated parser input before construction.

## Dependencies

- Existing `Site.get_recent_changes()` request construction, retry helper usage, pagination logic, and limit handling remain unchanged.
- Existing page title/fullname, timestamp, user, flags, and comment parsing remain unchanged.
- Existing `SiteChange` constructor validation remains responsible for direct local record construction.
- Existing `NoElementException` remains the generated-parser exception for malformed recent-change cells.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Future work should continue with fresh duplicate-checked parser boundaries, public input validation, result ergonomics, or measured complexity candidates outside this recent-change revision-cell shape path.

## Upstream-Safe Motivation

`SiteChange.revision_no` is a durable identity field used by recent-change monitoring, moderation summaries, migration checks, and audit ledgers. A generated revision cell with extra text should not be accepted merely because it contains a digit somewhere. Full-cell validation keeps malformed Wikidot module output visible while preserving valid recent-change rows.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established recent changes as a practical workflow through retry-aware fetching, pagination batching, parser scoping, response-body validation, title/page/revision/timestamp/user extraction, direct `SiteChange` constructor validation, and adjacent site workflows.
- Existing local drafts covered no-digit recent-change revision-cell diagnostics, direct revision-number type validation, and direct revision-number range validation; they did not reject digit-bearing malformed generated revision cells before construction.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML, private page names, saved page contents, and private edit comments out of upstream discussion.
