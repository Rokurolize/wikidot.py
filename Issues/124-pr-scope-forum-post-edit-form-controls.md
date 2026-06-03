# PR Draft: Scope Forum Post Edit Form Controls

## Summary

`ForumPostCollection.get_post_sources()` and `ForumPost.edit(...)` both parse `forum/sub/ForumEditPostFormModule` responses. Before this fix, source acquisition selected the first `textarea[name='source']` anywhere in the returned HTML, and edit selected the first `input[name='currentRevisionId']` anywhere in the returned HTML. If a nested preview, copied form fragment, or user-authored/form-like markup appeared before the generated edit controls, the parser could read the wrong source text or send a stale/wrong revision ID in the save request.

This fix scopes both controls to direct children of `form#edit-post-form`, which is the generated edit form boundary in the existing fixture and API response shape. Missing-form behavior still reports the existing source/revision missing exceptions.

## Related Issue

Builds on [043-pr-retry-forum-post-source-fetches.md](043-pr-retry-forum-post-source-fetches.md) and [044-pr-retry-forum-post-edit-form-fetch.md](044-pr-retry-forum-post-edit-form-fetch.md), because those drafts established `ForumEditPostFormModule` as a practical read surface for source inspection and edit preparation.

Also complements [055-pr-deduplicate-forum-post-source-fetches.md](055-pr-deduplicate-forum-post-source-fetches.md), which kept source acquisition efficient, and [123-pr-scope-forum-post-metadata-spans.md](123-pr-scope-forum-post-metadata-spans.md), which fixed the same class of descendant-selector contamination in forum post metadata.

No upstream issue was filed from this local workspace.

## Changes

- Scope source parsing in `ForumPostCollection._acquire_post_sources(...)` to `:scope > textarea[name='source']` under `form#edit-post-form`.
- Scope `ForumPost.edit(...)` revision parsing to `:scope > input[name='currentRevisionId']` under `form#edit-post-form`.
- Add a regression where a nested preview textarea appears before the real source textarea.
- Add a regression where a nested preview `currentRevisionId` input appears before the real hidden revision input.
- Preserve retry-aware form fetch behavior, source caching, duplicate-source behavior, exhausted-retry behavior, edit save request shape, local source/title updates, and surrounding forum post parsing behavior.

## Type Of Change

- Bug fix
- Parser robustness improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Source acquisition must use the generated edit form's direct source textarea. | `TestForumPostCollectionGetSources.test_get_post_sources_scopes_source_textarea_to_edit_form_direct_child` asserts the cached source remains `Test source content in wikidot syntax` when a nested preview textarea appears first. | The RED test failed before the fix because `_source` became `Preview source`. |
| Edit saves must use the generated edit form's direct `currentRevisionId`. | `TestForumPostEdit.test_edit_scopes_current_revision_id_to_edit_form_direct_child` asserts the save request uses `9001` when a nested preview input with value `9999` appears first. | The RED test failed before the fix because the save request used `9999`. |
| Existing source/edit behaviors remain intact. | `TestForumPostCollectionGetSources`, `TestForumPostSource`, and `TestForumPostEdit` passed 17 tests. | Regressions in retry, exhausted retry, cached source, duplicate source, successful edit, edit-with-title, or local-state updates reject this local completion claim. |
| Forum post and adjacent forum workflows stay green. | `uv run pytest tests/unit/test_forum_post.py -q` passed 42 tests, and `uv run pytest tests/unit/test_forum*.py -q` passed 130 tests. | Regressions in post parsing, source fetching, edit behavior, revision parsing, thread parsing, or category parsing reject this local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy src tests`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject this local completion claim. |

## Testing

Implemented locally in commit `4714f4a fix(forum_post): scope edit form controls`.

- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_scopes_source_textarea_to_edit_form_direct_child -q` failed before the fix because `_source` was `Preview source`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_scopes_source_textarea_to_edit_form_direct_child -q`
- RED: `uv run pytest tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_scopes_current_revision_id_to_edit_form_direct_child -q` failed before the fix because the save request used `9999`.
- GREEN: `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources::test_get_post_sources_scopes_source_textarea_to_edit_form_direct_child tests/unit/test_forum_post.py::TestForumPostEdit::test_edit_scopes_current_revision_id_to_edit_form_direct_child -q` passed 2 tests.
- `uv run pytest tests/unit/test_forum_post.py::TestForumPostCollectionGetSources tests/unit/test_forum_post.py::TestForumPostSource tests/unit/test_forum_post.py::TestForumPostEdit -q` passed 17 tests.
- `uv run pytest tests/unit/test_forum_post.py -q` passed 42 tests.
- `uv run pytest tests/unit/test_forum*.py -q` passed 130 tests.
- `uv run pytest tests/unit -q` passed 678 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy src tests`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Source acquisition reads source text only from the generated edit form's direct source textarea.
- Edit save requests read `currentRevisionId` only from the generated edit form's direct hidden input.
- Nested form-like markup inside the edit form cannot override source text or revision ID.
- Existing retry-aware edit-form fetches, exhausted retry behavior, duplicate source acquisition, cached source skipping, successful edit, edit-with-title, forum post parsing, and adjacent forum tests remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

`ForumEditPostFormModule` returns generated controls that are structural inputs for source inspection and edit saves. Descendant-wide selectors make those controls vulnerable to unrelated nested form-like markup. Scoping to direct children of `form#edit-post-form` keeps source and revision parsing tied to the generated edit form without changing the public API.

## Local Evidence, Not For Upstream Paste

- Earlier forum post drafts established edit-form reads, source reads, retry behavior, and duplicate-source acquisition as practical rollout-backed surfaces.
- The forum parser-boundary draft series repeatedly found that Wikidot-rendered content can contain UI-like or metadata-like fragments that should not be treated as generated structure.
- The refreshed complexity scan continues to flag `src/wikidot/module/forum_post.py` as an audit-worthy parser/acquisition path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved page/forum contents out of upstream discussion.

## Additional Notes

This slice does not change request batching, retry policy, save action retry semantics, title/source state updates, post-list parsing, revision parsing, or result object shape. It only narrows two edit-form control lookups to the generated edit form's direct controls.
