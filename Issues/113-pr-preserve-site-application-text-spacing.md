# PR Draft: Preserve Site-Application Text Spacing

## Summary

`SiteApplication.acquire_all(...)` parses pending site applications returned by `managesite/ManageSiteMembersApplicationsModule`, which are exposed through `site.applications`.

Before this fix, application body text was extracted with `text_cells[1].text.strip()`. When a rendered application message contained adjacent paragraphs or formatted child elements, visible text could be concatenated. The focused regression used `<p>First <span>part</span></p><p>Second part</p>` in the application text cell; before the fix, the parsed application text became `First partSecond part`.

This fix extracts pending application body text with a space separator and `strip=True`, preserving visible word boundaries while keeping login checks, request construction, retry handling, forbidden detection, empty list behavior, application header filtering, nested application-body markup filtering, duplicate text-table mismatch detection, missing text-cell errors, and accept/decline actions unchanged.

## Related Issue

Builds on [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), and [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), because those drafts established pending site applications as a practical read/action workflow and the application body as authored markup that must not contaminate structural parsing.

The parser-boundary shape is adjacent to [096-pr-scope-site-member-row-parsing.md](096-pr-scope-site-member-row-parsing.md), while the text-fidelity failure class is adjacent to [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), and [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md), because all of these fixes preserve user-visible text while avoiding accidental structural-parser changes.

No upstream issue was filed from this local workspace.

## Changes

- Extract pending application body text with `get_text(" ", strip=True)` instead of `.text.strip()`.
- Add a public acquisition regression where adjacent paragraphs and inline formatting keep a space between visible application text chunks.
- Preserve login checks, request construction, retry handling, forbidden detection, empty results, structural application-header filtering, nested body application-like markup filtering, duplicate text-table mismatch errors, missing text-cell errors, user parsing, and accept/decline action behavior.

## Type Of Change

- Bug fix
- Parser/text fidelity improvement
- Test addition/modification

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Pending site application text should not concatenate adjacent rendered paragraphs or formatted child text. | `TestSiteApplicationAcquireAll.test_acquire_all_preserves_application_text_spacing` asserts `applications[0].text == "First part Second part"` through `SiteApplication.acquire_all(...)`. | The RED test failed before the fix because the parsed application text was `First partSecond part`. |
| Application acquisition and parser boundaries should remain unchanged. | `uv run pytest tests/unit/test_site_application.py -q` passed 19 site-application tests covering normal parsing, retry handling, forbidden responses, empty lists, missing text cells, duplicate text-table mismatch detection, nested application-body markup filtering, and accept/decline behavior. | If request sequencing, parser-boundary filtering, error behavior, or action helpers regress, the site-application test module rejects the local completion claim. |
| Adjacent site/member workflows should remain green. | `uv run pytest tests/unit/test_site_application.py tests/unit/test_site_member.py tests/unit/test_site.py -q` passed 104 tests. | Regressions in application acquisition, site-member parsing, recent changes, page iteration, source collection, publishing, or site-level helpers reject the local completion claim. |
| Broad unit and static quality gates remain green. | `uv run pytest tests/unit -q`; `uv run ruff check .`; `uv run ruff format --check .`; `uv run mypy .`; `git diff --check`. | Test, lint, format, type, or whitespace failures reject the local completion claim. |

## Testing

Implemented locally in commit `325093d fix(site_application): preserve application text spacing`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_preserves_application_text_spacing -q` failed before the fix because `applications[0].text` was `First partSecond part`.
- GREEN: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationAcquireAll::test_acquire_all_preserves_application_text_spacing -q`
- `uv run pytest tests/unit/test_site_application.py -q` passed 19 tests.
- `uv run pytest tests/unit/test_site_application.py tests/unit/test_site_member.py tests/unit/test_site.py -q` passed 104 tests.
- `uv run pytest tests/unit -q` passed 665 tests.
- `uv run ruff check .`
- `uv run ruff format --check .`
- `uv run mypy .`
- `git diff --check`

Not run: `uv run pyright src tests` because this environment could not find a `pyright` executable on PATH.

## Acceptance Criteria

- Pending site application text preserves a separator between adjacent rendered paragraphs and formatted child text.
- Nested application body markup still cannot create fake application entries or text-table matches.
- Existing login checks, first-fetch retry handling, forbidden detection, empty results, missing text-cell errors, duplicate text-table mismatch detection, user parsing, `SiteApplication` output shape, and accept/decline action behavior remain unchanged.
- No browser, live Wikidot, upstream Issue, or upstream PR action is required for this local draft.

## Upstream-Safe Motivation

Pending site application messages are user-visible content and can render multiple paragraphs or formatted inline HTML. `SiteApplication.acquire_all(...)` should preserve visible word boundaries in application text without changing the request flow, structural application parsing, or application accept/decline actions.

## Local Evidence, Not For Upstream Paste

- Earlier local drafts [032-pr-retry-application-list-fetches.md](032-pr-retry-application-list-fetches.md), [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), and [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md) established `managesite/ManageSiteMembersApplicationsModule` as a practical local target and the application body as an authored-markup parser boundary.
- Text-fidelity drafts [106-pr-preserve-private-message-body-spacing.md](106-pr-preserve-private-message-body-spacing.md), [107-pr-preserve-thread-list-description-spacing.md](107-pr-preserve-thread-list-description-spacing.md), [108-pr-preserve-forum-category-description-spacing.md](108-pr-preserve-forum-category-description-spacing.md), [109-pr-preserve-forum-post-title-spacing.md](109-pr-preserve-forum-post-title-spacing.md), [110-pr-preserve-thread-list-title-spacing.md](110-pr-preserve-thread-list-title-spacing.md), [111-pr-preserve-forum-category-title-spacing.md](111-pr-preserve-forum-category-title-spacing.md), and [112-pr-preserve-recent-change-comment-spacing.md](112-pr-preserve-recent-change-comment-spacing.md) established visible text spacing as a recurring HTML flattening risk.
- The refreshed complexity scan continues to flag `src/wikidot/module/site_application.py` as small but connected to the broader site/application/member parser surface.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, credentials, and saved application text out of upstream discussion.

## Additional Notes

This slice does not change request construction, retry behavior, forbidden handling, application/user matching, structural header filtering, nested application body markup filtering, duplicate text-table mismatch detection, missing text-cell errors, or accept/decline actions. It only changes how pending application body text is flattened from rendered HTML into `SiteApplication.text`.
