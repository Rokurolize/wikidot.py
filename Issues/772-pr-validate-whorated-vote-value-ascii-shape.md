# PR Draft: Validate WhoRated Vote Value ASCII Shape

## Summary

`PageCollection.get_page_votes()` parses `pagerate/WhoRatedPageModule` vote values by preserving `+`, preserving `-`, and otherwise converting value text with `int(value_text)`. Earlier local work converted malformed non-integer values such as `not-a-vote` into contextual `NoElementException`, but Python `int(...)` still accepts Unicode digit glyphs. A generated vote value like `"\uff11"` could therefore be normalized into integer `1` before `PageVote` constructor validation ever saw it.

This change makes the WhoRated value parser accept only `+`, `-`, and ASCII signed integer text before integer conversion. The existing contextual malformed-value exception remains the public failure mode. ASCII integer vote values remain supported.

## Outcome

Generated WhoRated vote values now follow the same ASCII numeric boundary used by adjacent parser scalar fields. Unicode digit glyphs no longer silently become normal vote records.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators using browser-free WhoRated inventories, rating audit ledgers, moderation reports, duplicate cached vote-list reuse, lazy `Page.votes`, vote/cancel cache invalidation checks, generated migration ledgers, local fixtures, or serialized page vote snapshots.

## Current Evidence

