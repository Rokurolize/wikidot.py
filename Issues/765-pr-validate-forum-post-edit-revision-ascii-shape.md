# PR Draft: Validate Forum Post Edit Revision ID ASCII Shape

## Summary

`ForumPost.edit(...)` fetches `forum/sub/ForumEditPostFormModule`, reads the generated hidden `currentRevisionId`, and sends that value in the subsequent `saveEditPost` mutation. Issue 205 already converts missing and non-numeric edit-form revision values into site/post-context `NoElementException`, and Issue 649 already rejects negative edit-form revision IDs before save. One accepted-value gap remained: the accepted branch still used `int(str(revision_value))`, so Python accepted Unicode decimal digit strings such as `\uff19\uff10\uff10\uff11` and normalized them into ordinary `currentRevisionId=9001`.

This change requires the generated edit-form `currentRevisionId` value to match ASCII `-?[0-9]+` before integer conversion. Valid ASCII values such as `9001` continue to save normally, non-numeric values keep the established malformed-value diagnostic, negative ASCII values keep the established non-negative diagnostic, and Unicode digit-like values now fail before `saveEditPost` is attempted.

## Outcome

Forum post editing no longer fabricates mutation revision IDs by normalizing malformed generated edit-form state. A returned edit form with fullwidth, Arabic-Indic, superscript, or other non-ASCII digit-like `currentRevisionId` text now fails at the read-before-mutation boundary with site and post context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free forum editing, moderation tooling, discussion migration scripts, generated forum maintenance workflows, local fixtures, or adapters where malformed hidden edit-form state must never become a mutation payload.

## Current Evidence

Local rollout-backed drafts repeatedly identify `ForumPost.edit(...)` as a practical browser-free mutation workflow. Existing drafts cover retry-aware edit-form fetches, edit-form direct-child scoping, missing current-revision controls, missing revision values, malformed non-numeric revision values, missing and typed edit-form response bodies, save action status validation, save action status typing, edit revision-cache invalidation, retained post/thread ID validation, and negative edit-form revision IDs.

This slice is not a duplicate of [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md). Issue 205 covers values such as `not-a-number` that Python `int(...)` rejects; this slice covers Unicode digit strings that Python accepts.

This slice is not a duplicate of [649-pr-validate-non-negative-forum-post-edit-revision-ids.md](649-pr-validate-non-negative-forum-post-edit-revision-ids.md). Issue 649 rejects parseable negative ASCII values such as `-1`; this slice preserves that path and rejects Unicode digit normalization before conversion.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), [124-pr-scope-forum-post-edit-form-controls.md](124-pr-scope-forum-post-edit-form-controls.md), [173-pr-forum-post-edit-form-fetch-failure-context.md](173-pr-forum-post-edit-form-fetch-failure-context.md), [185-pr-forum-post-edit-revision-site-context.md](185-pr-forum-post-edit-revision-site-context.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-form-response-body-context.md](210-pr-forum-post-edit-form-response-body-context.md), [250-pr-forum-post-edit-action-status-context.md](250-pr-forum-post-edit-action-status-context.md), [263-pr-forum-post-edit-revision-cache-invalidation.md](263-pr-forum-post-edit-revision-cache-invalidation.md), [649-pr-validate-non-negative-forum-post-edit-revision-ids.md](649-pr-validate-non-negative-forum-post-edit-revision-ids.md), [721-pr-validate-forum-post-edit-status-type.md](721-pr-validate-forum-post-edit-status-type.md), and adjacent generated-scalar ASCII-shape drafts [758-pr-validate-forum-post-revision-id-ascii-shape.md](758-pr-validate-forum-post-revision-id-ascii-shape.md), [760-pr-validate-forum-thread-detail-post-count-ascii-shape.md](760-pr-validate-forum-thread-detail-post-count-ascii-shape.md), [763-pr-validate-forum-thread-list-post-count-ascii-shape.md](763-pr-validate-forum-thread-list-post-count-ascii-shape.md), and [764-pr-validate-quickmodule-user-id-ascii-shape.md](764-pr-validate-quickmodule-user-id-ascii-shape.md).

