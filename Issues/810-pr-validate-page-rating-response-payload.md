# PR Draft: Validate Page Rating Response Payload

## Summary

`Page.vote(...)` and the shared page rating action status helper now validate that decoded `ratePage` / `cancelVote` action responses are dictionaries before reading their `status` fields. Non-mapping payloads such as `["not-ok"]` raise contextual `NoElementException` with site, page, page ID, event, expected type, and actual type context instead of leaking a raw list-index `TypeError`.

The change is intentionally narrow: valid `{"status": "ok", "points": ...}` actions, missing `status` diagnostics, non-string `status` diagnostics, explicit non-ok string status handling, `points` parsing, local rating updates, and vote-cache invalidation remain unchanged.

## Problem Statement

Page rating actions treat decoded `ratePage` and `cancelVote` responses as status-bearing JSON objects before parsing returned `points`, updating local `Page.rating`, or invalidating cached votes. Earlier local slices covered missing rating action statuses, explicit non-ok string statuses, present non-string statuses such as `{"status": ["not-ok"]}`, and malformed `points` values. One response-shape gap remained: if `response.json()` returned a non-dictionary payload, `_require_page_rating_action_status(...)` attempted `data["status"]` and leaked a raw `TypeError`.

That failure gives callers neither the rating action context nor a stable wikidot.py data-shape exception. Generated fixtures, adapters, recorded traffic, or mocked responses should be classified before field access, and failed rating responses must not update local rating or clear cached votes.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page voting, rating audits, moderation tooling, publish checks, generated vote ledgers, migration scripts, and local fixtures as practical automation surfaces: [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [152-pr-page-vote-failure-context.md](152-pr-page-vote-failure-context.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [244-pr-page-rating-points-context.md](244-pr-page-rating-points-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [561-pr-validate-page-vote-site.md](561-pr-validate-page-vote-site.md), [723-pr-validate-page-rating-status-type.md](723-pr-validate-page-rating-status-type.md), and [773-pr-validate-rating-points-ascii-shape.md](773-pr-validate-rating-points-ascii-shape.md).

This slice is not a duplicate of [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md). Issue 337 covered mapping responses that omitted `status` and explicit non-ok string statuses.

This slice is not a duplicate of [723-pr-validate-page-rating-status-type.md](723-pr-validate-page-rating-status-type.md). Issue 723 covered a present non-string `status` field inside a mapping, such as `{"status": ["not-ok"], "points": 11}`. This slice covers the decoded rating action response payload not being a mapping before `status` lookup starts.

Issue [809-pr-validate-page-action-response-payload.md](809-pr-validate-page-action-response-payload.md) covers non-rating direct page actions such as `deletePage` and `renamePage`; Issue [808-pr-validate-page-save-response-payload.md](808-pr-validate-page-save-response-payload.md) covers `savePage`; Issue [403-pr-validate-amc-response-status-type.md](403-pr-validate-amc-response-status-type.md) covers the raw Ajax Module Connector response envelope before module-level action payload handling.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free page voting through `Page.vote(...)`.
- Browser-free vote cancellation through `Page.cancel_vote()`.
- Generated vote ledgers, migration tooling, moderation/rating audits, publish checks, fixtures, and recorded-response tests that decode action responses before returning them to wikidot.py module code.

## Proposed Fix

- Change `_require_page_rating_action_status(...)` to accept an object payload.
- Reject non-dictionary payloads with `NoElementException` before field access.
- Include only structural context and type names in the diagnostic, not raw response data.
- Preserve existing missing-status, malformed-status-type, non-ok string, success, `points`, rating, and vote-cache behavior.

## Implementation Notes

Implemented locally in commit `f5240c0 fix(page): validate rating response payload`.

The implementation adds one preflight guard in `src/wikidot/module/page.py`:

```python
if not isinstance(data, dict):
    raise exceptions.NoElementException(
        f"Page rating action response is malformed for site: {site.unix_name}, page: {page.fullname} "
        f"(id={page.id}, event={event}, expected=dict, actual={type(data).__name__})"
    )
```

The RED regression mocked `Page.vote(...)`'s `ratePage` response as `["not-ok"]`. Before the fix, the helper leaked `TypeError: list indices must be integers or slices, not str`. After the fix, the same case raises contextual `NoElementException`, decodes the response once, and preserves local rating plus cached votes.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Non-dictionary rating action payloads fail before `status` lookup. | `test_vote_malformed_action_response_type_does_not_update_local_state` failed RED with raw `TypeError`, then passed GREEN. | Reaching list indexing, leaking `TypeError`, coercing the payload, parsing points, or treating a list as a status response rejects this claim. |
| Missing `status` in a dictionary keeps the existing Issue 337 diagnostic. | Focused GREEN included `test_vote_missing_action_status_does_not_update_local_state`. | Reclassifying `{}` as the payload-type branch or dropping `field=status` rejects this claim. |
| Present non-string `status` keeps the existing Issue 723 diagnostic. | Focused GREEN included vote and cancel-vote malformed status-type regressions. | Reclassifying `{"status": ["not-ok"]}` as a payload-type error or treating the list as a status code rejects this claim. |
| Explicit non-ok string statuses still use `WikidotStatusCodeException`. | Focused GREEN included `test_cancel_vote_non_ok_action_status_does_not_update_local_state`. | Reclassifying non-ok strings as malformed response shape rejects this claim. |
| Failed rating action payloads do not update local rating or clear cached votes. | The new regression asserts unchanged `rating` and preserved `_votes`. | Updating rating, clearing cached votes, or parsing `points` before confirmed action status rejects this claim. |
| Adjacent page write behavior remains stable. | `TestPageWriteMethods` passed 129 tests and `tests/unit/test_page.py` passed 481 tests. | Regressing page voting, cancel-vote, rating points parsing, page deletion, rename, tags, parent, metadata, edit, or create/edit behavior rejects this claim. |
| Repository quality gates remain green. | Full unit passed 3907 tests; ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `f5240c0 fix(page): validate rating response payload`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_malformed_action_response_type_does_not_update_local_state -q --tb=short` failed before the fix with raw `TypeError: list indices must be integers or slices, not str`.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_vote_positive tests/unit/test_page.py::TestPageWriteMethods::test_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_vote_missing_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_vote_malformed_action_response_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_vote_malformed_action_status_type_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_success_invalidates_cached_votes tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_non_ok_action_status_does_not_update_local_state tests/unit/test_page.py::TestPageWriteMethods::test_cancel_vote_malformed_action_status_type_does_not_update_local_state -q --tb=short` passed 9 tests.
- Page write coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q --tb=short` passed 129 tests.
- Page module coverage: `uv run pytest tests/unit/test_page.py -q --tb=short` passed 481 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3907 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.vote(...)` with `response.json()` returning `["not-ok"]` raises `NoElementException` matching `Page rating action response is malformed for site: test-site, page: test-page (id=12345, event=ratePage, expected=dict, actual=list)`.
- `{}` still raises the existing missing-status message with `field=status`.
- `{"status": ["not-ok"], "points": 11}` still raises the existing malformed status-type message with `expected=str, actual=list`.
- `{"status": "not_ok", "points": 7}` still raises `WikidotStatusCodeException`.
- The malformed payload branch decodes the response JSON once, preserves local rating and cached votes, and does not include raw response data.
- The new test uses unit-level synthetic values only and does not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: A caller may have relied on raw `TypeError` from malformed synthetic responses. Mitigation: the public module expects a status-bearing JSON object, and repo validation style consistently routes malformed generated response shape through contextual `NoElementException`.
- Risk: This could be confused with status-field or points validation. Mitigation: missing `status`, non-string `status`, non-ok strings, and `points` parsing are preserved and tested separately.
- Risk: This could hide raw payload details useful for debugging. Mitigation: the diagnostic includes site, page, page ID, event, expected type, and actual type while avoiding raw response data that could contain private page content or account material.

## Dependencies

- Page rating action responses remain expected to decode as JSON objects with string `status` fields and parseable `points` after confirmed success.
- `WikidotStatusCodeException` remains responsible for explicit non-ok string statuses.
- `NoElementException` remains the parser/data-shape exception for malformed module response payloads.

## Open Questions

None for this local slice. Similar non-mapping action-payload guards may be useful on page metadata, forum, site-invitation, site-application, and site-member mutation helpers, but each surface should receive its own duplicate check against the existing action-status and status-type issue series before implementation.

## Rationale for Upstream Suitability

The patch is small, local, and consistent with existing wikidot.py response-shape diagnostics. It improves failure classification for malformed page rating action responses without changing successful voting, cancel-vote behavior, `points` parsing, local rating updates, vote-cache invalidation, or existing status-code behavior.

## Local Evidence

- Local rollout-backed page drafts established voting, cancel-vote, rating reads, moderation audits, generated vote ledgers, migration tooling, and publish checks as practical consumers of page rating behavior.
- Existing local drafts covered missing rating action status context, present non-string rating action status values, raw connector envelope status typing, direct page action payloads, page save payloads, rating points parsing, rating points ASCII-shape validation, vote value validation, and vote-time parent-site validation. They did not cover a decoded rating action response payload that is not a mapping before `status` lookup.
- This slice only validates page rating action payload shape. It does not change request construction, login checks, retry behavior, page save handling, direct non-rating page action handling, metadata-specific action handling, live Wikidot behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page content, raw response bodies, private site data, and private source text out of upstream discussion.
