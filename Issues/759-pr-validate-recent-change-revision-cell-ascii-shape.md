# PR Draft: Validate Recent Change Revision Cell ASCII Shape

## Summary

`Site.get_recent_changes()` parses each generated recent-change row's `td.revision-no` cell into `SiteChange.revision_no`. Issue 725 tightened the cell parser from "any embedded digit run" to valid full-cell shapes such as `(rev. 3)` and `rev. 3`, but the accepted branch still used Unicode-aware `\d+` before `int(...)`. A generated revision cell containing Unicode digit glyphs such as `(rev. \uff13)` was therefore accepted and normalized into ordinary revision number `3`.

This change accepts generated recent-change revision numbers only when the revision cell's numeric part matches ASCII digits. Valid generated cells such as `(rev. 3)` and `rev. 3` continue to parse normally, existing no-digit malformed cells keep the `Revision number is not found ...` diagnostic, existing digit-bearing malformed cells such as `rev. 3 latest` keep the contextual malformed path, and digit-like non-ASCII cells now fail with `NoElementException("Revision number is malformed ...")` including site, recent-changes page, change index, field, and observed cell value context.

## Outcome

Recent-change parsing no longer fabricates revision numbers by normalizing malformed generated revision-cell metadata. A `SiteChangesListModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like revision cell text now fails at the revision-cell parser boundary before any `SiteChange` record is created from that row.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free recent-change monitoring, moderation dashboards, migration checks, publication audits, generated ledgers, local fixtures, or reconciliation workflows where `SiteChange.revision_no` must reflect structurally valid Wikidot recent-change metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify `Site.get_recent_changes()` as a practical read-heavy workflow for monitoring, moderation, migration, and publication audit work. Existing drafts cover retry-aware fetching, paginated batching, parser scoping, title/comment text preservation, page title/fullname diagnostics, timestamp/user diagnostics, response-body validation, limit validation, direct `SiteChange` constructor validation, pager page ASCII-shape validation, and revision-cell full-shape validation.

This slice is not a duplicate of [725-pr-validate-recent-change-revision-cell-shape.md](725-pr-validate-recent-change-revision-cell-shape.md). Issue 725 rejects digit-bearing text that does not match the expected revision-cell shape, such as `rev. 3 latest`; it did not cover Unicode digit normalization inside otherwise valid-shaped cells.

It is also not a duplicate of [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [657-pr-validate-non-negative-site-change-revision-numbers.md](657-pr-validate-non-negative-site-change-revision-numbers.md), or [755-pr-validate-recent-changes-pager-page-ascii-shape.md](755-pr-validate-recent-changes-pager-page-ascii-shape.md), which cover no-digit generated cells, direct constructor state, direct range validation, or response-wide pager page labels rather than generated revision-cell Unicode normalization.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md), [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [604-pr-validate-site-change-actor-client.md](604-pr-validate-site-change-actor-client.md), [631-pr-validate-blank-site-change-page-fullnames.md](631-pr-validate-blank-site-change-page-fullnames.md), [657-pr-validate-non-negative-site-change-revision-numbers.md](657-pr-validate-non-negative-site-change-revision-numbers.md), [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md), [725-pr-validate-recent-change-revision-cell-shape.md](725-pr-validate-recent-change-revision-cell-shape.md), [738-pr-validate-recent-change-title-href-routes.md](738-pr-validate-recent-change-title-href-routes.md), [755-pr-validate-recent-changes-pager-page-ascii-shape.md](755-pr-validate-recent-changes-pager-page-ascii-shape.md), and adjacent generated-scalar ASCII-shape drafts [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md), [757-pr-validate-forum-post-id-ascii-shape.md](757-pr-validate-forum-post-id-ascii-shape.md), and [758-pr-validate-forum-post-revision-id-ascii-shape.md](758-pr-validate-forum-post-revision-id-ascii-shape.md).

## Changes

- Require ASCII `[0-9]+` before integer conversion when parsing generated recent-change revision-cell numeric text.
- Preserve the existing contextual `NoElementException` message family for present malformed revision-cell values, including no-digit cells and digit-bearing trailing text.
- Preserve valid `(rev. <digits>)` and `rev. <digits>` parsing, recent-change row scoping, title/comment extraction, page href validation, timestamp/user parsing, flags, retry/pagination behavior, limit handling, response-body validation, `SiteChange` constructor semantics, and adjacent site/page workflows.
- Add focused regression coverage for a generated revision cell containing fullwidth revision number text `(rev. \uff13)`.

## Type Of Change

- Bug fix
- Recent-change generated revision-cell validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated recent-change revision cell containing non-ASCII digit glyphs must fail before any `SiteChange` is created from that row. |
| R2 | The malformed revision-cell diagnostic must include site, recent-changes page, change index, field, and observed cell value context. |
| R3 | Valid ASCII revision cells such as `(rev. 3)` and `rev. 3` must continue to parse into the same revision numbers. |
| R4 | Existing malformed no-digit cells such as `rev. latest` and digit-bearing malformed cells such as `rev. 3 latest` must keep contextual `NoElementException` paths. |
| R5 | Existing recent-change parser behavior, retry/pagination, response-body validation, title/comment extraction, page href validation, timestamp/user parsing, flags, limit handling, direct `SiteChange` validation, and adjacent site/page/member/application workflows must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page names, private edit comments, raw generated HTML, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, recent-changes class tests, full site tests, adjacent site/page/member/application tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `(rev. \uff13)` raises before a recent-change list is returned. | `test_get_recent_changes_rejects_non_ascii_digit_revision_number` failed RED with `DID NOT RAISE`, then passed after ASCII-only revision-cell parsing. | Returning a `SiteChange`, normalizing `"\uff13"` into revision number `3`, or silently skipping the row rejects this local completion claim. | Recent-change revision-cell parser | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | The exception reports `Revision number is malformed for site: test (page=1, change=1, field=revision_no, value=(rev. \uff13))`. | The focused regression asserts the diagnostic family, structural location, field, and observed value. | A raw `ValueError`, omitted site/page/change context, omitted field/value, or unrelated row diagnostic rejects this local completion claim. | Recent-change revision diagnostics | focused test |
| R3 | Valid ASCII revision cells still parse successfully. | Focused GREEN included `test_get_recent_changes_success`, `TestSiteGetRecentChanges` passed 40 tests, and `tests/unit/test_site.py` passed 363 tests. | Rejecting `(rev. 3)`, changing parsed revision numbers, or changing recent-change row fields rejects this local completion claim. | Valid recent-change parsing | `tests/unit/test_site.py` |
| R4 | No-digit and digit-bearing malformed cells retain contextual failure. | Focused GREEN included `test_get_recent_changes_malformed_revision_number_includes_raw_value_context` and `test_get_recent_changes_rejects_revision_number_with_trailing_text`. | Reclassifying `rev. latest`, accepting `rev. 3 latest`, changing the message family, or dropping observed values rejects this local completion claim. | Existing revision-cell diagnostics | `tests/unit/test_site.py` |
| R5 | Adjacent site workflows remain green. | Adjacent site/page/member/application coverage passed 915 tests, and full unit passed 3760 tests. | Regressing title/fullname parsing, comment spacing, timestamp/user parsing, flags, pagination, retry handling, limit behavior, response-body diagnostics, page workflows, member/application workflows, or any unit test rejects this local completion claim. | Site and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses a synthetic fixture-derived recent-change body and mocked AMC response. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page names, private edit comments, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, recent-changes class, full site, adjacent site/page/member/application, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `a72e0bc fix(site): validate recent change revision number shape`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_non_ascii_digit_revision_number -q` failed before the fix with `DID NOT RAISE` because `(rev. \uff13)` was accepted and normalized as revision number `3`.
- GREEN focused revision-cell slice: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_non_ascii_digit_revision_number tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_revision_number_with_trailing_text tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_revision_number_includes_raw_value_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success -q` passed 4 tests.
- `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 40 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 363 tests after formatting.
- `uv run pytest tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_site_member.py tests/unit/test_site_application.py -q` passed 915 tests.
- `uv run pytest tests/unit -q` passed 3760 tests after formatting.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no revision-cell boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `Site.get_recent_changes()` raises `NoElementException("Revision number is malformed ...")` for a generated recent-change revision cell whose text is `(rev. \uff13)`.
- The malformed revision-cell diagnostic includes `site: test`, `page=1`, `change=1`, `field=revision_no`, and the observed cell value.
- The parser does not create or return a `SiteChange(revision_no=3, ...)` from non-ASCII digit revision metadata.
- Valid ASCII structural revision cells such as `(rev. 3)` and `rev. 3` still parse successfully.
- Existing malformed no-digit revision cells such as `rev. latest` still raise `Revision number is not found ...`.
- Existing malformed digit-bearing revision cells such as `rev. 3 latest` still raise `Revision number is malformed ...`.
- Existing successful recent-change parsing, retry behavior, paginated batching, limit handling, zero-limit behavior, empty-result behavior, structural pager parsing, comment-pager filtering, title/comment text spacing, page title/fullname validation, flags, modifier users, timestamps, response-body diagnostics, adjacent site/page/member/application suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, private page name, saved page content, or private edit comment is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 725. Mitigation: Issue 725 covers malformed digit-bearing text outside the expected revision-cell shape; this slice covers Unicode digit normalization inside an otherwise accepted shape.
- Risk: This could be confused with direct `SiteChange` validation. Mitigation: direct revision-number type/range validation remains separate; this slice runs at the generated recent-change parser boundary before object construction.
- Risk: This could break valid recent-change parsing. Mitigation: ASCII `[0-9]+` generated revision cells still convert to integers, and successful recent-change plus adjacent site/page/member/application tests remain green.
- Risk: Diagnostics could expose private edit content. Mitigation: the diagnostic includes only site/page/change structural location, field name, and the compact revision-cell scalar; tests use synthetic fixture HTML and do not include real page content or comments.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the regex now accepts only ASCII `[0-9]+`, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated recent-change revision cells through direct metadata rows.
- Normal Wikidot recent-change revision cells are expected to use ASCII decimal digits after `rev.`.
- Existing recent-change parser context continues to identify site, response page, and structural change index.
- Existing `SiteChange` constructor identity validation continues to validate direct record state after parser-side conversion.

## Open Questions

None for this local slice. Future generated scalar-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Recent-change revision numbers are durable generated metadata for monitoring, rollback context, moderation summaries, migration checks, publication audits, and local fixtures. Unicode digit normalization can silently turn malformed generated revision-cell text into a valid-looking revision number. Requiring ASCII digits keeps generated revision parsing strict while preserving valid Wikidot recent-change rows and existing contextual parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated revision cell value was accepted and normalized into revision number `3`.
- Existing local drafts covered recent-change retry behavior, batching, comment/title spacing, response-body diagnostics, title/page/timestamp/user diagnostics, no-digit revision-cell context, digit-bearing extra-text revision-cell shape, direct `SiteChange` revision-number validation, and adjacent generated scalar ASCII-shape fixes; they did not validate Unicode digit normalization in generated recent-change revision cells.
- This slice does not change request payloads, retry policy, response-body validation, pager parsing, title/comment extraction, page href validation, timestamp/user parsing, flags, limit behavior, live Wikidot behavior, direct `SiteChange` constructors, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, private page names, saved page contents, private edit comments, private site data, and private page source out of upstream discussion.
