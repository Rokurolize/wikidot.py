# PR: Validate forum post revision action shapes

## Summary

Forum post revision-list parsing should require the full `showRevision(event, <id>)` action shape before accepting a revision ID.

## Related Issue

No upstream issue or PR has been filed for this local finding.

This is distinct from local Issue 283, which covers contextual diagnostics for non-numeric `showRevision(event, latest)` values. It is also distinct from local Issue 758, which covers non-ASCII digit normalization in revision action IDs, and from local Issue 839, which validates rendered forum post revision HTML response payload roots.

## Problem Statement

`ForumPostRevisionCollection.acquire_all(...)` extracts forum post revision IDs from revision-list `onclick` handlers. The parser previously used a broad search for `showRevision(event, <digits>)`, so an action string such as `WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, 9003) latest` was accepted as revision ID `9003` even though the action had trailing text after the call.

That permissiveness can silently convert malformed module markup, adapter bugs, fixture mistakes, or changed Wikidot action text into a valid-looking `ForumPostRevision` object. The existing malformed-ID diagnostics should catch that boundary before later source, HTML, moderation, archive, migration, translation-review, or diff workflows rely on the retained revision ID.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify forum post revision lists as a practical surface for edit-history inspection, moderation ledgers, archival jobs, migration checks, translation review tooling, and generated comparison workflows.

Existing local drafts already hardened forum post revision retry behavior, duplicate request handling, cached duplicate reuse, revision-list response payloads, revision-list HTML parsing, rendered HTML payloads, retained revision IDs, retained post/thread/site state, and collection entries. The remaining source-level gap before this slice was that revision action parsing accepted a valid-looking call embedded inside a larger `onclick` payload instead of validating the complete action value.

The local fix is committed as `ba0aabf`.

## Affected Workflows

- Forum post revision-list acquisition through `ForumPostRevisionCollection.acquire_all(...)`.
- Optional rendered HTML acquisition through `ForumPostRevisionCollection.acquire_all_for_posts(..., with_html=True)` after revision-list parsing.
- Lazy forum post revision source or HTML reads that depend on revision objects created from revision-list rows.
- Moderation, archive, migration, translation-review, and diff workflows that compare historical forum post content.
- Generated fixtures, response adapters, and recorded-response tests that synthesize forum revision-list action markup.

## Proposed Fix

Require the revision-list `onclick` value to fully match the supported Wikidot action shape:

```text
showRevision(event, <ascii-digits>)
WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, <ascii-digits>)
```

If the value contains trailing text, extra tokens, non-ASCII digits, missing digits, or another malformed shape, raise the existing `NoElementException` path with site, post, row, field, and raw action-value context. Keep the accepted action prefix narrow to the known Wikidot listener namespace.

## Implementation Notes

The patch changes the revision ID extraction in `ForumPostRevisionCollection.acquire_all(...)` from `re.search(...)` to `re.fullmatch(...)`, while preserving the existing ASCII digit capture and malformed-ID diagnostic.

The regression test constructs a revision row with:

```text
WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, 9003) latest
```

It asserts that acquisition raises:

```text
Forum post revision ID is malformed for site: test-site, post: 5001 (row=1, field=revision_id, value=WIKIDOT.modules.ForumViewThreadModule.listeners.showRevision(event, 9003) latest)
```

It also asserts that the collection remains uncached and that no rendered HTML request is attempted after the malformed revision-list row.

## Tests And Verification

Local verification:

```text
uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_revision_id_with_trailing_action_text -q
uv run pytest tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_revision_id_with_trailing_action_text tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_rejects_non_ascii_digit_revision_id tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionAcquireAll::test_acquire_all_malformed_revision_id_includes_post_row_and_value_context tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_success tests/unit/test_forum_post_revision.py::TestForumPostRevisionCollectionParse::test_parse_uses_revision_cells_for_metadata -q
uv run pytest tests/unit/test_forum_post_revision.py -q
uv run pytest tests/unit -q
uv run ruff check .
uv run ruff format --check .
uv run mypy src tests
uv run pyright
git diff --check
```

Observed results:

```text
RED: failed with "Failed: DID NOT RAISE <class 'wikidot.common.exceptions.NoElementException'>" before the fix
focused GREEN: 5 passed
forum_post_revision module: 233 passed
full unit suite: 3943 passed
ruff: passed
format check: passed
mypy: passed with existing notes only
pyright: passed
diff whitespace: passed
```

The complexity scan reported only pre-existing hotspots outside the changed constant-time revision action validation path.

## Compatibility And Risk Notes

The change only affects malformed `onclick` values where a supported `showRevision(event, <digits>)` call is embedded inside a larger string. Valid short-form and known fully-qualified Wikidot listener calls remain accepted.

The diagnostic intentionally includes only site/post identifiers, row context, field name, and the malformed action string needed to debug the parser boundary. It does not include raw response HTML, forum post source, rendered forum content, page content, account material, cookies, tokens, passwords, secrets, auth JSON, or browser profile data.

## Rationale For Upstream Suitability

The patch replaces a permissive substring match with exact validation at the forum post revision-list parser boundary. It follows the existing local hardening pattern for forum post revision IDs, preserves behavior for valid Wikidot action shapes, and is covered by a regression through the public collection acquisition API.

## Acceptance Criteria

- Forum post revision-list parsing accepts valid short-form and known fully-qualified `showRevision(event, <ascii-digits>)` actions.
- Revision action values with trailing text are rejected with `NoElementException`.
- Malformed revision action diagnostics include site, post, row, field, and value context.
- Malformed revision-list rows do not populate the revision collection cache or trigger rendered HTML requests.
- Existing revision parsing and non-ASCII digit validation behavior remains covered.
- The full unit suite and static checks pass locally.

## Local Evidence, Not For Upstream Paste

- Local code commit: `ba0aabf`
- Thread workspace report records the RED/GREEN and full gate evidence for this slice.
- Clawpatch provenance was checked against local fork `d89ca91`, provider `codex`, state `missing`, `codex-cli 0.139.0`, and launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.
- No raw response HTML, forum post source, rendered forum content, page content, account material, cookies, tokens, passwords, secrets, auth JSON, or browser profile data were captured in this draft.
