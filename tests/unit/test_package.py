"""Package-level public API tests."""

import wikidot


def test_iter_submodule_names_skips_missing_base_dirs(tmp_path) -> None:
    assert list(wikidot._iter_submodule_names(tmp_path)) == []


def test_import_submodules_ignores_import_error(monkeypatch) -> None:
    monkeypatch.setattr(wikidot, "_iter_submodule_names", lambda package_dir: iter(["wikidot.missing_module"]))

    wikidot._import_submodules()


def test_import_star_exposes_top_level_classes() -> None:
    """Top-level classes exposed on wikidot should also be in __all__."""
    namespace: dict[str, object] = {}

    exec("from wikidot import *", namespace)

    for name in ["Client", "Page", "PageCollection", "Site", "ForumThread", "UserCollection"]:
        exported = getattr(wikidot, name)
        assert name in wikidot.__all__
        assert namespace[name] is exported
