# PR Draft: Validate SiteApplication Constructor User ID State

## Summary

`SiteApplication(...)` records already validate the parent site, applicant object type, applicant/site client coherence, application text type, constructor negative applicant ID range, accept/decline action-user ID type, action-user name type, action-user ID range, returned action status, `no_application` mappings, and accept-cache invalidation behavior. One constructor retained-state gap remained: a valid applicant `User` could be mutated, fixture-loaded, or rehydrated with malformed retained `user.id` state and then stored in a new `SiteApplication` row.

This change validates retained applicant user ID shape at the `SiteApplication(...)` constructor boundary. Malformed non-`None` retained applicant IDs now raise `ValueError("application.user.id must be an integer or None")`, negative retained applicant IDs continue to raise `ValueError("application.user.id must be non-negative")`, and valid optional `None` plus zero-ID compatibility remain accepted at construction time.

## Outcome

Direct `SiteApplication(...)` rows cannot store malformed retained applicant user IDs. Valid parser-created rows, same-client direct rows, missing applicant IDs, zero-ID compatibility, malformed site/user/text diagnostics, applicant/site client coherence, accept/decline action preflights, action-status diagnostics, `no_application` mapping, cache behavior, and adjacent site/member/user/private-message workflows remain unchanged.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use browser-free pending-application inventories, generated membership ledgers, local fixtures, serialized application rows, migration checks, moderation workflows, or rehydrated `SiteApplication` objects before processing pending applications.

## Current Evidence

Site-application drafts [053-pr-decline-application-status-text.md](053-pr-decline-application-status-text.md), [079-pr-reuse-application-response-body.md](079-pr-reuse-application-response-body.md), [090-pr-ignore-nested-application-body-markup.md](090-pr-ignore-nested-application-body-markup.md), [113-pr-preserve-site-application-text-spacing.md](113-pr-preserve-site-application-text-spacing.md), [155-pr-site-application-mismatch-context.md](155-pr-site-application-mismatch-context.md), [156-pr-site-application-text-parse-context.md](156-pr-site-application-text-parse-context.md), [177-pr-site-application-fetch-failure-context.md](177-pr-site-application-fetch-failure-context.md), [212-pr-site-application-list-response-body-context.md](212-pr-site-application-list-response-body-context.md), [256-pr-site-application-process-action-status-context.md](256-pr-site-application-process-action-status-context.md), [271-pr-site-application-accept-member-cache-invalidation.md](271-pr-site-application-accept-member-cache-invalidation.md), [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md), and [689-pr-validate-site-application-constructor-user-id-range.md](689-pr-validate-site-application-constructor-user-id-range.md) establish application acquisition, parser diagnostics, constructor field validation, applicant/site coherence, accept/decline behavior, action-user preflight, constructor range validation, and cache synchronization as practical workflow surfaces.

Related retained user-ID drafts [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md), [692-pr-validate-private-message-constructor-user-id-state.md](692-pr-validate-private-message-constructor-user-id-state.md), [693-pr-validate-site-change-actor-user-id-state.md](693-pr-validate-site-change-actor-user-id-state.md), [694-pr-validate-page-revision-creator-user-id-state.md](694-pr-validate-page-revision-creator-user-id-state.md), [695-pr-validate-forum-thread-creator-user-id-state.md](695-pr-validate-forum-thread-creator-user-id-state.md), [696-pr-validate-forum-post-actor-user-id-state.md](696-pr-validate-forum-post-actor-user-id-state.md), [697-pr-validate-forum-post-revision-creator-user-id-state.md](697-pr-validate-forum-post-revision-creator-user-id-state.md), and [698-pr-validate-page-metadata-user-id-state.md](698-pr-validate-page-metadata-user-id-state.md) establish direct user-ID validation and adjacent retained mutable user-state validation as active operational boundaries.

