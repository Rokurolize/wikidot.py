# PR Draft: Validate Page Action Site Clients

## Summary

Direct `Page` action methods now validate retained `page.site.client` state before authentication. Issue 800 covered the direct static save helper and high-level `Site.page.create(...)` / `Site.page.publish(...)` wrappers, but the action methods on an existing `Page` still validated `self.site` and retained page IDs before calling `site.client.login_check()` without checking that the retained client was still a `Client`.

This change reuses the page-module retained-site-client validator across `Page.edit(...)`, `Page.destroy()`, `Page.commit_tags()`, `Page.set_parent(...)`, `Page.rename(...)`, `Page.vote(...)`, `Page.cancel_vote()`, the `Page.metas` setter, and `Page.set_metadata(...)`. Valid action behavior, explicit input-validation precedence, retained page-ID precedence, request shapes, cache invalidation, local mutation timing, and response diagnostics remain unchanged.

## Problem Statement

Existing direct page action slices hardened malformed retained `page.site` objects, malformed retained page IDs, mutable page title/fullname state, metadata payloads, returned action statuses, returned rating points, and cache invalidation ordering. One adjacent retained-state boundary remained: a valid `Page` could retain a valid `Site` whose public `client` field was replaced after construction. The affected methods then authenticated through that malformed client and could reach AMC request diagnostics, metadata response pairing, or edit delegation before reporting the established `ValueError("client must be a Client")`.

## Rollout Evidence

Local rollout-backed drafts repeatedly identify direct page actions as browser-free maintenance surfaces. Related direct action drafts include [562-pr-validate-page-cancel-vote-site.md](562-pr-validate-page-cancel-vote-site.md), [565-pr-validate-page-metas-setter-site.md](565-pr-validate-page-metas-setter-site.md), [787-pr-validate-page-edit-retained-page-id.md](787-pr-validate-page-edit-retained-page-id.md), [788-pr-validate-commit-tags-retained-page-id.md](788-pr-validate-commit-tags-retained-page-id.md), [789-pr-validate-set-parent-retained-page-id.md](789-pr-validate-set-parent-retained-page-id.md), [790-pr-validate-rename-retained-page-id.md](790-pr-validate-rename-retained-page-id.md), [791-pr-validate-vote-retained-page-id.md](791-pr-validate-vote-retained-page-id.md), [792-pr-validate-cancel-vote-retained-page-id.md](792-pr-validate-cancel-vote-retained-page-id.md), [793-pr-validate-destroy-retained-page-id.md](793-pr-validate-destroy-retained-page-id.md), [794-pr-validate-set-metadata-retained-page-id.md](794-pr-validate-set-metadata-retained-page-id.md), [795-pr-validate-metas-setter-retained-page-id.md](795-pr-validate-metas-setter-retained-page-id.md), and [800-pr-validate-page-save-site-clients.md](800-pr-validate-page-save-site-clients.md).

This slice is not a duplicate of [701-pr-validate-site-constructor-client.md](701-pr-validate-site-constructor-client.md), which rejects malformed constructor clients, or [712-pr-validate-site-amc-request-state.md](712-pr-validate-site-amc-request-state.md), which validates retained Site state at the AMC request wrapper. These page action methods authenticate before reaching the AMC wrapper.

This slice is not a duplicate of [800-pr-validate-page-save-site-clients.md](800-pr-validate-page-save-site-clients.md). Issue 800 covers `Page.create_or_edit(...)` and `Site.page.create(...)` / `Site.page.publish(...)`; this draft covers direct action methods on an existing `Page`.

No upstream issue was filed from this local workspace.

## Affected Workflows

- Direct browser-free page editing through `Page.edit(...)`.
- Direct page deletion, tag saves, parent updates, renames, votes, and vote cancellation.
- Direct metadata writes through `Page.metas = ...` and `Page.set_metadata(...)`.
- Generated ledgers, serialized page jobs, migration scripts, moderation helpers, and local maintenance tasks that may rehydrate or mutate page parent state before action work.

