# PR Draft: Validate Recent Changes Pager Page ASCII Shape

## Summary

`Site.get_recent_changes(...)` parses the first generated `changes/SiteChangesListModule` response pager to decide whether additional recent-changes pages should be fetched. The structural pager scan used `page_text.isdigit()` before `int(page_text)`, so generated labels containing Unicode digit glyphs such as `"\uff12"` were accepted and normalized into ordinary page number `2`. That could turn malformed generated pager metadata into a real follow-up recent-changes request.

This change accepts recent-changes pager page labels only when they match ASCII digits. Ordinary non-numeric pager labels such as `next` continue to be ignored, valid ASCII pagination still batches subsequent pages, edit-comment pager markup remains scoped away from the structural pager, and digit-like non-ASCII labels now fail with `NoElementException("Recent changes pager page is malformed ...")` including site, first page, field, and observed value context.

## Outcome

Recent-changes acquisition no longer fabricates pagination traversal from malformed generated pager labels. A `SiteChangesListModule` response with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like pager text now fails at the pager boundary instead of issuing unintended extra page requests.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free recent-change monitoring, moderation ledgers, migration checks, publication audits, local fixtures, or generated workflows where site-change traversal must come only from structurally valid Wikidot pager metadata.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent changes as a practical retry-aware site inspection workflow. Existing drafts cover retry-aware fetches, batched pagination, limit handling, edit-comment parser scoping, comment-pager scoping, text fidelity, response-body diagnostics, row parser diagnostics, typed value extraction, result field validation, and direct `SiteChange` constructor validation.

