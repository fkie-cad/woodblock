"""Tests that the generated image bytes always match the recorded ground truth.

These cover the interaction between the (random) data generators, fragment hashing and the
image padding. The key guarantees are:

- every recorded SHA-256 matches the bytes actually written at the recorded image offsets,
  regardless of whether the metadata is computed before or after writing, and
- writing the same image twice produces byte-identical output (including padding).
"""

import hashlib
import io

import pytest

import woodblock
from woodblock.file import File
from woodblock.fragments import FileFragment, RandomDataFragment, ZeroesFragment
from woodblock.image import Image
from woodblock.scenario import Scenario


def _verify_ground_truth(image, meta, data):
    checked = 0
    for scenario_meta in meta['scenarios']:
        for file_meta in scenario_meta['files']:
            for frag_meta in file_meta['fragments']:
                offsets = frag_meta['image_offsets']
                on_disk = data[offsets['start']:offsets['end']]
                assert hashlib.sha256(on_disk).hexdigest() == frag_meta['sha256']
                checked += 1
    assert checked > 0


def _build_image():
    woodblock.random.seed(4711)
    image = Image(block_size=512)
    scenario = Scenario('random fillers')
    # Non-block-aligned sizes force padding between fragments; include one larger than the
    # default chunk size so re-iteration is exercised.
    scenario.add(RandomDataFragment(300))
    scenario.add(RandomDataFragment(700))
    scenario.add(RandomDataFragment(9000))
    image.add(scenario)
    return image


class TestGroundTruthIntegrity:
    def test_hashes_match_when_writing_before_reading_metadata(self):
        image = _build_image()
        buf = io.BytesIO()
        image.write(buf)
        _verify_ground_truth(image, image.metadata, buf.getvalue())

    def test_hashes_match_when_reading_metadata_before_writing(self):
        # Accessing metadata caches the fragment hashes; the data written afterwards must
        # still match those cached hashes.
        image = _build_image()
        meta = image.metadata
        buf = io.BytesIO()
        image.write(buf)
        _verify_ground_truth(image, meta, buf.getvalue())

    def test_hashes_match_for_mixed_fragment_types(self, path_test_file_4k):
        woodblock.random.seed(99)
        image = Image(block_size=512)
        scenario = Scenario('mixed')
        scenario.add(FileFragment(File(path_test_file_4k), 1, 0, 1500))
        scenario.add(RandomDataFragment(600))
        scenario.add(ZeroesFragment(800))
        scenario.add(RandomDataFragment(9000))
        image.add(scenario)
        meta = image.metadata
        buf = io.BytesIO()
        image.write(buf)
        _verify_ground_truth(image, meta, buf.getvalue())


class TestWriteIdempotency:
    def test_writing_the_same_image_twice_is_byte_identical(self):
        image = _build_image()
        first = io.BytesIO()
        second = io.BytesIO()
        image.write(first)
        image.write(second)
        assert first.getvalue() == second.getvalue()

    @pytest.mark.parametrize('passes', (2, 3, 5))
    def test_repeated_writes_are_stable(self, passes):
        image = _build_image()
        reference = io.BytesIO()
        image.write(reference)
        for _ in range(passes):
            buf = io.BytesIO()
            image.write(buf)
            assert buf.getvalue() == reference.getvalue()


class TestSeedReproducibility:
    def test_same_seed_produces_identical_images(self):
        def render():
            woodblock.random.seed(2023)
            image = Image(block_size=512)
            scenario = Scenario('s')
            scenario.add(RandomDataFragment(300))
            scenario.add(RandomDataFragment(9000))
            image.add(scenario)
            buf = io.BytesIO()
            image.write(buf)
            return buf.getvalue()

        assert render() == render()
