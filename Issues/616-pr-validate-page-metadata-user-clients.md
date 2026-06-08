# PR Draft: Validate Page Metadata User Clients

## Summary

`Page` records carry nullable user metadata for `created_by`, `updated_by`, and `commented_by`. Parser-created ListPages rows build those users with the parent site's client, and adjacent page-history and vote rows already validate their user/client coherence. One base page record gap remained: direct `Page(...)` construction could combine `site=site_a` with valid metadata users from `site_b.client`, leaving a page inventory row whose site and actor metadata came from different client contexts.

This change validates `created_by.client`, `updated_by.client`, and `commented_by.client` against `Page.site.client` during `Page.__post_init__`, after existing site, scalar, nullable user-shape, and nullable timestamp validation. Mismatches raise `ValueError("<field> must belong to the site")`. Valid nullable metadata, parser-created rows, same-client direct rows, existing scalar/timestamp diagnostics, cache ownership checks, and adjacent page workflows remain unchanged.

## Outcome

Direct `Page(...)` records can no longer retain page-level user metadata from a different client context than the parent site.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who construct page inventories from ListPages rows, generated fixtures, source/revision ledgers, search results, publish-adjacent checks, migration data, or cached local state before using page metadata in browser-free workflows.

## Current Evidence

Local rollout-backed drafts repeatedly identify page metadata, ListPages parsing, source/revision/vote/file traversal, and page record rehydration as practical workflow surfaces. Existing drafts [306-pr-listpages-user-context.md](306-pr-listpages-user-context.md), [487-pr-validate-page-constructor-nullable-metadata.md](487-pr-validate-page-constructor-nullable-metadata.md), [610-pr-validate-page-revision-creator-client.md](610-pr-validate-page-revision-creator-client.md), [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md), and [615-pr-validate-user-record-client.md](615-pr-validate-user-record-client.md) establish page metadata users and user-client coherence as active operational boundaries.

This is not a duplicate of Issue 487. Issue 487 validates that `created_by`, `updated_by`, and `commented_by` are `AbstractUser | None`, plus timestamp shape. It does not validate that valid user objects belong to the page's site client.

This is not a duplicate of Issue 610. Issue 610 validates `PageRevision.created_by.client` against the revision page's site. This slice validates the base `Page` record's nullable page metadata users.

This is not a duplicate of Issue 611. Issue 611 validates `PageVote.user.client` against the vote page's site. This slice validates page-level creator, updater, and commenter metadata.

This is not a duplicate of Issue 615. Issue 615 validates that user records retain a real `Client`. This slice validates the relationship between a valid user record and a valid page site.

No upstream issue was filed from this local workspace.

## Changes

