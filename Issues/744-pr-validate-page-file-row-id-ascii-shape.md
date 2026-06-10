# PR Draft: Validate Page File Row ID ASCII Shape

## Summary

`PageFileCollection.acquire(page)` and `PageCollection.get_page_files()` parse generated `files/PageFilesModule` table rows whose structural IDs use the `file-row-<id>` form before creating `PageFile` records. Issue [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md) made present malformed row IDs such as `file-row-not-a-number` fail with site/page/row/value context, but the parser still used Python `str.isdigit()`. That allowed Unicode decimal digit glyphs such as `file-row-\uff11\uff10\uff10` to normalize into ordinary file ID `100`.

This change requires the `file-row-` ID token to match ASCII digits before integer conversion. Valid generated IDs such as `file-row-100` remain compatible, rows without a `file-row-` marker keep their existing skip behavior, and present non-ASCII digit payloads now raise the existing contextual malformed-row-ID `NoElementException`.

## Outcome

Browser-free page-file inventories no longer fabricate attachment identities by normalizing non-ASCII digit glyphs from generated table row IDs. The malformed-value diagnostic remains actionable and does not include raw generated page HTML.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using attached-file reads for browser-free asset inventories, generated attachment ledgers, migration audits, publication checks, file download reconciliation, cached page-file reuse, local fixtures, or lazy `Page.files` reads where generated `file-row-<id>` metadata is treated as durable attachment identity.

## Current Evidence

Local rollout-backed drafts repeatedly identify page attachments as a practical read surface. Existing drafts cover retry-aware page-file fetching, duplicate page-ID batching, parse reuse, cached duplicate reuse, direct cache behavior, parser scoping, response-body diagnostics, file name, MIME, size, link href diagnostics, row-ID context, href route validation, collection ownership, cache ownership, lookup validation, constructor validation, and blank-name validation.

