"""This module contains data generators."""
import random

from woodblock.random import RandomBytes


class Zeroes:
    """Generates zero bytes."""

    def __call__(self, size):
        return b'\x00' * size

    def __str__(self):
        return 'zeroes'


class Random:
    """Generates random bytes."""

    def __init__(self, rng=RandomBytes()):
        self._seed = random.randint(0, 2 ** 32 - 1)  # nosec
        self._rng = rng
        self._rng.seed(self._seed)

    def __call__(self, size):
        return self._rng.bytes(size)

    def __str__(self):
        return 'random'

    def reset(self):
        """Reset the random state.

        After calling this method, the RNG will be set to its initial seed, so that subsequent calls return the same
        bytes as the calls before.
        """
        self._rng.seed(self._seed)
