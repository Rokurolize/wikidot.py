from datetime import datetime, timezone

import bs4

from .html import class_values


def odate_parse(odate_element: bs4.Tag) -> datetime:
    """Parse an odate element and return a datetime object

    Parameters
    ----------
    odate_element: bs4.Tag
        odate element

    Returns
    -------
    datetime
        Date and time represented by the odate element

    Raises
    ------
    ValueError
        If the odate element does not contain a valid unix time

    """
    if not isinstance(odate_element, bs4.Tag):
        raise ValueError("odate_element must be bs4.Tag")

    for _odate_class in class_values(odate_element):
        odate_class = str(_odate_class)
        if "time_" in odate_class:
            if not odate_class.startswith("time_"):
                raise ValueError(f"odate unix time is malformed: {odate_class}")
            unix_timestamp = odate_class.removeprefix("time_")
            if not unix_timestamp.isascii() or not unix_timestamp.isdecimal():
                raise ValueError(f"odate unix time is malformed: {odate_class}")
            try:
                unix_time = int(unix_timestamp)
                return datetime.fromtimestamp(unix_time, timezone.utc).replace(tzinfo=None)
            except (OverflowError, OSError, ValueError) as exc:
                raise ValueError(f"odate unix time is malformed: {odate_class}") from exc

    raise ValueError("odate element does not contain a valid unix time")
