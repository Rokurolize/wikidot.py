# PR Draft: Validate Commit Tags State Before Direct Tag Saves

## Summary

`Page.commit_tags()` saves the current mutable `Page.tags` field through the direct `saveTags` action. Direct `Page(tags=...)` construction already validates initial tag state, `SearchPagesQuery` and required-tag iterators already validate query/filter tag inputs, and explicit metadata write arguments already validate `Page.set_metadata(tags=...)` and `Site.page.publish(tags=...)`. The direct `commit_tags()` path still trusted the current `page.tags` value at save time. If caller code or a rehydrated fixture mutated `page.tags` after construction, `commit_tags()` could leak raw join errors, serialize a string as character-separated tags, or advance into login and AMC response handling before any stable tag diagnostic.

This change validates the current `Page.tags` state in `commit_tags()` before login checks or AMC request construction. Non-list values now raise `ValueError("tags must be a list")`, non-string list entries raise `ValueError("tags list entries must be strings")`, and valid `list[str]` tag saves still serialize exactly as before.

## Outcome

Direct tag saves now fail at the local tag-state boundary when `Page.tags` has been corrupted, instead of making login/request progress or surfacing incidental Python errors.

## Audience / Operators

This draft is for wikidot.py maintainers and downstream operators who use direct page tag saves, browser-free metadata cleanup, generated migration fixtures, local page ledgers, rehydrated `Page` objects, and scripts that mutate `page.tags` before committing it.

## Current Evidence

Local rollout-backed drafts establish direct tag writes and browser-free metadata/publish flows as practical surfaces. [012-pr-batch-page-metadata-updates.md](012-pr-batch-page-metadata-updates.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), [245-pr-page-metadata-action-status-context.md](245-pr-page-metadata-action-status-context.md), [246-pr-page-direct-metadata-action-status-context.md](246-pr-page-direct-metadata-action-status-context.md), [249-pr-page-metas-setter-action-status-context.md](249-pr-page-metas-setter-action-status-context.md), [342-pr-validate-tag-list-inputs.md](342-pr-validate-tag-list-inputs.md), [485-pr-validate-page-constructor-tags.md](485-pr-validate-page-constructor-tags.md), [530-pr-validate-tag-container-inputs.md](530-pr-validate-tag-container-inputs.md), and [531-pr-validate-metadata-tag-inputs.md](531-pr-validate-metadata-tag-inputs.md) cover metadata batching, direct metadata action status validation, query tag entries, constructor tag state, ListPages tag containers, and explicit metadata tag write arguments.

Those prior slices are not duplicates. Issue 485 validates the initial `Page(tags=...)` constructor value. Issue 531 validates explicit `tags` arguments passed into `Page.set_metadata(...)` and `Site.page.publish(...)`. Issue 342 and Issue 530 validate query and iterator tag inputs. Issue 246 validates the direct `commit_tags()` response status after an AMC request returns. None validates the mutable `Page.tags` state immediately before `Page.commit_tags()` serializes and sends it. No upstream issue was filed from this local workspace.

## Changes

- Validate `Page.commit_tags()` current `self.tags` state before login checks or AMC request construction.
- Reject non-list tag state with `ValueError("tags must be a list")`.
- Reject non-string tag entries with `ValueError("tags list entries must be strings")`.
- Serialize the validated local tag list for the `saveTags` request.
- Preserve valid direct tag saves, empty-list tag clearing, response-status validation, method chaining, local tag state, metadata batching, and adjacent publish behavior.

## Type Of Change

- Input/state validation
- Direct metadata write preflight hardening
- Test addition

## Requirements

| ID | Requirement |
| --- | --- |
| R1 | `Page.commit_tags()` must reject non-list current `Page.tags` values with `ValueError("tags must be a list")` before login checks or AMC requests. |
| R2 | `Page.commit_tags()` must reject non-string current tag entries with `ValueError("tags list entries must be strings")` before login checks or AMC requests. |
| R3 | Valid `list[str]` tag state and empty-list tag clearing must keep the existing request payload, response-status validation, and method-chaining behavior. |
| R4 | This slice must not change direct `Page(tags=...)` constructor validation, query tag validation, required-tag filtering, explicit `set_metadata(tags=...)` validation, publish validation, response-status validation, tag syntax, tag normalization, live Wikidot behavior, or response parsing. |
| R5 | Focused RED/GREEN, page write tests, adjacent page/site/search tests, full unit tests, lint, format, mypy, pyright, and whitespace gates must pass before claiming this local implementation complete. |
| R6 | The draft and tests must not require live Wikidot actions, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs. |

