# PR Draft: Validate Metadata Tag Inputs Before Metadata Writes

## Summary

`Page.set_metadata(tags=...)` and `Site.page.publish(tags=...)` both expose explicit tag write inputs for browser-free metadata and publishing workflows. Direct `Page(tags=...)` construction already rejected malformed stored tag state, ListPages query inputs already rejected malformed tag containers and list entries, and required-tag iterator filters already rejected malformed required-tag inputs. The explicit write paths still accepted malformed `tags` values until side-effect code ran. `Page.set_metadata(tags=3)` leaked a raw join error, string or tuple tag containers could advance into login and AMC request construction, and mixed lists such as `["tag-one", 3]` leaked raw join errors. `Site.page.publish(tags=...)` could advance into login, page lookup, create/edit work, post-save page-ID resolution, or result construction before any stable tag diagnostic.

This change validates explicit metadata tag write inputs before write-side effects. `Page.set_metadata(tags=...)` and `Site.page.publish(tags=...)` now reuse the existing page-tag validator, accepting only `list[str]` values when tags are provided. Non-list values raise `ValueError("tags must be a list")`, non-string list entries raise `ValueError("tags list entries must be strings")`, and `None` still means "leave tags unchanged." Valid tag metadata updates, parent updates, meta-tag updates, publish create/edit behavior, source verification ordering, visibility retry behavior, and publish result fields remain unchanged.

## Outcome

Browser-free metadata and publish callers now get deterministic tag-write preflight validation instead of raw Python errors, accidental login/request progress, or malformed tag payloads.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page metadata APIs, `Site.page.publish(...)`, browser-free page publishing, generated migration configuration, audit ledgers, source collection workflows, cleanup scripts, or local fixtures that supply page tag updates.

## Current Evidence

