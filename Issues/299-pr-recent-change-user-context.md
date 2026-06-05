# PR Draft: Report Malformed Recent Change Users

## Summary

`Site.get_recent_changes(...)` parses generated recent-change markup from `site/RecentChangesModule`. Earlier local slices made this read path retry-aware, batched paginated fetches, ignored nested comment markup, preserved title/comment spacing, validated missing response bodies, rejected missing or empty title links, rejected empty page fullnames and titles, and converted malformed revision numbers and `span.odate` timestamp classes into contextual `NoElementException` failures. One adjacent parser-value gap remained in the same generated metadata row: when the direct `td.mod-by > span.printuser` change author was present but its user ID metadata could not be parsed, the shared `user_parse(...)` utility raised raw `ValueError` without identifying the site, recent-change page, structural change position, affected field, or observed `onclick` value.

This follow-up keeps the shared `user_parse(...)` utility unchanged and catches malformed structural recent-change author metadata at the recent-change parser boundary. It raises `NoElementException` with site unix name, recent-change page number, structural change position, `field=changed_by`, and the offending direct `onclick` value. Valid recent-change parsing, valid user parsing, timestamp diagnostics, revision diagnostics, title/fullname diagnostics, comment filtering, pagination, retry behavior, limit handling, response-body diagnostics, flags parsing, and `SiteChange` construction remain unchanged.

## Outcome

