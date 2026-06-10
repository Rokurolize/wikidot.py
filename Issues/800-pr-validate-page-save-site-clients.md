# PR Draft: Validate Page Save Site Clients

## Summary

`Page.create_or_edit(...)`, `Site.page.create(...)`, and `Site.page.publish(...)` now validate the retained `Site.client` before authentication. Adjacent local slices already validate direct `Site(client=...)` construction, `Site.amc_request(...)` retained request state, and page-write parent `Site` objects, but a valid `Site` could still have its public `client` field replaced after construction. These save entry points then called `site.client.login_check()` before the existing AMC request-state validator could report `ValueError("client must be a Client")`.

This change adds pre-login retained-client validation for the direct page save helper and the two high-level site-page save wrappers. Valid page creation, existing-page edits, publish optional steps, input-validation precedence, page lookup behavior, metadata updates, source verification, and publish result fields remain unchanged.

## Problem Statement

Browser-free page save helpers should not authenticate or delegate write work through corrupted parent-client state. Before this slice, `Page.create_or_edit(...)` only validated that `site` was a `Site`, while `Site.page.create(...)` and `Site.page.publish(...)` only revalidated the retained accessor site. If a caller, generated fixture, or rehydrated job replaced `site.client` after construction, these helpers could call a duck-typed `login_check()`, reach mocked write delegation, or fail later with unrelated page-save diagnostics instead of using the package's established client diagnostic.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify browser-free page saves and publishing as practical maintenance surfaces. Directly related drafts include [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [351-pr-validate-page-write-bool-controls.md](351-pr-validate-page-write-bool-controls.md), [412-pr-validate-create-or-edit-page-ids.md](412-pr-validate-create-or-edit-page-ids.md), [701-pr-validate-site-constructor-client.md](701-pr-validate-site-constructor-client.md), [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md), and [799-pr-validate-page-write-site-boundaries.md](799-pr-validate-page-write-site-boundaries.md).

This slice is not a duplicate of [701-pr-validate-site-constructor-client.md](701-pr-validate-site-constructor-client.md). Issue 701 rejects malformed `Site(client=...)` constructor input, but it cannot cover a valid `Site` whose public `client` field is replaced later.

This slice is not a duplicate of [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md). Issue 712 validates retained Site AMC request state before non-empty `Site.amc_request(...)` work, but `Page.create_or_edit(...)`, `Site.page.create(...)`, and `Site.page.publish(...)` each authenticate through `site.client.login_check()` before reaching AMC request validation.

This slice is not a duplicate of [799-pr-validate-page-write-site-boundaries.md](799-pr-validate-page-write-site-boundaries.md). Issue 799 rejects malformed parent-site objects. This draft covers mutated retained `Site.client` on otherwise valid `Site` objects.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Direct browser-free page saves through `Page.create_or_edit(...)`.
- High-level page creation through `Site.page.create(...)`.
- Browser-free publishing through `Site.page.publish(...)`, including create-or-edit selection, post-save page-ID resolution, source verification, metadata updates, and publish result construction.
- Unit-test fixtures, generated ledgers, serialized page jobs, and local maintenance scripts that may rehydrate or mutate `Site` records before save work.

## Proposed Fix

- Add a page-module retained-site-client validator that reports `ValueError("client must be a Client")`.
- Use the new page-module validator in `Page.create_or_edit(...)` immediately after site validation and before `login_check()`.
- Reuse the existing site-module `_validate_site_client(...)` in `SitePageAccessor.create(...)` and `SitePageAccessor.publish(...)` immediately after retained-site validation and before `login_check()`.
- Use the validated client object for authentication.

## Implementation Notes

Implemented locally in commit `21456b2 fix(page): validate save site clients`.

The page module uses a local `_validate_page_site_client(...)` helper instead of importing `_validate_site_client(...)` from `site.py`, because `site.py` already imports page classes at module import time. The new helper lazily imports `Client`, preserves the existing public diagnostic, and avoids adding a circular import.

The focused RED failures demonstrated three save-boundary gaps:

