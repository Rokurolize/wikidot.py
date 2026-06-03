"""
A Python library for interacting with Wikidot sites

This package abstracts Wikidot site API operations and provides an intuitive interface.
It contains various classes for accessing major Wikidot elements such as users, sites, and pages.
"""

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

from .module.client import Client

__all__ = ["Client"]
__version__ = "4.4.1"
_SUBMODULE_DIRS = ("common", "connector", "module", "util")


def _iter_submodule_names(package_dir: Path) -> Iterator[str]:
    base_paths = [package_dir / base_dir for base_dir in _SUBMODULE_DIRS]
    module_paths: list[Path] = []
    for base_path in base_paths:
        if base_path.is_dir():
            module_paths.extend(base_path.glob("*.py"))
    module_paths.sort()

    for path in module_paths:
        if path.name.startswith("_"):
            continue

        yield f"{__name__}.{path.parent.name}.{path.stem}"


def _iter_module_classes(module: ModuleType, module_name: str) -> Iterator[tuple[str, type]]:
    for name, obj in module.__dict__.items():
        if isinstance(obj, type) and obj.__module__ == module_name:
            yield name, obj


def _expose_module_classes(current_module: ModuleType, module: ModuleType, module_name: str) -> None:
    for name, obj in _iter_module_classes(module, module_name):
        setattr(current_module, name, obj)
        if name not in __all__:
            __all__.append(name)


def _import_submodules() -> None:
    """
    Import classes from all submodules in the package and expose them at the top level

    Scans Python files within each subdirectory and imports contained classes
    into the top-level namespace. This allows access to classes in the format
    `wikidot.ClassName`.

    Notes
    -----
    Filenames starting with '_' are ignored.
    Import failures are silently ignored.
    """
    current_module = sys.modules[__name__]
    package_dir = Path(__file__).parent

    for full_module_name in _iter_submodule_names(package_dir):
        try:
            module = importlib.import_module(full_module_name)
            _expose_module_classes(current_module, module, full_module_name)
        except ImportError:
            pass


_import_submodules()
