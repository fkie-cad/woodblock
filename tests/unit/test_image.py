import io
from math import ceil

import pytest

import woodblock
from woodblock.fragments import ZeroesFragment
from woodblock.image import Image
from woodblock.scenario import Scenario


class FakePaddingGenerator:
    def __init__(self):
        self.size = 0

    def generate(self, size):
        self.size = size
        return b'A' * size


class TestImage:
    def test_that_an_empty_image_can_be_written(self):
        f = io.BytesIO()
        image = Image()
        image.write(f)
        f.seek(0)
        assert len(f.read()) == 0

    def test_that_an_empty_with_an_empty_scenario_can_be_written(self):
        s = Scenario('empty')
        image = Image()
        image.add(s)
        f = io.BytesIO()
        image.write(f)
        f.seek(0)
        assert len(f.read()) == 0

    def test_that_a_scenario_can_be_written(self):
        s = Scenario('scenario')
        s.add(ZeroesFragment(512))
        image = Image()
        image.add(s)
        f = io.BytesIO()
        image.write(f)
        f.seek(0)
        assert len(f.read()) == 512

    @pytest.mark.parametrize('fragment_size, expected_padding_size',
                             ((512, 0), (513, 511), (1023, 1), (1024, 0)))
    def test_that_correct_padding_is_applied(self, fragment_size, expected_padding_size):
        s = Scenario('scenario')
        s.add(ZeroesFragment(fragment_size))
        padder = FakePaddingGenerator()
        image = Image(padding_generator=padder.generate)
        image.add(s)
        f = io.BytesIO()
        image.write(f)
        f.seek(0)
        data = f.read()
        assert len(data) == ceil(fragment_size / 512) * 512
        assert padder.size == expected_padding_size
        if expected_padding_size > 0:
            assert data[-expected_padding_size:] == b'A' * expected_padding_size


class TestImageMetadata:
    def test_an_empty_image(self, test_corpus_path):
        woodblock.random.seed(13)
        assert Image(block_size=513).metadata == {'block_size': 513, 'seed': 13, 'corpus': str(test_corpus_path),
                                                  'scenarios': []}

    def test_an_image_with_a_single_scenario(self, test_corpus_path):
        woodblock.random.seed(13)
        image = Image(block_size=513)
        image.add(Scenario('some scenario'))
        assert image.metadata == {'block_size': 513, 'seed': 13, 'corpus': str(test_corpus_path),
                                  'scenarios': [{'name': 'some scenario', 'files': []}]}

    def test_an_image_with_multiple_scenarios(self, test_corpus_path):
        woodblock.random.seed(13)
        image = Image(block_size=513)
        image.add(Scenario('first scenario'))
        image.add(Scenario('second scenario'))
        image.add(Scenario('third scenario'))
        assert image.metadata == {'block_size': 513, 'seed': 13, 'corpus': str(test_corpus_path),
                                  'scenarios': [{'name': 'first scenario', 'files': []},
                                                {'name': 'second scenario', 'files': []},
                                                {'name': 'third scenario', 'files': []}]}
