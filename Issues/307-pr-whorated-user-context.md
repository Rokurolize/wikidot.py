# PR Draft: Report Malformed WhoRated Users

## Summary

`PageCollection.get_page_votes()` parses `pagerate/WhoRatedPageModule` responses by pairing direct `span.printuser` voter elements with direct colored vote-value spans inside the generated WhoRated column-count container. Earlier local slices made page-vote acquisition deduplicate duplicate page IDs, scope parsing to the generated WhoRated container, reuse cached duplicate votes, report missing vote response bodies with site/page context, report user/value count mismatches with site/page/count context, and report malformed vote values with site/page/id/field/value context. One adjacent parser-boundary gap remained: when a present WhoRated voter `span.printuser` contained malformed user metadata, the shared `user_parse(...)` utility raised raw `ValueError` without the affected site, page, page ID, field, or observed user metadata value.

This local slice keeps successful WhoRated vote parsing and the shared `user_parse(...)` utility unchanged. It catches malformed present WhoRated voter metadata at the page-vote parser boundary and raises `NoElementException` with site unix name, first affected page fullname, page ID, `field=user`, and the offending direct user `onclick` value or fallback rendered text.

## Outcome

Malformed WhoRated voter values now fail with page-vote-local context instead of leaking a raw shared user parser exception.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who hydrate page votes for moderation, audit, corpus reconciliation, page history review, author ledgers, or generated page reports.

## Related Issue

Builds on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), and the recent vote-value diagnostics slice that introduced `_parse_who_rated_vote_value(...)`.

