# PR Draft: Validate Recent Change Title Href Routes

## Summary

`Site.get_recent_changes(...)` parses generated `changes/SiteChangesListModule` rows into `SiteChange` records and derives `SiteChange.page_fullname` from the title anchor `href`. Earlier local slices reject missing or blank title hrefs, root hrefs that normalize to an empty page fullname, and empty rendered page titles. One adjacent route-boundary gap remained: a present title href such as a foreign absolute URL, an `http:` URL without a host, a `javascript:` URL, or a query/fragment-only href could still become the stored page fullname because the parser only used `href.strip().strip("/")`.

This change parses recent-change title hrefs with `urlsplit(...)`, rejects malformed route shapes before constructing `SiteChange`, and normalizes same-site absolute page URLs to their path-derived page fullname. Valid relative page hrefs remain compatible.

## Outcome

Recent-change rows no longer store foreign URLs, non-page schemes, hostless HTTP URL text, or query/fragment-only hrefs as page identities, while valid same-site absolute and relative page links still produce the expected `SiteChange.page_fullname`.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)` for browser-free change monitoring, moderation dashboards, migration checks, publication audits, generated recent-change ledgers, local fixtures, or follow-up page/source reads keyed by `SiteChange.page_fullname`.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent changes as a practical read surface. [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), [631-pr-validate-blank-site-change-page-fullnames.md](631-pr-validate-blank-site-change-page-fullnames.md), and [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md) establish recent-change fetching, parser scoping, text fidelity, response diagnostics, value validation, and direct record invariants as active operational boundaries.

This slice is not a duplicate of Issue 278, which rejects missing or blank title hrefs. It is not a duplicate of Issue 279, which rejects present hrefs that normalize to an empty page name such as `/`. It is not a duplicate of Issue 280, which rejects empty rendered page titles. It is not a duplicate of Issue 725, which validates recent-change revision cell shape, or Issue 631, which validates direct `SiteChange.page_fullname` blankness after parser output exists.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [725-pr-validate-recent-change-revision-cell-shape.md](725-pr-validate-recent-change-revision-cell-shape.md), and the recent-change parser/read-boundary drafts listed in Current Evidence.

## Changes

- Add a route parser for recent-change title hrefs using `urlsplit(...)`.
- Reject non-HTTP schemes such as `javascript:`.
- Reject `http` or `https` hrefs that lack a host.
- Reject absolute hrefs whose host does not match `site.domain`, case-insensitively.
- Reject query-only and fragment-only hrefs before they can become page names.
- Preserve the existing `Page fullname is not found ...` branch for root links such as `/`.
- Normalize valid same-site absolute page URLs by using the path portion and dropping query/fragment suffixes.
- Preserve valid relative page hrefs and successful recent-change parsing.
- Preserve existing title text extraction, missing href validation, empty page-fullname validation, empty title validation, revision parsing, timestamp parsing, user parsing, flag extraction, comment parsing, retry handling, pagination, limit handling, and `SiteChange` constructor invariants.

## Type Of Change

- Bug fix
- Recent-change parser route-shape validation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A foreign absolute recent-change title href must fail before constructing `SiteChange`. |
| R2 | An `http` or `https` title href without a host must fail before constructing `SiteChange`. |
| R3 | A title href with a non-page scheme such as `javascript:` must fail before constructing `SiteChange`. |
| R4 | Query-only and fragment-only title hrefs must fail before constructing `SiteChange`. |
| R5 | Malformed title-href route errors must include site unix name, recent-changes page number, change index, `field=href`, and the observed href value. |
| R6 | A same-site absolute page URL must normalize to the same `page_fullname` as its path-only form, ignoring query/fragment suffixes. |
| R7 | Existing valid relative page hrefs, missing href errors, root href errors, empty title errors, revision/timestamp/user parsing, retry, pagination, limit, comment, flag, and adjacent site/page workflows must remain compatible. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw recent-change bodies, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, full site tests, adjacent recent-change/site/page/user-parser/odate/client/Ajax/requestutil tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `http://example.com/test:test-page` and `https://other.wikidot.com/test:test-page` raise `NoElementException` before `SiteChange` construction. | Focused RED failed because both malformed hrefs returned changes instead of raising; focused GREEN passed after route parsing. | Storing a foreign URL or its path as `SiteChange.page_fullname` rejects this local completion claim. | Recent-change parser | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | `http:test:test-page` raises the contextual malformed-href error. | The parametrized malformed-route regression covers hostless HTTP. | Treating hostless HTTP text as a relative page name rejects this local completion claim. | Recent-change parser | site tests |
| R3 | `javascript:alert(1)` raises the contextual malformed-href error. | The parametrized malformed-route regression covers non-HTTP schemes. | Storing `alert(1)` or the full `javascript:` URL as page identity rejects this local completion claim. | Recent-change parser | site tests |
| R4 | `#test:test-page` and `?page=test:test-page` raise the contextual malformed-href error. | The parametrized malformed-route regression covers fragment-only and query-only hrefs. | Turning fragment/query payload into page identity, or falling through to an unrelated diagnostic, rejects this local completion claim. | Recent-change parser | site tests |
| R5 | Malformed route diagnostics include site, page, change, field, and raw href value. | The regression asserts `Page fullname href is malformed for site: test`, `(page=1, change=1, field=href`, and `value=<href>`. | Omitting the observed href or the row location rejects this local completion claim. | Parser diagnostics | site tests |
| R6 | `https://test.wikidot.com/test:test-page?from=changes#edit` produces `page_fullname == "test:test-page"`. | Focused RED failed because the parser stored the full URL; focused GREEN passed after path normalization. | Storing the absolute URL, preserving query/fragment in `page_fullname`, or rejecting a same-site absolute page URL rejects this local completion claim. | Recent-change parser compatibility | site tests |
| R7 | Existing recent-change and adjacent workflows remain green. | Focused nearby tests, full `test_site.py`, adjacent site/page/parser/client/Ajax/requestutil tests, and full unit tests passed. | Regressing valid relative page hrefs, missing/empty href diagnostics, title parsing, revision/timestamp/user parsing, retry, pagination, limit, comments, flags, or adjacent page/site workflows rejects this local completion claim. | Recent-change workflow | `tests/unit` |
| R8 | No live site state or private material is needed. | All regressions use synthetic recent-change HTML and mocked AMC responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page names, private comments, page source, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b98244c fix(site): validate recent change title href routes`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_malformed_page_href_routes tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_accepts_same_site_absolute_page_href -q` failed before the fix with 5 `DID NOT RAISE` malformed-route cases and one full-URL `page_fullname` assertion failure.
- GREEN focused: `uv run pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_malformed_page_href_routes tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_accepts_same_site_absolute_page_href tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_missing_title_href_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_empty_page_fullname_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_empty_page_title_includes_site_page_and_item_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_rejects_revision_number_with_trailing_text -q` passed 12 tests.
- `uv run pytest tests/unit/test_site.py -q` passed 361 tests.
- `uv run pytest tests/unit/parsers/test_user_parser.py tests/unit/parsers/test_odate_parser.py tests/unit/test_site.py tests/unit/test_page.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_client.py tests/unit/test_ajax.py tests/unit/test_requestutil.py -q` passed 1173 tests.
- `uv run pytest tests/unit -q` passed 3716 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Site.get_recent_changes(...)` raises a contextual `NoElementException` for `http://example.com/test:test-page`.
- `Site.get_recent_changes(...)` raises the same diagnostic family for `https://other.wikidot.com/test:test-page`.
- `Site.get_recent_changes(...)` raises the same diagnostic family for `http:test:test-page`.
- `Site.get_recent_changes(...)` raises the same diagnostic family for `javascript:alert(1)`.
- `Site.get_recent_changes(...)` raises the same diagnostic family for `#test:test-page`.
- `Site.get_recent_changes(...)` raises the same diagnostic family for `?page=test:test-page`.
- The malformed-href error includes site unix name, recent-changes page, change index, `field=href`, and the raw href value.
- A same-site absolute href such as `https://test.wikidot.com/test:test-page?from=changes#edit` produces `SiteChange.page_fullname == "test:test-page"`.
- Valid relative page href parsing remains unchanged.
- Existing missing title href, root href, empty page title, title/comment spacing, revision, timestamp, user, flags, comments, retry, pagination, limit, response-body, and direct `SiteChange` validation behavior remains unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw real recent-change HTML, local rollout path, private page name, private comment, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening title href route parsing could reject an unusual but valid generated Wikidot link. Mitigation: valid relative hrefs remain compatible, same-site absolute URLs are supported, and query/fragment suffixes are ignored only after a real page path is present.
- Risk: Host comparisons could be case-sensitive. Mitigation: the implementation compares parsed URL hostnames to `site.domain` case-insensitively.
- Risk: This could blur previous missing/root href diagnostics. Mitigation: missing or blank hrefs still use `Title href is not found ...`; root hrefs such as `/` still use `Page fullname is not found ...`; only malformed present route shapes use `Page fullname href is malformed ...`.
- Risk: Diagnostics could expose raw recent-change HTML. Mitigation: the new diagnostic reports only the scalar href value plus site/page/change/field context, not full response bodies, credentials, cookies, local paths, page source, or private comments.