Local rollout-backed drafts establish metadata/tag writes and browser-free publishing as practical surfaces. [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [007-pr-batch-meta-tag-updates.md](007-pr-batch-meta-tag-updates.md), [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [020-pr-publish-source-verification-normalizer.md](020-pr-publish-source-verification-normalizer.md), [021-pr-publish-post-save-visibility-retry.md](021-pr-publish-post-save-visibility-retry.md), [028-pr-publish-aggregate-status.md](028-pr-publish-aggregate-status.md), [070-pr-publish-result-audit-record.md](070-pr-publish-result-audit-record.md), [122-pr-verify-publish-source-before-metadata.md](122-pr-verify-publish-source-before-metadata.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [258-pr-publish-metadata-update-count.md](258-pr-publish-metadata-update-count.md), [343-pr-validate-parent-fullname-inputs.md](343-pr-validate-parent-fullname-inputs.md), [348-pr-validate-meta-tag-inputs.md](348-pr-validate-meta-tag-inputs.md), [485-pr-validate-page-constructor-tags.md](485-pr-validate-page-constructor-tags.md), and [530-pr-validate-tag-container-inputs.md](530-pr-validate-tag-container-inputs.md) cover the adjacent write helpers, publish result ergonomics, metadata action validation, parent and meta input validation, direct page tag state, query tag containers, and required-tag filters.

Those prior slices are not duplicates. Issue 342 validates tag list entries for search query and required-tag list inputs. Issue 485 validates direct `Page(tags=...)` constructor state. Issue 530 validates tag containers for `SearchPagesQuery` and required-tag iterator filters. Issue 348 validates `metas` payloads for metadata writes and publish. None validates explicit metadata tag write inputs for `Page.set_metadata(tags=...)` or `Site.page.publish(tags=...)` before write-side effects. No upstream issue was filed from this local workspace.

## Changes

- Validate `Page.set_metadata(tags=...)` with the existing page-tag validator before login checks, AMC request construction, or local `tags` mutation.
- Validate `Site.page.publish(tags=...)` before login checks, page lookup, create/edit save work, post-save page-ID resolution, source verification, metadata writes, or result creation.
- Reject non-list tag write inputs with `ValueError("tags must be a list")`.
- Reject non-string tag list entries with `ValueError("tags list entries must be strings")`.
- Preserve `tags=None` as "leave tags unchanged" for both public write paths.
- Preserve valid `list[str]` tag updates, empty-list tag clearing, parent updates, meta-tag updates, publish create/edit branching, source verification ordering, visibility retry behavior, and publish result fields.

## Type Of Change

- Input validation
- Metadata write preflight hardening
- Publish preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.set_metadata(tags=...)` must reject non-list tag inputs with `ValueError("tags must be a list")` before login checks, AMC requests, or local tag mutation. |
| R2 | `Page.set_metadata(tags=[...])` must reject non-string tag entries with `ValueError("tags list entries must be strings")` before login checks, AMC requests, or local tag mutation. |
| R3 | `Site.page.publish(tags=...)` must reject malformed tag inputs before login checks, page lookup, create/edit work, post-save page-ID resolution, source verification, metadata writes, or result creation. |
| R4 | Valid `tags=None`, valid `list[str]` tag updates, empty-list tag clearing, parent updates, meta-tag updates, publish create/edit behavior, source verification ordering, visibility retry behavior, and publish result fields must remain unchanged. |
| R5 | This slice must not change tag syntax, tag normalization, tag ordering, query tag serialization, required-tag filtering, direct constructor validation, meta tag validation, parent validation, page source validation, live Wikidot behavior, or response parsing. |
| R6 | Focused RED/GREEN, page write tests, site publish tests, adjacent page/site/search tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R7 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list `Page.set_metadata(tags=...)` inputs fail with a stable `ValueError` before metadata side effects. | `test_set_metadata_rejects_invalid_tags_before_request` failed RED for integer, string, and tuple containers with raw errors or side-effect progress, then passed GREEN after validation was added. | Calling login, calling AMC, accepting strings/tuples, coercing containers, or changing `Page.tags` rejects this local completion claim. | Page metadata preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Mixed tag lists fail with the existing tag-entry diagnostic before metadata side effects. | The same focused test failed RED for `["tag-one", 3]` with a raw join `TypeError`, then passed GREEN with `ValueError("tags list entries must be strings")`. | Stringifying entries, silently dropping entries, calling login, calling AMC, or mutating `Page.tags` rejects this local completion claim. | Page metadata preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Publish rejects malformed tag payloads before save-side work. | `test_publish_rejects_invalid_tags_before_save` failed RED because malformed tag inputs advanced into page save/result flow and raised `ValueError("page_id must be an integer")`, then passed GREEN after publish preflight validation was added. | Calling login, page lookup, `Page.create_or_edit(...)`, edit, page-ID resolution, source verification, metadata writes, or result creation rejects this local completion claim. | Publish metadata preflight | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R4 | Existing valid metadata and publish behavior remains green. | `TestPageWriteMethods` passed 49 tests, `TestSitePageAccessor` passed 75 tests, adjacent page constructor/create/edit/property/search tests passed 240 tests, adjacent site/search tests passed 83 tests, and full unit passed 2520 tests. | Regressing valid tag updates, empty-list clearing, parent or meta updates, publish create/edit, source verification, visibility retry, ListPages search, or result fields rejects this local completion claim. | Metadata, publish, and adjacent page/site workflows | `tests/unit/test_page.py`, `tests/unit/test_site.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_search_pages_query.py` |
| R5 | Broader tag and publish semantics remain outside scope. | The implementation only reuses the existing page-tag validator at the two explicit write boundaries. | Changing tag grammar, normalization, ordering, query serialization, required-tag filtering, constructor validation, response parsing, or live request semantics rejects this local completion claim. | Scope control | `src/wikidot/module/page.py`, `src/wikidot/module/site.py` |
| R6 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R7 | No private material or live action is needed to prove the behavior. | All regressions use synthetic unit-level values and local mocks; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `31006b2 fix(page): validate metadata tag inputs`.

- RED page metadata tag tests: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_invalid_tags_before_request -q` failed 4 cases before the fix. `tags=3` raised raw `TypeError: can only join an iterable`; string and tuple containers advanced into login/AMC mock handling and raised a raw `zip()` length `ValueError`; `tags=["tag-one", 3]` raised raw `TypeError: sequence item 1: expected str instance, int found`.
- RED publish tag tests: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_invalid_tags_before_save -q` failed 4 cases before the fix because each malformed input advanced into page save/result flow and raised `ValueError("page_id must be an integer")` instead of a tag diagnostic.
- GREEN focused page metadata tag tests: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_set_metadata_rejects_invalid_tags_before_request -q` passed 4 tests.
- GREEN focused publish tag tests: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_invalid_tags_before_save -q` passed 4 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 49 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePageAccessor -q` passed 75 tests.
- `uv run pytest tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_page_constructor.py -q` passed 240 tests.
- `uv run pytest tests/unit/test_site.py::TestSitePagesAccessor tests/unit/test_search_pages_query.py -q` passed 83 tests.
- `uv run pytest tests/unit -q` passed 2520 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `Page.set_metadata(tags=3)`, `Page.set_metadata(tags="tag-one tag-two")`, and `Page.set_metadata(tags=("tag-one",))` raise `ValueError("tags must be a list")` before login checks, AMC requests, or local `tags` mutation.
- `Page.set_metadata(tags=["tag-one", 3])` raises `ValueError("tags list entries must be strings")` before login checks, AMC requests, or local `tags` mutation.
- `Site.page.publish("new-page", tags=3)`, string containers, tuple containers, and mixed tag lists raise the same tag diagnostics before login checks, page lookup, create/edit save work, page-ID resolution, source verification, metadata writes, or result creation.
- `Page.set_metadata(tags=None)` and `Site.page.publish(..., tags=None)` still leave tags unchanged.
- Valid `list[str]` tag updates and empty-list tag clearing still work with parent and meta updates.
- Existing metadata action status validation, parent validation, meta tag validation, publish create/edit behavior, source verification ordering, visibility retry behavior, query tag validation, required-tag filtering, and static gates remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with earlier tag validation slices. Mitigation: earlier slices validate query tag inputs, required-tag filters, and direct `Page.tags` constructor state; this slice validates explicit metadata tag write inputs.
- Risk: Rejecting tuple or string containers could affect callers relying on iterable coercion. Mitigation: the public write contract is `list[str] | None`, and coercing strings or tuples can silently build unintended tag payloads.
- Risk: Adding tag syntax validation could overreach. Mitigation: this slice only validates container and entry type, preserving existing tag string content, ordering, and remote Wikidot semantics.
- Risk: Publish preflight ordering could change unrelated validation precedence. Mitigation: the tag validation is placed with adjacent publish input preflight before side effects, without changing title, source, comment, boolean, source-normalizer, parent, or metas validation.

## Out Of Scope

Changing tag syntax, parsing tag strings, accepting tuple/dict/set aliases, changing tag normalization, changing query tag serialization, changing required-tag filtering, changing direct `Page(tags=...)` constructor validation, changing meta tag validation, changing parent validation, changing page source validation, changing publish source verification, changing response parsing, changing live Wikidot behavior, and upstream Issue/PR creation are outside this slice.

## Why This Matters

Tags are write-path payloads for browser-free publishing and metadata cleanup. Generated configuration should fail before a login check, page save, source verification, or metadata request can run when the tag payload has the wrong shape.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used browser-free publish helpers, metadata/tag updates, source verification, visibility retries, and audit-friendly publish result records.
- Existing drafts covered metadata batching, tag-list search validation, required-tag filtering, direct page tag state, parent validation, meta tag validation, publish ordering, and result fields, but did not validate explicit metadata tag write inputs.
- The focused RED failures showed malformed tag write payloads leaking raw Python errors or advancing into publish save/result code before tag diagnostics. The GREEN regressions cover both public write boundaries before request payload construction or publish side effects can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
