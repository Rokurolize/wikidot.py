# PR Draft: Validate Site ID Script Shape

## Summary

`Site.from_unix_name(...)` bootstraps a `Site` from a Wikidot landing page by parsing generated metadata such as `WIKIREQUEST.info.siteId = 123;`. Earlier local slices made present non-numeric `siteId` assignments value-aware and made direct `Site.id` construction reject negative integers. One narrow parser-boundary gap remained: signed generated values still passed through `int(...)`, so `WIKIREQUEST.info.siteId = -1;` leaked the direct constructor's `ValueError`, while `WIKIREQUEST.info.siteId = +123;` was normalized into a valid site ID.

This change requires generated `siteId` values to match ASCII digits before integer conversion. Present signed values now raise the same contextual `NoElementException` as other malformed generated values, including the requested site host, `field=site_id`, and observed value. Truly absent `siteId` metadata remains the existing missing-site-ID `UnexpectedException`, and valid unsigned numeric site bootstrap remains unchanged.

## Outcome

Generated site bootstrap metadata now has one parser boundary for malformed present values: unsigned digit-only values are accepted, and signed or otherwise malformed values fail with observed-value context before `Site(...)` construction.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who create `Site` objects by UNIX name for browser-free site inspection, indexing, migration, moderation, publishing-adjacent workflows, or generated audits that depend on stable site identity.

## Current Evidence

Local rollout-backed drafts repeatedly identify site bootstrap and site identity as shared infrastructure. [310-pr-site-id-context.md](310-pr-site-id-context.md) made present malformed `siteId` assignments value-aware instead of reporting them as missing. [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md) validates direct constructor metadata types. [645-pr-validate-non-negative-site-ids.md](645-pr-validate-non-negative-site-ids.md) rejects direct negative `Site.id` values and direct negative QuickModule `site_id` arguments.

Those prior slices are not duplicates. Issue 310 established contextual diagnostics for generated `siteId` assignments but still converted signed values with `int(...)`. Issue 645 rejects negative direct IDs after construction input reaches the direct validation boundary; it does not keep malformed generated script values at the site bootstrap parser boundary, and it does not reject plus-prefixed generated values.

No upstream issue was filed from this local workspace.

## Related Issues

Builds on [310-pr-site-id-context.md](310-pr-site-id-context.md), [480-pr-validate-site-constructor-metadata.md](480-pr-validate-site-constructor-metadata.md), and [645-pr-validate-non-negative-site-ids.md](645-pr-validate-non-negative-site-ids.md).

## Changes

- Require captured `WIKIREQUEST.info.siteId` values to match `[0-9]+` before `int(...)`.
- Raise `NoElementException("Site ID is malformed for site: <site>.wikidot.com (field=site_id, value=<value>)")` for present signed generated values such as `-1` and `+123`.
- Preserve `UnexpectedException("Cannot find site id: <site>.wikidot.com")` for responses with no `siteId` assignment.
- Preserve valid unsigned numeric site bootstrap, redirect handling, 404 handling, SSL detection, title parsing, site unix-name parsing, and domain parsing.
- Add focused public `Site.from_unix_name(...)` regression coverage for signed generated `siteId` values.

## Type Of Change

- Bug fix
- Parser-shape validation
- Site bootstrap diagnostics
- Regression test

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | A landing-page response with `WIKIREQUEST.info.siteId = -1;` must fail at the `Site.from_unix_name(...)` parser boundary with `NoElementException` and observed value context. |
| R2 | A landing-page response with `WIKIREQUEST.info.siteId = +123;` must fail at the same parser boundary instead of normalizing to `123`. |
| R3 | Valid unsigned numeric `siteId` assignments must continue to construct `Site.id` from the parsed integer. |
| R4 | Responses without any `siteId` assignment must keep the existing missing-site-ID `UnexpectedException`. |
| R5 | Existing non-numeric generated `siteId` diagnostics must remain compatible. |
| R6 | Direct `Site.id` validation and direct QuickModule `site_id` validation remain unchanged. |
| R7 | Site bootstrap, direct constructor, QuickModule, client, and request utility adjacent tests must remain green. |
| R8 | Diagnostics, docs, and tests must not require live Wikidot actions, credentials, cookies, auth JSON, private site/user data, raw rollout paths, pushes, upstream Issues, or upstream PRs. |
| R9 | Focused RED/GREEN, site bootstrap tests, adjacent tests, full unit tests, lint, format, type, pyright, and whitespace gates must pass before claiming this local implementation complete. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | `-1` raises `NoElementException` with `bad-site.wikidot.com`, `field=site_id`, and `value=-1`. | Focused RED failed because the current parser leaked `ValueError("id must be non-negative")`; focused GREEN passed after digit-only validation. | Letting the constructor error escape, losing host/field/value context, fabricating an ID, or returning a `Site` rejects this local completion claim. | Site bootstrap parser | `src/wikidot/module/site.py`, `tests/unit/test_site.py` |
| R2 | `+123` raises `NoElementException` with `value=+123`. | Focused RED failed because the current parser returned a `Site`; focused GREEN passed after digit-only validation. | Normalizing the plus-prefixed payload to `123`, treating it as missing metadata, or accepting leading digits rejects this local completion claim. | Site bootstrap parser | `tests/unit/test_site.py` |
| R3 | Valid unsigned site IDs still bootstrap normally. | `TestSiteFromUnixName` and full `test_site.py` remained green in adjacent verification. | Regressing SSL/non-SSL bootstrap, redirects, title/unix-name/domain parsing, or valid site IDs rejects this local completion claim. | Site bootstrap workflow | site tests |
| R4 | Missing generated metadata still uses the existing missing-site-ID branch. | Existing `test_from_unix_name_missing_site_id` remained green. | Reclassifying absent metadata as malformed would blur missing and malformed branches and rejects this local completion claim. | Missing-field branch | `tests/unit/test_site.py` |
| R5 | Existing non-numeric `latest` diagnostics remain compatible. | Existing `test_from_unix_name_malformed_site_id_includes_raw_value_context` remained green. | Changing the exception type or losing the observed non-numeric value rejects this local completion claim. | Malformed generated-value branch | `tests/unit/test_site.py` |
| R6 | Direct ID validators remain the direct boundary for direct inputs. | Adjacent `test_site_constructor.py` and `test_quick_module.py` remained green. | Weakening direct negative-ID validation, changing direct type errors, or routing generated malformed values through direct validators rejects this local completion claim. | Direct validation boundaries | constructor and QuickModule tests |
| R7 | Adjacent site/client/request workflows remain compatible. | Site/client/request-adjacent tests passed 727 tests, and full unit passed 3702 tests. | Regressing site accessors, client accessors, request utility behavior, or QuickModule behavior rejects this local completion claim. | Adjacent workflows | affected unit suites |
| R8 | No live site state or private material is needed. | All regressions use synthetic response text and mocked HTTP responses. | Using credentials, cookies, auth JSON, raw private payloads, raw rollout paths, sandbox details, pushes, upstream Issues, upstream PRs, live Wikidot actions, private user content, or private site data rejects this local completion claim. | Test and draft privacy | this draft |
| R9 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN, bootstrap tests, adjacent tests, full unit, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, pyright, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |

