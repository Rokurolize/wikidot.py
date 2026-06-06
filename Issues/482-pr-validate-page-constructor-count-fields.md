# PR Draft: Validate Page Constructor Count Fields

## Summary

`Page` records store scalar count and size metadata that feeds browser-free page inventories, `latest_revision` lookup, source/revision/file/vote ledgers, publish verification, duplicate-cache reuse, edit result reconciliation, and generated audit rows. Before this change, direct `Page(...)` construction accepted malformed count values such as `children_count=None`, `comments_count=True`, `size="1000"`, `votes_count=5.0`, or `revisions_count="3"`, storing invalid state that could later leak into comparisons, cache decisions, diagnostics, or report ledgers.

This change validates the direct constructor's integer count and size fields during `Page.__post_init__`. Malformed `children_count`, `comments_count`, `size`, `votes_count`, and `revisions_count` values now raise stable `ValueError("<field> must be an integer")` diagnostics. Valid page construction, parser-created pages, `Page.latest_revision`, page edit revision-count sync, page source/revision/file/vote workflows, and site workflows remain unchanged.

## Outcome

Callers cannot silently construct `Page` objects with malformed integer count or size metadata, while valid page records and existing page/site workflows continue to work as before.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free page inventories, source collection, page publishing, revision/file/vote ledgers, duplicate page-cache reuse, generated audit rows, migration tooling, local fixtures, or rehydrated `Page` objects.

## Current Evidence

Local rollout-backed drafts already establish page count metadata as operationally meaningful. Parser-side drafts such as [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md) validate malformed generated ListPages integer cells before parsed `Page` construction. Revision-count behavior drafts such as [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), and [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md) show `revisions_count` directly affects page revision selection and edit reconciliation. Recent direct-constructor hardening in [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md) validates the adjacent identity text boundary.

Those prior slices are not duplicates. Issue 239 validates generated ListPages integer parsing before parser-created page rows exist. Issues 153 and 196 improve `latest_revision` failure context when no revision matches the stored count. Issue 262 synchronizes a newer revision count after successful edits. Issue 481 validates direct identity text fields only. None validates direct `Page(children_count=...)`, `Page(comments_count=...)`, `Page(size=...)`, `Page(votes_count=...)`, or `Page(revisions_count=...)` construction before malformed count values become stored page state.

## Related Issue / Non-Duplicate Analysis

Builds directly on the page metadata surfaces documented by [239-pr-listpages-integer-field-parse-context.md](239-pr-listpages-integer-field-parse-context.md), [153-pr-latest-revision-failure-context.md](153-pr-latest-revision-failure-context.md), [196-pr-page-property-site-context.md](196-pr-page-property-site-context.md), [262-pr-page-edit-revision-count-sync.md](262-pr-page-edit-revision-count-sync.md), [413-pr-validate-page-id-assignments.md](413-pr-validate-page-id-assignments.md), and [481-pr-validate-page-constructor-identity-fields.md](481-pr-validate-page-constructor-identity-fields.md).

No upstream issue was filed from this local workspace.

## Changes

- Add a shared page integer-field validator that rejects booleans.
- Validate `Page.children_count`, `Page.comments_count`, `Page.size`, `Page.votes_count`, and `Page.revisions_count` during `Page.__post_init__`.
- Reject malformed count/size values with stable `ValueError("<field> must be an integer")` messages.
- Preserve valid direct construction, parser-created pages, existing page/site fixtures, and adjacent page workflows.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Page metadata-state integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page(children_count=...)` must reject non-integer and boolean values with `ValueError("children_count must be an integer")`. |
| R2 | `Page(comments_count=...)` must reject non-integer and boolean values with `ValueError("comments_count must be an integer")`. |
| R3 | `Page(size=...)` must reject non-integer and boolean values with `ValueError("size must be an integer")`. |
| R4 | `Page(votes_count=...)` must reject non-integer and boolean values with `ValueError("votes_count must be an integer")`. |
| R5 | `Page(revisions_count=...)` must reject non-integer and boolean values with `ValueError("revisions_count must be an integer")`. |
| R6 | Valid `Page` construction, parser-created pages, `Page.latest_revision`, edit revision-count sync, page source/revision/file/vote workflows, and site workflows must remain unchanged. |
| R7 | This slice must not validate `rating`, `rating_percent`, parent site, user fields, timestamps, tags, parent fullname, cached source/revisions/votes/files, or parser-derived nullable metadata. |
| R8 | This slice must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, constructor tests, adjacent page/site/page-file/page-vote tests, full unit tests, lint, format, mypy, target pyright, and whitespace gates must pass before claiming this local implementation complete; broad pyright limitations must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct `Page.children_count` values fail at the constructor boundary. | `TestPageInit.test_init_rejects_malformed_counts` failed RED for 4 malformed `children_count` values because constructors did not raise, then passed GREEN after validation was added. | Accepting `None`, booleans, strings, floats, or arbitrary non-integers rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R2 | Malformed direct `Page.comments_count` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `comments_count` values. | Accepting non-integer comment counts or silently coercing values rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R3 | Malformed direct `Page.size` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `size` values. | Accepting non-integer sizes or relying only on page-file size validation rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R4 | Malformed direct `Page.votes_count` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `votes_count` values. | Accepting non-integer vote counts rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R5 | Malformed direct `Page.revisions_count` values fail at the constructor boundary. | The same RED/GREEN test failed and then passed for malformed `revisions_count` values. | Accepting non-integer revision counts or deferring failures to latest-revision behavior rejects this local completion claim. | `Page` constructor | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py` |
| R6 | Existing valid page and site workflows remain green. | `tests/unit/test_page_constructor.py` passed 37 tests; adjacent page/site/page-file/page-vote tests passed 664 tests; full unit tests passed 2019 tests. | Regressing valid fixture construction, parser-created pages, `Page.latest_revision`, page edit count sync, page lookup, page source/revision/file/vote workflows, or site workflows rejects this local completion claim. | Page and adjacent workflows | `tests/unit/test_page_constructor.py`, `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_file.py`, `tests/unit/test_page_votes.py`, `tests/unit` |
| R7 | Broader parser metadata remains outside scope. | Existing nullable `rating_percent`, creator, updater, timestamp, comment, parent, tag, cache, and collection fixture patterns remain unchanged and adjacent tests stay green. | Validating or changing rating, rating percent, parent site, users, timestamps, tags, parent fullname, cached state, or parser-derived nullable metadata rejects this local completion claim. | Page constructor scope | `src/wikidot/module/page.py`, `tests/unit/test_page_constructor.py`, adjacent tests |
| R8 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only, and this draft explicitly avoids live Wikidot and private payloads. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text, forum source text, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, adjacent tests passed, full unit passed, ruff, format, mypy, target pyright, and whitespace checks passed; broad pyright limitations were run and reported as existing typing issues outside this slice. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `6529ba6 fix(page): validate constructor count fields`.

