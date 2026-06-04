# PR Draft: Include Context In Malformed Page Rating Points Errors

## Summary

`Page.vote(...)` and `Page.cancel_vote()` send Wikidot rating actions and then use the returned `points` value to update the local page rating. Earlier local slices established page vote acquisition as a practical read-heavy surface by hardening WhoRated retry behavior, duplicate page handling, parser scoping, response-body validation, mismatch diagnostics, and malformed vote-value parsing. One adjacent action-response gap remained in the mutation path: if a `ratePage` or `cancelVote` response omitted `points`, or returned a non-integer `points` value, wikidot.py leaked a raw Python `KeyError` or `ValueError` instead of identifying the affected site, page, event, and field.

This follow-up keeps successful vote and cancel-vote behavior unchanged. It only routes rating action `points` through a small parser helper. Missing or malformed `points` now raises `NoElementException` with site, page, page ID, event, field, and raw value context before the page's local `rating` cache is updated.

## Related Issue

Builds on [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), and [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md). Those drafts established page voting and vote inspection as practical workflow surfaces and established the adjacent diagnostic pattern for malformed generated vote data.

No upstream issue was filed from this local workspace.

## Changes

- Add a small rating action `points` parser for `Page.vote(...)` and `Page.cancel_vote()`.
- Convert a missing `points` field into `NoElementException` with site, page, page ID, event, and field context.
- Convert a non-integer `points` value into `NoElementException` with site, page, page ID, event, field, and raw value context.
- Add focused public-interface regressions for missing `ratePage` points and malformed `cancelVote` points.
- Preserve login checks, vote value validation, rating action request payloads, successful positive/negative vote behavior, successful cancel-vote behavior, and local rating updates on valid responses.

## Type Of Change

- Bug fix / diagnostics improvement
- Page rating action response validation
- Test addition

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| A `ratePage` response missing `points` fails with wikidot.py's contextual parser exception rather than raw dictionary access. | `TestPageWriteMethods.test_vote_missing_points_includes_site_page_event_and_field_context` returns `{"status": "ok", "type": "P"}` from the action response and asserts `NoElementException`. | A raw `KeyError`, fabricated rating, generic error, or swallowed failure rejects this local completion claim. |
| A `cancelVote` response with non-integer `points` fails with wikidot.py's contextual parser exception rather than a raw conversion exception. | `TestPageWriteMethods.test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context` returns `points="not-a-number"` and asserts `NoElementException`. | A raw `ValueError`, fabricated rating, silent coercion, or swallowed failure rejects this local completion claim. |
| Malformed rating action errors identify the affected site, page, page ID, event, field, and raw value when present. | The focused regressions assert messages for `site: test-site`, `page: test-page`, `id=12345`, `event=ratePage` or `event=cancelVote`, `field=points`, and `value=not-a-number` for the malformed value path. | Omitting site, page fullname, page ID, event, field, or raw malformed value makes the failure ambiguous and rejects this local completion claim. |
| Malformed rating action responses do not update the local page rating. | Both focused regressions assert `mock_page_with_id.rating == 10` after the exception. | Updating the local rating after malformed response parsing rejects this local completion claim. |
| Successful vote and cancel-vote workflows remain unchanged. | `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_vote_negative tests/unit/test_page.py::TestPageWriteMethods::test_vote_invalid_value_raises tests/unit/test_page.py::TestPageWriteMethods::test_vote_not_logged_in tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success -q` passed 5 tests. | Regressions in request payloads, login behavior, invalid input handling, returned rating, or local rating updates reject this local completion claim. |
| Adjacent page, vote, and site workflows remain green. | `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 219 tests. | Regressions in page reads, page writes, page vote acquisition, page vote collection behavior, site page accessors, publish helpers, or recent changes reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check`; `uv run ruff format --check`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `def85c8 fix(page): report malformed rating points`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_points_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context -q` failed before the fix with raw `KeyError: 'points'` and raw `ValueError: invalid literal for int() with base 10: 'not-a-number'`.
- GREEN: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_points_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context -q` passed 2 tests after the helper was added.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_vote_negative tests/unit/test_page.py::TestPageWriteMethods::test_vote_invalid_value_raises tests/unit/test_page.py::TestPageWriteMethods::test_vote_not_logged_in tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 219 tests.
- `uv run pytest tests/unit -q` passed 793 tests.
- `uv run ruff check`.
- `uv run ruff format --check`.
- `git diff --check`.
- `uv run mypy src tests`.

Not run successfully: `uv run pyright --version` because this environment could not find a `pyright` executable.

## Acceptance Criteria

- A rating action response missing `points` raises `NoElementException`.
- A rating action response with non-integer `points` raises `NoElementException`.
- Malformed rating action messages include the site `unix_name`, page fullname, page ID, event name, field name, and raw malformed value when present.
- The page's local `rating` value remains unchanged after malformed action response parsing.
- Successful positive vote, negative vote, cancel vote, invalid input rejection, and login enforcement remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Rating mutations are small action workflows, but callers still rely on their returned `points` value to keep local page state in sync. If Wikidot emits a malformed rating response, wikidot.py should fail rather than inventing a rating or leaking generic Python exceptions. The failure should identify the site, page, event, field, and raw value so maintainers can triage from logs without storing raw action responses or page content.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts repeatedly identified page vote acquisition and page mutation helpers as practical workflow surfaces by improving retry behavior, duplicate grouping, cache reuse, parser scoping, vote mismatch diagnostics, and malformed generated vote value handling.
- Adjacent response-field slices showed that field-aware `NoElementException` messages improve resumable plain-text diagnostics without changing successful behavior or live Wikidot semantics.
- The refreshed complexity memo continues to list action/read boundaries and remaining parser messages as useful leads, and this slice addresses one narrow malformed-response boundary in the page rating mutation path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, raw action responses, vote data, and site contents out of upstream discussion.

## Additional Notes

This slice intentionally does not change login checks, allowed vote values, retry policy, rating action request construction, successful returned rating semantics, page vote collection, WhoRated parsing, page lookup, metadata writes, publish helpers, or live Wikidot behavior. It only converts missing and malformed rating action `points` values into contextual parser errors before local rating state is updated.
