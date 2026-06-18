import re
from typing import TYPE_CHECKING

import bs4

from ...module import user

if TYPE_CHECKING:
    from wikidot.module.client import Client


def user_parse(client: "Client", elem: bs4.Tag | str) -> user.AbstractUser:
    """Parse a printuser element and return a user object

    Parameters
    ----------
    elem: bs4.Tag
        Element to parse (element with printuser class)
    client: Client
        Client

    Returns
    -------
    user.AbstractUser
        Parsed user object
        One of User | DeletedUser | AnonymousUser | GuestUser | WikidotUser
    """

    if isinstance(elem, str):
        if elem.strip() != "(user deleted)":
            raise ValueError("elem must be bs4.Tag except DeletedUser")
        return user.DeletedUser(client=client, id=0)

    if not isinstance(elem, bs4.Tag):
        raise ValueError("elem must be bs4.Tag except DeletedUser")

    if "deleted" in elem.get("class", []):
        data_id = elem.get("data-id", 0)
        data_id_text = str(data_id)
        if re.fullmatch(r"[0-9]+", data_id_text) is None:
            raise ValueError(f"deleted user id is malformed: {data_id}")
        deleted_user_id = int(data_id_text)
        return user.DeletedUser(client=client, id=deleted_user_id)

    if "class" in elem.attrs and "anonymous" in elem["class"]:
        ip_elem = elem.find("span", class_="ip")
        if ip_elem is None:
            return user.AnonymousUser(client=client)
        ip = ip_elem.get_text().replace("(", "").replace(")", "").strip()
        return user.AnonymousUser(client=client, ip=ip)

    # Gravatar URLを持つ場合はGuestUserとする
    img_elem = elem.find("img")
    img_src = img_elem.get("src") if isinstance(img_elem, bs4.Tag) else None
    if isinstance(img_src, str) and "gravatar.com" in img_src:
        avatar_url = img_src
        guest_text = elem.get_text(" ", strip=True)
        guest_name = re.sub(r"\s*(?:\([^)]*\)|（[^）]*）)\s*$", "", guest_text)
        return user.GuestUser(
            client=client,
            name=guest_name,
            avatar_url=str(avatar_url) if avatar_url else None,
        )

    if elem.get_text(strip=True) == "Wikidot":
        return user.WikidotUser(client=client)

    user_links = elem.find_all("a")
    if not user_links:
        raise ValueError("link element is not found")

    _user = user_links[-1]
    if not isinstance(_user, bs4.Tag):
        raise ValueError("link element is not found")
    user_name = _user.get_text(" ", strip=True)
    href_attr = _user.get("href")
    if not isinstance(href_attr, str) or href_attr == "":
        raise ValueError("user href is not found")
    href = href_attr
    user_unix_match = re.fullmatch(r"(?:https?://www\.wikidot\.com)?/user:info/([^/?#]+)(?:[?#].*)?", href)
    if user_unix_match is None:
        raise ValueError(f"user href is malformed: {href}")
    user_unix = user_unix_match.group(1)
    onclick = str(_user.get("onclick", ""))
    user_id_match = re.fullmatch(
        r"\s*(?:WIKIDOT\.page\.listeners\.)?userInfo\(([0-9]+)\)(?:\s*;\s*return false;?)?\s*",
        onclick,
    )
    if user_id_match is None:
        malformed_user_id_match = re.fullmatch(
            r"\s*(?:WIKIDOT\.page\.listeners\.)?userInfo\(([^)]*)\)(?:\s*;\s*return false;?)?\s*",
            onclick,
        )
        if malformed_user_id_match is not None:
            raw_user_id = malformed_user_id_match.group(1)
            if raw_user_id.strip() != "":
                raise ValueError(f"user id is malformed: {raw_user_id}")
        if "userInfo(" in onclick:
            raise ValueError(f"user onclick is malformed: {onclick}")
        raise ValueError("user id is not found")
    user_id = int(user_id_match.group(1))

    return user.User(
        client=client,
        id=user_id,
        name=user_name,
        unix_name=user_unix,
        avatar_url=f"http://www.wikidot.com/avatar.php?userid={user_id}",
    )