Malformed present change-author metadata in a generated recent-change row is now reported as a recent-change parser failure instead of a raw shared-parser failure.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)` for browser-free site audit trails, change ledgers, archival indexing, moderation checks, source verification, or publication monitoring.

## Related Issue

Builds on [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [091-pr-scope-recent-changes-comment-markup.md](091-pr-scope-recent-changes-comment-markup.md), [099-pr-ignore-recent-change-comment-pager-markup.md](099-pr-ignore-recent-change-comment-pager-markup.md), [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), [115-pr-preserve-recent-change-title-spacing.md](115-pr-preserve-recent-change-title-spacing.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), and [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md). Those drafts established recent changes as a practical, retry-aware, parser-scoped read path. This slice follows the shared user parser-boundary pattern from [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), and [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md).

No upstream issue was filed from this local workspace.

## Changes

- Convert malformed present recent-change author `printuser` metadata from raw `ValueError` into contextual `NoElementException`.
- Include site unix name, recent-change page number, structural change position, `field=changed_by`, and the observed direct `onclick` value in the parser error.
- Preserve the shared `user_parse(...)` utility behavior and parser tests.
- Preserve successful `Site.get_recent_changes(...)` parsing, valid `SiteChange.changed_by` construction, pagination, retry handling, limit handling, response-body diagnostics, title/fullname diagnostics, revision diagnostics, timestamp diagnostics, comment filtering, flags parsing, and nested markup filtering.
- Add a focused public `Site.get_recent_changes(...)` regression for a malformed `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Recent-change parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A structural recent-change row with malformed present `changed_by` `printuser` metadata must fail at the recent-change parser boundary. |
| R2 | The malformed change-author error must identify the affected site, recent-change page, structural change position, field, and observed direct `onclick` value. |
| R3 | Existing valid recent-change parsing and shared user parsing must remain compatible. |
| R4 | Existing recent-change response handling, retries, pagination, limit handling, comment filtering, title/fullname diagnostics, revision diagnostics, timestamp diagnostics, and flags parsing must remain unchanged. |
| R5 | Broad unit, lint, format, type, and whitespace gates must remain green before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `Site.get_recent_changes()` raises `NoElementException` for `userInfo(latest)` in the structural recent-change author element. | `TestSiteGetRecentChanges.test_get_recent_changes_malformed_user_includes_raw_onclick_context` returns a recent-change page and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, skipping the change row, or returning a malformed `SiteChange` rejects this local completion claim. | `src/wikidot/module/site.py` | `tests/unit/test_site.py` |
| R2 | The error names site, page, structural change position, `field=changed_by`, and the bad direct `onclick` value. | The focused regression asserts `Recent change user is malformed for site: test (page=1, change=1, field=changed_by, value=WIKIDOT.page.listeners.userInfo(latest); return false;)`. | Omitting any location field, reporting the wrong field, using only rendered user text, or hiding the raw `onclick` value makes the failure ambiguous and rejects this local completion claim. | Recent-change diagnostics | `tests/unit/test_site.py` |
| R3 | Valid recent-change rows still parse through the existing public API and shared user parser. | Focused GREEN includes successful recent-change parsing and nested comment-markup filtering; the whole `test_site.py` file passed 81 tests. | Regressing page fullname, title, revision number, author, timestamp, flags, comment text, order, or collection length rejects this local completion claim. | `Site.get_recent_changes(...)` | `tests/unit/test_site.py` |
| R4 | Adjacent recent-change behaviors stay green. | Focused GREEN includes malformed timestamp context, malformed revision context, successful parsing, comment filtering, and paginated batching; full unit passed 856 tests. | Regressing response-body context, retry behavior, pagination, limit clipping, comment pager filtering, title/fullname validation, revision diagnostics, timestamp diagnostics, or flags parsing rejects this local completion claim. | Recent-change workflows | `tests/unit/test_site.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d16fbf1 fix(site): report malformed recent change users`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_user_includes_raw_onclick_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run --extra test pytest tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_user_includes_raw_onclick_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_odate_includes_raw_class_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_malformed_revision_number_includes_raw_value_context tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_success tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_ignores_comment_change_like_markup tests/unit/test_site.py::TestSiteGetRecentChanges::test_get_recent_changes_batches_paginated_pages -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_site.py -q` passed 81 tests.
- `uv run --extra test pytest tests/unit -q` passed 856 tests.
- `uv run ruff check .`.
- `uv run ruff format --check .`.
- `uv run mypy src tests`.
- `git diff --check`.

Not run successfully: `command -v pyright` did not find a `pyright` executable.

## Acceptance Criteria

- `Site.get_recent_changes()` raises `NoElementException` when a recent-change response has a structural change-author `span.printuser` element whose direct `onclick` value cannot be parsed by the shared user parser.
- The malformed change-author error includes the site unix name, recent-change page number, structural change position, `field=changed_by`, and observed direct `onclick` value.
- Valid recent-change rows still parse `SiteChange.changed_by` through `user_parser(...)`.
- Existing response-body diagnostics, retry-exhausted handling, pagination, `limit` behavior, comment filtering, comment pager filtering, title href validation, page fullname validation, page title validation, revision diagnostics, timestamp diagnostics, flags parsing, and `SiteChange` construction remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated recent-change HTML, real page names, real user names, credentials, cookies, or local rollout paths are required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected change-author parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only recent-change location metadata.
- Risk: Changing the shared user parser could affect unrelated modules. Mitigation: this slice intentionally leaves `user_parse(...)` unchanged and validates parser-adjacent recent-change behavior through the full unit suite.
- Risk: User-like markup inside edit comments could be mistaken for the structural change author. Mitigation: the existing structural row and direct-cell scoping remain unchanged, and focused GREEN includes nested comment-markup filtering.

## Dependencies

- BeautifulSoup continues to expose direct recent-change `td.mod-by > span.printuser` elements and direct anchor `onclick` values in the generated recent-change metadata row.
- The shared `user_parse(...)` utility remains the source of truth for valid Wikidot user metadata extraction.
- Recent-change pages still identify change authors through direct `span.printuser` metadata under `td.mod-by`.

## Open Questions

None for this local slice. Recent-change title, fullname, revision, timestamp, and author parser boundaries now share contextual diagnostics.

## Upstream-Safe Motivation

Recent-change inspection is a read-heavy prerequisite for browser-free audit trails, source verification, archival indexing, publication monitoring, and moderation-oriented tooling. If Wikidot emits a structural recent-change row with malformed direct author metadata, wikidot.py should return a structured parser failure naming the affected site, recent-change page, change position, field, and observed value instead of forcing operators to infer context from a raw shared helper exception. That keeps recent-change diagnostics actionable without retaining generated recent-change HTML, raw response JSON, credentials, user names from real sites, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts established recent-change acquisition as a practical read-heavy workflow, including retry-aware fetching, batched pagination, response-body validation, structural parser context, nested comment filtering, title text spacing, comment text spacing, title href validation, page fullname validation, page title validation, revision diagnostics, timestamp diagnostics, and comment pager filtering.
- Recent parser-boundary drafts validated the same shared user parser failure pattern in private-message detail users, site-member users, forum thread-list users, forum thread-detail users, forum post-list users, and forum post-list edit users. Recent-change author parsing uses the same shared user parser but needs recent-change context at its own parser boundary.
- The immediate RED failure showed the same raw `ValueError` class that prior parser-boundary user slices converted in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated recent-change HTML, real page names, real user names, and private site history out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding recent-change parser diagnostics.
