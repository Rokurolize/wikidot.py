# PR Draft: Validate Page Write Site Boundaries

## Summary

`Page.create_or_edit(...)`, `Site.page.create(...)`, and `Site.page.publish(...)` are browser-free page write entry points that document a `Site` parent. Adjacent write paths already validate retained page sites, accessor constructor parents, and many write-control inputs before authentication or request work, but these three boundaries still trusted malformed site-like stand-ins in specific paths.

This change validates the direct `Page.create_or_edit(site=...)` argument with the existing page-site validator before `login_check()` and edit-lock requests. It also revalidates the retained `SitePageAccessor.site` before `Site.page.create(...)` and `Site.page.publish(...)` can authenticate, look up pages, delegate saves, resolve post-save visibility, verify sources, or update metadata. Valid page creation, existing-page edits, publish optional steps, input-validation precedence, and result fields remain unchanged.

## Problem Statement

Direct page writes and high-level browser-free publish helpers should reject malformed parent-site state at the local API boundary. Before this slice, a structurally similar mock, dictionary-backed object, or rehydrated malformed accessor parent could reach login checks, mocked AMC request work, delegated `Page.create_or_edit(...)`, or later result construction before the package reported a stable `ValueError("site must be a Site")`.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page writes and publishing as practical operational surfaces. The directly related write-path drafts are [001-pr-page-lookup-create-edit-hardening.md](001-pr-page-lookup-create-edit-hardening.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [189-pr-page-edit-login-guard-before-source-fetch.md](189-pr-page-edit-login-guard-before-source-fetch.md), [242-pr-page-edit-lock-field-context.md](242-pr-page-edit-lock-field-context.md), [243-pr-page-save-status-context.md](243-pr-page-save-status-context.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md), [786-pr-validate-page-edit-retained-fullname.md](786-pr-validate-page-edit-retained-fullname.md), [787-pr-validate-page-edit-retained-page-id.md](787-pr-validate-page-edit-retained-page-id.md), and [794-pr-validate-set-metadata-retained-page-id.md](794-pr-validate-set-metadata-retained-page-id.md).

Parent-state drafts also establish the local validation pattern: [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [701-pr-validate-site-constructor-client.md](701-pr-validate-site-constructor-client.md), and [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md).

This slice is not a duplicate of [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md). Issue 478 validates accessor construction, while this draft covers post-construction retained accessor-site mutation before high-level create/publish work.

This slice is not a duplicate of [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md) or [564-pr-validate-page-edit-site.md](564-pr-validate-page-edit-site.md). Those drafts cover `Page(...)` construction and `Page.edit()` retained page-site state; this draft covers the direct static `Page.create_or_edit(site=...)` argument plus the high-level site-page accessor wrappers.

This slice is not a duplicate of [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md). Issue 712 validates mutated `Site` request metadata before `Site.amc_request(...)`; this draft rejects non-`Site` parent objects before page write helpers can authenticate or delegate.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Browser-free page creation and editing through `Page.create_or_edit(...)`.
- High-level page creation through `Site.page.create(...)`.
- Browser-free publishing through `Site.page.publish(...)`, including create-or-edit selection, source verification, metadata updates, and publish audit result creation.
- Unit-test fixtures, generated ledgers, rehydrated page jobs, and local maintenance scripts that may use structural stand-ins while assembling write tasks.

## Proposed Fix

- Validate `Page.create_or_edit(site=...)` with `_validate_page_site(site)` after explicit write-input validation and before `site.client.login_check()`.
- Validate retained `SitePageAccessor.site` with `_validate_site_accessor_site(self.site)` in `create(...)` and `publish(...)` after explicit argument validation and before authentication.
- Use the validated site for login, new-page save delegation, and publish source-verification diagnostics.
- Preserve all existing valid write behavior, invalid input precedence, page lookup behavior, post-save visibility behavior, metadata update behavior, and result fields.

## Implementation Notes

Implemented locally in commit `961cbe3 fix(page): validate write site boundaries`.

The implementation intentionally reuses existing validators rather than adding new abstractions. `Page.create_or_edit(...)` rebinds the public `site` argument after validating fullname, title, source, comment, optional page ID, and boolean controls, preserving existing explicit input precedence. `SitePageAccessor.create(...)` and `SitePageAccessor.publish(...)` validate the retained accessor site before calling `login_check()`, and pass the validated object into the direct save helper when creating a page.

The focused RED failures demonstrated three distinct gaps:

- `Page.create_or_edit(cast(Any, malformed_site), "new-page", ...)` reached the mocked write path and raised `TargetErrorException("Page new-page is locked or other locks exist")` instead of `ValueError("site must be a Site")`.
- `Site.page.create(...)` with mutated `mock_site_no_http.page.site` failed with `DID NOT RAISE` because the malformed accessor parent reached mocked `Page.create_or_edit(...)`.
- `Site.page.publish(...)` with mutated `mock_site_no_http.page.site` reached login, lookup, and mocked write delegation before failing later with `ValueError("page_id must be an integer")`.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Page.create_or_edit(...)` rejects malformed `site` before authentication or write requests. | `TestPageCreateOrEdit.test_create_or_edit_rejects_malformed_site_before_login` failed RED with downstream write behavior, then passed GREEN. | Calling `login_check()`, calling `amc_request(...)`, accepting non-`Site` stand-ins, or leaking edit-lock/save diagnostics rejects this claim. |
| `Site.page.create(...)` rejects mutated non-`Site` accessor parents before login, lookup, or save delegation. | `TestSitePageAccessor.test_create_rejects_malformed_accessor_site_before_login` failed RED with `DID NOT RAISE`, then passed GREEN. | Calling malformed parent `login_check()`, calling `get(...)`, or delegating to `Page.create_or_edit(...)` rejects this claim. |
| `Site.page.publish(...)` rejects mutated non-`Site` accessor parents before login, lookup, save delegation, result construction, verification, or metadata work. | `TestSitePageAccessor.test_publish_rejects_malformed_accessor_site_before_save` failed RED after reaching later result construction, then passed GREEN. | Calling malformed parent `login_check()`, `amc_request(...)`, `get(...)`, `Page.create_or_edit(...)`, source verification, metadata writes, or result construction rejects this claim. |
| Existing valid direct and high-level page write behavior remains stable. | Focused page create/edit and site accessor coverage passed 192 tests; page+site coverage passed 840 tests; full unit passed 3873 tests. | Regressing direct create/edit, `Page.edit()`, `Site.page.create(...)`, `Site.page.publish(...)`, post-save visibility, source verification, metadata updates, or publish result fields rejects this claim. |
| Repository quality gates remain green. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `961cbe3 fix(page): validate write site boundaries`.

- RED direct helper: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_malformed_site_before_login -q --tb=short` failed before the fix with `TargetErrorException: Page new-page is locked or other locks exist`.
- RED high-level create: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_malformed_accessor_site_before_login -q --tb=short` failed before the accessor fix with `DID NOT RAISE`.
- RED high-level publish: `uv run pytest tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_malformed_accessor_site_before_save -q --tb=short` failed before the publish fix with `ValueError("page_id must be an integer")` after later result construction was reached.
- GREEN focused: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_malformed_site_before_login tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_malformed_accessor_site_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_malformed_accessor_site_before_save -q --tb=short` passed 3 tests.
- Adjacent create/edit/site accessor coverage: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_site.py::TestSitePageAccessor -q --tb=short` passed 192 tests.
- Adjacent page/site modules: `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q --tb=short` passed 840 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3873 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.create_or_edit(cast(Any, malformed_site), "new-page", ...)` raises `ValueError("site must be a Site")` before login checks, edit-lock AMC requests, save AMC requests, stale search fallback, post-save lookup, or local cache mutation.
- `Site.page.create(...)` with a mutated non-`Site` `SitePageAccessor.site` raises `ValueError("site must be a Site")` before login, page lookup, existing-page edit delegation, or `Page.create_or_edit(...)`.
- `Site.page.publish(...)` with a mutated non-`Site` `SitePageAccessor.site` raises `ValueError("site must be a Site")` before login, page lookup, create/edit saves, post-save page-ID resolution, source verification, metadata writes, or result construction.
- Existing explicit input validation still runs before site validation for malformed fullname, title, source, comment, force-edit, verify-source, visibility, tags, parent, and metas values.
- Existing successful create, edit, and publish behavior remains green for valid `Site` parents.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: Earlier site validation could change precedence for calls that pass both malformed site state and malformed explicit inputs. Mitigation: validation is placed after existing explicit input validators, matching adjacent write-path ordering.
- Risk: High-level `create(...)` and `publish(...)` now reject mutated accessor parents before the lower-level helper can reject them. Mitigation: `SitePageAccessor(site=...)` already requires `Site` at construction, and this slice only applies the same invariant at action time.
- Risk: The source-verification diagnostic now reads `site.unix_name` from the validated local site. Mitigation: valid behavior is unchanged because the validated object is the same retained `Site` instance for normal calls.

## Dependencies

- Existing `_validate_page_site(...)` remains the canonical page parent-site validator.
- Existing `_validate_site_accessor_site(...)` remains the canonical site-accessor parent validator.
- Existing page write input validators continue to define fullname, title, source, comment, optional page ID, boolean control, metadata, and visibility-control precedence.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, cache ownership boundaries, result ergonomics, or complexity candidates outside this now-covered page-write site-boundary path.

## Rationale for Upstream Suitability

The change makes documented page write boundaries fail locally and deterministically when their parent site is malformed, using validators already present in the package. It prevents authentication and write-side work from starting with corrupted parent state while preserving valid browser-free page creation, edit, publish, source verification, metadata updates, and publish result behavior.

## Local Evidence

- Local browser-free publishing drafts repeatedly use direct page writes and high-level publishing to create, edit, verify, and audit page updates.
- Existing local drafts covered page lookup/create/edit hardening, edit-lock diagnostics, save diagnostics, direct page-ID validation, write boolean controls, page constructor site validation, accessor constructor parent validation, page edit retained-site validation, and adjacent retained page-ID validation. They did not cover the direct `Page.create_or_edit(site=...)` site argument or post-construction mutation of `SitePageAccessor.site` before high-level create/publish calls.
- This slice only validates page write parent-site boundaries. It does not change live Wikidot behavior, page lookup selectors, edit-lock parsing, save response parsing, source serialization, source verification comparison, metadata request shape, visibility retry behavior, result dictionary fields, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source, private page content, private site data, and private forum metadata out of upstream discussion.

## Additional Notes

The implementation intentionally rejects malformed parent objects instead of using duck typing. Callers that construct fixtures or deserialize jobs should create real `Site` instances before invoking page write APIs.
