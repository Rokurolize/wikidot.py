# PR Draft: Validate Non-Negative Forum Post Edit Revision IDs

## Summary

`ForumPost.edit(...)` fetches the edit form, reads its hidden `currentRevisionId`, and includes that value in the subsequent `saveEditPost` mutation. Existing local drafts hardened the edit workflow around form scoping, missing fields, malformed non-numeric values, status handling, cache invalidation, and direct revision object IDs, but a parseable negative value such as `-1` still passed `int(...)` and reached the save mutation.

This change rejects negative edit-form `currentRevisionId` values before `saveEditPost` is attempted. It deliberately preserves the existing direct-child form scoping, missing-value diagnostics, malformed-value diagnostics, successful positive edit path, retry behavior, and local cache invalidation behavior.

## Outcome

Negative forum-post edit revision IDs now fail at the read-before-mutation boundary with site and post context. Valid positive revision IDs continue to save exactly as before, while missing and malformed values keep their established exception messages.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who rely on browser-free forum editing helpers, generated forum maintenance scripts, local automation, fixtures, or adapters where invalid edit-form state must not become a mutation payload.

## Current Evidence

Forum editing drafts [044-pr-forum-post-edit-context.md](044-pr-forum-post-edit-context.md), [124-pr-forum-post-edit-cache-invalidation.md](124-pr-forum-post-edit-cache-invalidation.md), [162-pr-forum-post-edit-response-body-context.md](162-pr-forum-post-edit-response-body-context.md), [173-pr-forum-post-edit-form-scoping.md](173-pr-forum-post-edit-form-scoping.md), [185-pr-forum-post-edit-status-validation.md](185-pr-forum-post-edit-status-validation.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-retries.md](210-pr-forum-post-edit-retries.md), [250-pr-forum-post-edit-empty-form-response.md](250-pr-forum-post-edit-empty-form-response.md), and [263-pr-forum-post-edit-cache-after-title-change.md](263-pr-forum-post-edit-cache-after-title-change.md) establish `ForumPost.edit(...)` as a practical local automation surface.

This slice is not a duplicate of those drafts or of [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md). Issue 205 covers missing and non-numeric `currentRevisionId` values. Issue 638 validates direct `PageRevision.id` and `ForumPostRevision.id` objects. None of the existing drafts reject a parseable negative edit-form `currentRevisionId` before the forum edit save mutation.

## Related Issue / Non-Duplicate Analysis

Builds directly on [173-pr-forum-post-edit-form-scoping.md](173-pr-forum-post-edit-form-scoping.md), [185-pr-forum-post-edit-status-validation.md](185-pr-forum-post-edit-status-validation.md), [205-pr-forum-post-edit-revision-value-context.md](205-pr-forum-post-edit-revision-value-context.md), [210-pr-forum-post-edit-retries.md](210-pr-forum-post-edit-retries.md), and [638-pr-validate-non-negative-revision-ids.md](638-pr-validate-non-negative-revision-ids.md).

No upstream issue was filed from this local workspace.

## Changes

- Reject an edit-form `currentRevisionId` value below zero with `NoElementException`.
- Include `site` and `post` context in the negative-value diagnostic.
- Reject negative values before `site.amc_request(...)` sends `saveEditPost`.
- Preserve the existing missing `currentRevisionId` input diagnostic.
- Preserve the existing missing `value` diagnostic.
- Preserve the existing malformed non-numeric value diagnostic.
- Preserve direct-child form scoping so nested preview markup cannot override the form control.
- Leave live Wikidot behavior, pushes, upstream Issues, and upstream PRs unchanged.

## Type Of Change