## Traceability

| Req | Acceptance | Verification | Negative Control | Owner / Surface | Evidence Path |
| --- | --- | --- | --- | --- | --- |
| R1 | Non-list mutable `Page.tags` state fails locally before direct tag save side effects. | `test_commit_tags_rejects_invalid_tags_before_request` failed RED for integer, string, and tuple values; integer leaked raw join `TypeError`, while string and tuple values reached AMC response handling. It passed GREEN after validation was added. | Calling login, calling AMC, accepting strings/tuples, serializing strings character-by-character, or coercing containers rejects this local completion claim. | Direct tag save preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R2 | Mixed mutable tag lists fail with the same stable tag-entry diagnostic used by other page tag boundaries. | The same focused test failed RED for `["tag-one", 3]` with raw join `TypeError`, then passed GREEN with `ValueError("tags list entries must be strings")`. | Stringifying entries, dropping entries, calling login, calling AMC, or allowing raw join errors rejects this local completion claim. | Direct tag save preflight | `src/wikidot/module/page.py`, `tests/unit/test_page.py` |
| R3 | Existing valid direct tag save behavior remains green. | `TestPageWriteMethods` passed 53 tests, including direct tag save success and missing-status response diagnostics. | Regressing request bodies, empty-list handling, response-status validation, method chaining, or successful local behavior rejects this local completion claim. | Direct page write methods | `tests/unit/test_page.py` |
| R4 | Adjacent tag and publish surfaces remain unchanged. | Adjacent page constructor/create/edit/property, site publish, and search query suites passed 360 tests. | Changing constructor tag validation, query tag validation, required-tag filtering, explicit metadata tag arguments, publish behavior, or response parsing rejects this local completion claim. | Adjacent page/site/search workflows | `tests/unit/test_page.py`, `tests/unit/test_page_constructor.py`, `tests/unit/test_site.py`, `tests/unit/test_search_pages_query.py` |
| R5 | Repository quality gates pass in the local dependency environment. | Focused RED/GREEN passed, affected and adjacent tests passed, full unit passed, ruff, format, mypy, pyright, and whitespace checks passed. | Test, lint, format, type, whitespace, or unreported tooling failures reject this local completion claim. | Repo quality gates | Verification commands below |
| R6 | No private material or live action is needed to prove the behavior. | All regressions use synthetic unit-level values and local mocks; the draft contains no raw credentials, cookies, auth JSON, response bodies, private content, or live site data. | Using real account names, credentials, cookies, auth JSON, sandbox details, raw response bodies, pushes, upstream Issues, upstream PRs, live Wikidot actions, or private content rejects this local completion claim. | Test and draft privacy | this draft |

## Testing

Implemented locally in commit `189b0d3 fix(page): validate committed tag state`.

