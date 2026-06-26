"""Tests for the data generators, focusing on RNG independence and reproducibility."""

import hashlib

from woodblock.datagen import Random, Zeroes


class RecordingRng:
    """A fake RNG that records the seed it was given and returns deterministic bytes."""

    def __init__(self):
        self.seeds = []

    def seed(self, seed):
        self.seeds.append(seed)

    @staticmethod
    def bytes(size):
        return b'A' * size


class TestRandom:
    def test_that_each_instance_owns_its_own_rng(self):
        # Regression test: a shared (mutable default) RNG entangles the byte streams of all
        # generators. Every Random instance must get an independent RNG.
        assert Random()._rng is not Random()._rng

    def test_that_the_generated_seed_is_passed_to_the_rng(self):
        rng = RecordingRng()
        generator = Random(rng=rng)
        assert rng.seeds == [generator._seed]

    def test_that_reset_re_seeds_the_rng(self):
        rng = RecordingRng()
        generator = Random(rng=rng)
        generator.reset()
        assert rng.seeds == [generator._seed, generator._seed]

    def test_that_reset_reproduces_the_same_bytes(self):
        generator = Random()
        first = generator(64)
        generator.reset()
        assert generator(64) == first

    def test_that_reset_is_idempotent(self):
        generator = Random()
        generator.reset()
        first = generator(64)
        generator.reset()
        generator.reset()
        assert generator(64) == first

    def test_that_two_instances_do_not_interfere(self):
        # Each generator must reproduce its own stream even when their use is interleaved.
        gen_a = Random()
        gen_b = Random()
        a_first = gen_a(64)
        gen_b(64)  # advance the other generator in between
        gen_a.reset()
        gen_b.reset()
        assert gen_a(64) == a_first

    def test_that_two_independent_instances_produce_different_streams(self):
        # With independent RNGs the probability of two random 1 KiB blocks colliding is
        # negligible; this guards against accidentally sharing a single RNG again.
        assert Random()(1024) != Random()(1024)

    def test_str(self):
        assert str(Random()) == 'random'


class TestZeroes:
    def test_that_it_generates_zero_bytes(self):
        assert Zeroes()(128) == b'\x00' * 128

    def test_that_reset_is_a_callable_no_op(self):
        generator = Zeroes()
        assert generator.reset() is None
        assert generator(16) == b'\x00' * 16

    def test_str(self):
        assert str(Zeroes()) == 'zeroes'


def test_random_data_is_actually_random_looking():
    # Sanity check that Random does not collapse to a constant.
    data = Random()(4096)
    assert len(set(data)) > 1
    assert hashlib.sha256(data).hexdigest() != hashlib.sha256(b'\x00' * 4096).hexdigest()