This slice is not a duplicate of [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md). That issue made present non-numeric row IDs contextual instead of silently skipped, but it still allowed Python Unicode digit normalization. This slice also follows the newer ASCII scalar-shape boundary from [734-pr-validate-page-id-script-shape.md](734-pr-validate-page-id-script-shape.md), [735-pr-validate-site-id-script-shape.md](735-pr-validate-site-id-script-shape.md), and [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md).

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [095-pr-scope-page-file-row-parsing.md](095-pr-scope-page-file-row-parsing.md), [117-pr-preserve-page-file-name-spacing.md](117-pr-preserve-page-file-name-spacing.md), [274-pr-page-file-mime-title-context.md](274-pr-page-file-mime-title-context.md), [275-pr-page-file-size-context.md](275-pr-page-file-size-context.md), [276-pr-page-file-link-href-context.md](276-pr-page-file-link-href-context.md), [277-pr-page-file-name-context.md](277-pr-page-file-name-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [632-pr-validate-non-negative-page-file-sizes.md](632-pr-validate-non-negative-page-file-sizes.md), [739-pr-validate-page-file-link-href-routes.md](739-pr-validate-page-file-link-href-routes.md), and [743-pr-validate-forum-thread-script-id-ascii-shape.md](743-pr-validate-forum-thread-script-id-ascii-shape.md).

## Changes

- Require generated `file-row-<id>` ID tokens to match `[0-9]+` before `int(...)`.
- Preserve the existing site/page/row/value malformed-row-ID diagnostic.
- Preserve valid ASCII numeric row IDs such as `file-row-100`.
- Preserve existing skip behavior for rows without IDs, rows whose IDs do not start with `file-row-`, short rows, and rows without direct attachment anchors.
- Preserve existing file name, link href, MIME title, size, response-body, retry, caching, and adjacent page-file workflows.
- Add focused regression coverage for escaped fullwidth file ID text `\uff11\uff10\uff10`.

## Type Of Change

- Bug fix
- Generated row-ID scalar-shape validation
- Page-file parser hardening
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageFileCollection.acquire(page)` must reject a present `file-row-` ID token made of non-ASCII digit glyphs before creating a `PageFile`. |
| R2 | The malformed-row-ID error must preserve existing site, page, row, `field=id`, and observed value context. |
| R3 | Valid ASCII `file-row-100` IDs must continue to parse normally. |
| R4 | Existing `file-row-not-a-number` diagnostics from Issue 286 must remain compatible. |
| R5 | Existing non-file row skipping and adjacent page-file field diagnostics must remain compatible. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw generated page HTML from real sites, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, page-file tests, adjacent page workflow tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A row with `id="file-row-\uff11\uff10\uff10"` raises before returning a `PageFile`. | `test_acquire_rejects_non_ascii_digit_file_row_id` failed RED with `DID NOT RAISE`, then passed after ASCII-only validation. | Returning a `PageFile`, storing ID `100`, or treating the value as an absent row ID rejects this local completion claim. | Page-file row parser | `src/wikidot/module/page_file.py`, `tests/unit/test_page_file.py` |
| R2 | The diagnostic includes site, page, row, `field=id`, and the observed full row ID value. | The focused regression matches the existing malformed-row-ID message shape. | Dropping location context, replacing the branch with a generic `ValueError`, or omitting the observed row ID rejects this local completion claim. | Parser diagnostics | focused test |
| R3 | Valid generated ASCII file row IDs continue to work. | Focused GREEN included `test_acquire_success`; `tests/unit/test_page_file.py` passed. | Rejecting `file-row-100`, changing parsed fields, or changing file URL/name/MIME/size output rejects this local completion claim. | Valid row compatibility | page-file tests |
| R4 | Existing non-numeric row-ID diagnostics stay green. | Focused GREEN included `test_acquire_malformed_file_row_id_includes_page_row_and_value_context`. | Regressing `file-row-not-a-number` context or silently skipping present malformed row IDs rejects this local completion claim. | Prior malformed-value branch | page-file tests |
| R5 | Adjacent workflows remain green. | Page-file tests passed 123 tests, adjacent page/site/page-revision/page-votes coverage passed 1116 tests, and full unit passed 3745 tests. | Regressing parser scoping, file names, href validation, MIME parsing, size parsing, response-body handling, retry behavior, lazy `Page.files`, cached file reuse, page revision, page vote, or site workflows rejects this local completion claim. | Page-file and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed. | The regression uses synthetic unit-level table markup and mocked responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw generated HTML from real sites, file contents, page contents, private site data, or real account names rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, touched tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `1001572 fix(page_file): validate row id ascii shape`.

- RED: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_non_ascii_digit_file_row_id -q` failed before the fix with `DID NOT RAISE` because `file-row-\uff11\uff10\uff10` was accepted and normalized as file ID `100`.
- GREEN focused: `uv run --extra test pytest tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_rejects_non_ascii_digit_file_row_id tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_malformed_file_row_id_includes_page_row_and_value_context tests/unit/test_page_file.py::TestPageFileCollectionAcquire::test_acquire_success -q` passed 3 tests.
- `uv run --extra test pytest tests/unit/test_page_file.py -q` passed 123 tests.
- `uv run --extra test pytest tests/unit/test_page_file.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_revision.py tests/unit/test_page_votes.py -q` passed 1116 tests.
- `uv run --extra test pytest tests/unit -q` passed 3745 tests.
- `uv run --extra lint ruff check src tests` passed.
- `uv run --extra format ruff format --check src tests` passed with 87 files already formatted.
- `uv run --extra lint mypy src tests --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `PageFileCollection.acquire(page)` raises contextual `NoElementException` for a present generated row ID built from escaped fullwidth digit text `file-row-\uff11\uff10\uff10`.
- The same shared parser behavior is used by `PageCollection.get_page_files()`.
- Valid ASCII `file-row-100` rows still parse ID, name, relative/absolute URL, MIME title, and size as before.
- Existing `file-row-not-a-number` malformed-value diagnostics remain compatible.
- Rows with no row ID, rows whose ID does not start with `file-row-`, short rows, and rows without a direct attachment anchor keep their existing structural skip behavior.
- Existing response-body validation, retry behavior, file name, link href, MIME title, size, URL route validation, lazy `Page.files`, cached file reuse, page revision, page vote, site, and parser diagnostics remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated HTML from real sites, raw rollout path, file contents, page contents, real account name, or private site data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 286. Mitigation: Issue 286 covers present non-numeric values and missing-vs-malformed row separation; this slice covers Unicode digit normalization that still passes that branch.
- Risk: Tightening generated row-ID parsing could reject unusual but valid generated output. Mitigation: Wikidot file row IDs in existing fixtures are ordinary ASCII decimal digits, and valid `file-row-100` behavior remains tested.
- Risk: The change could alter permissive skip semantics for non-file rows. Mitigation: the parser still skips rows until the ID starts with `file-row-`; only the numeric token after that structural marker is stricter.
- Risk: Diagnostics could expose generated page content. Mitigation: the diagnostic includes only site/page, row number, field name, and the scalar row ID value, not raw response bodies, page source, file contents, credentials, cookies, local paths, or private account data.

## Dependencies

- Page-file module responses continue to expose attachment rows through `table.page-files > tbody > tr` with `file-row-<id>` structural IDs.
- `PageFileCollection.acquire(page)` and `PageCollection.get_page_files()` continue to share `_parse_file_fields_from_html(...)`.
- File name, URL, MIME, and size parsing remain downstream of a valid row ID.

## Open Questions

None for this local slice. Future scalar-shape work should be selected only with a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

Generated `file-row-<id>` values are attachment identity metadata for browser-free page-file inventories. Unicode digit normalization can silently turn malformed generated row metadata into a valid-looking file ID. Requiring ASCII digits keeps generated identity parsing strict and consistent with adjacent page/site/forum scalar-shape fixes while preserving existing valid numeric behavior and contextual malformed-value diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: escaped fullwidth digit row IDs were accepted and normalized to file ID `100`.
- Existing local drafts covered page-file retry behavior, duplicate page-ID batching, row parser scoping, present non-numeric row-ID context, field-level diagnostics, response-body diagnostics, direct cache behavior, cache ownership, lookup validation, blank-name validation, and link href route validation; they did not validate Unicode digit normalization in generated `file-row-<id>` scalars.
- This slice does not change request payloads, retry policy, response-body checks, row scoping, file URL normalization, MIME parsing, size parsing, file-name parsing, cached file reuse, lookup helpers, live Wikidot behavior, upstream filing state, or valid ASCII generated output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated page HTML from real sites, file contents, page source text, real usernames, and private site data out of upstream discussion.