This slice also follows the shared user parser-boundary pattern from [295-pr-forum-post-list-user-context.md](295-pr-forum-post-list-user-context.md), [297-pr-forum-post-list-edit-user-context.md](297-pr-forum-post-list-edit-user-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), and the shared parser validation slices [301-pr-deleted-user-id-validation.md](301-pr-deleted-user-id-validation.md) and [302-pr-regular-user-href-validation.md](302-pr-regular-user-href-validation.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a small WhoRated voter parser that raises contextual `NoElementException` on malformed generated `span.printuser` values.
- Route direct WhoRated voter elements through that helper after the existing user/value count check identifies the first page associated with the response page ID.
- Include site unix name, first affected page fullname, page ID, `field=user`, and the observed direct user `onclick` value or fallback rendered text in the parser error.
- Preserve successful WhoRated parsing, direct-child container scoping, missing response-body diagnostics, user/value mismatch diagnostics, vote-value diagnostics, request batching, retry behavior, duplicate page ID grouping, cached duplicate vote reuse, vote object construction, and lazy `Page.votes` behavior.
- Add a focused public `PageCollection.get_page_votes()` regression for a malformed voter `userInfo(latest)` value.

## Type Of Change

- Bug fix / diagnostics improvement
- Page-vote parser hardening
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated WhoRated response with a malformed present voter `span.printuser` must fail at the page-vote parser boundary. |
| R2 | The malformed voter error must identify the affected site, first affected page fullname, page ID, field, and observed direct user metadata value. |
| R3 | Existing valid WhoRated user parsing, vote value parsing, direct-child scoping, user/value mismatch detection, duplicate page propagation, and cached duplicate vote reuse must remain compatible. |
| R4 | Existing page-vote response handling, page-ID acquisition, retry behavior, request deduplication, `PageVoteCollection` construction, and lazy `Page.votes` behavior must remain unchanged. |
| R5 | Focused, page-level, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `PageCollection.get_page_votes()` raises `NoElementException` for `userInfo(latest)` in a generated WhoRated voter. | `TestPageCollectionAcquire.test_acquire_votes_malformed_user_includes_site_page_and_value_context` mutates the first generated voter anchor and expects `NoElementException`. | Leaking raw `ValueError`, fabricating a user, silently skipping the voter, truncating the vote list, or returning a malformed `PageVoteCollection` rejects this local completion claim. | `src/wikidot/module/page.py` | `tests/unit/test_page.py` |
| R2 | The error names `site: test-site`, `page: test-page`, `id=12345`, `field=user`, and `value=WIKIDOT.page.listeners.userInfo(latest); return false;`. | The focused regression matches all fields. | Omitting site, page fullname, page ID, field name, or the bad direct user metadata value makes the failure ambiguous and rejects this local completion claim. | WhoRated voter diagnostics | `tests/unit/test_page.py` |
| R3 | Valid WhoRated rows still parse, values still parse, non-vote colored spans remain ignored, mismatches still report counts, and duplicate page votes still propagate. | Focused GREEN includes success, missing body, non-vote colored span filtering, mismatch, malformed vote value, duplicate page ID, and cached duplicate vote tests. | Regressing direct-child scoping, value conversion, mismatch behavior, duplicate vote propagation, or cached vote cloning rejects this local completion claim. | Page vote parser | `tests/unit/test_page.py` |
| R4 | Adjacent page acquisition and lazy page-vote behavior stay green. | The full page suite covers page IDs, source, revision, vote, file, search, metadata, and mutation-adjacent behavior; the full unit suite covers `PageVoteCollection` behavior. | Regressing request construction, retry use, cache population, page ID acquisition, vote object ownership, or lazy failure behavior rejects this local completion claim. | Page workflows | `tests/unit/test_page.py`, `tests/unit/test_page_votes.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit suite and static checks passed before the code commit. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `2d9dbd8 fix(page): report malformed whorated users`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_user_includes_site_page_and_value_context -q` failed before the fix with `ValueError: user id is not found`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_user_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_success tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_missing_response_body_includes_site_page_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_ignores_non_vote_colored_spans tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_site_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_value_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_deduplicates_duplicate_page_ids tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_reuses_cached_duplicate_page_votes -q` passed 8 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 157 tests.
- `uv run pytest tests/unit -q` passed 865 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 80 files already formatted.
- `uv run mypy src` passed with no issues in 35 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright` could not spawn `pyright` because no executable was available in this environment.

## Acceptance Criteria

- A generated WhoRated response whose present voter `span.printuser` value has malformed user metadata raises `NoElementException`.
- The malformed voter message includes the site `unix_name`, first affected page fullname, page ID, `field=user`, and observed direct user metadata value.
- Valid WhoRated voters still parse through `user_parse(...)`.
- Successful WhoRated parsing, direct-child container scoping, non-vote colored span filtering, missing response-body diagnostics, user/value mismatch diagnostics, vote-value diagnostics, request batching, retry behavior, duplicate page ID grouping, cached duplicate vote reuse, vote object construction, and lazy `Page.votes` behavior remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, raw generated WhoRated HTML from real sites, page titles from real sites, credentials, cookies, auth JSON, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and the local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Wrapping shared-parser `ValueError` could hide an unexpected voter parsing failure. Mitigation: the wrapper preserves exception chaining with `from exc` and adds only WhoRated location metadata.
- Risk: Changing the shared user parser could affect unrelated modules. Mitigation: this slice intentionally leaves `user_parse(...)` unchanged and validates parser-adjacent page behavior through the full unit suite.
- Risk: A single WhoRated response can map to duplicate `Page` objects for the same page ID. Mitigation: diagnostics use the same first-page representative already used by missing response-body, mismatch, and vote-value diagnostics, while successful parsing still propagates cloned votes to every page object for that page ID.
- Risk: WhoRated markup can contain surrounding colored spans or authored content. Mitigation: this slice uses the already-scoped direct voter elements from the generated column-count container and does not broaden selectors.

## Dependencies

- BeautifulSoup continues to expose direct WhoRated `span.printuser` voter elements and direct anchor metadata in generated vote-list markup.
- The shared `user_parse(...)` utility remains the source of truth for valid Wikidot user metadata extraction.
- WhoRated output continues to pair direct voter spans and direct colored vote-value spans inside the generated column-count container.

## Open Questions

None for this local slice. Broader centralization of repeated user value wrappers could be considered later only if it reduces duplication without changing parser behavior.

## Upstream-Safe Motivation

WhoRated vote lists are read-heavy page-detail data used in moderation, audit, corpus reconciliation, and page reports. When Wikidot returns a present voter with malformed generated metadata, wikidot.py should fail with a structured parser error naming the affected site, page, page ID, field, and observed value instead of leaking a generic shared helper exception. That keeps logs actionable without retaining raw WhoRated HTML, raw response JSON, credentials, or local rollout paths.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page-vote acquisition as a practical workflow surface by improving duplicate page ID handling, WhoRated parser scoping, cached duplicate vote reuse, lazy failure context, response-body validation, mismatch diagnostics, and vote-value diagnostics.
- Recent user parser-boundary drafts validated the same shared `user_parse(...)` failure pattern in forum post lists, forum post edit metadata, recent changes, page revision lists, and ListPages linked-user fields.
- The immediate RED failure showed the same raw `ValueError` class that prior parser-boundary user slices converted in adjacent modules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, generated WhoRated HTML, page names from real sites, page titles from real sites, page source text, and private page content out of upstream discussion.

## Additional Notes

This is a parser correctness and observability fix. It narrows a raw utility-parser exception into the same local exception family used by surrounding page-vote parser diagnostics.
