"""This module contains data generators."""

import random

from woodblock.random import RandomBytes


class Zeroes:
    """Generates zero bytes."""

    def __call__(self, size):
        return b'\x00' * size

    def __str__(self):
        return 'zeroes'

    def reset(self):
        """Reset the generator.

        ``Zeroes`` is stateless, so this is a no-op. It exists so that all data generators
        share the same interface and can be reset interchangeably.
        """


class Random:
    """Generates random bytes."""

    def __init__(self, rng=None):
        self._seed = random.randint(0, 2**32 - 1)  # nosec
        # Each Random instance must own its own RNG. Using a shared default instance would
        # entangle the byte streams of all fillers and the image padding, breaking
        # reproducibility and making a fragment's data depend on unrelated generators.
        self._rng = rng if rng is not None else RandomBytes()
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
