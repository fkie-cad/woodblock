"""This module takes care about the randomness and reproducibility of the generated data sets."""

import random

import numpy as np


class Randomness:
    """This class acts as the main random number generator.

    ``Randomness`` is basically just a wrapper for the random modules of the Python core and NumPy. All it does is
    initializing the seed of both modules so that the user doesn't have to do this.

    If no seed is set by the user, the seed will be randomly generated.
    """

    def __init__(self):
        self._seed = random.randint(0, 2 ** 32 - 1)  # nosec
        self.seed(self._seed)

    def seed(self, random_seed: int):
        """Set the seed.

        Args:
            random_seed: The seed to use.
        """
        self._seed = random_seed
        random.seed(self._seed)
        np.random.seed(self._seed)

    def get_seed(self) -> int:
        """Return the random seed."""
        return self._seed


_RANDOM = Randomness()

seed = _RANDOM.seed  # pylint: disable=invalid-name

get_seed = _RANDOM.get_seed  # pylint: disable=invalid-name


class RandomBytes:  # pylint: disable=too-few-public-methods
    """This class can be used to generate random bytes."""

    def __init__(self):
        self._rng = np.random.RandomState()  # pylint: disable=no-member

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
