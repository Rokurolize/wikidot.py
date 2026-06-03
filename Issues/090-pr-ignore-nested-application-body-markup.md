# PR Draft: Ignore Nested Site Application Body Markup

## Summary

`SiteApplication.acquire_all(...)` parses pending membership applications returned by `managesite/ManageSiteMembersApplicationsModule`.

Before this fix, the parser found application headers with response-wide `h3` and descendant `span.printuser` selectors. If a user-authored application body rendered an application-like `h3` with a `span.printuser` and a following table, that body markup was parsed as a second pending application. The same parsing path also read all descendant `td` elements from the text table instead of the structural first row cells.

This fix keeps the existing header-to-next-table pairing model, but only accepts application headers that are outside application text tables and whose `span.printuser` is a direct header child. It also reads the application text from the direct cells of the direct first row of the matching table. Application-like markup inside the applicant's message no longer creates extra `SiteApplication` objects, while empty-list behavior, forbidden-page detection, retry exhaustion handling, real multi-application mismatch detection, and accept/decline actions remain unchanged.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), because pending-application acquisition is the public fetch path affected by this parser. It also follows the site-application improvement line in [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md) and [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md). The parser-boundary motivation matches the authored-content fixes in [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), and [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md).

No upstream issue was filed from this local workspace.

## Changes

- Ignore candidate application `h3` headers that are nested inside a table.
- Parse applicant user metadata from a direct `span.printuser` child of the application header.
- Parse application text from direct cells in the direct first row of the associated text table.
- Add a public `SiteApplication.acquire_all(...)` regression test where the application body contains an application-like nested header and table.
- Preserve empty application lists, forbidden access detection, retry exhaustion errors, duplicate text-table mismatch detection, normal application parsing, and accept/decline actions.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Pending-application headers should come from structural application headers, not application body content. | `TestSiteApplicationAcquireAll.test_acquire_all_ignores_application_like_body_markup` asserts only one application is returned and `user_parser` is called once. | The RED test failed before the fix because two applications were returned; the second came from the nested body header/table. |
| Application text should be parsed from the structural first row cells of the associated text table. | The same regression keeps the real application text on the structural application and avoids treating nested body table cells as another application record. | Descendant `td` parsing or body-header parsing that changes the application count rejects the local completion claim. |
| Public pending-application behavior should remain green. | `uv run pytest tests/unit/test_site_application.py -q` passed 18 tests. | Regressions in retry handling, empty-list handling, forbidden detection, malformed table errors, or accept/decline behavior reject the local completion claim. |
| Adjacent site-facing behavior stays green. | `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 98 tests. | Site property or member-list regressions reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `0c75d21 fix(site_application): ignore nested application body markup`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_ignores_application_like_body_markup -q` failed before the fix because `len(applications)` was `2` instead of `1`.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_ignores_application_like_body_markup -q`
- `uv run pytest tests/unit/test_site_application.py -q` passed 18 tests.
- `uv run pytest tests/unit/test_site_application.py tests/unit/test_site.py tests/unit/test_site_member.py -q` passed 98 tests.
- `uv run pytest tests/unit -q` passed 642 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH in earlier checks.

## Acceptance Criteria

- Pending site applications are parsed from structural application headers outside the application text table.
- Applicant user metadata is parsed from the direct `span.printuser` child of that structural header.
- Application text is parsed from the direct second cell of the direct first row of the matching text table.
- An application body that renders a nested `h3 span.printuser` plus a following table does not create an additional `SiteApplication`.
- Existing empty-list behavior, forbidden-page detection, retry exhaustion handling, malformed-table errors, mismatch detection, normal application parsing, and accept/decline actions remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Membership application messages are user-authored content. The parser should treat the membership-application module's structural `h3` plus following text table as the metadata boundary instead of selecting every descendant application-like header in the response. Scoping the parser prevents applicant text from changing the number of pending applications returned by the public API while preserving the current acquisition and moderation flow.

## Local Evidence, Not For Upstream Paste

- The rollout ledger for this research run records broad practical `wikidot.py` usage and a high candidate-thread count, including site administration and membership-management paths as practical local usage surfaces.
- Earlier site-application drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), and [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md) established pending membership applications as an actively hardened local path.
- Parser-boundary drafts [081-pr-ignore-forum-content-pseudo-posts.md](081-pr-ignore-forum-content-pseudo-posts.md), [082-pr-ignore-content-edit-metadata.md](082-pr-ignore-content-edit-metadata.md), [083-pr-ignore-content-post-containers.md](083-pr-ignore-content-post-containers.md), [084-pr-scope-thread-list-metadata.md](084-pr-scope-thread-list-metadata.md), [085-pr-scope-forum-revision-metadata.md](085-pr-scope-forum-revision-metadata.md), [086-pr-ignore-nested-category-tables.md](086-pr-ignore-nested-category-tables.md), [087-pr-ignore-nested-thread-tables.md](087-pr-ignore-nested-thread-tables.md), [088-pr-scope-thread-detail-statistics.md](088-pr-scope-thread-detail-statistics.md), and [089-pr-scope-private-message-detail-header.md](089-pr-scope-private-message-detail-header.md) established the concrete failure pattern: authored content can collide with structural parser selectors.
- The refreshed complexity scan continues to treat broad BeautifulSoup descendant parsing as an audit-worthy area in this codebase.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, and saved application text out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry behavior, empty-list handling, permission mapping, status text, or application accept/decline actions. It only narrows pending-application list parsing to structural headers and direct text-table cells.
