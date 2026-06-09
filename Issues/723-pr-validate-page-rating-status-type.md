# PR Draft: Validate Page Rating Action Status Type

## Summary

`Page.vote(...)` and `Page.cancel_vote()` both consume Wikidot `RateAction` payloads before updating local `Page.rating` and clearing cached `Page.votes`. Issue [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md) covered missing rating action `status` and explicit non-ok string statuses, but present non-string values such as `{"status": ["not-ok"]}` were still routed into `WikidotStatusCodeException` as if they were real Wikidot status codes. This change rejects malformed generated rating action data before parsing `points`, updating local rating, or invalidating the cached vote list.

## Outcome

Page rating actions now distinguish malformed action-response shape from real Wikidot status-code failures, preserving existing string-status behavior while surfacing type-corrupt generated responses with site, page, page ID, event, field, and type context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page voting, rating audits, moderation tooling, page publication checks, generated vote ledgers, migration scripts, or local fixtures where malformed rating action responses must not be mistaken for confirmed Wikidot action results.

## Current Evidence

Local rollout-backed drafts already identify browser-free page rating reads and writes as practical shared workflows. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), and [561-pr-validate-page-vote-site.md](561-pr-validate-page-vote-site.md) cover vote-list fetching, rating points parsing, action status presence/non-ok strings, vote-value validation, cache invalidation after confirmed successful mutations, and vote-time parent-site validation.

Adjacent action-status type drafts [714-pr-validate-page-save-status-type.md](714-pr-validate-page-save-status-type.md), [715-pr-validate-private-message-send-status-type.md](715-pr-validate-private-message-send-status-type.md), [716-pr-validate-site-application-action-status-type.md](716-pr-validate-site-application-action-status-type.md), [717-pr-validate-site-member-action-status-type.md](717-pr-validate-site-member-action-status-type.md), [718-pr-validate-site-invite-action-status-type.md](718-pr-validate-site-invite-action-status-type.md), [719-pr-validate-forum-category-create-thread-status-type.md](719-pr-validate-forum-category-create-thread-status-type.md), [720-pr-validate-forum-thread-reply-status-type.md](720-pr-validate-forum-thread-reply-status-type.md), [721-pr-validate-forum-post-edit-status-type.md](721-pr-validate-forum-post-edit-status-type.md), and [722-pr-validate-page-action-status-type.md](722-pr-validate-page-action-status-type.md) establish the same module-level response-shape pattern on other mutation actions. Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) is not a duplicate: it covers raw Ajax Module Connector response envelope status typing before module-level action payload handling. This slice validates the rating action payload consumed by `Page.vote(...)` and `Page.cancel_vote()`. No upstream issue was filed from this local workspace.

## Changes

- Add a type guard in the page rating action status extractor.
- Raise `NoElementException` for a present non-string `status` with site, page fullname, page ID, event, field, expected type, and actual type context.
- Preserve Issue 337 missing-status diagnostics.
- Preserve explicit non-ok string handling through `WikidotStatusCodeException`.
- Preserve Issue 244 rating `points` parsing after confirmed `status: ok`.
- Add a `Page.vote(...)` regression proving malformed `ratePage` status types preserve local rating and cached votes.
- Add a `Page.cancel_vote()` regression proving malformed `cancelVote` status types preserve local rating and cached votes.

## Type Of Change