## Changes

- Require ASCII `-?[0-9]+` before integer conversion for generated edit-form `currentRevisionId` values.
- Preserve successful edits for valid ASCII positive revision IDs such as `9001`.
- Preserve the existing missing value, malformed non-numeric value, and negative value diagnostics.
- Reject fullwidth edit-form revision IDs before `saveEditPost` is called.
- Add regression coverage for generated edit-form `currentRevisionId="\uff19\uff10\uff10\uff11"`.

## Type Of Change

- Bug fix
- Mutation-boundary hardening
- Forum post edit-form parser validation
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | Generated edit-form `currentRevisionId` values containing non-ASCII digit glyphs must fail before `saveEditPost` is attempted. |
| R2 | The malformed revision-ID diagnostic must retain the existing site/post context. |
| R3 | Valid ASCII positive revision IDs must still reach the save request unchanged. |
| R4 | Existing missing input, missing value, non-numeric malformed value, negative value, direct-child scoping, retry, save-status, local source/title update, and cache invalidation behavior must remain compatible. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, real forum markup, raw edit-form HTML, raw post content, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, forum-post tests, adjacent forum tests, full unit tests, lint, format, type, pyright, whitespace, focused Brooks review, and Clawpatch doctor gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `\uff19\uff10\uff10\uff11` in the generated edit-form `currentRevisionId` value raises before save. | `test_edit_fullwidth_current_revision_id_value_fails_before_save` failed RED with `DID NOT RAISE`, then passed after ASCII-only revision parsing. | Calling `saveEditPost`, updating local source/title, normalizing the value into `9001`, or silently dropping the value rejects this local completion claim. | `ForumPost.edit` edit-form parser | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | The exception reports `Current revision ID value is malformed for site: test-site, post: 5001`. | The new regression asserts the established malformed-value diagnostic. | A raw `ValueError`, omitted site/post context, negative-value reclassification, or a different exception family rejects this local completion claim. | Edit-form diagnostics | focused test |
| R3 | Valid ASCII positive revision IDs still save successfully. | Focused GREEN included `test_edit_success`; `tests/unit/test_forum_post.py` passed 295 tests. | Rejecting `9001`, changing the save payload, failing to update local source/title after confirmed save, or changing method chaining rejects this local completion claim. | Valid edit path | `tests/unit/test_forum_post.py` |
| R4 | Existing malformed and negative paths stay stable. | Focused GREEN included missing-value, malformed non-numeric, negative-value, and direct-child scoping guards. Adjacent forum coverage passed 911 tests and full unit passed 3768 tests. | Regressing form scoping, retry behavior, status validation, cache invalidation, adjacent forum behavior, or any unit test rejects this local completion claim. | Forum edit workflow | `tests/unit` |
| R5 | No live site state or private material is needed. | The regression mutates a synthetic edit-form fixture and mocked AMC responses only. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, real forum markup, raw edit-form HTML, raw post content, private forum data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-post suite, adjacent suite, full unit, ruff, format, mypy, pyright, whitespace, focused Brooks review, and Clawpatch doctor checks passed. | Test, lint, format, type, pyright, whitespace, review, doctor, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `16ae334 fix(forum_post): validate edit revision ascii shape`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_fullwidth_current_revision_id_value_fails_before_save -q` failed before the fix with `DID NOT RAISE` because generated edit-form revision ID text `\uff19\uff10\uff10\uff11` was accepted and sent as `currentRevisionId=9001`.
- GREEN focused edit-form revision slice: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_fullwidth_current_revision_id_value_fails_before_save tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_value_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_current_revision_id_value_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_negative_current_revision_id_value_fails_before_save tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_scopes_current_revision_id_to_edit_form_direct_child tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_success -q` passed 6 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 295 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 911 tests.
- `uv run pytest tests/unit -q` passed 3768 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src` passed with no issues in 36 source files, plus an existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Focused Brooks changed-file review found no parser boundary, mutation-safety, compatibility, architecture, or test-decay findings; the full autonomous Brooks sweep was not run because the skill gates broad repository auto-fix behind explicit user consent.
- Clawpatch doctor evidence was collected without starting a review worker. Code pre-commit evidence reported `provider=codex`, `state=missing`, `providerVersion="codex-cli 0.138.0-alpha.6"`, local clawpatch commit `59e2dea`, and launcher SHA256 `d6726fac4db7531d06c27d38e71e881f5e6360b1536df9a51f72bd8c4913ece1`. The docs pre-commit rerun observed the same clawpatch commit with `providerVersion="codex-cli 0.139.0"` and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `ForumPost.edit(...)` raises `NoElementException("Current revision ID value is malformed ...")` for a generated edit-form `currentRevisionId` value of `\uff19\uff10\uff10\uff11`.
- `saveEditPost` is not called for that malformed generated edit-form value.
- The local post source/title and caches are not updated before the malformed-value failure.
- Valid ASCII positive revision IDs such as `9001` still reach the save request and preserve successful edit behavior.
- Missing `currentRevisionId`, missing `value`, non-numeric values such as `not-a-number`, and negative ASCII values such as `-1` keep their established diagnostics.
- Direct-child edit-form scoping remains intact, so nested preview markup cannot override the revision ID.
- Retry-aware edit-form fetches, response-body diagnostics, save-status validation, source/title updates, revision/thread cache invalidation, source reads, post-list parsing, reply behavior, adjacent forum workflows, and full unit behavior remain green.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, push, raw generated edit-form HTML from real accounts, raw rollout path, private forum content, private post body, or private site detail is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 205. Mitigation: Issue 205 covers values that Python already rejects as non-numeric; this slice covers Unicode decimal digit text that Python accepts.
- Risk: This could be confused with Issue 649. Mitigation: Issue 649 covers negative edit-form revision IDs; this slice keeps ASCII negative values parseable so the existing non-negative diagnostic remains intact.
- Risk: This could alter valid forum post edits. Mitigation: ASCII positive values still convert through `int(...)`, focused GREEN included successful edit coverage, the forum-post suite passed, and adjacent forum coverage remained green.
- Risk: Diagnostics could expose post content or raw edit-form HTML. Mitigation: the diagnostic includes only site and post context; tests use synthetic fixture HTML and mocked responses.

## Dependencies

- Wikidot edit forms continue to expose the current forum post revision ID as a direct hidden `input[name='currentRevisionId']` child of `form#edit-post-form`.
- Normal generated edit-form revision IDs are expected to use ASCII decimal digits.
- Existing forum post edit diagnostics continue to report site unix name and post ID without retaining raw edit-form HTML.

