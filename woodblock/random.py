"""This module takes care about the randomness and reproducibility of the generated data sets."""

import random

import numpy as np


class Randomness:
    """This class acts as the main random number generator.

    ``Randomness`` seeds Python's core ``random`` module so that the user doesn't have to do this. Every
    :class:`RandomBytes` / :class:`woodblock.datagen.Random` generator derives its own seed from this seeded
    ``random`` module and keeps it in a private NumPy ``RandomState``; reproducibility therefore flows entirely
    through Python's ``random``. NumPy's *global* RNG is intentionally **not** seeded, because no data-generation
    path uses it (the only NumPy call outside per-instance ``RandomState``s is the deterministic ``np.array_split``).

    If no seed is set by the user, the seed will be randomly generated.
    """

    def __init__(self):
        self._seed = random.randint(0, 2**32 - 1)  # nosec
        self.seed(self._seed)

    def seed(self, random_seed: int):
        """Set the seed.

        Args:
            random_seed: The seed to use. Must be an integer in ``[0, 2**32)`` since this is the
                range accepted by NumPy's RNG.

        Raises:
            ValueError: If ``random_seed`` is not an integer in ``[0, 2**32)``.
        """
        if not isinstance(random_seed, int) or isinstance(random_seed, bool):
            raise ValueError(f'Seed must be an integer in [0, 2**32), got {random_seed!r}.')
        if not 0 <= random_seed < 2**32:
            raise ValueError(f'Seed must be an integer in [0, 2**32), got {random_seed}.')
        self._seed = random_seed
        # Only Python's global ``random`` is seeded. Each RandomBytes/Random generator draws its own seed from it
        # and keeps a private NumPy RandomState, so seeding NumPy's global RNG would change nothing. (np.array_split,
        # the only other NumPy use, is deterministic.)
        random.seed(self._seed)

    def get_seed(self) -> int:
        """Return the random seed."""
        return self._seed


_RANDOM = Randomness()

seed = _RANDOM.seed

get_seed = _RANDOM.get_seed


class RandomBytes:
    """This class can be used to generate random bytes."""

    def __init__(self):
        self._rng = np.random.RandomState()

    def bytes(self, size: int):
        """Return ``size`` random bytes.

        Args:
            size: The number of bytes to return.
        """
        return self._rng.bytes(size)

    def seed(self, random_seed: int):
        """Set the seed for the RNG.

        Args:
            random_seed: The seed to use.
        """
        self._rng.seed(random_seed)