Local rollout-backed drafts repeatedly identify page vote acquisition as a practical workflow surface. Existing drafts [065-pr-deduplicate-page-vote-fetches.md](065-pr-deduplicate-page-vote-fetches.md), [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [129-pr-reuse-cached-duplicate-page-votes.md](129-pr-reuse-cached-duplicate-page-votes.md), [154-pr-page-vote-mismatch-context.md](154-pr-page-vote-mismatch-context.md), [202-pr-page-vote-mismatch-site-context.md](202-pr-page-vote-mismatch-site-context.md), [223-pr-page-vote-batch-response-body-context.md](223-pr-page-vote-batch-response-body-context.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [261-pr-page-vote-cache-invalidation.md](261-pr-page-vote-cache-invalidation.md), [307-pr-whorated-user-context.md](307-pr-whorated-user-context.md), [333-pr-page-vote-response-body-type-context.md](333-pr-page-vote-response-body-type-context.md), [337-pr-page-rating-action-status-context.md](337-pr-page-rating-action-status-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [374-pr-validate-page-vote-find-user.md](374-pr-validate-page-vote-find-user.md), [416-pr-validate-page-votes-assignments.md](416-pr-validate-page-votes-assignments.md), [418-pr-validate-page-vote-collection-initialization.md](418-pr-validate-page-vote-collection-initialization.md), [444-pr-validate-page-vote-page-field.md](444-pr-validate-page-vote-page-field.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), and [611-pr-validate-page-vote-user-client.md](611-pr-validate-page-vote-user-client.md) establish vote reads, parser diagnostics, response diagnostics, public write-value validation, lookup validation, cache invalidation, assignment validation, direct record-state validation, retained-owner validation, and actor/client coherence as active operational boundaries.

This slice is not a duplicate of [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md). Issue 241 catches values that are neither `+`, `-`, nor accepted by integer conversion and reports site/page/id/value context. It does not constrain Python's accepted integer string grammar.

This slice is not a duplicate of [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md). Issue 353 validates the public write-side `Page.vote(value=...)` argument before remote action work; this issue covers generated read-side WhoRated markup.

This slice is not a duplicate of [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md). Issue 469 validates direct `PageVote(...)` constructor state after parsing; it cannot detect Unicode digit normalization once the parser has already produced a native integer.

This slice follows the adjacent ASCII-shape parser pattern from recent generated scalar fixes such as [756-pr-validate-page-revision-row-id-ascii-shape.md](756-pr-validate-page-revision-row-id-ascii-shape.md), [761-pr-validate-page-revision-number-ascii-shape.md](761-pr-validate-page-revision-number-ascii-shape.md), and [767-pr-validate-listpages-integer-field-ascii-shape.md](767-pr-validate-listpages-integer-field-ascii-shape.md).

No upstream issue was filed from this local workspace.

## Related Issues

Builds directly on [093-pr-scope-who-rated-vote-parsing.md](093-pr-scope-who-rated-vote-parsing.md), [241-pr-whorated-vote-value-parse-context.md](241-pr-whorated-vote-value-parse-context.md), [353-pr-validate-page-vote-values.md](353-pr-validate-page-vote-values.md), [469-pr-validate-page-vote-user-value-fields.md](469-pr-validate-page-vote-user-value-fields.md), and [767-pr-validate-listpages-integer-field-ascii-shape.md](767-pr-validate-listpages-integer-field-ascii-shape.md).

## Changes

- Require generated WhoRated integer vote text to match ASCII signed integer shape before calling `int(...)`.
- Preserve existing `+` and `-` vote symbol behavior.
- Preserve existing ASCII integer vote text behavior, including values outside `1` and `-1` used by broader rating fixtures.
- Convert non-ASCII digit vote text into the existing contextual `NoElementException`.
- Add a focused RED/GREEN regression for a fullwidth digit vote value.
- Add a preservation regression for ASCII integer vote text.

## Type Of Change

- Parser validation
- Page vote read-path hardening
- Regression tests

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A generated WhoRated vote value containing a fullwidth digit must raise `NoElementException` before a `PageVote` row is created. |
| R2 | The malformed-value exception must include site, page, page ID, field, and the original value text. |
| R3 | Existing `+` and `-` vote symbol behavior must remain unchanged. |
| R4 | Existing ASCII integer vote text behavior must remain supported. |
| R5 | Existing WhoRated response parsing, non-vote span filtering, mismatch diagnostics, user parsing, duplicate cached vote reuse, lazy vote acquisition, and vote collection behavior must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private page/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | RED/GREEN, affected page vote tests, adjacent page/site tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Unicode digit glyph vote text is rejected at the parser boundary. | `TestPageCollectionAcquire.test_acquire_votes_rejects_non_ascii_digit_vote_value` failed RED because no exception was raised, then passed GREEN after the ASCII-shape guard was added. | Normalizing `"\uff11"` to `1`, creating a partial vote collection, or silently skipping the vote rejects this local completion claim. | WhoRated vote parser | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | The malformed-value error remains contextual. | The focused regression asserts `WhoRated vote value is malformed for site: test-site, page: test-page (id=12345, field=vote_value, value=\uff11)`. | Omitting site, page, page ID, field, or original value text makes the failure ambiguous and rejects this local completion claim. | Parser diagnostics | `tests/unit/test_page.py` |
| R3 | Vote symbols still parse as before. | Existing WhoRated success and non-vote span tests passed in the affected page acquisition suite. | Regressing `+` to `1`, `-` to `-1`, or surrounding-markup filtering rejects this local completion claim. | WhoRated vote parser | `tests/unit/test_page.py` |
| R4 | ASCII integer text remains valid. | `TestPageCollectionAcquire.test_acquire_votes_accepts_ascii_integer_vote_value` passed and asserted values `[5, 1, -1]`. | Rejecting ASCII integer text or coercing it to a different value rejects this local completion claim. | WhoRated vote parser | `tests/unit/test_page.py` |
| R5 | Adjacent page vote behavior remains compatible. | Focused 5 vote parser tests passed, affected PageCollectionAcquire plus page vote tests passed 142 tests, adjacent page/page-votes/site tests passed 831 tests, and full unit passed 3782 tests. | Regressing page-ID acquisition, response-body validation, user/value mismatch diagnostics, user parsing, duplicate vote propagation, cache reuse, vote collection behavior, page writes, or site workflows rejects this local completion claim. | Page vote workflows | `tests/unit/test_page.py`, `tests/unit/test_page_votes.py`, `tests/unit/test_site.py`, `tests/unit` |
| R6 | No live site state or private material is needed. | All regressions use synthetic unit-level HTML and local mocks. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private page/user content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | RED/GREEN, affected tests, adjacent tests, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `217e73e fix(page): reject non-ascii whorated vote digits`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_rejects_non_ascii_digit_vote_value -q --tb=short` failed before the fix with `DID NOT RAISE` because the fullwidth digit vote text was accepted.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_malformed_value_includes_site_page_and_value_context tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_accepts_ascii_integer_vote_value tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_rejects_non_ascii_digit_vote_value tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_ignores_non_vote_colored_spans tests/unit/test_page.py::TestPageCollectionAcquire::test_acquire_votes_mismatch_includes_site_context -q` passed 5 tests.
- `uv run pytest tests/unit/test_page.py::TestPageCollectionAcquire tests/unit/test_page_votes.py -q` passed 142 tests.
- `uv run pytest tests/unit/test_page.py tests/unit/test_page_votes.py tests/unit/test_site.py -q` passed 831 tests.
- `uv run pytest tests/unit -q` passed 3782 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no blocking change-propagation, cognitive-load, duplication, accidental-complexity, dependency, domain-model, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Evidence reported CLI `0.5.0`, branch `roku-local-codex-goal`, commit `d89ca91`, `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.139.0"`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- A generated WhoRated vote value containing `"\uff11"` raises `NoElementException`.
- The malformed-value message includes the site `unix_name`, representative page fullname, page ID, field name, and original value text.
- The affected page's `_votes` cache remains unset after malformed value parsing.
- `+`, `-`, and ASCII integer vote values keep the existing behavior.
- Existing WhoRated parser scoping, non-vote colored span filtering, mismatch diagnostics, user parsing, response-body validation, duplicate cached vote reuse, vote collection behavior, lazy `Page.votes`, vote mutation behavior, and adjacent site/page workflows remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tightening parser input could reject a value Wikidot intentionally emits. Mitigation: the parser still preserves `+`, `-`, and ASCII integer text, which were the documented local semantics after Issue 241.
- Risk: The fix could remove broader numeric rating support. Mitigation: an explicit preservation regression verifies ASCII integer text still parses, including value `5`.
- Risk: The same malformed-value message path could hide the Unicode-specific cause. Mitigation: the message includes the original value text, and the draft documents the ASCII-shape requirement.

## Dependencies

- `PageCollection.get_page_votes()` still owns WhoRated generated-module parsing.
- `PageVote` still validates constructed vote rows after parsing.
- Existing page vote cache, duplicate propagation, vote mutation, response-body validation, and live Wikidot request behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, response-shape validation, result ergonomics, action/read boundaries, or measured complexity candidates outside this now-covered WhoRated vote-value ASCII boundary.

## Upstream-Safe Motivation

Adjacent generated numeric parsers already avoid Unicode digit normalization because response markup is a protocol boundary, not a free-form localized number field. WhoRated vote values should do the same: accept the known symbols and ASCII integer text, and fail contextually for other shapes instead of silently creating normalized vote records.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: fullwidth digit vote text was accepted as a normal integer vote.
- Existing local drafts covered WhoRated parser scoping, non-integer malformed value diagnostics, public write-value validation, direct vote row value type validation, and adjacent generated ASCII scalar fields; they did not cover Unicode digit normalization inside the WhoRated parser.
- This slice only changes generated WhoRated vote-value parsing. It does not change request construction, paging, retry policy, response-body validation, user parsing, `PageVote` construction rules, cached vote reuse, duplicate page propagation, vote mutation methods, or live Wikidot behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, page or user names from private workflows, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.

## Additional Notes

The change intentionally checks string shape before `int(...)` rather than checking the resulting integer. Once `int(...)` has normalized the text, downstream `PageVote` validation can no longer distinguish ASCII protocol digits from other accepted Python digit glyphs.
