"""Spotbit exception module."""

class SpotbitException(Exception):
    """Base class for all exceptions in Spotbit."""


class ClientException(SpotbitException):
    """Exception occured on the client side.

    Examples:
    - Client ID or Client Secret isn't specified.
    - User's generated mistakes.
    """