- Input validation
- Mutation-boundary hardening
- Forum edit workflow integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A negative edit-form `currentRevisionId` such as `-1` must raise `NoElementException("Current revision ID value must be non-negative ...")` before `saveEditPost` is attempted. |
| R2 | Missing `currentRevisionId`, missing `value`, and malformed non-numeric value diagnostics must remain unchanged. |
| R3 | Direct-child form scoping must remain unchanged so nested preview markup cannot supply the revision ID. |
| R4 | Existing successful positive edit behavior, edit-form retry behavior, save status validation, source/title updates, and cache invalidation must remain unchanged. |
| R5 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private forum data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R6 | Focused RED/GREEN, full forum-post tests, adjacent forum tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Negative edit-form revision IDs cannot reach the save mutation. | `test_edit_negative_current_revision_id_value_fails_before_save` failed RED because the negative value reached `saveEditPost`, then passed GREEN after the non-negative guard was added. | Accepting negative values, sending them in `saveEditPost`, silently coercing them, or raising without site/post context rejects this local completion claim. | `ForumPost.edit` edit-form revision validation | `src/wikidot/module/forum_post.py`, `tests/unit/test_forum_post.py` |
| R2 | Existing missing and malformed diagnostics remain stable. | Missing-value and malformed-value tests passed in the focused RED and GREEN commands. | Changing the existing missing-input, missing-value, or malformed-value messages rejects this local completion claim. | Forum edit form parsing | `tests/unit/test_forum_post.py` |
| R3 | Revision ID scoping remains tied to the edit form direct child. | `test_edit_scopes_current_revision_id_to_edit_form_direct_child` passed in the focused RED and GREEN commands. | Letting nested preview markup override the direct form control rejects this local completion claim. | Forum edit form scoping | `tests/unit/test_forum_post.py` |
| R4 | Forum edit and adjacent forum behavior stay green. | The full forum-post suite passed 171 tests, adjacent forum category/thread/post/revision suites passed 578 tests, and the full unit suite passed 2941 tests. | Regressing successful edits, retries, status validation, source/title updates, cache invalidation, forum category/thread/post/revision behavior, or any existing unit test rejects this local completion claim. | Forum workflows | `tests/unit/test_forum_post.py`, `tests/unit/test_forum_category.py`, `tests/unit/test_forum_thread.py`, `tests/unit/test_forum_post_revision.py`, `tests/unit` |
| R5 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level form fixtures only. | Using real account names, credentials, cookies, auth JSON, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, raw forum markup from real sites, private post data, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, forum-post tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `b18db27 fix(forum): validate edit revision ids`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_missing_current_revision_id_value_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_malformed_current_revision_id_value_includes_site_and_post_context tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_negative_current_revision_id_value_fails_before_save tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_scopes_current_revision_id_to_edit_form_direct_child -q` failed 1 negative edit-form revision-ID case before the fix; 3 missing/malformed/scoping guards stayed green.
- GREEN: the same focused command passed 4 tests after the non-negative guard was added.
- `uv run ruff format src/wikidot/module/forum_post.py tests/unit/test_forum_post.py` left both files unchanged.
- Re-running the same focused command after formatting passed 4 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 171 tests.
- `uv run pytest tests/unit/test_forum_category.py tests/unit/test_forum_thread.py tests/unit/test_forum_post.py tests/unit/test_forum_post_revision.py -q` passed 578 tests.
- `uv run pytest tests/unit -q` passed 2941 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- An edit form with `<input type="hidden" name="currentRevisionId" value="-1"/>` raises `NoElementException`.
- The exception message includes `Current revision ID value must be non-negative`, the site unix name, and the post ID.
- `saveEditPost` is not called for negative edit-form revision IDs.
- Missing `currentRevisionId` input still raises `Current revision ID input is not found ...`.
- Missing `currentRevisionId` value still raises `Current revision ID value is not found ...`.
- Non-numeric `currentRevisionId` value still raises `Current revision ID value is malformed ...`.
- Positive direct-child edit-form revision IDs still reach `saveEditPost`.
- Nested preview markup cannot override the direct-child edit-form revision ID.
- Live Wikidot behavior, pushes, upstream Issues, and upstream PRs remain outside this local slice.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`ForumPost.edit(...)` is a mutation helper that already treats the current revision ID as required form state. A negative revision ID is impossible Wikidot revision state, but Python parsed it as an integer and the library previously forwarded it to the save request. Rejecting it locally keeps invalid form state from becoming a mutation payload while preserving all valid positive edit flows.

## Local Evidence

- Local rollout-backed drafts repeatedly use browser-free forum editing, forum post source retrieval, forum revision handling, generated fixtures, and automation where invalid hidden-form state should fail before mutation.
- Existing local drafts covered form scoping, missing and malformed `currentRevisionId` values, status validation, retry behavior, and direct revision object IDs, but did not cover parseable negative edit-form revision IDs.
- The focused RED failure showed a negative `currentRevisionId` reached the save path before this slice.
- This slice only validates non-negative edit-form revision IDs. It does not change positive edit saves, title/source validation, retry logic, status validation, cache invalidation, direct revision objects, live Wikidot behavior, or upstream actions.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw forum markup from real sites, private post data, and private site data out of upstream discussion.

## Additional Notes

This change intentionally stays narrower than the direct revision-object validation draft. The field being hardened here is a parsed edit-form control used immediately before a mutation, so the regression test asserts that the save request is not called.