This slice is not a duplicate of those drafts. Issue 449 validates that `SiteApplication.user` is an `AbstractUser`, but it does not validate retained applicant ID shape. Issue 606 validates that the applicant belongs to the parent site client, not the retained ID shape or range. Issue 687 validates malformed and negative retained `application.user.id` at the accept/decline action boundary, but a direct `SiteApplication(...)` row could still store corrupted applicant ID state until action time. Issue 689 validates negative retained applicant IDs at construction time, but it did not reject malformed non-`None` retained applicant IDs such as booleans, numeric strings, floats, or lists. Issue 647 validates direct `User` and `DeletedUser` construction, but it cannot cover a valid user object whose public `id` is corrupted after construction and then stored in an application row.

## Related Issue / Non-Duplicate Analysis

Builds directly on [371-pr-validate-site-application-user-input.md](371-pr-validate-site-application-user-input.md), [449-pr-validate-site-application-user-field.md](449-pr-validate-site-application-user-field.md), [500-pr-validate-site-application-site-field.md](500-pr-validate-site-application-site-field.md), [606-pr-validate-site-application-user-client.md](606-pr-validate-site-application-user-client.md), [647-pr-validate-non-negative-user-ids.md](647-pr-validate-non-negative-user-ids.md), [687-pr-validate-site-application-user-id-range.md](687-pr-validate-site-application-user-id-range.md), [689-pr-validate-site-application-constructor-user-id-range.md](689-pr-validate-site-application-constructor-user-id-range.md), and adjacent retained user-ID state drafts [691-pr-validate-page-vote-constructor-user-id-state.md](691-pr-validate-page-vote-constructor-user-id-state.md) through [698-pr-validate-page-metadata-user-id-state.md](698-pr-validate-page-metadata-user-id-state.md).

No upstream issue was filed from this local workspace.

## Changes

- Validate retained `application.user.id` shape inside the existing `SiteApplication` user object validator used by `__post_init__`.
- Reject retained constructor applicant IDs `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("application.user.id must be an integer or None")`.
- Preserve retained constructor applicant IDs `None` and `0`.
- Preserve the existing negative retained applicant ID diagnostic `ValueError("application.user.id must be non-negative")`.
- Keep action-time malformed ID type and malformed name validation in the existing accept/decline helper.
- Preserve existing site validation, applicant object validation, applicant/site client validation, text validation, action-status diagnostics, `no_application` handling, cache behavior, and successful application behavior.

## Type Of Change