This slice is not a duplicate of [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), which protects edit comments from being mistaken for the structural pager. It is not a duplicate of [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), or [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), which cover request reliability, response shape, and pagination count boundaries. This slice covers the accepted-value shape of structural recent-changes pager page labels.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md), [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [509-pr-validate-site-change-actor-client.md](509-pr-validate-site-change-actor-client.md), [631-pr-validate-blank-site-change-page-fullnames.md](631-pr-validate-blank-site-change-page-fullnames.md), and the adjacent response-wide pager-page drafts [750-pr-validate-site-member-pager-page-ascii-shape.md](750-pr-validate-site-member-pager-page-ascii-shape.md), [751-pr-validate-private-message-pager-page-ascii-shape.md](751-pr-validate-private-message-pager-page-ascii-shape.md), [752-pr-validate-forum-post-pager-page-ascii-shape.md](752-pr-validate-forum-post-pager-page-ascii-shape.md), [753-pr-validate-forum-thread-pager-page-ascii-shape.md](753-pr-validate-forum-thread-pager-page-ascii-shape.md), and [754-pr-validate-listpages-pager-page-ascii-shape.md](754-pr-validate-listpages-pager-page-ascii-shape.md).

## Changes

- Require ASCII `[0-9]+` before integer conversion when reading structural recent-changes pager page labels.
- Raise `NoElementException` with site, first-page, field, and observed value context when a pager label is digit-like but not ASCII digits.
- Preserve ordinary non-numeric pager labels, missing pager behavior, valid ASCII pagination batching, limit-bounded batching, edit-comment pager filtering, paginated retry handling, response-body diagnostics, and recent-change row parsing.
- Add focused regression coverage for a structural recent-changes pager containing fullwidth page label `"\uff12"`.

## Type Of Change

- Bug fix
- Recent-changes pager scalar-shape validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A structural recent-changes pager label containing non-ASCII digit glyphs must fail before any extra page request is issued. |
| R2 | The malformed pager diagnostic must include site, first page, field, and observed value context. |
| R3 | Valid ASCII pager labels must continue to batch subsequent recent-changes pages. |
| R4 | Ordinary non-numeric pager labels such as `next` must continue to be ignored. |
| R5 | Edit-comment-local pager markup must continue to be ignored as comment content, not structural pagination. |
| R6 | Existing response-body, retry-exhaustion, limit-bounding, row parser, and adjacent page/site/member/application workflows must remain compatible. |
| R7 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real page content, raw generated HTML from real accounts, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R8 | Focused RED/GREEN, site tests, adjacent site/page/member/application tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `"\uff12"` in the structural pager raises before a page-2 request can be made. | `test_get_recent_changes_rejects_non_ascii_digit_pager_link` failed RED with `DID NOT RAISE`, then passed after ASCII-only pager parsing. | Returning changes, normalizing `"\uff12"` into page `2`, issuing a second request, or silently dropping the malformed digit rejects this local completion claim. | Recent-changes pager parser | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | The exception reports `Recent changes pager page is malformed for site: test, page: 1 (field=page, value=\uff12)`. | The focused regression asserts the diagnostic family and contextual fields. | A raw `ValueError`, omitted site/page context, omitted scalar value, or unrelated recent-change row diagnostic rejects this local completion claim. | Pager diagnostics | focused test |
| R3 | Valid ASCII pager label `2` still batches later recent-changes pages. | Focused GREEN included `test_get_recent_changes_batches_paginated_pages` and `test_get_recent_changes_batches_only_pages_needed_for_limit`. | Failing to request later pages, changing page batching, ignoring `limit`, or returning only first-page changes rejects this local completion claim. | Valid pagination | recent-changes batching tests |
| R4 | `next` remains ignored when no numeric page label exists. | Focused GREEN included `test_get_recent_changes_ignores_non_numeric_pager_links`. | Raising for `next` or making a synthetic extra request rejects this local completion claim. | Non-numeric pager compatibility | recent-changes pager test |
| R5 | Pager-like markup inside an edit comment remains scoped away from structural pagination. | Focused GREEN included `test_get_recent_changes_ignores_comment_pager_markup`. | Treating edit-comment content as structural pagination or issuing a page-2 request rejects this local completion claim. | Comment scoping | recent-changes comment-pager test |
| R6 | Adjacent site/page workflows remain green. | `tests/unit/test_site.py` passed 362 tests, adjacent site/page/member/application coverage passed 913 tests, and full unit passed 3756 tests. | Regressing first-page retry, paginated retry, response-body diagnostics, limit behavior, row parsing, page/search workflows, site-member/application behavior, or any unit test rejects this local completion claim. | Site workflows | `tests/unit` |
| R7 | No live site state or private material is needed. | The regression uses synthetic unit-level recent-changes HTML and mock AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real account names, real page content, or raw generated HTML from real accounts rejects this local completion claim. | Test and draft privacy | this draft |
| R8 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site tests, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `e19e338 fix(site): validate recent changes pager page shape`.

- RED setup correction: the first new test draft used `exceptions.NoElementException`, but `test_site.py` imports `NoElementException` directly; after aligning with the file style, the same focused RED produced the intended production failure.
- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_non_ascii_digit_pager_link -q` failed before the fix with `DID NOT RAISE` because pager label `"\uff12"` was accepted and normalized as page `2`.
- GREEN focused pager slice: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_non_ascii_digit_pager_link tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_ignores_non_numeric_pager_links tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_ignores_comment_pager_markup tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_paginated_pages tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_only_pages_needed_for_limit tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_retry_exhaustion_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_missing_response_body_includes_site_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_paginated_malformed_response_body_type_includes_site_context -q` passed 8 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 362 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_page.py -q` passed 913 tests.
- `uv run --extra test pytest tests/unit -q` passed 3756 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no recent-changes pager-boundary, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker: `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`.

## Acceptance Criteria

- `Site.get_recent_changes()` raises `NoElementException("Recent changes pager page is malformed ...")` for a structural pager label whose text is `"\uff12"`.
- The malformed pager diagnostic includes `site: test`, `page: 1`, `field=page`, and `value=\uff12` context.
- The parser does not issue a page-2 recent-changes request from non-ASCII digit pager text.
- Valid ASCII structural pager labels such as `2` still batch and parse paginated recent changes.
- Ordinary non-numeric pager labels such as `next` still leave recent changes as a single-page result when no numeric page label exists.
- Edit-comment-local pager-like markup is still ignored as comment content and does not drive structural pagination.
- Existing response-body diagnostics, retry-exhaustion behavior, limit bounding, row parser diagnostics, page/search workflows, adjacent site/member/application suites, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real accounts, raw rollout path, real account name, real page content, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with edit-comment pager scoping. Mitigation: comment-local pager markup remains covered by Issue 099; this slice validates structural pager page-label shape after pager selection.
- Risk: This could be confused with recent-changes retry or batching work. Mitigation: Issues 030, 072, 182, and 373 cover request reliability and page counts; this slice runs before valid later-page request bodies are built.
- Risk: This could break ordinary pager labels such as `next`. Mitigation: non-numeric labels are still ignored; only digit-like non-ASCII labels that the old code treated as numeric now fail.
- Risk: This could break valid pagination. Mitigation: ASCII `[0-9]+` labels still convert to integers, and the existing batching and limit-bounded batching tests remain green.
- Risk: Diagnostics could expose page content. Mitigation: the new diagnostic includes only site/page context and the malformed pager scalar; tests use synthetic HTML and do not include real page content.
- Risk: Another digit-like Unicode category could behave differently than fullwidth digits. Mitigation: the code rejects any `str.isdigit()` value that does not match ASCII digits, covering fullwidth, superscript, Arabic-Indic, and similar digit glyphs.

## Dependencies

- BeautifulSoup continues to expose generated pager link text through `get_text(strip=True)`.
- Normal Wikidot recent-changes pager page labels are expected to be ASCII decimal digits.
- `Site.get_recent_changes(...)` continues to choose a structural pager outside edit-comment cells before page-number parsing.
- Recent-changes response body validation continues to run before pager and row parsing.

## Open Questions

None for this local slice. Future recent-changes pagination changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Recent-changes pagination is a browser-free acquisition boundary. Unicode digit normalization can silently turn malformed generated pager text into a valid-looking page request, which is surprising and hard to diagnose in site monitoring, moderation summaries, migration checks, publication audits, or generated recent-change ledgers. Requiring ASCII digits keeps generated pagination strict while preserving valid Wikidot pager behavior and existing parser diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit pager text was accepted and normalized into page `2`.
- Existing local drafts covered recent-changes retries, batched pagination, limit validation, comment scoping, comment-pager filtering, text fidelity, response-body diagnostics, row parser diagnostics, typed scalar diagnostics, direct `SiteChange` fields, and adjacent response-wide pager-page fixes; they did not validate Unicode digit normalization in structural recent-changes pager labels.
- This slice does not change request module names, retry policy, valid ASCII pagination, first-page parsing, paginated response-body diagnostics, row parsing, edit-comment pager scoping, page/search workflows, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated HTML from real accounts, real account names, real page content, private site data, and private page source out of upstream discussion.