## Proposed Fix

- Reuse `_validate_page_site_client(site)` after each method's existing retained-site and retained-ID validation and before `login_check()`.
- Call `client.login_check()` on the validated client object.
- Preserve existing explicit input and retained page-ID validation order by placing the client check after those validators.
- Leave request construction, response parsing, cache invalidation, and local mutation behavior unchanged for valid `Site` / `Client` parents.

## Implementation Notes

Implemented locally in commit `806cf96 fix(page): validate action site clients`.

The implementation intentionally builds on the Issue 800 page helper instead of adding another abstraction. The helper still lazily imports `Client`, preserving the existing module import direction while producing the same `ValueError("client must be a Client")` diagnostic used by site and client validators.

The focused RED failures demonstrated a shared direct-action gap:

- `Page.destroy()`, `Page.commit_tags()`, `Page.set_parent(...)`, `Page.rename(...)`, `Page.vote(...)`, and `Page.cancel_vote()` reached malformed login and later action-response diagnostics.
- The `Page.metas` setter and `Page.set_metadata(...)` reached malformed login and then response-pairing failures such as `ValueError("zip() argument 2 is shorter than argument 1")`.
- `Page.edit(...)` reached delegated save behavior and failed with a mocked revision-count comparison instead of a retained-client diagnostic.

## Requirements Traceability

| Requirement | Verification | Negative Check |
| --- | --- | --- |
| Direct write actions reject mutated retained `page.site.client` before login and AMC request work. | `TestPageWriteMethods.test_write_methods_reject_mutated_site_client_before_login` failed RED for eight action variants, then passed GREEN. | Calling malformed `login_check()`, calling `site.amc_request(...)`, mutating local page state, or surfacing response diagnostics rejects this claim. |
| `Page.edit(...)` rejects mutated retained `page.site.client` before login, source reads, save delegation, or cache mutation. | `TestPageEdit.test_edit_rejects_mutated_site_client_before_login_or_delegation` failed RED with delegated mocked behavior, then passed GREEN. | Calling malformed `login_check()`, calling `Page.create_or_edit(...)`, reading source unnecessarily, changing title/revision/source state, or leaking delegated errors rejects this claim. |
| Existing explicit input and retained page-ID diagnostics keep precedence. | Affected page write/edit/create coverage passed 217 tests; full page module passed 477 tests. | Moving client validation before malformed action inputs or retained page-ID diagnostics rejects this claim. |
| Existing valid direct page action behavior remains stable. | Full unit coverage passed 3885 tests. | Regressing edit, delete, tag save, parent update, rename, vote, cancel-vote, metadata writes, cache invalidation, or response diagnostics rejects this claim. |
| Repository quality gates remain green. | Ruff, format check, mypy, pyright, whitespace, Brooks focused review, and Clawpatch provenance checks passed. | Test, lint, format, type, whitespace, review, or unreported tooling failures reject this claim. |

## Tests and Verification

Implemented locally in commit `806cf96 fix(page): validate action site clients`.

- RED: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_write_methods_reject_mutated_site_client_before_login tests/unit/test_page.py::TestPageEdit::test_edit_rejects_mutated_site_client_before_login_or_delegation -q --tb=short` failed 9 cases before the fix with malformed action-response diagnostics, metadata response-pairing errors, and delegated mocked edit behavior instead of `ValueError("client must be a Client")`.
- GREEN focused: the same focused command passed 9 tests after retained-client validation was added to the direct action methods.
- Affected page action coverage: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods tests/unit/test_page.py::TestPageEdit tests/unit/test_page.py::TestPageCreateOrEdit -q --tb=short` passed 217 tests.
- Full page module: `uv run pytest tests/unit/test_page.py -q --tb=short` passed 477 tests.
- Full unit: `uv run pytest tests/unit -q --tb=short` passed 3885 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files, plus existing notes about unchecked untyped function bodies and the existing unused-section note from `pyproject.toml`.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.
- Brooks focused changed-file review found no blocking findings. Full Brooks sweep was not run because the skill requires explicit full-repository auto-fix consent.
- Clawpatch local provenance check passed: local fork commit `d89ca91`, provider `codex-cli 0.139.0`, doctor state `missing`, secrets redacted, launcher SHA256 `6527a7f968bca0e270cb98fa4e6b7707ca951868309562078e518faefa6726b8`.

