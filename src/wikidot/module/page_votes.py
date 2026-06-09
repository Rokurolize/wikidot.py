"""
Module for handling Wikidot page votes (ratings)

This module provides classes and functions related to Wikidot page votes (ratings).
It enables operations such as retrieving and displaying vote information for pages.
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING, cast

from .user import AbstractUser

if TYPE_CHECKING:
    from .page import Page


def _validate_vote_page(value: object) -> "Page":
    from .page import Page

    if not isinstance(value, Page):
        raise ValueError("page must be a Page")
    return value


def _validate_vote_user(value: object) -> AbstractUser:
    if not isinstance(value, AbstractUser):
        raise ValueError("user must be an AbstractUser")
    return value


def _validate_vote_user_site(page: "Page", user: AbstractUser) -> None:
    if user.client is not page.site.client:
        raise ValueError("user must belong to the site")


def _validate_vote_value(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("value must be an integer")
    return value


def _validate_vote_search_user_id(value: object) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("user.id must be an integer")
    if value < 0:
        raise ValueError("user.id must be non-negative")
    return value


def _validate_stored_vote_user_id(value: object) -> int | None:
    if value is None:
        return None
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError("vote.user.id must be an integer or None")
    if value < 0:
        raise ValueError("vote.user.id must be non-negative or None")
    return value


def _validate_vote_search_user(user: object) -> AbstractUser:
    if not isinstance(user, AbstractUser):
        raise ValueError("user must be an AbstractUser")
    _validate_vote_search_user_id(user.id)
    return user


def _validate_page_votes(votes: object) -> list["PageVote"]:
    if not isinstance(votes, list):
        raise ValueError("votes must be a list")
    if any(not isinstance(vote, PageVote) for vote in votes):
        raise ValueError("votes list entries must be PageVote")
    return cast(list["PageVote"], votes)


def _validate_votes_belong_to_page(page: "Page", votes: list["PageVote"]) -> None:
    if any(vote.page is not page for vote in votes):
        raise ValueError("votes must belong to the collection page")


class PageVoteCollection(list["PageVote"]):
    """
    Class representing a collection of page votes

    A list extension class for storing and operating on multiple votes (ratings)
    for a page in bulk.
    """

    page: "Page"

    def __init__(self, page: "Page", votes: list["PageVote"]):
        """
        Initialize the collection

        Parameters
        ----------
        page : Page
            The page the votes belong to
        votes : list[PageVote]
            List of votes to store
        """
        self.page = _validate_vote_page(page)
        votes = _validate_page_votes(votes)
        _validate_votes_belong_to_page(self.page, votes)
        super().__init__(votes)

    def __iter__(self) -> Iterator["PageVote"]:
        """
        Return an iterator over the votes in the collection

        Returns
        -------
        Iterator[PageVote]
            Iterator of vote objects
        """
        return super().__iter__()

    def find(self, user: "AbstractUser") -> "PageVote":
        """
        Get the vote by the specified user

        Parameters
        ----------
        user : AbstractUser
            The user who cast the vote

        Returns
        -------
        PageVote
            The user's vote information
        """
        user = _validate_vote_search_user(user)
        _validate_vote_user_site(self.page, user)
        user_id = _validate_vote_search_user_id(user.id)
        for vote in self:
            if _validate_stored_vote_user_id(vote.user.id) == user_id:
                return vote
        raise ValueError(f"User {user} has not voted on page {self.page}")


@dataclass
class PageVote:
    """
    Class representing a vote (rating) for a page

    Holds information about a vote (rating) cast by a user for a page.

    Attributes
    ----------
    page : Page
        The page the vote belongs to
    user : AbstractUser
        The user who cast the vote
    value : int
        The vote value (+1/-1 or numeric)
    """

    page: "Page"
    user: "AbstractUser"
    value: int

    def __post_init__(self) -> None:
        self.page = _validate_vote_page(self.page)
        self.user = _validate_vote_user(self.user)
        _validate_vote_user_site(self.page, self.user)
        self.value = _validate_vote_value(self.value)
