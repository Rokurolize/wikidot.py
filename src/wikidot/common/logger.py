"""
Module providing logging functionality

This module configures and provides loggers used throughout the library.
It uses NullHandler to enable log control on the application side.
"""

import logging


def get_logger(name: str = "wikidot") -> logging.Logger:
    """
    Get the library logger

    Parameters
    ----------
    name : str, default "wikidot"
        Logger name

    Returns
    -------
    logging.Logger
        Logger instance
    """
    _logger = logging.getLogger(name)

    if not _logger.handlers:
        _logger.addHandler(logging.NullHandler())

    return _logger


def _validate_logging_level(level: object) -> int:
    if isinstance(level, str):
        level_value = getattr(logging, level.upper(), None)
        if not isinstance(level_value, int):
            raise ValueError(f"Invalid logging level: {level}")
        return level_value
    if isinstance(level, bool) or not isinstance(level, int):
        raise ValueError("logging level must be a string or integer")
    return level


def setup_console_handler(logger: logging.Logger, level: str | int = logging.WARNING) -> None:
    """
    Configure console output handler

    Parameters
    ----------
    logger : logging.Logger
        Logger to configure
    level : str | int, default logging.WARNING
        Log level
    """
    level_value = _validate_logging_level(level)

    # Remove existing console handlers owned by this setup path without removing FileHandler.
    for handler in logger.handlers[:]:
        if type(handler) is logging.StreamHandler:
            logger.removeHandler(handler)

    # Add new StreamHandler
    formatter = logging.Formatter("%(asctime)s [%(name)s/%(levelname)s] %(message)s")
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    logger.setLevel(level_value)


# Default logger used throughout the package
logger = get_logger()