- RED direct commit-tags tests: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_invalid_tags_before_request -q` failed 4 cases before the fix. `page.tags = 3` raised raw `TypeError: can only join an iterable`; `page.tags = "tag-one tag-two"` and `page.tags = ("tag-one",)` advanced into AMC response handling and raised `WikidotStatusCodeException`; `page.tags = ["tag-one", 3]` raised raw `TypeError: sequence item 1: expected str instance, int found`.
- GREEN focused direct commit-tags tests: `uv run pytest tests/unit/test_page.py::TestPageWriteMethods::test_commit_tags_rejects_invalid_tags_before_request -q` passed 4 tests.
- `uv run pytest tests/unit/test_page.py::TestPageWriteMethods -q` passed 53 tests.
- `uv run pytest tests/unit/test_page.py::TestPageProperties tests/unit/test_page.py::TestPageCreateOrEdit tests/unit/test_page.py::TestPageEdit tests/unit/test_page_constructor.py tests/unit/test_site.py::TestSitePageAccessor tests/unit/test_search_pages_query.py -q` passed 360 tests.
- `uv run pytest tests/unit -q` passed 2524 tests.
- `uv run ruff check` passed.
- `uv run ruff format --check src tests` passed with 87 files already formatted.
- `uv run mypy src tests` passed with no issues in 87 source files.
- `uv run pyright src tests` passed with 0 errors, 0 warnings, and 0 informations.
- `git diff --check` passed.

## Acceptance Criteria

- `page.tags = 3`, then `page.commit_tags()`, raises `ValueError("tags must be a list")` before login checks or AMC requests.
- `page.tags = "tag-one tag-two"` and `page.tags = ("tag-one",)`, then `page.commit_tags()`, raise `ValueError("tags must be a list")` before login checks or AMC requests.
- `page.tags = ["tag-one", 3]`, then `page.commit_tags()`, raises `ValueError("tags list entries must be strings")` before login checks or AMC requests.
- Valid `page.tags = ["tag-one", "tag-two"]` still serializes to `tags: "tag-one tag-two"` and validates the returned `saveTags` status.
- Valid empty tag lists still clear tags through the existing direct request shape.
- Existing constructor tag validation, query tag validation, required-tag filtering, explicit metadata tag argument validation, publish behavior, metadata response-status validation, and static gates remain green.
- The new tests use synthetic values only and do not require live Wikidot, credentials, cookies, auth JSON, raw rollout paths, private site data, pushes, upstream Issues, or upstream PRs.

## Definition Of Done

- Code and tests are committed locally.
- The local issue draft documents behavior, scope, verification, acceptance criteria, and false-positive rejection checks.
- `Issues/README.md` indexes the draft and local implementation commit.
- The thread progress report and complexity memo are refreshed after the docs commit.
- Private-data and local-path leak checks over the new draft pass before finalizing the turn.

## Risks And Mitigations

- Risk: This could be confused with direct constructor tag validation. Mitigation: the constructor guard only runs at object creation; this slice protects the mutable field at direct save time.
- Risk: This could be confused with explicit metadata tag argument validation. Mitigation: `set_metadata(tags=...)` and `publish(tags=...)` validate caller arguments; this slice validates `Page.commit_tags()` current object state.
- Risk: Rejecting string or tuple tag state could affect callers relying on accidental iterable behavior. Mitigation: `Page.tags` is a stored tag list, and direct string joining can silently build character-separated tag payloads.
- Risk: Adding tag syntax validation could overreach. Mitigation: this slice only validates container and entry type, preserving existing tag content, ordering, and remote semantics.

## Out Of Scope

Changing tag syntax, parsing tag strings, accepting tuple/dict/set aliases, changing tag normalization, changing direct constructor validation, changing query tag validation, changing required-tag filtering, changing explicit `set_metadata(tags=...)` or publish tag validation, changing metadata response-status validation, changing live Wikidot behavior, changing response parsing, and upstream Issue/PR creation are outside this slice.

## Why This Matters

`Page.commit_tags()` is the low-level direct tag save primitive. If local state is corrupted by generated fixtures, JSON/YAML rehydration, or script mutation, wikidot.py should fail before login and request work rather than sending malformed tags or surfacing incidental Python errors.

## Rollout-Backed Notes

- Local rollout-backed work repeatedly used direct and batched metadata/tag writes for browser-free publishing and cleanup workflows.
- Existing drafts covered direct metadata action status, constructor tag state, query tag validation, required-tag filtering, explicit metadata tag arguments, and publish behavior, but did not validate mutable `Page.tags` state at the direct `commit_tags()` boundary.
- The focused RED failures showed malformed current tag state either leaking raw join errors or advancing into AMC response handling before tag diagnostics. The GREEN regression covers the direct save boundary before login or request construction can run.
- Keep private rollout paths, local account names, sandbox details, raw command transcripts, usernames, passwords, session-cookie values, credentials, cookies, auth JSON, raw HTTP bodies, private content, private site data, and source text from real sites out of upstream discussion.
