"""Logger utility unit tests."""

import logging
from typing import Any

import pytest

from wikidot.common.logger import setup_console_handler


def _test_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.handlers.clear()
    logger.setLevel(logging.NOTSET)
    return logger


class TestSetupConsoleHandler:
    """setup_console_handlerのテスト"""

    @pytest.mark.parametrize(
        ("level", "expected"),
        [
            ("debug", logging.DEBUG),
            ("INFO", logging.INFO),
            (logging.ERROR, logging.ERROR),
        ],
    )
    def test_accepts_named_string_and_integer_levels(self, level: str | int, expected: int) -> None:
        logger = _test_logger(f"wikidot-test-valid-{expected}")

        setup_console_handler(logger, level)

        assert logger.level == expected

    def test_rejects_unknown_string_level(self) -> None:
        logger = _test_logger("wikidot-test-invalid-string")

        with pytest.raises(ValueError, match="Invalid logging level: not-a-level"):
            setup_console_handler(logger, "not-a-level")

    @pytest.mark.parametrize("level", [None, True, False, 1.5, object(), [], {}])
    def test_rejects_malformed_level_values(self, level: Any) -> None:
        logger = _test_logger("wikidot-test-malformed")

        with pytest.raises(ValueError, match="logging level must be a string or integer"):
            setup_console_handler(logger, level)
