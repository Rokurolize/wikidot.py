# PR Draft: Validate Page Rating Action Status Before Local Updates

## Summary

`Page.vote(...)` and `Page.cancel_vote()` send Wikidot `RateAction` mutations, then parse the returned `points` value and update the local page rating and cached vote-list state. Issue 244 made malformed `points` values contextual, and Issue 261 invalidated cached votes after successful rating mutations. One adjacent action-response boundary remained: a response with `points` but no `status`, or a non-`ok` `status` with `points`, could still be treated as a successful local rating mutation.

This local slice validates the returned rating action `status` before parsing `points` or mutating local state. Missing status now raises `NoElementException` with site, page, page ID, event, and field context. Non-`ok` status now raises `WikidotStatusCodeException`. Successful `status: ok` vote and cancel-vote behavior, request payloads, `points` parsing, rating updates, and vote-cache invalidation remain unchanged.

## Outcome

Malformed or failed rating action responses no longer update the local page rating or clear the cached vote list solely because a `points` field is present.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream callers using browser-free page voting, rating audits, moderation tooling, or publish-adjacent workflows that rely on local `Page.rating` consistency after mutations.

## Related Issue

Builds on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), and [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md). Those drafts established page voting as a practical read/write surface with retry-aware reads, contextual response parsing, and local cache consistency rules.

No upstream issue was filed from this local workspace.

## Changes

- Add a rating action status validator for `Page.vote(...)` and `Page.cancel_vote()`.
- Validate `status` before parsing `points` or updating local `rating` / `_votes`.
- Convert missing rating action `status` into contextual `NoElementException`.
- Convert non-`ok` rating action `status` into `WikidotStatusCodeException`.
- Preserve existing malformed `points` diagnostics for `status: ok` responses.
- Add focused public-interface regressions for missing `ratePage` status and non-`ok` `cancelVote` status.

## Type Of Change

- Bug fix / action-response validation
- Page rating local-state consistency
- Test update

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.vote(...)` must reject a response that has `points` but lacks `status` before updating local state. |
| R2 | `Page.cancel_vote()` must reject a response with non-`ok` `status` even when `points` is present. |
| R3 | Rating action status diagnostics must identify site, page, page ID, event, and field without logging raw action response bodies. |
| R4 | Existing `status: ok` vote, cancel-vote, malformed-points, invalid-input, and login behavior must remain compatible. |
| R5 | Focused, page-write, adjacent page/vote/site, full unit, lint, format, type, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | A `ratePage` response `{"type": "P", "points": 11}` raises contextual `NoElementException` and leaves `rating` plus `_votes` unchanged. | `TestPageWriteMethods.test_vote_missing_action_status_does_not_update_local_state` asserts the message `Page rating action response is malformed for site: test-site, page: test-page (id=12345, event=ratePage, field=status)`. | Returning success, parsing `points`, updating `rating`, clearing `_votes`, or raising a raw `KeyError` rejects this local completion claim. | Page vote action status | `tests/unit/test_page.py` |
| R2 | A `cancelVote` response `{"status": "not_ok", "type": "P", "points": 7}` raises `WikidotStatusCodeException("not_ok")` and leaves `rating` plus `_votes` unchanged. | `TestPageWriteMethods.test_cancel_vote_non_ok_action_status_does_not_update_local_state` asserts `status_code == "not_ok"` and unchanged local state. | Treating `points` as success, updating `rating`, clearing `_votes`, swallowing the failure, or raising a generic parser error rejects this local completion claim. | Page cancel-vote action status | `tests/unit/test_page.py` |
| R3 | Missing status diagnostics include structural identifiers and omit raw response payloads. | The focused missing-status regression matches the full context string using only site/page/id/event/field. | Including raw response JSON, private vote data, credentials, local rollout paths, account names, or page content rejects this local completion claim. | Rating action diagnostics | `src/wikidot/module/page.py` |
| R4 | Existing successful and malformed-points behavior remains green. | Focused GREEN included success, missing-points, malformed-points, and both new status regressions. `TestPageWriteMethods` passed 37 tests. | Regressing request payloads, allowed vote values, login guard, returned ratings, malformed-points messages, or cache invalidation rejects this local completion claim. | Page write methods | `tests/unit/test_page.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Full unit passed 913 tests; `ruff`, format check, `mypy`, and whitespace checks passed before the code commit; `pyright` remained unavailable in this environment. | Test, lint, format, type, or whitespace failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `01516e9 fix(page): guard rating action status`.

