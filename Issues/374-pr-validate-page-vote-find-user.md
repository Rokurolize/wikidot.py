# PR Draft: Validate PageVoteCollection.find User Input

## Summary

`PageVoteCollection.find(user)` documents `user` as `AbstractUser`, but malformed caller-provided values were not rejected at the public search boundary. Non-user values such as `None`, `True`, strings, or dicts leaked `AttributeError`; users with `id=None` or string IDs were treated as ordinary "has not voted" misses; and `id=True` could match a vote whose user ID is `1` because `bool` is an `int` subclass.

This change validates the search target before iterating the vote collection. Non-`AbstractUser` values now raise `ValueError("user must be an AbstractUser")`; `AbstractUser` instances whose `id` is missing, boolean, or non-integer now raise `ValueError("user.id must be an integer")`. Existing valid lookup and valid not-found behavior remain unchanged.

## Outcome

Page vote collection callers now get deterministic Python-side preflight validation for malformed search users instead of raw attribute errors, misleading not-voted misses, or accidental boolean ID matches.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using page vote data for moderation ledgers, rating audits, corpus reports, cleanup tooling, or browser-free page inspection workflows that need stable vote lookup behavior.

## Current Evidence

Local rollout-backed drafts repeatedly identify page vote and WhoRated data as practical read surfaces. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), and [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md) cover vote-list fetching, WhoRated parsing, response diagnostics, cache invalidation, vote mutation input validation, and adjacent collection validation.

Those prior slices are not duplicates. They preserve or consume `PageVoteCollection` data but do not validate the caller-provided `user` argument to `PageVoteCollection.find(...)` before scanning stored votes.

## Related Issue

