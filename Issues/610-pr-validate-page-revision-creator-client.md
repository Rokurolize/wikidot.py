# PR Draft: Validate PageRevision Creator Client

## Summary

`PageRevision` records carry the parent `Page` and the revision creator in `created_by`. Existing page-revision slices validate parser-side user extraction, direct `created_by` type, direct `created_at` type, direct parent-page state, identity fields, comment fields, source/HTML cache state, collection ownership, retained parent state before revision reads, and adjacent page workflows. One constructor coherence gap remained: direct `PageRevision(...)` construction could combine `page=page_from_site_a` with `created_by=User(client=site_b.client, ...)`, producing a page-history row whose creator came from a different client context than the parent page's site.

This change validates `PageRevision.created_by.client` against `PageRevision.page.site.client` during `PageRevision.__post_init__` after existing page, revision ID, revision number, comment, and creator type checks. Mismatches raise `ValueError("created_by must belong to the site")`. Parser-created revision rows remain aligned because `_parse_revision_created_by(site, ...)` already calls `user_parser(site.client, user_elem)` for revision creator metadata. Existing malformed field diagnostics, revision-list parsing, lazy revision source/HTML reads, batch revision acquisition, collection ownership checks, retained-parent read preflights, and adjacent page workflows remain unchanged.

## Outcome

Page revision rows cannot store a creator user from a different client context than the parent page's site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page-history reads, generated revision ledgers, source/HTML comparison, rollback inspection, latest-revision checks, migration audits, publication verification, local fixtures, or serialized and rehydrated page revision rows.

## Current Evidence

Local rollout-backed drafts repeatedly identify page revision reads as practical workflow surfaces. Existing drafts [040-pr-page-revisions-exhausted-retry-error.md](040-pr-page-revisions-exhausted-retry-error.md), [061-pr-deduplicate-page-revision-fetches.md](061-pr-deduplicate-page-revision-fetches.md), [063-pr-deduplicate-page-revision-list-fetches.md](063-pr-deduplicate-page-revision-list-fetches.md), [074-pr-reuse-page-revision-list-parsing.md](074-pr-reuse-page-revision-list-parsing.md), [078-pr-reuse-page-revision-source-html-parsing.md](078-pr-reuse-page-revision-source-html-parsing.md), [094-pr-scope-page-revision-row-cells.md](094-pr-scope-page-revision-row-cells.md), [114-pr-preserve-page-revision-comment-spacing.md](114-pr-preserve-page-revision-comment-spacing.md), [126-pr-reuse-cached-duplicate-page-revision-data.md](126-pr-reuse-cached-duplicate-page-revision-data.md), [128-pr-reuse-cached-duplicate-page-revisions.md](128-pr-reuse-cached-duplicate-page-revisions.md), [145-pr-surface-lazy-page-revision-fetch-failures.md](145-pr-surface-lazy-page-revision-fetch-failures.md), [150-pr-page-revision-failure-context.md](150-pr-page-revision-failure-context.md), [164-pr-page-revision-source-parse-context.md](164-pr-page-revision-source-parse-context.md), [179-pr-page-revision-lazy-failure-context.md](179-pr-page-revision-lazy-failure-context.md), [199-pr-page-revision-row-site-context.md](199-pr-page-revision-row-site-context.md), [200-pr-page-revision-source-parse-site-context.md](200-pr-page-revision-source-parse-site-context.md), [201-pr-page-revision-lazy-site-context.md](201-pr-page-revision-lazy-site-context.md), [216-pr-page-revision-response-body-context.md](216-pr-page-revision-response-body-context.md), [222-pr-page-revision-batch-response-body-context.md](222-pr-page-revision-batch-response-body-context.md), [236-pr-page-revision-row-id-parse-context.md](236-pr-page-revision-row-id-parse-context.md), [237-pr-page-revision-number-parse-context.md](237-pr-page-revision-number-parse-context.md), [303-pr-page-revision-user-context.md](303-pr-page-revision-user-context.md), [304-pr-page-revision-timestamp-context.md](304-pr-page-revision-timestamp-context.md), [328-pr-page-revision-response-body-type-context.md](328-pr-page-revision-response-body-type-context.md), [332-pr-page-revision-list-response-body-type-context.md](332-pr-page-revision-list-response-body-type-context.md), [365-pr-validate-page-revision-collection-entries.md](365-pr-validate-page-revision-collection-entries.md), [376-pr-validate-page-revision-find-id.md](376-pr-validate-page-revision-find-id.md), [415-pr-validate-page-revisions-assignments.md](415-pr-validate-page-revisions-assignments.md), [419-pr-validate-page-revision-collection-initialization.md](419-pr-validate-page-revision-collection-initialization.md), [431-pr-validate-page-revision-source-assignments.md](431-pr-validate-page-revision-source-assignments.md), [432-pr-validate-page-revision-html-assignments.md](432-pr-validate-page-revision-html-assignments.md), [442-pr-validate-page-revision-page-field.md](442-pr-validate-page-revision-page-field.md), [465-pr-validate-page-revision-identity-fields.md](465-pr-validate-page-revision-identity-fields.md), [466-pr-validate-page-revision-comment-field.md](466-pr-validate-page-revision-comment-field.md), [467-pr-validate-page-revision-creator-time-fields.md](467-pr-validate-page-revision-creator-time-fields.md), [472-pr-validate-page-revision-collection-page-field.md](472-pr-validate-page-revision-collection-page-field.md), [509-pr-validate-page-revision-source-cache.md](509-pr-validate-page-revision-source-cache.md), [510-pr-validate-page-revision-html-cache.md](510-pr-validate-page-revision-html-cache.md), [587-pr-validate-page-revision-collection-page-ownership.md](587-pr-validate-page-revision-collection-page-ownership.md), [597-pr-validate-page-revisions-cache-ownership.md](597-pr-validate-page-revisions-cache-ownership.md), [601-pr-validate-page-revision-source-cache-ownership.md](601-pr-validate-page-revision-source-cache-ownership.md), and adjacent actor-client slices [607-pr-validate-forum-thread-creator-client.md](607-pr-validate-forum-thread-creator-client.md), [608-pr-validate-forum-post-actor-clients.md](608-pr-validate-forum-post-actor-clients.md), and [609-pr-validate-forum-post-revision-creator-client.md](609-pr-validate-forum-post-revision-creator-client.md) establish page revision acquisition, parser diagnostics, response diagnostics, duplicate/cache behavior, direct record-state validation, collection ownership, retained-parent safety, and actor/client coherence as active operational boundaries.

