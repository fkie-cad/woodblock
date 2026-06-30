"""Tests for seed handling and validation in ``woodblock.random``."""

import random as _stdlib_random

import numpy as np
import pytest

import woodblock.random


class TestSeedValidation:
    def test_that_a_valid_seed_is_accepted_and_returned(self):
        woodblock.random.seed(1234)
        assert woodblock.random.get_seed() == 1234

    def test_that_zero_is_a_valid_seed(self):
        woodblock.random.seed(0)
        assert woodblock.random.get_seed() == 0

    def test_that_the_maximum_seed_is_accepted(self):
        woodblock.random.seed(2 ** 32 - 1)
        assert woodblock.random.get_seed() == 2 ** 32 - 1

    @pytest.mark.parametrize('bad_seed', [2 ** 32, 2 ** 40, -1, -2 ** 40])
    def test_that_out_of_range_seeds_are_rejected(self, bad_seed):
        with pytest.raises(ValueError):
            woodblock.random.seed(bad_seed)

    @pytest.mark.parametrize('bad_seed', [1.5, '7', None, True])
    def test_that_non_integer_seeds_are_rejected(self, bad_seed):
        with pytest.raises(ValueError):
            woodblock.random.seed(bad_seed)

    def test_that_an_invalid_seed_does_not_mutate_rng_state(self):
        # An out-of-range seed previously mutated Python's RNG before NumPy raised, leaving a
        # half-seeded, inconsistent state. Validation must happen before any RNG is touched.
        woodblock.random.seed(42)
        py_state = _stdlib_random.getstate()
        np_state = np.random.get_state()

        with pytest.raises(ValueError):
            woodblock.random.seed(2 ** 40)

        assert _stdlib_random.getstate() == py_state
        assert np.array_equal(np.random.get_state()[1], np_state[1])
        assert woodblock.random.get_seed() == 42
