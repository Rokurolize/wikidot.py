"""Package-level public API tests."""

import wikidot


def test_import_star_exposes_top_level_classes() -> None:
    """Top-level classes exposed on wikidot should also be in __all__."""
    namespace: dict[str, object] = {}

    exec("from wikidot import *", namespace)

    for name in ["Client", "Page", "PageCollection", "Site", "ForumThread", "UserCollection"]:
        exported = getattr(wikidot, name)
        assert name in wikidot.__all__
        assert namespace[name] is exported
