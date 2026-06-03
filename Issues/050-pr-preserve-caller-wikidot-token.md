# PR Draft: Preserve Caller Wikidot Tokens In AMC Requests

## Summary

`AjaxModuleConnectorClient.request(...)` automatically adds `wikidot_token7` to every Ajax Module Connector request body. Before this fix it always set the request-body token to the default dummy value `123456`, even when the caller supplied a different `wikidot_token7` in the body or updated the request header cookie.

Rollout evidence included public-source collection scripts that read a public Wikidot page, extracted the anonymous `wikidot_token7`, and then posted `viewsource/ViewSourceModule` through `ajax-module-connector.php`. Overwriting caller-supplied tokens makes that workflow harder to express through wikidot.py and can produce a body/header token mismatch when code deliberately updates the header cookie.

The fix keeps the existing default token behavior for normal callers, but preserves explicit caller tokens and uses the current header cookie token as the default request-body token.

## Related Issue

Complements the source-collection and browser-free workflow drafts [004-feature-large-corpus-page-source-collection.md](004-feature-large-corpus-page-source-collection.md), [014-pr-preserve-viewsource-text.md](014-pr-preserve-viewsource-text.md), [027-pr-source-result-wiki-text.md](027-pr-source-result-wiki-text.md), and [029-pr-recursive-sensitive-log-masking.md](029-pr-recursive-sensitive-log-masking.md). It targets the lower-level AMC connector token handling rather than adding a new anonymous source-fetching API. No upstream issue filed yet.

## Changes

- Build AMC request bodies with the current header cookie `wikidot_token7` as the default token.
- Preserve an explicit `wikidot_token7` supplied in a caller request body.
- Keep the existing `123456` fallback when neither the body nor header cookie supplies a token.
- Preserve the no-mutation behavior for caller request dictionaries.
- Keep sensitive-token masking unchanged.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [ ] Refactoring
- [x] Security/privacy hardening
- [x] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: Explicit caller tokens are preserved | Passing `{"wikidot_token7": 987654}` sends `wikidot_token7=987654` in the encoded AMC body | `test_request_preserves_explicit_wikidot_token` | The RED test failed before the fix because the body contained `wikidot_token7=123456` |
| R2: Header cookie tokens are used as the default body token | Setting `client.header.set_cookie("wikidot_token7", 987654)` sends both the header cookie and body field with `987654` when the request body omits the token | `test_request_uses_header_wikidot_token_by_default` | The RED test failed before the fix because the header had `987654` but the body still had `123456` |
| R3: Existing default behavior is preserved | A normal request with no explicit token still sends `wikidot_token7=123456` and does not mutate the caller dictionary | `test_request_does_not_mutate_body`; `tests/unit/test_amc_client.py` | The existing default-token assertion remains green |
| R4: Connector-wide behavior remains stable | Existing AMC request, retry, status-error, and masking tests continue to pass | `tests/unit/test_ajax.py tests/unit/test_amc_client.py`; `tests/unit` | Broad unit coverage proves this did not change request status handling or sensitive logging |

## Testing

Local implementation commit: `1b4f404 fix(ajax): preserve caller wikidot token`

- [x] `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_preserves_explicit_wikidot_token -q` failed before the fix with encoded body `wikidot_token7=123456` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_uses_header_wikidot_token_by_default -q` failed before the header-cookie default fix with encoded body `wikidot_token7=123456` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_preserves_explicit_wikidot_token tests/unit/test_amc_client.py::TestAjaxModuleConnectorClientRequest::test_request_uses_header_wikidot_token_by_default -q` passed with 2 tests.
- [x] `uv run --extra test pytest tests/unit/test_amc_client.py -q` passed with 33 tests.
- [x] `uv run --extra test pytest tests/unit/test_ajax.py tests/unit/test_amc_client.py -q` passed with 46 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 605 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] Complexity scan refreshed at `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/complexity_analysis_wikidot.md`

## Acceptance Criteria

- `AjaxModuleConnectorClient.request(...)` does not overwrite an explicit caller-provided `wikidot_token7`.
- If the caller omits `wikidot_token7`, the request body uses the current `AjaxRequestHeader.cookie["wikidot_token7"]` value.
- If no custom token exists, the existing default `123456` token is still sent.
- Caller request dictionaries are not mutated.
- Sensitive token masking remains unchanged in logs and tests.
- No browser automation, live Wikidot mutation, upstream issue, or upstream PR is performed by this local slice.

## Upstream-Safe Motivation

Some Wikidot AMC workflows, especially public source inspection, require a token discovered from the target page. A connector should not silently replace that token with a hard-coded default, and the request body should stay consistent with the caller-managed header cookie. Preserving caller tokens keeps the existing default behavior while making token-aware read workflows possible through the library.

## Local Evidence, Not For Upstream Paste

- Local rollout evidence included an anonymous source fetcher that read public Wikidot pages, extracted page IDs and anonymous `wikidot_token7` values, and requested `viewsource/ViewSourceModule` through `ajax-module-connector.php`.
- Existing local source-collection drafts established that ViewSource-based workflows are operationally important for browser-free publishing, dependency source capture, and large corpus collection.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, extracted tokens, cookies, or private source payloads into an upstream PR.

## Additional Notes

This slice deliberately does not add a public anonymous source-fetch helper. It only fixes the lower-level connector behavior needed by such workflows and by any caller that deliberately controls AMC tokens.
