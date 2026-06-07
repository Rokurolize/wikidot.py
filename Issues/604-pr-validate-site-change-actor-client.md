# PR Draft: Validate Site Change Actor Client

## Summary

`SiteChange` records returned by `Site.get_recent_changes(...)` carry both the parent `Site` and the actor in `changed_by`. Existing recent-change slices validate parser-side user extraction, direct actor type, direct timestamp type, and direct site type. One constructor coherence gap remained: direct `SiteChange(...)` construction could combine `site=site_a` with `changed_by=User(client=site_b.client, ...)`. The resulting recent-change ledger row then claimed that a site-scoped change was made by an actor bound to a different client context.

This change validates `SiteChange.changed_by.client` against `SiteChange.site.client` during `SiteChange.__post_init__` after existing field-shape checks. Mismatches raise `ValueError("changed_by must belong to the site")` before contradictory record state is stored. Valid direct `SiteChange` rows, parser-created recent-change rows, existing malformed field diagnostics, recent-change pagination, parser context, and adjacent site workflows remain unchanged.

## Outcome

Directly constructed recent-change rows cannot combine a parent site with an actor from another client context.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use `Site.get_recent_changes(...)`, direct `SiteChange(...)` construction in tests or local ledgers, recent-change audit exports, moderation dashboards, migration checks, browser-free change monitoring, multi-site reports, or generated recent-change records.

## Current Evidence

Local rollout-backed drafts repeatedly identify recent changes and direct result objects as practical workflow surfaces. Existing drafts [030-pr-retry-recent-changes-fetches.md](030-pr-retry-recent-changes-fetches.md), [072-pr-batch-recent-changes-pages.md](072-pr-batch-recent-changes-pages.md), [165-pr-recent-change-parse-context.md](165-pr-recent-change-parse-context.md), [182-pr-recent-changes-fetch-failure-context.md](182-pr-recent-changes-fetch-failure-context.md), [218-pr-recent-changes-response-body-context.md](218-pr-recent-changes-response-body-context.md), [278-pr-recent-change-title-href-context.md](278-pr-recent-change-title-href-context.md), [279-pr-recent-change-page-name-context.md](279-pr-recent-change-page-name-context.md), [280-pr-recent-change-page-title-context.md](280-pr-recent-change-page-title-context.md), [281-pr-recent-change-revision-value-context.md](281-pr-recent-change-revision-value-context.md), [282-pr-recent-change-timestamp-value-context.md](282-pr-recent-change-timestamp-value-context.md), [299-pr-recent-change-user-context.md](299-pr-recent-change-user-context.md), [336-pr-recent-changes-response-body-type-context.md](336-pr-recent-changes-response-body-type-context.md), [373-pr-validate-recent-changes-limit.md](373-pr-validate-recent-changes-limit.md), [427-pr-validate-site-change-flags.md](427-pr-validate-site-change-flags.md), [436-pr-validate-site-change-revision-numbers.md](436-pr-validate-site-change-revision-numbers.md), [437-pr-validate-site-change-text-fields.md](437-pr-validate-site-change-text-fields.md), [438-pr-validate-site-change-actor-time-fields.md](438-pr-validate-site-change-actor-time-fields.md), and [439-pr-validate-site-change-site-field.md](439-pr-validate-site-change-site-field.md) establish recent-change fetching, parser diagnostics, direct field validation, and parent-site type validation as active operational boundaries.

The parser path already constructs actors with the parent site's client by calling the shared user parser as `user_parser(site.client, user_elem)`. The new rule brings direct constructor behavior in line with that parser invariant without changing how live recent-change rows are parsed.

## Related Issue / Non-Duplicate Analysis

This is not a duplicate of Issue 438. Issue 438 validates that `changed_by` is an `AbstractUser` and that `changed_at` is a `datetime`; it intentionally accepts all valid user subclasses and does not check whether the user belongs to the same client context as the row's site.

This is not a duplicate of Issue 439. Issue 439 validates that `SiteChange.site` is a `Site` instance; it does not compare the valid site object with the valid actor object.

This is not a duplicate of Issue 299. Issue 299 validates parser-side malformed recent-change user markup before `SiteChange` construction; it does not validate direct `SiteChange(changed_by=...)` coherence.

No upstream issue was filed from this local workspace.

## Changes

- Add `SiteChange` actor-client coherence validation.
- Reject direct rows where `changed_by.client is not site.client` with `ValueError("changed_by must belong to the site")`.
- Preserve existing field-shape validation and diagnostics by running the coherence check after `flags`, `revision_no`, text fields, `comment`, `changed_by`, `changed_at`, and `site` have already been validated.
- Preserve parser-created recent-change rows, because `_parse_recent_change_user(...)` already parses users with the parent site's client.
- Preserve side-effect-free construction: the new check compares object identity only and does not perform login checks, HTTP requests, profile lookups, coercion, or site mutation.

## Type Of Change