## Dependencies

- Recent-change title anchors continue to identify changed pages through local or same-site page hrefs.
- `site.domain` remains the canonical host for same-site absolute links.
- `Site.get_recent_changes(...)` remains the source of truth for generated recent-change parsing.

## Open Questions

None for this local slice. Future recent-change parser changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

`SiteChange.page_fullname` is the key that downstream callers use to connect a recent-change row to later page reads, source checks, publication audits, and moderation reports. A foreign URL, non-page scheme, hostless HTTP URL, or query/fragment-only href is not a page identity for the current site. Structured route parsing keeps malformed generated markup visible while preserving valid relative and same-site page links.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior for the initial route set: five malformed present hrefs did not raise, and a same-site absolute URL was stored as a full URL instead of its path-derived page fullname. The final focused GREEN keeps those cases plus the hostless HTTP variant covered in the same malformed-route regression.
- Existing local drafts covered recent-change fetch retry, pagination, comment/title text fidelity, missing hrefs, root hrefs, empty titles, revision/timestamp/user diagnostics, response-body typing, limit validation, direct row invariants, and retained actor identity; they did not validate present href route shape.
- This slice does not change request payloads, retry policy, pagination math, title text extraction, comment extraction, user parser semantics, timestamp parser semantics, revision parser semantics, flag-code semantics, direct `SiteChange` constructor rules, live Wikidot behavior, upstream filing state, or valid relative recent-change output.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML from real sites, saved page contents, page source, private page names, private edit comments, and private site data out of upstream discussion.