- Add `_validate_optional_page_user_belongs_to_site(...)`.
- Validate `created_by`, `updated_by`, and `commented_by` against `Page.site.client` after existing nullable metadata shape checks.
- Add a focused regression for mismatched metadata users across all three fields.
- Use an inert real `Client` shell in the test so the regression covers different valid clients, not malformed user construction.

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(site=site_a, created_by=User(client=site_b.client, ...), ...)` must raise `ValueError("created_by must belong to the site")`. |
| R2 | `updated_by` and `commented_by` must reject the same cross-client mismatch with field-specific diagnostics. |
| R3 | Existing nullable user-shape and timestamp-shape diagnostics must keep their current precedence. |
| R4 | Valid same-client metadata users and `None` metadata users must remain accepted. |
| R5 | Parser-created ListPages rows, page source/revision/file/vote workflows, search-query user conversion, and adjacent site workflows must remain unchanged. |
| R6 | Full unit, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Page creator metadata cannot come from another client context. | `TestPageInit.test_init_rejects_user_metadata_from_different_client[created_by]` failed RED with `DID NOT RAISE`, then passed GREEN after the page constructor coherence check. | Accepting a valid `User` from another client or deferring the mismatch to later page reads rejects this local completion claim. | `Page.__post_init__` | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Page updater and commenter metadata follow the same rule. | The same parameterized regression failed RED and passed GREEN for `updated_by` and `commented_by`. | Accepting mismatched updater/commenter users or using a non-field-specific diagnostic rejects this local completion claim. | Page metadata user fields | `tests/unit/test_page_constructor.py` |
| R3 | Existing field-shape validation remains earlier than client coherence. | `uv run pytest tests/unit/test_page_constructor.py -q` passed 168 tests, including existing malformed nullable metadata and timestamp diagnostics. | Moving malformed user or timestamp values behind client coherence rejects this local completion claim. | Page constructor metadata validation | `tests/unit/test_page_constructor.py` |
| R4 | Valid same-client and missing metadata remain accepted. | Existing valid metadata and missing metadata constructor tests passed in the 168-test page-constructor run. | Rejecting `None` metadata or same-client user metadata rejects this local completion claim. | Page constructor metadata validation | `tests/unit/test_page_constructor.py` |
| R5 | Adjacent page workflows remain green. | Adjacent page/page-constructor/page-revision/page-source/page-file/page-votes/site/search coverage passed 1059 tests. | Regressing ListPages parsing, source/revision/file/vote acquisition, cache ownership checks, search-query user conversion, or site workflows rejects this local completion claim. | Adjacent page workflows | `tests/unit` |
| R6 | Repository quality gates remain green. | Full unit coverage passed 2775 tests; full ruff check, full format check, mypy, pyright, and `git diff --check` passed. | Any unreported test, lint, format, type, or whitespace failure rejects this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No live auth material or private state is needed to prove the behavior. | All tests use synthetic `Site`, `Client`, and `User` objects; this draft contains no credentials, cookies, auth JSON, raw account data, private response bodies, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, private usernames, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `aeb4de4 fix(page): validate metadata user clients`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_user_metadata_from_different_client -q` failed 3 tests before the fix because mismatched page metadata users did not raise.
- GREEN regression: the same focused command passed 3 tests.
- Page constructor coverage: `uv run pytest tests/unit/test_page_constructor.py -q` passed 168 tests.
- Adjacent page workflow coverage: `uv run pytest tests/unit/test_page.py tests/unit/test_page_constructor.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_file.py tests/unit/test_page_votes.py tests/unit/test_site.py tests/unit/test_search_pages_query.py -q` passed 1059 tests.
- `uv run pytest tests/unit -q` passed 2775 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` reformatted 1 file and left 1 file unchanged.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page(site=site_a, created_by=User(client=site_b.client, ...), ...)` raises `ValueError("created_by must belong to the site")`.
- `updated_by` and `commented_by` reject the same cross-client mismatch with field-specific diagnostics.
- Existing malformed nullable user metadata still raises `ValueError("<field> must be an AbstractUser or None")`.
- Existing malformed nullable timestamp metadata still raises `ValueError("<field> must be a datetime or None")`.
- Valid same-client and missing page metadata remain accepted.
- Parser-created ListPages rows, page source/revision/file/vote workflows, cache ownership checks, search-query conversion, and site workflows remain unchanged.
- The new tests use unit-level synthetic state only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page metadata users are page/site-scoped actor fields. Parser paths already create these actors with the parent site's client, and adjacent revision/vote rows already enforce equivalent client coherence. Constructor validation keeps generated inventories, local fixtures, and rehydrated page rows from mixing page site state with actor metadata from another client context, without changing valid metadata, parser behavior, live request behavior, or downstream cache ownership rules.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed `Page(site=site_a, created_by=User(client=site_b.client, ...))`, `updated_by`, and `commented_by` silently accepted contradictory metadata rows.
- Existing local drafts covered ListPages user parser context, nullable page metadata type validation, page revision creator-client coherence, page vote user-client coherence, and base user record-client validation, but did not cover base `Page` metadata user/client coherence.
- This slice only validates constructor-time page metadata user/client coherence. It does not change ListPages selectors, user parser semantics, timestamp parsing, source/revision/file/vote acquisition, page write behavior, live site behavior, authentication semantics, search-query conversion, or cache ownership rules.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private page/forum content, private message bodies, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than usernames, user IDs, site names, login state, or remote account identity. That matches the existing site/page/forum/vote/private-message ownership validations and avoids network lookups or ambiguous cross-client equivalence rules.