## Open Questions

None for this local slice. Future generated scalar-shape changes should be selected only after a fresh duplicate check and public RED test.

## Upstream-Safe Motivation

`ForumPost.edit(...)` is a mutation helper that must trust a server-provided revision ID immediately before saving. Unicode digit normalization can silently turn malformed generated hidden-form state into a valid-looking `saveEditPost` payload. Requiring ASCII digits keeps the mutation boundary strict while preserving valid forum edits and established diagnostics.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated prior behavior: a fullwidth generated edit-form `currentRevisionId` was accepted, sent as `currentRevisionId=9001`, and the local source was updated.
- Existing local drafts covered edit-form fetch retries, direct-child scoping, missing current-revision inputs, missing and non-numeric values, response-body validation, save-status validation, save-status typing, cache invalidation, retained ID state, and negative edit-form revision IDs; they did not validate Unicode digit normalization in generated edit-form revision IDs.
- This slice does not change request module names, request payload shape for valid edits, retry policy, login checks, response-body validation, direct-child scoping, save-status validation, title/source validation, source fetching, post-list parsing, reply behavior, live Wikidot behavior, or upstream filing state.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, cookies, auth JSON, raw forum markup from real sites, raw edit-form HTML, private post data, private forum content, private site data, usernames, passwords, and session-cookie values out of upstream discussion.

## Additional Notes

This is a read-before-mutation parser fix. It preserves valid ASCII edit-form behavior while preventing Python's Unicode digit support from manufacturing ordinary revision IDs out of malformed generated hidden-form metadata.
