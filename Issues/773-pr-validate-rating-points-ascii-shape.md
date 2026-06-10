# PR Draft: Validate Page Rating Points ASCII Shape

## Summary

`Page.vote(...)` and `Page.cancel_vote()` parse successful rating action responses and use the returned `points` field to update local `Page.rating` state. Earlier local work made missing and malformed `points` contextual, and made rating action `status` validation happen before local mutation, but the accepted `points` branch still converted stripped response text with `int(value_text)`. Python accepts Unicode digit glyphs, so response text such as `"\uff11\uff11"` could be normalized into integer `11` and update local rating state.

This change makes the rating action `points` parser accept only ASCII signed integer text before conversion. The existing contextual malformed-points exception remains the public failure mode. Integer values and ASCII numeric strings remain supported.

## Outcome

Rating action responses no longer use Python's broader integer grammar as the protocol boundary. Non-ASCII digit glyphs are rejected before local rating state or cached vote-list state is updated.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free page voting, rating audits, moderation tooling, publish-adjacent workflows, generated migration ledgers, or fixtures that rely on local `Page.rating` and `Page.votes` state after rating actions.

## Current Evidence

Local rollout-backed drafts repeatedly identify page rating mutations as practical read/write surfaces. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), and [772-pr-validate-whorated-vote-value-ascii-shape.md](772-pr-validate-whorated-vote-value-ascii-shape.md) establish vote reads, parser diagnostics, response diagnostics, status validation, public write-value validation, cache invalidation, and generated WhoRated value-shape validation as active operational boundaries.

This slice is not a duplicate of [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md). Issue 244 catches missing `points` and values that Python integer conversion rejects, then reports site/page/event/field/value context. It does not constrain Python's accepted integer string grammar.

This slice is not a duplicate of [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md). Issue 337 validates returned action status before parsing `points` or mutating local state; this issue covers the accepted `points` scalar shape after status is confirmed.

This slice is not a duplicate of [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md). Issue 353 validates the public `Page.vote(value=...)` input argument before remote action work; this issue covers response-side `points`.

This slice is not a duplicate of [772-pr-validate-whorated-vote-value-ascii-shape.md](772-pr-validate-whorated-vote-value-ascii-shape.md). Issue 772 covers generated WhoRated read-side vote values; this issue covers returned write-side rating action points.

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), and [772-pr-validate-whorated-vote-value-ascii-shape.md](772-pr-validate-whorated-vote-value-ascii-shape.md).

## Changes

- Require rating action `points` text to match ASCII signed integer shape before calling `int(...)`.
- Preserve integer and ASCII numeric-string `points` behavior.
- Convert non-ASCII digit `points` text into the existing contextual `NoElementException`.
- Add a focused RED/GREEN regression for fullwidth returned `points`.
- Add a preservation regression for ASCII string `points`.
- Preserve status validation, missing-points diagnostics, malformed-points diagnostics, successful vote/cancel behavior, local rating updates for valid responses, and vote-cache invalidation after successful actions.

## Type Of Change

