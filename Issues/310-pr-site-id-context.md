# PR Draft: Report Malformed Site IDs

## Summary

`Site.from_unix_name(...)` bootstraps a `Site` object from the Wikidot landing page by reading `WIKIREQUEST.info.siteId`, the page title, `siteUnixName`, and domain. Earlier local slices hardened many downstream generated-module parsers so present malformed scalar values fail with contextual diagnostics. One adjacent bootstrap gap remained: `siteId` was matched with a digit-only regex, so a present malformed assignment such as `WIKIREQUEST.info.siteId = latest;` was treated the same as a missing site ID and raised a generic `UnexpectedException` without the observed value.

This local slice keeps successful site bootstrap, missing site ID diagnostics, missing title diagnostics, missing unix-name diagnostics, missing domain diagnostics, redirect handling, and 404 handling unchanged. It captures present `siteId` assignments before integer conversion and raises `NoElementException` with the requested site host, `field=site_id`, and the observed value when the assignment is malformed.

## Outcome

Malformed landing-page site IDs now fail with value-aware bootstrap context instead of being reported as a missing site ID.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who create `Site` objects by UNIX name for browser-free site inspection, indexing, migration, moderation, or publishing-adjacent workflows.

## Related Issue

Builds on the scalar parser-boundary pattern from [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [240-pr-listpages-rating-parse-context.md](240-pr-listpages-rating-parse-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [283-pr-forum-post-revision-id-context.md](283-pr-forum-post-revision-id-context.md), [286-pr-page-file-row-id-context.md](286-pr-page-file-row-id-context.md), [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md), and [309-pr-page-discussion-thread-id-context.md](309-pr-page-discussion-thread-id-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Parse present `WIKIREQUEST.info.siteId` assignments with a value-capturing regex instead of a digit-only regex.
- Reject present non-numeric or empty site ID values with contextual `NoElementException`.
- Include the requested site host, `field=site_id`, and observed value in the parser error.
- Preserve `UnexpectedException` behavior for responses that contain no `siteId` assignment at all.
- Preserve redirect handling, 404 `NotFoundException`, valid SSL and non-SSL bootstrap, title/unix-name/domain parsing, and existing missing-field diagnostics.
- Add a focused public `Site.from_unix_name(...)` regression for `WIKIREQUEST.info.siteId = latest;`.

## Type Of Change

- Bug fix / diagnostics improvement
- Site bootstrap parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A landing-page response with a present non-numeric `WIKIREQUEST.info.siteId` assignment must fail at the `Site.from_unix_name(...)` parser boundary. |
| R2 | The malformed site ID error must identify the requested site host, affected field, and observed value. |
| R3 | A landing-page response without any `siteId` assignment must still use the existing missing-site-ID diagnostic. |
| R4 | Valid SSL and non-SSL site bootstrap, redirect handling, 404 handling, and title/unix-name/domain parsing must remain compatible. |
| R5 | Focused, site-level, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Site.from_unix_name(...)` raises `NoElementException` for `WIKIREQUEST.info.siteId = latest;`. | `TestSiteFromUnixName.test_from_unix_name_malformed_site_id_includes_raw_value_context` expects `NoElementException`. | Treating the malformed assignment as missing, leaking a raw scalar parse error, fabricating a site ID, or returning a `Site` rejects this local completion claim. | `src/wikidot/module/site.py` | `tests/unit/test_site.py` |
| R2 | The error names `bad-site.wikidot.com`, `field=site_id`, and `value=latest`. | The focused regression matches all fields. | Omitting the host, field, or observed value makes the failure ambiguous and rejects this local completion claim. | Site bootstrap diagnostics | `tests/unit/test_site.py` |
| R3 | Responses with no `siteId` assignment continue to raise the existing missing-site-ID `UnexpectedException`. | Existing `test_from_unix_name_missing_site_id` remained green. | Treating absent metadata as a malformed value would blur distinct failure modes and rejects this local completion claim. | Site bootstrap missing-field handling | `tests/unit/test_site.py` |
| R4 | Valid site bootstrap and adjacent failure modes remain green. | The full `TestSiteFromUnixName` class passed 9 tests and `test_site.py` passed 82 tests. | Regressing valid SSL/non-SSL bootstrap, redirects, 404 handling, missing title, missing unix-name, or missing domain rejects this local completion claim. | Site bootstrap workflow | `tests/unit/test_site.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `c998791 fix(site): report malformed site ids`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_malformed_site_id_includes_raw_value_context -q` failed before the fix with `UnexpectedException: Cannot find site id: bad-site.wikidot.com`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_malformed_site_id_includes_raw_value_context -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_site.py::TestSiteFromUnixName -q` passed 9 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 82 tests.
- `uv run --extra test pytest tests/unit -q` passed 868 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- A landing-page response whose present `WIKIREQUEST.info.siteId` value is non-numeric raises `NoElementException`.
- The malformed site ID message includes the requested site host, `field=site_id`, and observed value.
- Valid numeric site IDs still construct `Site.id` from the parsed integer.
- Responses without a `siteId` assignment still use the existing missing-site-ID failure path.
- Missing title, missing unix-name, missing domain, redirect handling, SSL detection, and 404 behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, generated landing-page HTML from real sites, credentials, cookies, auth JSON, or private site data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Treating absent site metadata as malformed could change the existing missing-field contract. Mitigation: this slice raises the new malformed-value error only when a `siteId` assignment is present.
- Risk: The wider regex could alter valid bootstrap parsing. Mitigation: existing SSL and non-SSL bootstrap tests remained green, and valid numeric values still route through `int(...)`.
- Risk: Diagnostics could expose page content. Mitigation: the error reports only the requested host, field name, and scalar value, not raw landing-page HTML.

## Dependencies

- Wikidot landing pages continue to expose site bootstrap metadata through `WIKIREQUEST.info.siteId = <id>;`.
- `Site.from_unix_name(...)` remains the source of truth for constructing a `Site` from a UNIX site name.
- Existing responses without a `siteId` assignment continue to represent a missing bootstrap field rather than a malformed scalar value.

## Open Questions

None for this local slice. A future cleanup could centralize small scalar context wrappers only if it removes duplication without hiding parser-specific diagnostics.

## Upstream-Safe Motivation

Site bootstrap is the entry point for many browser-free workflows. If Wikidot emits a present but malformed site ID, wikidot.py should fail with structured host-local diagnostics instead of reporting the value as missing. That keeps logs actionable without retaining raw landing-page HTML, credentials, local rollout paths, or private site data.

## Local Evidence, Not For Upstream Paste

- The direct scalar audit identified `Site.from_unix_name(...)` as one of the remaining `int(...)` bootstrap paths outside the already-covered generated-module parser slices.
- The immediate RED failure showed the existing digit-only regex skipped `WIKIREQUEST.info.siteId = latest;` and raised the missing-site-ID `UnexpectedException`.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated landing-page HTML, page source text, and private site data out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It preserves valid site bootstrap while preventing a malformed present site ID from losing the raw value that operators need for diagnosis.
