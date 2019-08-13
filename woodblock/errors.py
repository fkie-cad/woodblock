"""This module contains the Woodblock errors/exceptions."""


class WoodblockError(Exception):
    """Base class for all Woodblock errors."""


class InvalidFragmentationPointError(WoodblockError):
    """This error indicates an invalid fragmentation point."""


class ImageConfigError(WoodblockError):
    """This error is raised when an invalid image configuration file is used."""