- `Page.create_or_edit(...)` with a valid `Site` whose `client` was replaced by `MagicMock()` called the malformed client's `login_check()` and reached edit-lock handling, failing with `TargetErrorException: Page new-page is locked or other locks exist`.
- `Site.page.create(...)` with a mutated retained `site.client` failed with `DID NOT RAISE` because the malformed client was accepted through login and the helper delegated to mocked `Page.create_or_edit(...)`.
- `Site.page.publish(...)` with a mutated retained `site.client` reached login, lookup, and mocked write delegation before failing later with `ValueError("page_id must be an integer")`.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| `Page.create_or_edit(...)` rejects mutated retained `site.client` before authentication or edit-lock requests. | `TestPageCreateOrEdit.test_create_or_edit_rejects_mutated_site_client_before_login` failed RED with edit-lock handling, then passed GREEN. | Calling malformed `login_check()`, calling `site.amc_request(...)`, accepting duck-typed clients, or leaking page-lock diagnostics rejects this claim. |
| `Site.page.create(...)` rejects mutated retained `site.client` before login, lookup, or save delegation. | `TestSitePageAccessor.test_create_rejects_mutated_site_client_before_login` failed RED with `DID NOT RAISE`, then passed GREEN. | Calling malformed `login_check()`, calling `get(...)`, or delegating to `Page.create_or_edit(...)` rejects this claim. |
| `Site.page.publish(...)` rejects mutated retained `site.client` before login, lookup, save delegation, result construction, verification, or metadata work. | `TestSitePageAccessor.test_publish_rejects_mutated_site_client_before_save` failed RED with later result validation, then passed GREEN. | Calling malformed `login_check()`, `get(...)`, `Page.create_or_edit(...)`, source verification, metadata writes, or result construction rejects this claim. |
| Existing valid direct and high-level page save behavior remains stable. | Focused affected classes passed 174 tests; page+site coverage passed 843 tests; full unit passed 3876 tests. | Regressing direct create/edit, `Site.page.create(...)`, `Site.page.publish(...)`, source verification, metadata updates, visibility retry behavior, or publish result fields rejects this claim. |
| Repository quality gates remain green. | Full unit, ruff, format, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `21456b2 fix(page): validate save site clients`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit::test_create_or_edit_rejects_mutated_site_client_before_login tests/unit/test_site.py::TestSitePageAccessor::test_create_rejects_mutated_site_client_before_login tests/unit/test_site.py::TestSitePageAccessor::test_publish_rejects_mutated_site_client_before_save -q --tb=short` failed 3 tests before the fix with `TargetErrorException`, `DID NOT RAISE`, and `ValueError("page_id must be an integer")`.
- GREEN focused: the same focused command passed 3 tests after retained-client validation was added.
- Affected create/edit/site accessor coverage: `uv run pytest tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_site.py::TestSitePageAccessor -q --tb=short` passed 174 tests.
- Adjacent page/site modules: `uv run pytest tests/unit/test_page.py tests/unit/test_site.py -q --tb=short` passed 843 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3876 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.create_or_edit(...)` with a valid `Site` whose `client` field has been replaced by a non-`Client` object raises `ValueError("client must be a Client")` before login checks, edit-lock AMC requests, save AMC requests, stale search fallback, post-save lookup, or local cache mutation.
- `Site.page.create(...)` with a mutated non-`Client` retained `site.client` raises `ValueError("client must be a Client")` before login, page lookup, existing-page edit delegation, or `Page.create_or_edit(...)`.
- `Site.page.publish(...)` with a mutated non-`Client` retained `site.client` raises `ValueError("client must be a Client")` before login, page lookup, create/edit saves, post-save page-ID resolution, source verification, metadata writes, or result construction.
- Existing explicit input validation still runs before retained-client validation for malformed fullname, title, source, comment, force-edit, verify-source, visibility, tags, parent, and metas values.
- Existing successful create, edit, and publish behavior remains green for valid `Site` and `Client` parents.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: Earlier client validation could change precedence for calls that pass both malformed retained client state and malformed explicit inputs. Mitigation: validation is placed after existing explicit input validators, matching adjacent page-write ordering.
- Risk: The page module now has a client validator that duplicates the site-module diagnostic. Mitigation: importing the site-module helper directly would couple into the existing `site.py` to `page.py` import direction; the local helper preserves the public diagnostic without introducing a circular import.
- Risk: High-level wrappers now reject mutated clients before the lower-level `Site.amc_request(...)` validator can report them. Mitigation: the new behavior fails earlier with the same `ValueError("client must be a Client")` diagnostic and prevents authentication through malformed state.

## Dependencies

- Existing `Client` class identity remains the parent-client contract.
- Existing `_validate_page_site(...)` and `_validate_site_accessor_site(...)` still define parent-site validation.
- Existing page save input validators continue to define fullname, title, source, comment, optional page ID, boolean control, metadata, and visibility-control precedence.

## Open Questions

Direct page action methods that already validate `self.site` but still authenticate through `site.client` remain separate future candidates. This slice only claims the direct static save helper and high-level `Site.page.create(...)` / `Site.page.publish(...)` save wrappers.

## Rationale for Upstream Suitability

The change makes documented page save boundaries fail locally and deterministically when their retained parent client is corrupted, using the same client diagnostic already enforced by constructor and AMC request-state validators. It prevents authentication and write-side work from starting with malformed parent-client state while preserving valid browser-free page creation, editing, publishing, source verification, metadata updates, and publish result behavior.

## Local Evidence

- Local browser-free publishing drafts repeatedly use direct page saves and high-level publishing to create, edit, verify, and audit page updates.
- Existing local drafts covered `Site(client=...)` constructor validation, Site AMC request-state validation, page write parent-site validation, page write input validation, create/edit page-ID validation, and publish result ergonomics. They did not cover post-construction retained `Site.client` mutation before page-save authentication.
- This slice only validates retained client state for page save entry points. It does not change live Wikidot behavior, page lookup selectors, edit-lock parsing, save response parsing, source serialization, source verification comparison, metadata request shape, visibility retry behavior, result dictionary fields, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source, private page content, private site data, and private forum metadata out of upstream discussion.

## Additional Notes

Callers that construct fixtures or deserialize jobs should keep retained `Site.client` values as real `Client` instances before invoking page save APIs.
