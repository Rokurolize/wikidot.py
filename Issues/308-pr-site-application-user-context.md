# PR Draft: Report Malformed Site Application Users

## Summary

`SiteApplication.acquire_all(...)`, exposed through `site.applications`, parses pending join applications returned by `managesite/ManageSiteMembersApplicationsModule`. Earlier local slices made that read retry-aware, reused the successful response body, ignored nested application-like body markup, preserved application text spacing, reported malformed application text/table structure with site and application position context, validated missing list response bodies, and guarded accept/decline action status responses. One adjacent parser-boundary gap remained: when a structural application header contained a present `span.printuser` with malformed generated user metadata, the shared `user_parse(...)` utility raised raw `ValueError` without the affected site, application index, field, or observed metadata value.

This local slice keeps successful pending-application parsing and the shared `user_parse(...)` utility unchanged. It catches malformed applicant `span.printuser` metadata at the site-application parser boundary and raises `NoElementException` with site unix name, application index, total application count, `field=user`, and the offending direct user `onclick` value or fallback rendered text.

## Outcome

Malformed pending-application applicant values now fail with site-application-local context instead of leaking a raw shared user parser exception.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who inspect pending site join applications, moderate membership queues, or run browser-free site administration reports.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), and [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md). Those drafts established pending site applications as a practical read/action workflow and made the list acquisition path retry-aware, parser-scoped, diagnosable, and action-safe.

This slice also follows the shared user parser-boundary pattern from [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), and the shared parser validation slices [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md) and [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small applicant user parser wrapper that raises contextual `NoElementException` on malformed generated `span.printuser` values.
- Include site unix name, application index, total application count, `field=user`, and the observed direct user `onclick` value or fallback rendered text in the parser error.
- Keep the existing application parse context helper as the source of application position diagnostics.
- Preserve successful pending-application parsing, forbidden detection, empty-list behavior, structural header filtering, nested application body-markup filtering, application text spacing, text table/row/cell diagnostics, mismatch diagnostics, response-body diagnostics, accept/decline action handling, and member-cache invalidation behavior.
- Add a focused public `SiteApplication.acquire_all(...)` regression for a malformed applicant `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Site-application parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated pending-application response with a malformed present applicant `span.printuser` must fail at the site-application parser boundary. |
| R2 | The malformed applicant error must identify the affected site, application index, total application count, field, and observed direct user metadata value. |
| R3 | Existing valid application user parsing, application text extraction, structural parser boundaries, response-body validation, mismatch diagnostics, and text-cell diagnostics must remain compatible. |
| R4 | Existing accept/decline action behavior, action-status validation, retry-aware list fetching, forbidden handling, empty-list behavior, and member-cache invalidation must remain unchanged. |
| R5 | Focused, site-application, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `SiteApplication.acquire_all(site)` raises `NoElementException` for `userInfo(latest)` in a structural application header applicant. | `TestSiteApplicationAcquireAll.test_acquire_all_malformed_user_includes_site_application_and_value_context` expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, silently skipping the application, or returning a malformed `SiteApplication` rejects this local completion claim. | `src/wikidot/module/site_application.py` | `tests/unit/test_site_application.py` |
| R2 | The error names `site: test-site`, `application=1`, `applications=1`, `field=user`, and `value=WIKIDOT.page.listeners.userInfo(latest); return false;`. | The focused regression matches all fields. | Omitting site, application position, total count, field name, or the bad direct user metadata value makes the failure ambiguous and rejects this local completion claim. | Applicant diagnostics | `tests/unit/test_site_application.py` |
| R3 | Valid application rows still parse, application text spacing remains preserved, missing response bodies still use site context, malformed text cells still use application context, and duplicate text-table mismatches still fail with counts. | The site-application suite passed 25 tests. | Regressing structural header filtering, text extraction, response-body validation, mismatch behavior, or text-cell diagnostics rejects this local completion claim. | Application list parser | `tests/unit/test_site_application.py` |
| R4 | Application action helpers and adjacent member workflows stay compatible. | The full unit suite covers accept/decline action payloads, action-status validation, cache invalidation, site members, invitations, and user parser callers. | Regressing action payload construction, status handling, retry use, forbidden detection, empty applications, or member cache behavior rejects this local completion claim. | Application workflows | `tests/unit/test_site_application.py`, `tests/unit/test_site_member.py`, `tests/unit/test_site.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `80f3a32 fix(site_application): report malformed application users`.

- RED: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_user_includes_site_application_and_value_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_user_includes_site_application_and_value_context -q` passed 1 test.
- `uv run --extra test pytest tests/unit/test_site_application.py -q` passed 25 tests.
- `uv run --extra test pytest tests/unit -q` passed 866 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy src` passed with no issues in 35 source files.
- `git diff --check` passed.

Not run successfully: `pyright` was unavailable in this environment; `command -v pyright` returned no executable path.

## Acceptance Criteria

- A generated pending-application response whose structural applicant `span.printuser` value has malformed user metadata raises `NoElementException`.
- The malformed applicant message includes the site `unix_name`, application index, total application count, `field=user`, and observed direct user metadata value.
- Valid pending-application applicants still parse through `user_parse(...)`.
- Successful application parsing, structural header filtering, nested body-markup filtering, application text spacing, text table/row/cell diagnostics, mismatch diagnostics, response-body diagnostics, retry behavior, forbidden detection, empty-list behavior, accept/decline action handling, and member-cache invalidation behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated application HTML from real sites, applicant text from real sites, credentials, cookies, auth JSON, or private site/member data is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected applicant parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only site/application location metadata.
- Risk: Changing the shared user parser could affect unrelated modules. Mitigation: this slice intentionally leaves `user_parse(...)` unchanged and validates adjacent parser behavior through the site-application suite and full unit suite.
- Risk: Application body markup can render user-authored HTML that resembles generated application structure. Mitigation: this slice uses the already-scoped structural application headers and direct applicant `span.printuser` elements without broadening selectors.
- Risk: Diagnostics could expose sensitive applicant text. Mitigation: the error reports only structural site/application position and generated user metadata value, not the application message body.

## Dependencies

- BeautifulSoup continues to expose structural pending-application headers as direct `h3` elements with direct `span.printuser` children.
- The shared `user_parse(...)` utility remains the source of truth for valid Wikidot user metadata extraction.
- Pending-application responses continue to pair each structural application header with the following application text table.

## Open Questions

None for this local slice. Broader centralization of repeated user value wrappers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

Pending site applications are an administrative workflow where malformed generated user metadata can appear in logs without the raw manager-page HTML. wikidot.py should report a structured parser error naming the affected site, application position, field, and observed metadata value instead of leaking a generic shared helper exception. That keeps moderation and browser-free administration logs actionable without retaining raw application HTML, applicant messages, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified pending site application acquisition and processing as practical workflow surfaces by improving retry behavior, response reuse, parser scoping, text spacing, malformed markup diagnostics, action-status validation, and member-cache behavior.
- Recent user parser-boundary drafts validated the same shared `user_parse(...)` failure pattern in site members, forum thread lists, forum thread details, forum post lists, forum post edit metadata, recent changes, page revisions, ListPages fields, and WhoRated voters.
- The immediate RED failure showed the same raw `ValueError` class that prior parser-boundary user slices converted in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated application HTML, applicant messages, private site names, and private member data out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding site-application parser diagnostics.