Builds directly on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), and the collection-entry validation pattern from [368-pr-validate-page-collection-entries.md](368-pr-validate-page-collection-entries.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate `PageVoteCollection.find(user=...)` accepts only `AbstractUser` instances before scanning votes.
- Validate the search user's `id` is a non-boolean integer before comparing it with stored vote user IDs.
- Preserve valid vote lookup behavior for a user with the same numeric ID.
- Preserve valid unknown-user behavior: a well-formed user ID that is not present still raises the existing not-voted `ValueError`.
- Preserve page vote acquisition, `PageVoteCollection` ownership, WhoRated parsing, page vote mutation behavior, and vote-cache invalidation semantics.

## Type Of Change

- Input validation
- Public API behavior hardening
- Page vote lookup preflight safety
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `PageVoteCollection.find(user=...)` must reject non-`AbstractUser` values with `ValueError("user must be an AbstractUser")` before scanning votes. |
| R2 | `PageVoteCollection.find(user=...)` must reject `AbstractUser` instances whose `id` is missing, boolean, or non-integer with `ValueError("user.id must be an integer")`. |
| R3 | Valid lookup and valid not-found behavior must remain unchanged for well-formed users with integer IDs. |
| R4 | Existing page vote acquisition, WhoRated parser diagnostics, `Page.vote(...)`, `Page.cancel_vote()`, vote-cache invalidation, and collection ownership behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private vote data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, page vote collection tests, adjacent page/site tests, full unit tests, lint, format, type, and whitespace gates must pass before claiming this local implementation complete; unavailable tools must be reported instead of hidden. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-user search values fail before vote iteration can access `.id`. | `TestPageVoteCollection.test_find_rejects_non_user_values` failed RED before the fix for `None`, `True`, `"12345"`, and a dict, then passed GREEN after validation was added. | Leaking `AttributeError`, coercing values, scanning votes, or treating dict/string/bool inputs as users rejects this local completion claim. | Page vote search preflight | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R2 | Malformed user IDs fail before ID comparison. | `TestPageVoteCollection.test_find_rejects_users_without_integer_id` failed RED before the fix for `User(id=None)`, `User(id=True)`, and `User(id="12345")`, then passed GREEN after validation was added. | Reporting "has not voted" for malformed IDs, comparing strings/None, or matching `True` to vote user ID `1` rejects this local completion claim. | Page vote search preflight | `src/wikidot/module/page_votes.py`, `tests/unit/test_page_votes.py` |
| R3 | Well-formed lookup semantics stay unchanged. | Existing `test_find_existing_vote` and `test_find_nonexistent_vote_raises` passed after switching them to real `User` objects. | Changing returned vote identity, changing valid not-voted errors, or requiring the same `User` object instance instead of matching integer IDs rejects this local completion claim. | Page vote collection lookup | `tests/unit/test_page_votes.py` |
| R4 | Adjacent page vote behavior remains green. | `tests/unit/test_page_votes.py` passed 16 tests, and adjacent page/page-vote/site tests passed 260 tests. | Regressing WhoRated rows, page vote acquisition, page write vote behavior, cache invalidation, or site/page tests rejects this local completion claim. | Page vote workflow | affected page vote, page, and site tests |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw vote response bodies, private vote data, or private page content rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, page vote tests passed, adjacent tests passed, full unit passed, ruff, format, mypy, and whitespace checks passed; pyright was unavailable. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `60d80ff fix(page_votes): validate vote search user`.

- RED: `.venv/bin/python -m pytest -q tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_non_user_values tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_users_without_integer_id` failed 7 parameterized cases before the fix: non-user values leaked `AttributeError`, `User(id=None)` and `User(id="12345")` reached the generic not-voted path, and `User(id=True)` matched vote user ID `1`.
- GREEN: `.venv/bin/python -m pytest -q tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_non_user_values tests/unit/test_page_votes.py::TestPageVoteCollection::test_find_rejects_users_without_integer_id` passed 7 tests after adding search-user preflight.
- `.venv/bin/python -m pytest -q tests/unit/test_page_votes.py` passed 16 tests.
- `.venv/bin/python -m pytest -q tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page_votes.py tests/unit/test_site.py` passed 260 tests.
- `.venv/bin/python -m pytest -q tests/unit` passed 1066 tests.
- `.venv/bin/ruff check src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` passed.
- `.venv/bin/ruff format src/wikidot/module/page_votes.py tests/unit/test_page_votes.py` left 2 files unchanged.
- `.venv/bin/ruff check .` passed.
- `.venv/bin/ruff format --check .` passed with 81 files already formatted.
- `.venv/bin/mypy src tests` passed with no issues in 81 source files.
- `git diff --check` passed.

Not run successfully: `pyright src tests` was unavailable because neither `.venv/bin/pyright` nor a PATH `pyright` executable existed in this environment.

## Acceptance Criteria

- `collection.find(None)`, `collection.find(True)`, `collection.find("12345")`, and `collection.find({"id": 12345})` raise `ValueError("user must be an AbstractUser")`.
- `collection.find(User(id=None))`, `collection.find(User(id=True))`, and `collection.find(User(id="12345"))` raise `ValueError("user.id must be an integer")`.
- A well-formed user with an integer ID matching an existing vote still returns that vote.
- A well-formed user with an integer ID that is absent from the collection still raises the existing not-voted `ValueError`.
- Existing page vote acquisition, WhoRated parsing, `Page.vote(...)`, `Page.cancel_vote()`, returned rating handling, and vote-cache invalidation behavior remain unchanged.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private vote data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Rejecting `User(id=True)` tightens behavior for a value that could previously match integer ID `1`. Mitigation: `bool` is not a meaningful user ID even though it is an `int` subclass, and accepting it can hide caller payload bugs.
- Risk: Requiring `AbstractUser` could reject duck-typed objects with only an `id` attribute. Mitigation: the documented API type is `AbstractUser`; real `User` instances and other `AbstractUser` subclasses remain accepted.
- Risk: Diagnostics could expose private vote context. Mitigation: the new error messages contain only the input-field name and expected type, not vote values, usernames, response bodies, page content, or site names.

## Dependencies

- Existing `PageVoteCollection` storage and iteration semantics remain authoritative for valid users.
- Existing WhoRated acquisition and page vote mutation code remain unchanged.
- The helper is local to `src/wikidot/module/page_votes.py` and does not affect page lookup, site user lookup, or vote writes.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, or complexity candidates outside this now-covered page vote find-user validation path.

## Upstream-Safe Motivation

Vote lookup is often fed by generated ledgers, audit scripts, moderation reports, or corpus joins. Since `find(...)` compares the supplied user ID against stored vote user IDs, malformed search users should fail deterministically before collection scanning rather than leaking attribute errors, producing misleading not-voted misses, or accidentally matching a boolean ID to integer ID `1`.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established page vote data as a practical workflow through vote-list acquisition, WhoRated parser diagnostics, response-body diagnostics, cache invalidation after successful mutations, and vote-value input validation.
- Existing page vote drafts covered fetching, parsing, response diagnostics, cache invalidation, and `Page.vote(value=...)`; they did not validate the caller-provided `PageVoteCollection.find(user=...)` search target.
- This slice only validates `PageVoteCollection.find(...)` inputs. It does not change WhoRated parsing, vote response-body validation, page vote acquisition, `Page.vote(...)`, `Page.cancel_vote()`, rating action status handling, vote-cache invalidation, page source/revision/file caches, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw vote response bodies, vote data, source text from real sites, private page content, and private site data out of upstream discussion.

## Additional Notes

The change intentionally rejects malformed search users instead of coercing or duck-typing them. Callers that load vote search targets from JSON, YAML, CLI flags, spreadsheets, generated structures, or audit ledgers should resolve them into `AbstractUser` instances with integer IDs before calling `PageVoteCollection.find(...)`.