## Testing

Implemented locally in commit `f3551fe fix(site): validate generated site id shape`.

- RED: `uv run --extra test pytest tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_signed_site_id_includes_raw_value_context -q` failed before the fix because `-1` leaked `ValueError("id must be non-negative")` and `+123` did not raise.
- GREEN focused: `uv run --extra test pytest tests/unit/test_site.py::TestSiteFromUnixName::test_from_unix_name_signed_site_id_includes_raw_value_context -q` passed 2 tests.
- `uv run --extra test pytest tests/unit/test_site.py::TestSiteFromUnixName -q` passed 24 tests.
- `uv run --extra test pytest tests/unit/test_site.py tests/unit/test_site_constructor.py tests/unit/test_quick_module.py tests/unit/test_client.py tests/unit/test_client_accessors.py tests/unit/test_requestutil.py -q` passed 727 tests.
- `uv run --extra test pytest tests/unit -q` passed 3702 tests.
- `uv run ruff check .` passed.
- `uv run ruff format --check .` passed with 87 files already formatted.
- `uv run mypy . --install-types --non-interactive` passed with no issues in 87 source files, plus existing annotation notes.
- `uv run pyright` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- A landing-page response containing `WIKIREQUEST.info.siteId = -1;` raises `NoElementException("Site ID is malformed for site: bad-site.wikidot.com (field=site_id, value=-1)")`.
- A landing-page response containing `WIKIREQUEST.info.siteId = +123;` raises `NoElementException("Site ID is malformed for site: bad-site.wikidot.com (field=site_id, value=+123)")`.
- A landing-page response containing `WIKIREQUEST.info.siteId = 123;` still constructs `Site.id == 123`.
- A landing-page response with no `WIKIREQUEST.info.siteId` assignment still raises the existing missing-site-ID `UnexpectedException`.
- Existing non-numeric generated `siteId` diagnostics remain value-aware.
- Direct negative `Site.id` and direct negative QuickModule `site_id` validation remain unchanged.
- No live Wikidot action, credential, cookie, auth JSON, upstream Issue, upstream PR, or push is required for this local draft.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread HTML report and complexity memo are refreshed after the docs commit.
- Secret and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with Issue 310. Mitigation: Issue 310 made present generated values value-aware; this slice specifically closes signed generated values that `int(...)` still accepted or forwarded.
- Risk: This could be confused with Issue 645. Mitigation: Issue 645 covers direct negative IDs; this slice keeps generated parser-shape failures at `Site.from_unix_name(...)` before direct construction.
- Risk: Reclassifying absent site metadata as malformed could break missing-field behavior. Mitigation: the new check only runs after a `siteId` assignment is captured, and the existing missing-site-ID test remained green.
- Risk: Tightening parsing could affect valid bootstrap. Mitigation: valid generated IDs are unsigned decimal values, and site bootstrap plus adjacent tests remained green.

## Dependencies

- Wikidot landing pages continue to expose site bootstrap metadata through `WIKIREQUEST.info.siteId = <id>;`.
- `Site.from_unix_name(...)` remains the source of truth for constructing a `Site` from a UNIX site name.
- Direct `Site.id` and QuickModule `site_id` validation remain responsible for direct caller-provided values.

## Open Questions

None for this local slice. Other generated script scalar parsers should be selected only with a concrete non-duplicate parser boundary and RED test.

## Upstream-Safe Motivation

Site bootstrap is the entry point for many browser-free workflows. A generated `siteId` scalar with a sign is not the same shape as Wikidot's unsigned script metadata and should be reported as a malformed generated value with host-local context, not accepted by Python integer normalization or leaked through direct constructor validation.

## Local Evidence, Not For Upstream Paste

- The focused RED test demonstrated the two prior behaviors: `-1` escaped as a direct constructor range error, while `+123` was accepted as a valid site ID.
- Existing local drafts prove site bootstrap and site identity are shared infrastructure, but did not enforce unsigned digit-only generated `siteId` shape.
- This slice does not change live request behavior, direct site construction policy, QuickModule request validation, site accessor behavior, upstream filing state, or any credential-bearing path.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, private access material, generated markup from real private sites, real user names, and private page content out of upstream discussion.