- RED: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_non_ok_action_status_does_not_update_local_state -q` failed before the fix because neither test raised: current code accepted present `points` without validating `status`.
- GREEN: `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_non_ok_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_points_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success -q` passed 6 tests.
- `uv run --extra test pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 37 tests.
- `uv run --extra test pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 261 tests.
- `uv run --extra test pytest tests/unit -q` passed 913 tests.
- `uv run ruff format src tests` left 80 files unchanged.
- `uv run ruff check src tests` passed.
- `uv run ruff format --check src tests` passed with 80 files already formatted.
- `uv run mypy src tests` passed with no issues in 80 source files.
- `git diff --check` passed.

Not run successfully: `uv run pyright src tests` failed because this environment could not spawn a `pyright` executable.

## Acceptance Criteria

- `Page.vote(...)` validates rating action `status` before parsing `points`.
- `Page.cancel_vote()` validates rating action `status` before parsing `points`.
- Missing `status` raises `NoElementException` with site/page/page ID/event/field context.
- Non-`ok` `status` raises `WikidotStatusCodeException` and preserves the returned status code.
- Missing or malformed `points` on `status: ok` responses keeps the existing contextual `NoElementException` behavior.
- Failed or malformed rating action responses do not change local `rating` or clear `_votes`.
- Successful positive vote, negative vote, cancel-vote, invalid input rejection, login enforcement, returned rating values, and successful vote-cache invalidation remain unchanged.
- No live Wikidot action, upstream Issue, upstream PR, push, real action response body, account material, credentials, vote data, or private page content is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: A historical Wikidot rating response might include `points` without `status`. Mitigation: adjacent mutation helpers already require action status before accepting success; treating absent status as malformed keeps local state from being updated by an unclassified response.
- Risk: Status validation could mask malformed `points` on failed responses. Mitigation: `points` is only needed after confirmed success; failed or malformed action status should be reported before local state is synchronized from response fields.
- Risk: Diagnostics could expose vote data. Mitigation: status diagnostics include only site/page/page ID/event/field and do not include raw action response JSON or vote content.

## Dependencies

- The AMC connector already raises for present non-`ok` statuses in real non-mocked requests, but method-level status validation keeps the public method robust when tests or callers supply decoded action responses and keeps behavior consistent with adjacent page, metadata, forum, member, application, invitation, and private-message action helpers.
- Issue 244's `points` parser remains the source of truth for returned rating values after status is confirmed.

## Open Questions

None for this local slice. Remaining useful work should continue action/read boundary audits or performance/caching leads rather than expanding rating semantics beyond status validation.

## Upstream-Safe Motivation

Rating mutations are small but stateful write workflows. Callers should not observe a new local rating or a cleared vote cache from an action response that never confirmed success. Validating `status` before `points` keeps page rating mutations aligned with adjacent wikidot.py action helpers and gives callers an event-specific failure signal.

## Local Evidence, Not For Upstream Paste

- The RED tests showed that current `Page.vote(...)` and `Page.cancel_vote()` accepted present `points` without validating action status.
- Existing Issue 244 covered missing/malformed `points`, but intentionally did not prove that action `status` was required before local state updates.
- Existing Issue 261 made successful rating mutations clear cached votes, which makes status validation more important: failed or malformed actions must not clear cached vote data.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, vote data, account material, and private page content out of upstream discussion.

## Additional Notes

This is an action-response validation fix. It preserves valid rating behavior while preventing unclassified or failed rating action responses from changing local page state.