- RED: `uv run pytest tests/unit/test_page_constructor.py::TestPageInit::test_init_rejects_malformed_counts -q` failed 20 tests before the fix; every malformed count/size case reported `DID NOT RAISE`.
- GREEN: the same focused command passed 20 tests after count-field validation was added.
- `uv run pytest tests/unit/test_page_constructor.py -q` passed 37 tests.
- `uv run pytest tests/unit/test_page_constructor.py tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_votes.py -q` passed 664 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page_constructor.py` formatted 1 file, then the final touched-file format rerun left files in project format.
- `uv run ruff check src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed.
- `uv run mypy src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with no issues in 2 source files.
- `uv run pyright src/wikidot/module/page.py tests/unit/test_page_constructor.py` passed with 0 errors, 0 warnings, and 0 informations.
- `uv run pytest tests/unit -q` passed 2019 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 86 files already formatted.
- `uv run mypy src tests` passed with no issues in 86 source files.
- `git diff --check` passed.

Not used as a completion blocker: `uv run pyright src tests` ran but failed with 54 existing full-tree typing errors outside this slice, including test fixture `None` mismatches, intentional invalid-input `SearchPagesQuery` calls, requestutil response narrowing issues, client/mock typing, invalid test cookie arguments, and existing site test mock typing issues. The changed source file and constructor test module pass pyright together.

## Acceptance Criteria

- `Page(children_count=None)`, `Page(children_count=True)`, `Page(children_count="0")`, and `Page(children_count=0.0)` raise `ValueError("children_count must be an integer")` when every other constructor field is valid.
- `Page(comments_count=None)`, `Page(comments_count=True)`, `Page(comments_count="0")`, and `Page(comments_count=0.0)` raise `ValueError("comments_count must be an integer")`.
- `Page(size=None)`, `Page(size=True)`, `Page(size="1000")`, and `Page(size=1000.0)` raise `ValueError("size must be an integer")`.
- `Page(votes_count=None)`, `Page(votes_count=True)`, `Page(votes_count="5")`, and `Page(votes_count=5.0)` raise `ValueError("votes_count must be an integer")`.
- `Page(revisions_count=None)`, `Page(revisions_count=True)`, `Page(revisions_count="3")`, and `Page(revisions_count=3.0)` raise `ValueError("revisions_count must be an integer")`.
- Valid page count and size fields are stored unchanged.
- Existing parser-created pages, direct page fixtures, page lookup behavior, `Page.latest_revision`, page edit revision-count sync, page source/revision/file/vote workflows, and site workflows remain green.
- The new tests use unit-level code only and do not validate broader `Page` metadata, require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

Page count and size metadata affects page inventories, `latest_revision`, revision/source/file/vote ledgers, edit reconciliation, and generated audit rows. Parser-side integer validation already protects ListPages-generated values, so this change is intentionally conservative: it only prevents direct callers, fixtures, generated adapters, or rehydrated page state from storing malformed integer counts that later fail as less informative comparison, cache, or diagnostic behavior.

## Local Evidence

- Local rollout evidence used page count metadata in ListPages inventories, page detail ledgers, source/revision/file/vote acquisition, duplicate cache reuse, edit reconciliation, and site workflows.
- Existing local drafts covered ListPages integer parsing, latest-revision failure context, edit revision-count sync, direct page ID/source/revisions/votes assignments, and direct page identity text construction, but did not cover direct `Page(...)` count and size construction.
- Existing unit fixtures intentionally allow some broader parser metadata to be nullable. This slice preserves that pattern and validates only `children_count`, `comments_count`, `size`, `votes_count`, and `revisions_count`.
- This slice does not change parser extraction, page write behavior, page ID/source/revision/file/vote acquisition, cached state, live Wikidot behavior, rating/rating-percent behavior, user/timestamp metadata, tags, parent fullname, or parent site validation.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text, forum source text, and private site data out of upstream discussion.

## Additional Notes

The change rejects malformed integer values rather than coercing them. Booleans are rejected even though `bool` is a subclass of `int`; negative integers remain governed by existing semantics because this slice validates type integrity, not domain-specific minimums.
