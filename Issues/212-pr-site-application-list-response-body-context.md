# PR Draft: Validate Site Application List Response Bodies

## Summary

`SiteApplication.acquire_all(site)`, also exposed through `site.applications`, retrieves pending site join applications with `managesite/ManageSiteMembersApplicationsModule` and parses the generated manager page. Earlier local slices made that read retry-aware, reused the successful response body, rejected nested application-like body markup, preserved application text spacing, and added site/context diagnostics for malformed application markup. The remaining malformed response-body path still read `response.json()["body"]`, so an AMC response without a `body` field leaked a raw `KeyError` before the parser could report which site produced the malformed pending-application response.

This follow-up keeps the request module and payload, retry-exhausted `None` handling, forbidden-page detection, empty-list behavior, structural application parsing, nested body-markup filtering, application text spacing, parser context, and accept/decline actions unchanged. It only treats a missing application-list response `body` as a malformed list response and raises `NoElementException` with site context before forbidden detection, BeautifulSoup parsing, or application row parsing.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), and [177-pr-site-application-fetch-failure-context.md](177-pr-site-application-fetch-failure-context.md). Those drafts established pending site applications as a practical administrative read/action workflow and made the list acquisition path retry-aware, parser-scoped, and diagnosable.

No upstream issue was filed from this local workspace.

## Changes

- Add a small site application list response-body helper that reads `response.json().get("body")`.
- Convert missing application-list response `body` into site-specific `NoElementException`.
- Preserve retry-exhausted `None` response handling as an `UnexpectedException`.
- Preserve successful application parsing, forbidden-page detection, empty result handling, nested body-markup filtering, application text spacing, parser context, and accept/decline behavior.
- Add a focused regression for missing site application list response body handling through public `SiteApplication.acquire_all(site)`.

## Type Of Change

- Bug fix / diagnostics improvement
- Site application list response validation
- Test coverage

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A site application list response without JSON `body` still fails before forbidden detection, HTML parsing, or application parsing. | `TestSiteApplicationAcquireAll.test_acquire_all_missing_response_body_includes_site_context` returns `{}` from the application-list AMC response and expects `NoElementException`. | A change that raises raw `KeyError`, silently returns an empty list, or starts parser work rejects this local completion claim. |
| Malformed application-list response errors identify the affected site. | The focused regression asserts `Site application list response body is not found for site: test-site`. | A generic parser exception without site context rejects this local completion claim. |
| Retry-exhausted `None` application-list responses remain distinct from malformed JSON body responses. | Existing `test_acquire_all_raises_when_retry_is_exhausted` remains green and expects `UnexpectedException`. | A change that turns skipped/exhausted `None` responses into body-validation failures rejects this local completion claim. |
| Existing site application behavior remains green. | `uv run pytest tests/unit/test_site_application.py -q` passed 20 tests. | Regressions in successful parsing, forbidden handling, empty lists, nested body-markup filtering, text spacing, parser context, or accept/decline actions reject this local completion claim. |
| Adjacent site/member workflows remain green. | `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 117 tests. | Regressions in site accessors, recent changes, site members, or pending application workflows reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff format src tests`; `uv run ruff check src tests`; `uv run ruff format --check src tests`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4229fb7 fix(site_application): validate list response bodies`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_missing_response_body_includes_site_context -q` failed before the fix with `KeyError: 'body'`.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_missing_response_body_includes_site_context tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_success tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_empty tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_raises_when_retry_is_exhausted tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_forbidden -q` passed 5 tests.
- `uv run pytest tests/unit/test_site_application.py -q` passed 20 tests.
- `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 117 tests.
- `uv run pytest tests/unit -q` passed 747 tests.
- `uv run ruff format src tests` reformatted one changed test/source file and left 79 files unchanged.
- `uv run ruff check src tests`.
- `uv run ruff format --check src tests`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- Site application list requests still use `managesite/ManageSiteMembersApplicationsModule`.
- Missing application-list response JSON `body` raises `NoElementException` naming the site.
- Missing response-body handling does not convert retry-exhausted `None` responses into malformed-body failures.
- Successful application parsing, forbidden-page detection, empty application lists, nested application-body filtering, text spacing, parser context, and accept/decline behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Pending site application inspection depends on Wikidot returning a JSON `body` field for the generated management module. If that field is missing, wikidot.py should report a structured malformed-response failure with the site name, not a raw dictionary `KeyError`, so caller logs can route the failure without preserving raw response JSON, generated management HTML, applicant messages, credentials, local rollout paths, or account details.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established pending site application acquisition as retry-aware, parser-scoped, and used through both `SiteApplication.acquire_all(site)` and `site.applications`.
- Recent response-body validation slices in private-message, forum-post, and forum-category modules showed the same raw `KeyError` failure mode at AMC response-body boundaries.
- The refreshed complexity memo continues to list raw response-body boundaries in `forum_thread`, `site_member`, `page_file`, `page_revision`, `forum_post_revision`, `page`, and `site` as follow-up leads, but this slice only claims site application list response-body validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw response JSON, generated manager-page HTML, applicant messages, and private site/user data out of upstream discussion.

## Additional Notes

This slice intentionally does not change request module names, request payloads, retry policy, retry-exhausted `None` handling, forbidden detection, empty-list handling, application header selection, text extraction, parser context, `SiteApplication.accept()`, `SiteApplication.decline()`, or live Wikidot behavior. It only converts missing site application list response `body` fields into site-context `NoElementException` failures before parser work.