## Acceptance Criteria

- `Page.edit(...)` with a valid `Page` whose retained `page.site.client` has been replaced by a non-`Client` object raises `ValueError("client must be a Client")` before login, source reads, create/edit delegation, local title/source mutation, revision-count sync, or revision-cache invalidation.
- `Page.destroy()`, `Page.commit_tags()`, `Page.set_parent(...)`, `Page.rename(...)`, `Page.vote(...)`, `Page.cancel_vote()`, `Page.metas = ...`, and `Page.set_metadata(...)` with a mutated non-`Client` retained `page.site.client` raise `ValueError("client must be a Client")` before login, AMC requests, returned-status parsing, response-pairing, local state mutation, or cache invalidation.
- Existing explicit input validation and retained page-ID validation still run before retained-client validation for valid-client calls.
- Existing successful direct page action behavior remains green for valid `Site` and `Client` parents.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the slice.

## Compatibility and Risk Notes

- Risk: Earlier client validation could change precedence for calls that pass both malformed retained client state and malformed explicit action inputs. Mitigation: the client check is placed after existing explicit input and retained-ID validators.
- Risk: This could be confused with the save-helper client validation from Issue 800. Mitigation: this draft covers direct action methods on an existing `Page`; Issue 800 remains limited to `Page.create_or_edit(...)` and high-level `Site.page` save wrappers.
- Risk: Broadening the helper across many methods could hide method-specific behavior changes. Mitigation: the implementation only replaces `site.client.login_check()` with `client = _validate_page_site_client(site)` followed by `client.login_check()`, and full page plus full unit coverage remains green.

## Dependencies

- Existing `Client` class identity remains the parent-client contract.
- Existing `_validate_page_site(...)`, `_validate_page_site_client(...)`, `_validate_retained_page_id(...)`, and page action input validators continue to define pre-authentication boundaries.
- Existing page action response validators continue to define malformed remote response diagnostics after valid authentication and request work.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked parser diagnostics, public input boundaries, retained state boundaries, result ergonomics, cache ownership checks, cross-owner batch checks, or complexity candidates outside this now-covered direct page action retained-client boundary.

## Rationale for Upstream Suitability

The change makes documented direct page action methods fail locally and deterministically when their retained parent client is corrupted, using the same client diagnostic already enforced by constructor, AMC request-state, and page save-boundary validators. It prevents authentication and write-side work from starting with malformed parent-client state while preserving valid browser-free page editing, deletion, metadata maintenance, renaming, voting, cache invalidation, and response handling.

## Local Evidence

- Local browser-free maintenance drafts repeatedly use direct page actions to edit, delete, tag, parent, rename, vote, cancel votes, and update metadata.
- Existing local drafts covered malformed retained page sites, retained page IDs, page save retained-client validation, direct action response diagnostics, and cache invalidation ordering. They did not cover post-construction retained `page.site.client` mutation before direct page action authentication.
- This slice only validates retained client state for direct page action entry points. It does not change live Wikidot behavior, page lookup selectors, edit-lock parsing, save response parsing, action response parsing, metadata request shape, cache invalidation timing, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, credentials, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, cookies, auth JSON, raw page source, private page content, private site data, and private forum metadata out of upstream discussion.

## Additional Notes

Callers that mutate or rehydrate page records should keep `page.site.client` as a real `Client` instance before invoking direct page action APIs.