- State validation
- Site application constructor hardening
- Retained user identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteApplication(site=site, user=user, text=...)` must reject retained applicant `user.id` values `True`, `False`, `"12345"`, `12345.0`, and `[]` with `ValueError("application.user.id must be an integer or None")` before storing the application row. |
| R2 | Valid retained applicant IDs `None` and `0` must remain accepted in direct `SiteApplication(...)` construction. |
| R3 | Existing constructor negative-ID validation must continue to reject retained applicant IDs `-1` and `-100` with `ValueError("application.user.id must be non-negative")`. |
| R4 | Existing action-time malformed-ID, missing-ID, malformed-name, and post-construction mutation preflights must continue to reject before login or AMC request work. |
| R5 | Existing malformed site validation, non-`AbstractUser` applicant validation, applicant/site client validation, text validation, action-status diagnostics, `no_application` mapping, cache behavior, and adjacent site/member/application/user/private-message workflows must remain unchanged. |
| R6 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private applicant data, private application text, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R7 | Focused RED/GREEN, site-application tests, adjacent site/member/application/user/private-message tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Malformed retained applicant IDs fail at the direct constructor boundary. | `test_init_rejects_malformed_retained_user_id` failed RED for five malformed retained-ID cases with `DID NOT RAISE`, then passed GREEN after constructor user-ID state validation was added. | Accepting booleans, numeric strings, floats, lists, coercing values, or deferring failure only to `accept()` / `decline()` rejects this local completion claim. | `SiteApplication` constructor | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R2 | Optional missing and zero applicant IDs remain compatible constructor state. | `test_init_accepts_optional_retained_user_id` passed RED and GREEN for `None` and `0`, asserting the stored value is preserved. | Rejecting `None`, rejecting `0`, coercing either value, or requiring a concrete regular-user ID rejects this local completion claim. | `SiteApplication` constructor | `tests/unit/test_site_application.py` |
| R3 | Negative retained applicant IDs still fail at the direct constructor boundary. | Existing `test_init_rejects_negative_user_id` passed after the new validator preserved the prior negative-ID diagnostic and behavior. | Accepting negative retained applicant IDs, storing the row, or changing the existing negative diagnostic rejects this local completion claim. | `SiteApplication` constructor | `src/wikidot/module/site_application.py`, `tests/unit/test_site_application.py` |
| R4 | Action-time preflights still defend post-construction mutation before side effects. | `test_accept_rejects_malformed_user_before_login` now constructs a valid row, mutates the retained user state, and passes by rejecting before `login_check()` or AMC request work. Existing negative-ID action-time tests also remain green. | Losing action-time mutation coverage, calling `login_check()`, sending `ManageSiteMembershipAction`, or raising returned-status diagnostics rejects this local completion claim. | `SiteApplication.accept()` / `decline()` | `tests/unit/test_site_application.py` |
| R5 | Existing site-application behavior and adjacent workflows remain green. | `tests/unit/test_site_application.py` passed 68 tests, adjacent site/member/application/user/private-message coverage passed 768 tests, and full unit coverage passed 3517 tests. | Regressing parser-created applications, constructor site/user/text diagnostics, client coherence, action preflights, action-status handling, cache behavior, site/member/user/private-message workflows, or any unit test rejects this local completion claim. | Site application and adjacent workflows | `tests/unit` |
| R6 | No live site state or private material is needed to prove the behavior. | All regressions use unit-level tests only with synthetic sites, applicants, and safe application text. | Using credentials, cookies, auth JSON, private applicant names, private application text, raw rollout paths, live Wikidot actions, pushes, upstream Issues, or upstream PRs rejects this local completion claim. | Test and draft privacy | this draft |
| R7 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, site-application/adjacent/full-unit tests, ruff, format check, mypy, temporary pyright, and `git diff --check` passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `50c2c50 fix(site_application): validate constructor user id state`.

- RED: `uv run pytest tests/unit/test_site_application.py::TestSiteApplicationDataclass -k retained_user_id -q` selected 7 constructor retained-user-ID tests; 5 malformed retained-ID cases failed before the fix with `DID NOT RAISE`, while the 2 `None` and zero-ID compatibility guards passed.
- GREEN: the same focused command passed 7 tests after constructor retained-ID validation was added.
- `uv run ruff format src/wikidot/module/site_application.py tests/unit/test_site_application.py` left both files unchanged.
- `uv run pytest tests/unit/test_site_application.py -q` passed 68 tests.
- `uv run pytest tests/unit/test_site.py tests/unit/test_site_member.py tests/unit/test_site_application.py tests/unit/test_user.py tests/unit/test_private_message.py -q` passed 768 tests.
- `uv run pytest tests/unit -q` passed 3517 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `git diff --check` passed.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run --with pyright pyright` passed with 0 errors, 0 warnings, and 0 informations.

## Acceptance Criteria