The parser path already constructs revision creators with the parent page site's client: `_parse_revision_created_by(site, ...)` calls `user_parser(site.client, user_elem)`. The new rule brings direct constructor behavior in line with that parser invariant.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 467. Issue 467 validates that `PageRevision.created_by` is an `AbstractUser` and `created_at` is a `datetime`; it does not validate the relationship between a valid creator object and the parent page's site client.

This is not a duplicate of Issue 442. Issue 442 validates the direct parent `page` field type; it does not validate creator users against the retained page site's client.

This is not a duplicate of Issue 303. Issue 303 wraps parser-side malformed page revision author metadata with page/revision context; it does not validate direct constructor coherence for a valid `User` object.

This is not a duplicate of Issues 607, 608, or 609. Those slices validate forum thread, forum post, and forum post revision actor/client coherence. This slice validates `PageRevision.created_by.client` against the revision's retained page site.

No upstream issue was filed from this local workspace.

## Changes

- Add `PageRevision` creator-client coherence validation.
- Reject direct revision rows where `created_by.client is not page.site.client` with `ValueError("created_by must belong to the site")`.
- Preserve existing validation order for malformed `page`, `id`, `rev_no`, `comment`, `created_by`, `created_at`, `_source`, and `_html` diagnostics.
- Keep valid test revision fixtures aligned with their parent page's site client.
- Preserve side-effect-free construction: the new check compares object identity only and does not perform login checks, HTTP requests, user lookups, coercion, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page history actor identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageRevision(page=page_a, created_by=User(client=site_b.client, ...), ...)` must reject the mismatched creator client with `ValueError("created_by must belong to the site")` before contradictory revision record state can be used. |
| R2 | Valid direct `PageRevision(...)` rows where `created_by.client is page.site.client` and parser-created revision rows must remain valid. |
| R3 | Existing malformed `page`, `id`, `rev_no`, `comment`, `created_by`, `created_at`, `_source`, and `_html` diagnostics must remain unchanged. |
| R4 | Existing revision-list acquisition, lazy revision source/HTML reads, batch revision acquisition, collection ownership checks, retained-parent read preflights, and adjacent page workflows must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Constructor creator/client mismatches fail at the public dataclass boundary. | `TestPageRevision.test_init_rejects_created_by_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `PageRevision.__post_init__` called the creator-client preflight. | Accepting a valid `User` object from another client context, emitting a revision row whose page site and creator client disagree, or deferring the mismatch to later revision-list or source/HTML paths rejects this local completion claim. | `PageRevision` constructor | `src/wikidot/module/page_revision.py`, `tests/unit/test_page_revision.py` |
| R2 | Existing valid direct and parser-created revision rows stay green. | `tests/unit/test_page_revision.py` passed 116 tests, including parser-created revision rows and same-client direct fixture rows. | Rejecting same-client users, replacing creator objects, coercing users, breaking parser-created rows, or requiring live authentication rejects this local completion claim. | Page revision constructor and parser | `tests/unit/test_page_revision.py` |
| R3 | Existing diagnostics stay stable. | Focused page-revision coverage passed existing malformed page, ID, revision number, comment, creator type, timestamp, source cache, HTML cache, collection, lookup, and ownership validation tests. | Changing existing `ValueError` diagnostics, validating coherence before malformed field checks, or accepting previously rejected malformed values rejects this local completion claim. | PageRevision validation order | `tests/unit/test_page_revision.py` |
| R4 | Existing adjacent workflows remain green. | Adjacent page, page-constructor, page-revision, page-source, page-file, page-votes, and site coverage passed 1010 tests, and full unit coverage passed 2738 tests. | Regressing page parsing, page history acquisition, revision source/HTML reads, duplicate reuse, source/file/vote workflows, parser diagnostics, retained-parent request preflights, or adjacent site behavior rejects this local completion claim. | Page workflows | `tests/unit` |
| R5 | No live auth material or private site state is needed to prove the behavior. | The regression uses synthetic `Page` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw page HTML, private usernames, page source, revision comments, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `25425d8 fix(page_revision): validate creator client`.

