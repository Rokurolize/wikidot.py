# PR Draft: Validate Site Constructor Client

## Summary

`Site(...)` records already validate site ID shape and range, title text, routing metadata, blank routing metadata, URL-time metadata, lookup clients for `Site.from_unix_name(...)`, accessor parent sites, site-scoped record parent fields, and downstream action/read parent-site state. One direct constructor gap remained: `Site(client=...)` accepted arbitrary non-`Client` objects and still initialized `Site.pages`, `Site.page`, and `Site.forum` accessors around the malformed parent client.

This change validates the direct constructor client field at `Site.__post_init__()`. Malformed constructor clients now raise `ValueError("client must be a Client")`, while valid `Client` instances, site metadata validation, accessors, site lookup behavior, empty AMC-batch short-circuit behavior, and adjacent client/user/request workflows remain unchanged.

## Outcome

Direct `Site(...)` rows cannot store malformed parent-client state. Valid parser-created and directly constructed sites, constructor metadata validation, site lookup preflight, accessor construction, empty AMC batch behavior, retry-empty batch behavior, and adjacent site/client/user/auth/request utility workflows remain green.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free site lookup, generated site ledgers, local fixtures, serialized site records, migration tooling, moderation workflows, or rehydrated `Site` objects before page, forum, member, application, or recent-change work.

## Current Evidence