- `SiteApplication(...)` raises `ValueError("application.user.id must be an integer or None")` when the applicant user's retained `id` is `True`, `False`, `"12345"`, `12345.0`, or `[]`.
- Malformed non-`None` retained applicant IDs fail before the application row is stored by direct construction.
- Valid retained applicant IDs `None` and `0` remain accepted by direct construction.
- Existing negative retained applicant IDs still raise `ValueError("application.user.id must be non-negative")` by direct construction.
- Existing action-time accept/decline malformed-ID, missing-ID, malformed-name, and negative-ID tests still prove post-construction mutation fails before `site.client.login_check()`, `site.amc_request(...)`, returned action-status parsing, `no_application` mapping, or member-cache mutation.
- Existing malformed site validation, non-`AbstractUser` applicant validation, applicant/site client ownership validation, text validation, valid accept/decline actions, returned application action-status validation, `no_application` mapping, accept cache invalidation, decline cache preservation, site member workflows, site invitation workflows, user behavior, and private-message send behavior remain green.
- The new tests use unit-level code only and do not require live Wikidot, credentials, cookies, auth JSON, private applicant data, private application text, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: Directly constructed application rows with corrupted retained applicant IDs now fail during construction instead of later accept/decline work. Mitigation: those values are impossible user identity state; failing before storage is deterministic and keeps application rows coherent.
- Risk: Optional applicant IDs could be rejected accidentally. Mitigation: focused compatibility guards assert that `None` and `0` remain accepted and preserved at construction time.
- Risk: The constructor fix could erase action-time mutation coverage. Mitigation: the accept malformed-user test now constructs a valid row first and mutates the retained user afterward, proving the action helper still rejects before login and AMC request work.
- Risk: Validation precedence could regress earlier application diagnostics. Mitigation: the retained-ID check runs after the existing `AbstractUser` check; stricter action payload name and concrete-ID requirements remain in the existing action helper; site-application, adjacent, and full unit suites remain green.

## Dependencies

- Existing `User` constructor validation remains unchanged.
- Existing site-application site validation, applicant object validation, applicant/site client validation, text validation, action-user concrete ID validation, action-user name validation, action-status validation, `no_application` handling, and cache behavior remain unchanged.

## Open Questions

None for this local slice. Remaining useful work should continue with fresh duplicate-checked public input boundaries, parser diagnostics, result ergonomics, action/read boundaries, retained cache/collection state, downstream mutable user-state preflights, or complexity candidates outside this now-covered `SiteApplication` constructor retained user-ID state boundary.

## Upstream-Safe Motivation

`SiteApplication` is the durable row shape behind pending-application inventories, membership ledgers, moderation workflows, and accept/decline automation. Parser-created application users can legitimately have optional IDs, while direct `User` construction already rejects malformed and negative IDs. Constructor-side validation keeps corrupted fixture-loaded or rehydrated applicant identity out of stored application rows while preserving optional missing IDs, zero-ID compatibility, valid parser-created rows, client coherence, text validation, and action-time mutation preflights.

## Local Evidence, Not For Upstream Paste

- Local rollout-backed work established site applications as a practical workflow through application-list retry, parser diagnostics, response-body diagnostics, applicant field validation, applicant/site client validation, accept/decline action-status validation, applicant action-time ID range validation, constructor negative applicant ID validation, and accept member-cache invalidation.
- Existing local drafts covered non-`AbstractUser` applicants, malformed action-time applicant ID types, missing action-time applicant IDs, malformed action-time applicant names, applicant client mismatch, direct user constructor ID ranges, site-application constructor negative applicant IDs, and adjacent retained user-ID state; they did not validate corrupted malformed non-`None` `User.id` values at the direct `SiteApplication(...)` constructor boundary.
- The focused RED failure showed malformed retained applicant IDs could be stored in direct application rows. The GREEN regressions cover constructor malformed rejection, optional-ID and zero-ID constructor compatibility, existing negative constructor rejection, action-time post-construction mutation coverage, site-application behavior, adjacent site/member/application/user/private-message workflows, and full unit compatibility.
- This slice only validates retained applicant user ID state at the `SiteApplication` constructor boundary. It does not change application-list parsing, site invitation actions, site member role changes, member lookup filters, user construction, profile lookup, live site behavior, pushes, upstream Issues, or upstream PRs.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, private application text, private applicant data, raw action responses, source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The implementation intentionally accepts `None` for retained constructor applicant IDs instead of requiring a concrete regular-user ID. The accept/decline path still owns the stricter action-payload requirement for concrete integer IDs and applicant names before membership mutation requests are built.
