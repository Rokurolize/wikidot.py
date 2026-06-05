# PR Draft: Report Malformed Site Application Response Body Types

## Summary

`SiteApplication.acquire_all(site)`, also exposed through `site.applications`, parses `managesite/ManageSiteMembersApplicationsModule` AMC response `body` values as generated pending-application HTML. Earlier local slices made site-application list reads retry-aware, reused the successful response body, ignored nested application-like body markup, preserved application text spacing, added malformed application structure context, validated missing response `body` fields, guarded applicant user parsing, and validated accept/decline action responses. One adjacent response-boundary gap remained: if the decoded AMC response was a dictionary with a present but non-string `body` value, the code passed that value into BeautifulSoup and leaked a low-level parser `AttributeError`.

This local slice validates present site-application list response `body` values before forbidden-page detection and HTML parsing. Non-string bodies now raise site-specific `NoElementException` with `field=body`, expected type, and observed type. The diagnostic reports only compact structural context and type names; it does not include raw application HTML, response JSON, local rollout paths, credentials, account material, applicant messages, or private member data.

## Outcome

Malformed site-application list response body types now fail at the module response boundary with actionable site/type context instead of BeautifulSoup internals.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free pending-application review, membership workflows, or moderation tooling.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [177-pr-site-application-fetch-failure-context.md](177-pr-site-application-fetch-failure-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), and [308-pr-site-application-user-context.md](308-pr-site-application-user-context.md). Those drafts established pending site applications as a practical retry-aware, parser-scoped, and diagnosable administrative read/action path while leaving present non-string response bodies as a separate parser-entry boundary.

No upstream issue was filed from this local workspace.

## Changes

- Validate site-application list response `body` values are strings before forbidden-page detection and BeautifulSoup parsing.
- Convert present non-string application-list body values into site-specific `NoElementException`.
- Preserve missing-body diagnostics, retry-exhausted behavior, forbidden detection, empty-list behavior, structural application parsing, application text extraction, malformed applicant diagnostics, accept/decline behavior, and member-cache invalidation behavior.

## Type Of Change

- Bug fix / diagnostics improvement
- Site application response-body type validation
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A site-application list response with a present non-string `body` field must fail before forbidden detection or BeautifulSoup parsing. |
| R2 | Malformed-body-type errors must identify the affected site, `field=body`, expected type, and observed type while omitting raw generated application content. |
| R3 | Existing missing-body diagnostics, retry handling, application parsing, adjacent site/member workflows, and repository quality gates must remain compatible. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `SiteApplication.acquire_all(site)` raises contextual `NoElementException` when `managesite/ManageSiteMembersApplicationsModule` returns a list-valued `body`. | `TestSiteApplicationAcquireAll.test_acquire_all_malformed_response_body_type_includes_site_context` expects `Site application list response body is malformed for site: test-site (field=body, expected=str, actual=list)`. | Leaking BeautifulSoup `AttributeError`, silently returning an empty list, entering `user_parser`, or parsing an application record rejects this local completion claim. | Site application list reads | `tests/unit/test_site_application.py` |
| R2 | The malformed-body-type diagnostic includes only site, field name, expected type, and observed type. | The focused regression matches the full message shape and uses a synthetic list-valued body. | Including raw response JSON, generated application HTML, applicant messages, credentials, local rollout paths, account names, or private member data rejects this local completion claim. | Site application diagnostics | `src/wikidot/module/site_application.py` |
| R3 | Existing site-application and adjacent site/member behavior remains green. | The site-application suite passed 26 tests, the adjacent site/application/member run passed 146 tests, and the full unit suite passed 891 tests. | Regressing missing-body diagnostics, retry exhaustion, forbidden detection, empty lists, structural parsing, nested body-markup filtering, text spacing, malformed applicant diagnostics, accept/decline actions, site accessors, or member-list behavior rejects this local completion claim. | Site administration workflows | `tests/unit/test_site_application.py`; `tests/unit/test_site.py`; `tests/unit/test_site_member.py` |

## Testing

Implemented locally in commit `3ad1400 fix(site_application): report malformed body types`.

- RED: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_context -q` failed before the fix with BeautifulSoup `AttributeError` for the list-valued application-list body.
- GREEN: `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_context -q` passed.
- `uv run --extra test pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_malformed_response_body_type_includes_site_context tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_missing_response_body_includes_site_context tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_success tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_empty tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_raises_when_retry_is_exhausted tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_forbidden -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_site_application.py -q` passed 26 tests.
- `uv run --extra test pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 146 tests.
- `uv run --extra test pytest tests/unit -q` passed 891 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 80 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` failed because `pyright` was not installed in this environment.

## Acceptance Criteria

- Site-application list reads still request `managesite/ManageSiteMembersApplicationsModule` with the existing payload.
- Missing `body` fields still raise the existing not-found diagnostic from Issue 212.
- Present non-string `body` values raise contextual `NoElementException` before forbidden-page detection and BeautifulSoup parsing.
- The malformed-body-type message includes site, `field=body`, expected type, and observed type.
- The malformed-body-type message does not include raw response JSON, generated application HTML, applicant messages, credentials, local rollout paths, private member data, or private account material.
- Existing retry-exhausted behavior, forbidden detection, empty-list behavior, structural application parsing, nested body-markup filtering, text spacing, malformed applicant diagnostics, accept/decline behavior, and member-cache invalidation behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real application-list response body, local rollout path, account material, private member data, applicant messages, or generated application HTML is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Type validation could treat a future bytes-like body as malformed. Mitigation: AMC JSON bodies are expected to decode generated HTML as strings; preserving only string input keeps the parser boundary explicit.
- Risk: Type validation could mask missing-body diagnostics. Mitigation: `None` remains on the existing missing-body path; only present non-string values use the malformed-type diagnostic.
- Risk: Diagnostics could expose generated application content. Mitigation: messages include site and type names only.

## Dependencies

- The AMC connector already validates decoded response roots as dictionaries before normal module parsing; this slice targets the `body` field value within that dictionary.
- Site-application HTML parser behavior remains unchanged after a valid string body is supplied.

## Open Questions

None for this local slice. Remaining useful work should continue the broader response-body field-type audit across other modules rather than expanding this site-application change beyond its list boundary.

## Upstream-Safe Motivation

Pending application review is a practical browser-free site-administration workflow. If the generated application-list response contains a present non-string `body`, wikidot.py should report the affected site and type mismatch before BeautifulSoup internals obscure the failure.

## Local Evidence, Not For Upstream Paste

- The RED failure showed a list-valued application-list `body` leaking BeautifulSoup `AttributeError`.
- Existing Issue 212 covered missing `body` fields but intentionally left present malformed values as a separate boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated application HTML, applicant messages, and private member data out of upstream discussion.

## Additional Notes

This is a response-body field type diagnostics fix. It preserves valid site-application behavior while making malformed present response bodies actionable without retaining generated application content.
