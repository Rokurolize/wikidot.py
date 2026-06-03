# PR Draft: Sync Package Top-Level Exports

## Summary

`wikidot.__init__` dynamically imports classes from `common`, `connector`, `module`, and `util` submodules and exposes them on the top-level `wikidot` package. Its docstring describes access in the form `wikidot.ClassName`, and the README's basic usage starts with `import wikidot`.

However, `__all__` still contained only `Client`. As a result, classes that were already available as attributes such as `wikidot.Page`, `wikidot.Site`, and `wikidot.ForumThread` were not exported by `from wikidot import *`. The same import helper also used `inspect.getmembers(...)`, which sorts and scans every imported module's members even though only classes defined in that exact module are needed.

The fix keeps the existing top-level attribute behavior, synchronizes `__all__` with those dynamically exposed classes, and simplifies the importer into small helpers that enumerate module paths and locally defined classes directly.

## Related Issue

Complements the local reliability and ergonomics drafts that made top-level practical workflows easier to use, especially [003-feature-browser-free-page-publisher.md](003-feature-browser-free-page-publisher.md), [017-pr-browser-free-page-publish-helper.md](017-pr-browser-free-page-publish-helper.md), and [018-pr-bounded-page-search-iterator.md](018-pr-bounded-page-search-iterator.md). No upstream issue filed yet.

## Changes

- Add deterministic package submodule enumeration for `common`, `connector`, `module`, and `util`.
- Replace `inspect.getmembers(module, inspect.isclass)` with direct `module.__dict__` class iteration filtered by `obj.__module__`.
- Append each dynamically exposed class name to `wikidot.__all__`.
- Preserve top-level attribute exposure for classes already exposed as `wikidot.ClassName`.
- Add package-level regression coverage for `from wikidot import *`.

## Type Of Change

- [x] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update
- [x] Refactoring
- [ ] Security/privacy hardening
- [ ] Reliability improvement
- [x] Test addition/modification
- [ ] CI/CD or build related

## Requirements Traceability

| Requirement | Acceptance | Verification | Negative Control |
| --- | --- | --- | --- |
| R1: `__all__` matches top-level dynamic exports | Representative classes exposed on `wikidot` are also listed in `wikidot.__all__` | `test_import_star_exposes_top_level_classes` | The test failed before the fix because `Page` was available on `wikidot` but absent from `__all__` |
| R2: Star import exposes the same public classes | `from wikidot import *` includes representative top-level classes and binds the exact package attributes | `test_import_star_exposes_top_level_classes` | The test executes a real star import and checks identity with `getattr(wikidot, name)` |
| R3: Existing import and client/site behavior is preserved | Package import, `Client`, and site accessor tests remain green | `tests/unit/test_package.py tests/unit/test_client.py tests/unit/test_site.py`; `tests/unit` | Broad unit coverage still passes after the package importer refactor |
| R4: `__init__.py` complexity hotspot is reduced | The refreshed complexity scan no longer lists `src/wikidot/__init__.py` in the top hotspot section | Complexity scan artifact | The prior scan flagged `src/wikidot/__init__.py` nested-loop and sort-in-loop leads |

## Testing

Local implementation commit: `8400050 fix(package): sync top-level exports`

- [x] `uv run --extra test pytest tests/unit/test_package.py -q` failed before the fix with `AssertionError: assert 'Page' in ['Client']` and passed after the fix.
- [x] `uv run --extra test pytest tests/unit/test_package.py tests/unit/test_client.py tests/unit/test_site.py -q` passed with 67 tests.
- [x] `uv run --extra test pytest tests/unit -q` passed with 600 tests.
- [x] `uv run ruff check .`
- [x] `uv run ruff format --check .`
- [x] `uv run mypy src tests`
- [x] `git diff --check`
- [x] Complexity scan refreshed at `/home/roku/codex-thread-workspaces/019e8a3a-20fd-7113-975d-8c92336695cd/artifacts/complexity_analysis_wikidot.md`; the `src/wikidot/__init__.py` hotspot no longer appears in the top findings.

## Acceptance Criteria

- `wikidot.__all__` includes dynamically exposed package-level classes such as `Page`, `PageCollection`, `Site`, `ForumThread`, and `UserCollection`.
- `from wikidot import *` imports those representative classes.
- `wikidot.Client` and existing module-level imports continue to work.
- Import helper behavior remains local to package initialization; no AMC, browser, live Wikidot, upstream issue, or upstream PR action is performed by this local slice.
- Complexity scan evidence confirms the previous package-initializer hotspot is gone.

## Upstream-Safe Motivation

The package already exposes classes as `wikidot.ClassName`, but `__all__` did not reflect that public surface. Keeping `__all__` in sync makes star import behavior consistent with the package's dynamic top-level attributes and with the README's package-level usage style. The refactor also avoids unnecessary reflection/sorting work during package initialization while keeping the same module import boundary.

## Local Evidence, Not For Upstream Paste

- The README shows the package-level usage style: `import wikidot` followed by `wikidot.Client()`.
- Local rollout evidence repeatedly used package-level imports such as `import wikidot` and `from wikidot import Client` in browser-free Wikidot scripts.
- The refreshed local complexity scan previously flagged `src/wikidot/__init__.py` before this slice and no longer does after the helper split.
- This draft is local-only. Do not paste private rollout paths, local account names, thread workspace paths, raw command transcripts, or sandbox details into an upstream PR.

## Additional Notes

This slice intentionally does not change submodule import failure behavior: import failures are still silently ignored, matching the existing package initializer contract.