- Response validation
- Page rating write-path hardening
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A successful rating action response whose `points` value contains fullwidth digits must raise `NoElementException` before local rating state or cached vote-list state changes. |
| R2 | The malformed-points exception must include site, page, page ID, event, field, and the original value text. |
| R3 | Existing integer and ASCII string `points` behavior must remain supported. |
| R4 | Existing missing-points, non-integer malformed-points, action-status, invalid vote input, login, vote success, cancel-vote success, and cache invalidation behavior must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | RED/GREEN, affected page write/vote tests, adjacent page/site tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Unicode digit glyph `points` text is rejected before state mutation. | `TestPageWriteMethods.test_vote_rejects_non_ascii_digit_points_before_state_update` failed RED because no exception was raised, then passed GREEN after the ASCII-shape guard was added. | Normalizing `"\uff11\uff11"` to `11`, updating `Page.rating`, clearing `_votes`, or swallowing the malformed response rejects this local completion claim. | Rating action response parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The malformed-points error remains contextual. | The focused regression asserts `Page rating response is malformed for site: test-site, page: test-page (id=12345, event=ratePage, field=points, value=\uff11\uff11)`. | Omitting site, page, page ID, event, field, or original value text makes the failure ambiguous and rejects this local completion claim. | Parser diagnostics | `tests/unit/test_page.py` |
| R3 | ASCII numeric response values remain valid. | `TestPageWriteMethods.test_vote_accepts_ascii_string_points` passed and asserted returned/local rating `11`; existing integer `points` success tests also passed. | Rejecting integer values, rejecting ASCII numeric strings, or changing returned rating values rejects this local completion claim. | Rating action response parser | `tests/unit/test_page.py` |
| R4 | Adjacent rating action behavior remains compatible. | Focused 7 rating action tests passed, affected `TestPageWriteMethods` plus page-vote coverage passed 135 tests, adjacent page/page-votes/site tests passed 833 tests, and full unit passed 3784 tests. | Regressing missing `points`, malformed text `points`, action status checks, login checks, valid vote/cancel actions, cache invalidation, page writes, or site workflows rejects this local completion claim. | Page rating workflows | `tests/unit/test_page.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R5 | No live site state or private material is needed. | All regressions use unit-level mocked responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | RED/GREEN, affected tests, adjacent tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `5b8a8a0 fix(page): validate rating points ascii shape`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_rejects_non_ascii_digit_points_before_state_update -q --tb=short` failed before the fix with `DID NOT RAISE` because fullwidth returned `points` text was accepted.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_points_includes_site_page_event_and_field_context tests/unit/test_page.py::TestPageWriteMethods::test_vote_accepts_ascii_string_points tests/unit/test_page.py::TestPageWriteMethods::test_vote_rejects_non_ascii_digit_points_before_state_update tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_points_includes_site_page_event_field_and_value_context tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_vote_negative tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success -q` passed 7 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page_votes.py -q` passed 135 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 833 tests.
- `uv run pytest tests/unit -q` passed 3784 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no blocking change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Evidence reported CLI `0.5.0`, branch `roku-local-codex-goal`, commit `d89ca91`, `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- A successful `ratePage` response with `points="\uff11\uff11"` raises `NoElementException`.
- The malformed-points message includes the site `unix_name`, representative page fullname, page ID, event name, field name, and original value text.
- Rejected malformed points do not update `Page.rating` and do not clear cached votes.
- Integer and ASCII numeric string `points` values keep the existing behavior.
- Missing `points`, malformed non-integer `points`, action-status validation, valid vote/cancel actions, invalid public vote values, login behavior, cache invalidation, adjacent page/site workflows, and full unit coverage remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening response parsing could reject a value Wikidot intentionally emits. Mitigation: the parser still accepts native integers and ASCII numeric strings, which preserve the established local semantics from Issue 244.
- Risk: The fix could mutate state before detecting malformed response values. Mitigation: the guard lives inside `_parse_page_rating_points(...)`, which is called before assigning `Page.rating` or clearing cached votes.
- Risk: This could duplicate WhoRated validation. Mitigation: Issue 772 covers read-side generated WhoRated values; this slice covers write-side action response points.

## Dependencies

- `_require_page_rating_action_status(...)` still validates action status before points parsing.
- `_parse_page_rating_points(...)` still owns successful returned rating scalar conversion.
- Existing vote request construction, login checks, cache invalidation, WhoRated parsing, page lookup, metadata writes, publish helpers, and live Wikidot behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-shape validation, result ergonomics, action/read boundaries, or measured complexity candidates outside this now-covered rating action points ASCII boundary.

## Upstream-Safe Motivation

Rating action `points` is a response protocol field that synchronizes local page state after a write. It should accept the known numeric shape and fail contextually for other shapes instead of relying on Python's permissive Unicode digit normalization.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth returned `points` text was accepted and did not raise.
- Existing local drafts covered missing/non-integer rating points, action status validation, public vote input values, and WhoRated read-side vote-value shape; they did not cover Unicode digit normalization in returned rating action `points`.
- This slice only changes successful rating action response `points` parsing. It does not change request payloads, login checks, status validation, vote-cache invalidation after valid success, WhoRated parsing, page lookup, metadata writes, publish helpers, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally checks string shape before `int(...)` rather than checking the resulting integer. Once conversion has normalized the response text, downstream state updates cannot distinguish ASCII protocol digits from other accepted Python digit glyphs.