- Input validation
- Public dataclass constructor behavior hardening
- Recent-change ledger identity integrity
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `SiteChange(site=site_a, changed_by=User(client=site_b.client, ...), ...)` must reject the mismatched actor client with `ValueError("changed_by must belong to the site")` before storing record state. |
| R2 | Valid direct `SiteChange(...)` rows where `changed_by.client is site.client` must remain valid. |
| R3 | Existing malformed `flags`, `revision_no`, page text fields, `comment`, `changed_by`, `changed_at`, and `site` diagnostics must remain unchanged. |
| R4 | Existing `Site.get_recent_changes(...)` parser workflows, retry/pagination behavior, limit validation, parser diagnostics, page/user/timestamp/revision parsing, response-body validation, and title/comment text handling must remain unchanged. |
| R5 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Actor/client mismatches fail at the public constructor boundary. | `TestSiteChangeDataclass.test_init_rejects_changed_by_from_different_client` failed RED with `DID NOT RAISE`, then passed GREEN after `SiteChange.__post_init__` called the coherence preflight. | Accepting a valid `User` object from another client context, emitting a row whose site and actor client disagree, or deferring the mismatch to later use rejects this local completion claim. | `SiteChange` constructor | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | Existing valid constructor rows stay green. | `TestSiteChangeDataclass` passed with the default same-client `User` helper, and parser-created recent-change rows stayed green. | Rejecting the default same-client user, replacing actor objects, coercing users, or requiring live authentication rejects this local completion claim. | `SiteChange` constructor and parser-created rows | `tests/unit/test_site.py` |
| R3 | Existing constructor diagnostics stay stable. | Focused recent-change constructor coverage passed 76 tests covering malformed flags, malformed flag entries, malformed site, valid flags, malformed revision numbers, malformed text fields, optional comments, malformed actor/time values, actor/client mismatch, and recent-change parser rows. | Changing existing `ValueError` diagnostics, validating coherence before malformed field checks, or accepting previously rejected malformed values rejects this local completion claim. | `SiteChange` validation order | `tests/unit/test_site.py` |
| R4 | Existing recent-change and adjacent site workflows remain green. | `tests/unit/test_site.py` passed 287 tests, and full unit coverage passed 2729 tests. | Regressing recent-change parsing, actor extraction, timestamp extraction, page fullname extraction, page-title extraction, comment extraction, revision extraction, flags extraction, retry behavior, pagination, limit validation, response-body diagnostics, or adjacent site workflows rejects this local completion claim. | Recent changes and adjacent site workflows | `tests/unit` |
| R5 | No live auth material or private site state is needed to prove the behavior. | The regressions use synthetic `Site` and `User` objects only, and this draft contains no credentials, cookies, auth JSON, raw response bodies, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw rollout paths, pushes, upstream Issues, upstream PRs, live Wikidot actions, page source text from real sites, or private site data rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `8c4b07a fix(site): validate site change actor client`.

- RED: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_changed_by_from_different_client -q` failed before the fix with `DID NOT RAISE`.
- GREEN regression: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass::test_init_rejects_changed_by_from_different_client -q` passed 1 test.
- Focused recent-change constructor and parser coverage: `uv run pytest tests/unit/test_site.py::TestSiteChangeDataclass tests/unit/test_site.py::TestSiteGetRecentChanges -q` passed 76 tests.
- Site coverage: `uv run pytest tests/unit/test_site.py -q` passed 287 tests.
- `uv run pytest tests/unit -q` passed 2729 tests.
- `uv run ruff format src/wikidot/module/site.py tests/unit/test_site.py` left 2 files unchanged.
- `uv run ruff check src/wikidot/module/site.py tests/unit/test_site.py` passed.
- `uv run ruff check` passed.
- `uv run ruff format --check` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `SiteChange(site=site_a, changed_by=User(client=site_b.client, ...), ...)` raises `ValueError("changed_by must belong to the site")`.
- Valid direct rows where `changed_by.client is site.client` remain valid.
- Existing malformed `changed_by` values still raise `ValueError("changed_by must be an AbstractUser")`.
- Existing malformed `site` values still raise `ValueError("site must be a Site")`.
- Existing `flags`, `revision_no`, page text-field, `comment`, and `changed_at` diagnostics remain unchanged.
- Existing recent-change parser rows still produce valid `SiteChange` records.
- Existing `Site.get_recent_changes(...)`, recent-change parser diagnostics, retry/pagination behavior, `limit` validation, page/user/timestamp/revision parsing, response-body validation, and title/comment text handling remain green.
- The new tests use unit-level synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, private site data, raw rollout paths, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.

## Upstream-Safe Motivation

`SiteChange` is the durable row shape behind browser-free recent-change monitoring, moderation dashboards, audit exports, migration checks, and generated multi-site reports. A recent-change row is site-scoped, and the parser already creates actors through the parent site's client. Constructor coherence validation keeps direct fixtures, rehydrated rows, and generated ledgers from mixing site and actor client contexts while preserving the normal parser path.

## Local Evidence, Not For Upstream Paste

- The focused RED failure showed direct `SiteChange(site=site_a, changed_by=User(client=site_b.client, ...), ...)` construction silently accepted a contradictory row.
- Existing local drafts covered recent-change fetch retry, pagination batching, parser diagnostics, response-body validation, parser-side user extraction, direct actor/time type validation, and direct site type validation, but did not validate coherence between a valid actor object and a valid parent site.
- This slice only validates constructor-time actor/client coherence. It does not change recent-change request construction, parser selectors, flag-code semantics, page fullname parsing, title extraction, comment extraction, revision extraction, timestamp extraction, user parser semantics, response-body validation, `limit` validation, live site behavior, authentication semantics, or request helper behavior.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw login response bodies, page source text from real sites, and private site data out of upstream discussion.

## Additional Notes

The check intentionally compares client object identity rather than site IDs, user IDs, usernames, or authentication state. The parser path and the rest of the object graph preserve client identity, and identity comparison avoids network lookups, login checks, and ambiguous cross-client equivalence rules.