- Response-shape validation
- Page rating action hardening
- Generated response data diagnostics
- Cache/state consistency preservation
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.vote(...)` must reject a non-string `ratePage` response `status` with `NoElementException` containing site, page fullname, page ID, event, `field=status`, `expected=str`, and the actual type. |
| R2 | `Page.cancel_vote()` must reject a non-string `cancelVote` response `status` with the same malformed action status context. |
| R3 | Missing `status` fields must keep the existing Issue 337 missing-status diagnostics. |
| R4 | Explicit non-ok string statuses must still raise `WikidotStatusCodeException`. |
| R5 | Malformed, missing, and explicit non-ok action statuses must not update local rating or clear cached votes. |
| R6 | Valid successful positive vote, negative vote, cancel-vote, returned rating updates, and successful vote-cache invalidation must remain unchanged. |
| R7 | Adjacent page/site/vote workflows and repository quality gates must remain green. |
| R8 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private vote data, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `{"status": ["not-ok"], "type": "P", "points": 11}` from `ratePage` fails with malformed action status context. | `test_vote_malformed_action_status_type_does_not_update_local_state` failed RED with `WikidotStatusCodeException`, then passed GREEN after status typing was added. | Treating a list, dict, number, or object as a Wikidot status code rejects this local completion claim. | Page vote action response shape | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | `{"status": ["not-ok"], "type": "P", "points": 7}` from `cancelVote` fails with malformed action status context. | `test_cancel_vote_malformed_action_status_type_does_not_update_local_state` passed after the shared helper guard and asserts local rating plus cached votes remain intact. | Updating rating, clearing cached votes, or treating malformed status as a cancel-vote status-code failure rejects this local completion claim. | Page cancel-vote action response shape | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Missing status fields still raise the Issue 337 missing-status message. | `test_vote_missing_action_status_does_not_update_local_state` passed unchanged in focused GREEN. | Changing missing-status exception type, dropping context, or masking it behind type/status-code handling rejects this local completion claim. | Page rating missing status | `tests/unit/test_page.py` |
| R4 | `{"status": "not_ok"}` keeps the status-code path. | `test_cancel_vote_non_ok_action_status_does_not_update_local_state` passed and asserts `status_code == "not_ok"`. | Reclassifying non-ok strings as malformed response shape rejects this local completion claim. | Page rating status-code handling | `tests/unit/test_page.py` |
| R5 | Malformed, missing, and explicit non-ok statuses preserve local rating and cached votes. | The status regressions assert unchanged `rating` and non-cleared `_votes`. | Updating local rating, clearing cached votes, or parsing `points` before classifying malformed/failed action status rejects this local completion claim. | Page mutation/cache boundary | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R6 | Successful valid vote/cancel behavior remains stable. | Focused GREEN covered `test_vote_positive`, `test_vote_success_invalidates_cached_votes`, `test_vote_negative`, `test_cancel_vote_success`, and `test_cancel_vote_success_invalidates_cached_votes`; `TestPageWriteMethods` passed 67 tests. | Regressing login, request payloads, returned rating values, allowed vote values, or cache invalidation after confirmed success rejects this local completion claim. | Vote/cancel workflows | `tests/unit/test_page.py` |
| R7 | Adjacent page behavior and repo quality gates remain green. | Page module passed 388 tests, adjacent page/site coverage passed 1105 tests, full unit passed 3595 tests, ruff, mypy, pyright, and `git diff --check` passed. | Any test, lint, format, type, or whitespace failure rejects this local completion claim. | Repository quality gates | `tests/unit`, `src`, `tests` |
| R8 | No live site state or private material is needed to prove the behavior. | The regressions use synthetic unit-level response bodies and mocks only. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, live Wikidot actions, private vote data, private page content, raw rollout paths, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `34d87c2 fix(page): validate rating status type`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_malformed_action_status_type_does_not_update_local_state -q` failed before the fix with `WikidotStatusCodeException` instead of the expected malformed-shape `NoElementException`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_points_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_vote_malformed_action_status_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_vote_negative tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_non_ok_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_action_status_type_does_not_update_local_state -q` passed 11 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 67 tests.
- `uv run pytest tests/unit/test_page.py -q` passed 388 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_site.py tests/unit/test_page_file.py tests/unit/test_page_revision.py tests/unit/test_page_source.py tests/unit/test_page_votes.py -q` passed 1105 tests.
- `uv run pytest tests/unit -q` passed 3595 tests.
- `uv run ruff format src/wikidot/module/page.py tests/unit/test_page.py` left both files unchanged.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `{"status": ["not-ok"]}` from `ratePage` raises `NoElementException` with site, page fullname, page ID, event, `field=status`, `expected=str`, and `actual=list` context.
- `{"status": ["not-ok"]}` from `cancelVote` raises the same malformed status type context.
- Missing `status` values still raise the existing missing-status message from Issue 337.
- `{"status": "not_ok"}` still raises `WikidotStatusCodeException`.
- Malformed, missing, and explicit non-ok statuses do not update local `Page.rating`.
- Malformed, missing, and explicit non-ok statuses do not clear cached page votes before a confirmed successful rating mutation.
- Successful positive votes, negative votes, and cancel-vote calls keep the existing login checks, request payloads, rating updates, vote-cache invalidation, and return values.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private vote data, private page data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A caller may have relied on a non-string `status` object being formatted into a `WikidotStatusCodeException`. Mitigation: Wikidot action statuses are strings, Issue 403 already validates raw AMC statuses as strings, and module-level action responses should reject malformed generated data before business handling.
- Risk: This could be confused with rating missing-status handling. Mitigation: Issue 337 covers missing status and non-ok string status; this slice covers a present status with malformed type.
- Risk: This could be confused with page save or non-metadata page action status typing. Mitigation: Issue 714 covers `Page.create_or_edit(...)` `savePage`; Issue 722 covers `deletePage`/`renamePage`; this slice covers `ratePage`/`cancelVote`.
- Risk: This could be confused with page metadata action responses. Mitigation: metadata helpers are separate response surfaces and should only be changed after their own duplicate check.
- Risk: Tightening action response shape could hide legitimate non-ok Wikidot string statuses. Mitigation: non-ok strings are deliberately preserved on the existing `WikidotStatusCodeException` path.
- Risk: The error could become too generic for generated fixtures. Mitigation: the diagnostic names the site, page fullname, page ID, event, field, expected type, and actual type.

## Dependencies

- Existing `Page.vote(...)` remains responsible for vote request construction, returned `points` parsing, local rating update, and vote-cache invalidation only after confirmed successful rating status.
- Existing `Page.cancel_vote()` remains responsible for cancel-vote request construction, returned `points` parsing, local rating update, and vote-cache invalidation only after confirmed successful cancel status.
- Existing `WikidotStatusCodeException` handling remains responsible for explicit non-ok string statuses.
- Existing `NoElementException` remains the parser/data-shape exception for missing or malformed response fields.
- No new dependency, live Wikidot action, credential, or upstream API change is required.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, complexity candidates, page metadata action status type guards, or other response-shape candidates outside this now-covered page rating action status type path.

## Upstream-Safe Motivation

`Page.vote(...)` and `Page.cancel_vote()` treat `ratePage` and `cancelVote` responses as status-bearing action payloads before parsing returned rating points, updating local `Page.rating`, and invalidating cached vote lists. Rejecting malformed status types at that boundary keeps generated or adapted response data from masquerading as a real Wikidot status code and makes rating mutation failures easier to diagnose without changing successful actions or valid string status handling.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established browser-free page rating reads, rating mutations, vote-list cache behavior, moderation ledgers, migration ledgers, and page action diagnostics as practical consumers of vote/cancel behavior.
- Existing page-rating and raw AMC drafts covered missing action status context, explicit non-ok action strings, returned `points` parsing, vote-value validation, vote-time parent-site validation, successful vote-cache invalidation, and raw connector envelope status typing; they did not validate the page rating action status type.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, raw action response bodies, private vote data, private page content, private site data, and source text from real sites out of upstream discussion.