Site and lookup drafts [310-pr-site-id-context.md](310-pr-site-id-context.md), [338-pr-result-ledger-site-field.md](338-pr-result-ledger-site-field.md), [359-pr-validate-site-lookup-unix-names.md](359-pr-validate-site-lookup-unix-names.md), [394-pr-validate-site-amc-retry-controls.md](394-pr-validate-site-amc-retry-controls.md), [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [525-pr-validate-site-lookup-config-object.md](525-pr-validate-site-lookup-config-object.md), [526-pr-validate-site-amc-retry-config-object.md](526-pr-validate-site-amc-retry-config-object.md), [548-pr-validate-site-lookup-client.md](548-pr-validate-site-lookup-client.md), [571-pr-validate-site-url-metadata-state.md](571-pr-validate-site-url-metadata-state.md), [629-pr-validate-blank-site-routing-metadata.md](629-pr-validate-blank-site-routing-metadata.md), and [645-pr-validate-non-negative-site-ids.md](645-pr-validate-non-negative-site-ids.md) establish site identity, lookup, request controls, constructor metadata, URL metadata, lookup-client validation, and ID/routing invariants as practical browser-free infrastructure boundaries.

Adjacent parent-state drafts [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md), [475-pr-validate-forum-thread-collection-site-field.md](475-pr-validate-forum-thread-collection-site-field.md), [476-pr-validate-forum-category-collection-site-field.md](476-pr-validate-forum-category-collection-site-field.md), [477-pr-validate-page-collection-site-field.md](477-pr-validate-page-collection-site-field.md), [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), and [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md) establish the local pattern for validating parent objects at public constructor boundaries instead of relying only on parser-created objects or later request failures.

This slice is not a duplicate of those drafts. Issue 548 validates the caller-provided `client` argument to `Site.from_unix_name(...)`, not direct `Site(client=...)` construction. Issue 480 validates direct `Site` metadata fields, not the parent client field. Issues 525 and 526 validate retained config objects used by lookup and retry paths. Issue 478 validates the child accessors receive a `Site`, but it does not validate the `Site` object's own retained client. No upstream issue was filed from this local workspace.

## Related Issue / Non-Duplicate Analysis

Builds directly on [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), [548-pr-validate-site-lookup-client.md](548-pr-validate-site-lookup-client.md), [571-pr-validate-site-url-metadata-state.md](571-pr-validate-site-url-metadata-state.md), [629-pr-validate-blank-site-routing-metadata.md](629-pr-validate-blank-site-routing-metadata.md), [645-pr-validate-non-negative-site-ids.md](645-pr-validate-non-negative-site-ids.md), and the parent-state validation pattern from [478-pr-validate-site-accessor-parent-sites.md](478-pr-validate-site-accessor-parent-sites.md), [486-pr-validate-page-constructor-site.md](486-pr-validate-page-constructor-site.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [501-pr-validate-site-member-site-field.md](501-pr-validate-site-member-site-field.md), [502-pr-validate-forum-category-site-field.md](502-pr-validate-forum-category-site-field.md), and [503-pr-validate-forum-thread-site-field.md](503-pr-validate-forum-thread-site-field.md).

## Changes

- Add a direct `Site` client validator that reuses the established `ValueError("client must be a Client")` diagnostic.
- Validate `self.client` at the start of `Site.__post_init__()` before site metadata validation and accessor construction.
- Keep `Site.from_unix_name(...)` on the same client diagnostic path by delegating its lookup-client helper to the shared validator.
- Update AMC empty-batch tests to use a valid `Client` subclass whose `amc_client` property raises if touched, preserving the no-access assertion under the new constructor invariant.

## Type Of Change

- State validation
- Site constructor hardening
- Parent-client integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Site(client=...)` must reject `None`, `True`, `"test-client"`, `{"username": "test-user"}`, and arbitrary objects with `ValueError("client must be a Client")` before storing accessors around malformed client state. |
| R2 | Valid `Client` objects and existing `mock_client_no_http` test doubles that satisfy `isinstance(..., Client)` must remain accepted. |
| R3 | Existing site metadata diagnostics for `id`, `title`, `unix_name`, `domain`, and `ssl_supported` must remain unchanged once the client is valid. |
| R4 | `Site.from_unix_name(...)` must keep the same malformed-client diagnostic and lookup behavior. |
| R5 | Empty `Site.amc_request([])` and `Site.amc_request_with_retry([])` calls must still return `()` without reading `site.client.amc_client` when the retained client is a valid `Client` object. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, constructor tests, adjacent site/client/user/auth/request tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed direct clients fail at the constructor boundary. | `TestSiteInit.test_init_rejects_malformed_client` failed RED for five malformed clients with `DID NOT RAISE`, then passed GREEN after `Site.__post_init__()` validated `self.client`. | Accepting non-`Client` values, coercing values, initializing accessors around malformed clients, or deferring failure to later request paths rejects this local completion claim. | `Site` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site_constructor.py` |
| R2 | Valid `Client` instances remain accepted by direct construction. | Existing `TestSiteInit.test_init_accepts_valid_metadata` and broad site fixture coverage passed after the constructor check. | Rejecting valid `Client` instances, breaking `mock_client_no_http`, or requiring initialized network state rejects this local completion claim. | `Site` constructor fixtures | `tests/unit/test_site_constructor.py`, `tests/unit/test_site.py` |
| R3 | Existing metadata validation remains stable. | `tests/unit/test_site_constructor.py` passed 41 tests, including malformed metadata, negative ID, blank routing metadata, zero ID, and URL-time metadata mutation coverage. | Changing metadata diagnostic order after a valid client, accepting malformed metadata, or rejecting valid metadata rejects this local completion claim. | `Site` constructor metadata | `tests/unit/test_site_constructor.py` |
| R4 | Lookup-client validation remains compatible. | Adjacent site lookup tests in `tests/unit/test_site.py` passed in the 749-test adjacent run. | Weakening direct lookup validation, changing `ValueError("client must be a Client")`, or changing site lookup parsing rejects this local completion claim. | `Site.from_unix_name(...)` | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R5 | Empty AMC batch short-circuits remain independent of `amc_client`. | `TestSiteAmcRequest` empty-batch tests passed after their sentinels became valid `Client` subclasses with raising `amc_client` properties. | Reading `amc_client`, requiring config/header state for empty batches, or changing the empty result from `()` rejects this local completion claim. | `Site.amc_request(...)`, `Site.amc_request_with_retry(...)` | `tests/unit/test_site.py` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level synthetic clients and site metadata only. | Using credentials, cookies, auth JSON, private site data, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, constructor/adjacent/full-unit tests, ruff, format check, mypy, pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `d9e71b3 fix(site): validate constructor client`.

- RED: `uv run pytest tests/unit/test_site_constructor.py::TestSiteInit::test_init_rejects_malformed_client -q` failed 5 tests before the fix with `DID NOT RAISE`.
- GREEN: the same focused command passed 5 tests after direct constructor client validation was added.
- `uv run pytest tests/unit/test_site_constructor.py -q` passed 41 tests.
- First adjacent run: `uv run pytest tests/unit/test_site.py tests/unit/test_site_constructor.py tests/unit/test_site_accessors.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_user.py tests/unit/test_auth.py tests/unit/test_requestutil.py -q` initially failed 7 empty-AMC sentinel tests because those tests constructed `Site` with a non-`Client` object.
- Corrected adjacent run: the same adjacent command passed 749 tests after the sentinels were changed to valid `Client` subclasses that still raise if `amc_client` is touched.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py tests/unit/test_site_constructor.py` left all 3 files unchanged.
- `uv run pytest tests/unit -q` passed 3529 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy` reported the expected local CLI usage error `Missing target module, package, files, or command`; corrected gate `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `Site(client=None)`, `Site(client=True)`, `Site(client="test-client")`, `Site(client={"username": "test-user"})`, and `Site(client=object())` raise `ValueError("client must be a Client")`.
- Malformed direct clients fail before `Site.pages`, `Site.page`, or `Site.forum` accessors can be used around invalid client state.
- Valid `Client` objects and existing valid test doubles remain accepted.
- Existing constructor metadata validation, URL-time metadata validation, site lookup behavior, accessor behavior, empty AMC request behavior, empty AMC retry behavior, and adjacent client/user/auth/request utility behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Tests or downstream code may have used arbitrary duck-typed client sentinels when building direct `Site` rows. Mitigation: `Site` is the central parent object for request, user, member, application, forum, page, and recent-change workflows; using a real `Client` object keeps the same invariant already enforced by direct lookup/auth/request helpers and adjacent user/message constructors.
- Risk: Empty AMC batch tests could regress by requiring initialized network state. Mitigation: the tests now use a valid `Client` subclass created via `object.__new__` with an `amc_client` property that raises if read, preserving the short-circuit proof.
- Risk: Sharing the lookup-client helper could alter `Site.from_unix_name(...)` diagnostics. Mitigation: the lookup helper delegates to the new shared validator and adjacent site lookup tests remain green.

## Dependencies

- Existing `Client` class identity remains the parent-client contract.
- Existing site metadata, lookup, accessor, AMC request, auth, user, and request utility validators remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable state preflights, or complexity candidates outside this now-covered `Site(client=...)` constructor boundary.

## Upstream-Safe Motivation

`Site` is the root record for page, forum, member, application, recent-change, lookup, and AMC request workflows. Constructor-side client validation keeps malformed local fixtures, serialized records, or rehydrated site objects from carrying arbitrary parent objects into accessors and downstream requests, while preserving valid direct construction, lookup behavior, empty-batch shortcuts, and existing metadata validation.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work repeatedly used `Site` as the parent for page/source collection, forum traversal, membership administration, pending application processing, recent changes, browser-free publishing, and AMC request retries.
- Existing local drafts covered direct site metadata validation, blank and non-negative routing/ID invariants, direct site lookup client validation, lookup config validation, URL-time metadata validation, accessor parent-site validation, and many child-record parent-site validations, but did not validate the direct `Site.client` field.
- The focused RED failure showed malformed direct clients could be stored while accessors were initialized. The GREEN regressions cover malformed client rejection, metadata preservation, empty AMC batch compatibility under valid `Client` sentinels, adjacent site/client/user/auth/request behavior, and full unit compatibility.
- This slice only validates direct `Site(client=...)` constructor state. It does not change site lookup HTTP behavior, AMC retry logic, metadata parsing, page/forum/member/application behavior, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private site data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The test fixture update is intentional: empty AMC batches should still prove they do not read `amc_client`, but they should do so with a valid `Client` parent because direct `Site` records now reject arbitrary duck-typed client placeholders.
