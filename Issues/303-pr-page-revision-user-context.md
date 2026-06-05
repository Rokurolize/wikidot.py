# PR Draft: Report Malformed Page Revision Users

## Summary

`PageCollection.get_page_revisions()` parses Wikidot page history rows from `history/PageRevisionListModule`. The surrounding parser already reports malformed revision row IDs, malformed revision numbers, missing author elements, and missing timestamp elements with site/page/revision context. One adjacent boundary still called the shared `user_parser(...)` directly: when the author `span.printuser` existed but contained malformed normal-user metadata, the shared parser's raw `ValueError` escaped without the page revision location.

This local slice keeps valid page revision parsing unchanged. It only wraps `ValueError` from the page revision author parser and raises `NoElementException` with the site unix name, page fullname, page ID, revision ID, `field=created_by`, and the observed `onclick` value when available.

## Outcome

Malformed page revision authors now fail with page/revision-local context instead of leaking a shared parser exception.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who parse generated page history in browser-free audit, archival, moderation, source collection, or import workflows.

## Related Issue

Builds on the same parser-boundary diagnostics pattern as [285-pr-forum-post-revision-user-context.md](285-pr-forum-post-revision-user-context.md), [288-pr-private-message-detail-user-context.md](288-pr-private-message-detail-user-context.md), [289-pr-site-member-user-context.md](289-pr-site-member-user-context.md), [291-pr-forum-thread-list-user-context.md](291-pr-forum-thread-list-user-context.md), [293-pr-forum-thread-detail-user-context.md](293-pr-forum-thread-detail-user-context.md), [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), and [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md). Those drafts established that shared user parser failures should be converted at module boundaries into local workflow context.

No upstream issue was filed from this local workspace.

## Changes

- Add a page-module helper that extracts a `printuser` anchor `onclick` value for diagnostics.
- Wrap page revision `created_by` parsing so shared user parser `ValueError` becomes `NoElementException`.
- Include site, page, page ID, revision ID, field, and observed value in the failure message.
- Preserve direct-child page history cell scoping and valid revision parsing.
- Add a focused regression for a page revision author with `userInfo(latest)`.

## Type Of Change

- Bug fix / diagnostics improvement
- Parser-boundary hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A page revision row whose `created_by` `printuser` exists but has malformed user metadata must raise `NoElementException`, not the shared parser's raw `ValueError`. |
| R2 | The malformed user exception must include site, page, page ID, revision ID, `field=created_by`, and the observed user value. |
| R3 | Valid page revision list parsing must remain unchanged. |
| R4 | Existing missing-cell, malformed row-ID, malformed revision-number, missing-author, and missing-timestamp diagnostics must remain unchanged. |
| R5 | Focused, page-level, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `collection.get_page_revisions()` raises `NoElementException` when a page history author has `onclick="WIKIDOT.page.listeners.userInfo(latest); return false;"`. | `TestPageCollectionAcquire.test_acquire_revisions_malformed_created_by_includes_site_page_and_value_context` expects `NoElementException`. | Leaking `ValueError: user id is not found` rejects this local completion claim. | `src/wikidot/module/page.py` | `tests/unit/test_page.py` |
| R2 | The exception message contains `site: test-site`, `page: test-page`, `revision: 123`, `id=12345`, `field=created_by`, and the observed `onclick` value. | The focused regression matches all fields. | Omitting page/revision identity or hiding the malformed value rejects this local completion claim. | Page revision list parser diagnostics | `tests/unit/test_page.py` |
| R3 | Valid revision rows still produce the same `PageRevisionCollection`. | `tests/unit/test_page.py` passed 153 tests, including revision-list success and nested-cell scoping. | Regressing revision IDs, revision numbers, authors, timestamps, comments, duplicate-page reuse, or cache behavior rejects this local completion claim. | Page acquisition | `tests/unit/test_page.py` |
| R4 | Existing contextual parser failures remain stable. | Existing tests for malformed revision row IDs, malformed revision numbers, missing author elements, and missing timestamp elements stayed green. | Rewording unrelated diagnostics or changing missing-element behavior rejects this local completion claim. | Page revision diagnostics | `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the docs commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `35f6cf5 fix(page): report malformed revision users`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_created_by_includes_site_page_and_value_context -q` failed before the fix because `ValueError: user id is not found` escaped from `user_parser(...)`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_revisions_malformed_created_by_includes_site_page_and_value_context -q` passed 1 test.
- `uv run pytest tests/unit/test_page.py -q` passed 153 tests.
- `uv run pytest tests/unit -q` passed 861 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy src` passed with no issues in 35 source files.
- `git diff --check` passed.
- A leak check for local paths and token-like assignments found no matches.

Not run successfully: `uv run pyright` could not spawn `pyright` because no executable was available in this environment.

## Acceptance Criteria

- Malformed page revision `created_by` user metadata raises `NoElementException` with page/revision context.
- The diagnostic includes the malformed user value, preferring the anchor `onclick` value when present.
- Valid page revision list parsing continues to populate revision ID, revision number, author, timestamp, and comment fields.
- Existing page revision diagnostics for row ID, revision number, missing author, missing timestamp, and missing response body remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated user markup from real sites, credentials, cookies, auth JSON, local rollout paths, or private account details are required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Page revision parsing is a shared page history path. Mitigation: the change only wraps an existing shared parser failure and does not alter successful parsing.
- Risk: The new helper duplicates a small diagnostic helper used in other modules. Mitigation: this keeps the patch surgical and avoids a cross-module refactor while multiple parser-boundary drafts remain local.
- Risk: Contextual wrapping could mask the original parser reason. Mitigation: the original `ValueError` is preserved as the exception cause with `raise ... from exc`.

## Dependencies

- BeautifulSoup continues to expose `onclick` on direct child author anchors.
- The shared user parser continues to raise `ValueError` for malformed `printuser` metadata.
- Page revision list rows continue to identify revisions through `tr#revision-row-...` and authors through `span.printuser`.

## Open Questions

None for this local slice. Broader validation of all regular-user `href` shapes is intentionally out of scope because local fixture evidence includes `href="#"` printuser markup in module tests.

## Upstream-Safe Motivation

Page revision history is a common read path for source collection and audit work. When one revision row contains malformed author metadata, users need to know which page and revision caused the failure. The parser already provides this level of context for adjacent page history fields; wrapping the author parser makes the page revision diagnostics consistent without changing valid behavior.

## Local Evidence, Not For Upstream Paste

- Recent local drafts repeatedly improved parser-boundary diagnostics around the shared user parser in private messages, site members, forum thread lists, forum thread details, forum post lists, forum post edit metadata, recent changes, and forum post revisions.
- The immediate RED failure showed page revision parsing leaking `ValueError: user id is not found` from `user_parser(...)`.
- The page unit suite stayed green after wrapping only the malformed author path.
- A rejected broader idea was strict validation of every regular-user `href` shape; local tests include `href="#"` printuser fixtures, so this issue keeps scope to the clearer malformed-user exception boundary.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated user markup from real sites, real user names, and private site history out of upstream discussion.

## Additional Notes

This is a parser observability fix. It does not change request behavior, successful page revision parsing, cache behavior, shared user parser behavior, live Wikidot behavior, or any upstream filing state.