- RED: `uv run pytest tests/unit/test_page_revision.py::TestPageRevision::test_init_rejects_created_by_from_different_client -q` failed before the fix with `DID NOT RAISE`.
- GREEN regression: the same focused command passed 1 test.
- Page-revision coverage: `uv run pytest tests/unit/test_page_revision.py -q` passed 116 tests.
- Adjacent page/page-constructor/page-revision/page-source/page-file/page-votes/site coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 1010 tests.
- `uv run pytest tests/unit -q` passed 2738 tests.
- `uv run ruff format src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/page_revision.py tests/unit/test_page_revision.py` passed.
- `git diff --check` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `PageRevision(page=page_a, created_by=User(client=site_b.client, ...), ...)` raises `ValueError("created_by must belong to the site")`.
- Valid direct rows where `created_by.client is page.site.client` remain valid.
- Existing malformed `created_by` values still raise `ValueError("created_by must be an AbstractUser")`.
- Existing malformed `page`, `id`, `rev_no`, `comment`, `created_at`, `_source`, and `_html` diagnostics remain unchanged.
- Existing parser-created revision rows still produce valid `PageRevision` records.
- Existing revision-list acquisition, lazy revision source/HTML reads, batch revision acquisition, collection ownership checks, retained-parent read preflights, and adjacent page workflows remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`PageRevision` is the durable row shape behind browser-free page-history reads, generated revision ledgers, source/HTML comparison, rollback inspection, latest-revision checks, migration audits, publication verification, local fixtures, and rehydrated records. A revision row is page/site-scoped, and parser-created creator users already come from the parent page site's client. Constructor coherence validation keeps direct fixtures and serialized rows from mixing parent-page and revision-creator client contexts while preserving normal revision-list, source, HTML, cache, and parser paths.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `PageRevision(page=page_a, created_by=User(client=site_b.client, ...), ...)` construction silently accepted a contradictory row.
- Existing local drafts covered page revision fetch retry behavior, duplicate revision-list and revision data reduction, parse reuse, parser ID/user/timestamp diagnostics, response diagnostics, cached direct acquisition, collection validation, source/html assignment validation, direct parent-page validation, direct identity-field validation, direct comment-field validation, direct creator/time type validation, collection page ownership, retained-parent request preflights, and page revision source cache ownership, but did not cover direct creator/client coherence at `PageRevision(...)` construction.
- This slice only validates constructor-time revision creator/client coherence. It does not change revision-list request construction, parser selectors, user parser semantics, timestamp parsing, revision ID parsing, revision-number parsing, source/HTML request payloads, cache invalidation semantics, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw page HTML, revision comments, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than user IDs, usernames, page IDs, fullnames, site IDs, UNIX names, or authentication state. The parser path and retained object graph preserve client identity, and identity comparison avoids network lookups, login checks, and ambiguous cross-client equivalence rules.
