import pytest

from woodblock.fragments import ZeroesFragment
from woodblock.scenario import Scenario


class TestScenario:

    def test_an_empty_scenario(self):
        s = Scenario('empty')
        call_count = 0
        for _ in s:
            call_count += 1
        assert call_count == 0
        assert s.name == 'empty'

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4, 5, 6, 1000))
    def test_that_fragments_can_be_added(self, num_fragments):
        s = Scenario('Test Scenario')
        for _ in range(num_fragments):
            s.add(ZeroesFragment(512))
        call_count = 0
        for _ in s:
            call_count += 1
        assert call_count == num_fragments

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4, 5, 6, 1000))
    def test_that_a_list_of_fragments_can_be_added(self, num_fragments):
        s = Scenario('Test Scenario')
        fragments = list(ZeroesFragment(512) for _ in range(num_fragments))
        s.add(fragments)
        call_count = 0
        for _ in s:
            call_count += 1
        assert call_count == num_fragments

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4, 5, 6, 1000))
    def test_that_a_tuple_of_fragments_can_be_added(self, num_fragments):
        s = Scenario('Test Scenario')
        fragments = tuple(ZeroesFragment(512) for _ in range(num_fragments))
        s.add(fragments)
        call_count = 0
        for _ in s:
            call_count += 1
        assert call_count == num_fragments

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4, 5, 6, 1000))
    def test_that_fragments_can_be_read(self, num_fragments):
        chunk_size = 512
        s = Scenario('Test Scenario')
        for _ in range(num_fragments):
            s.add(ZeroesFragment(512, chunk_size=chunk_size))
        call_count = 0
        for fragment in s:
            call_count += 1
            assert fragment.size == 512
            for chunk in fragment:
                assert chunk == b'\x00' * chunk_size
        assert call_count == num_fragments


class TestScenarioMetadata:
    def test_empty_scenario(self):
        assert Scenario('test scenario').metadata == {'name': 'test scenario', 'files': []}

    def test_with_a_single_fragment(self):
        s = Scenario('test scenario with a single file')
        s.add(ZeroesFragment(1024))
        expected = {'name': 'test scenario with a single file', 'files': [
            {
                'original': {
                    'size': 1024, 'id': 'uuid', 'type': 'filler', 'path': 'zeroes',
                    'sha256': '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef'},
                'fragments': [
                    {
                        'size': 1024, 'number': 1, 'file_offsets': {'start': 0, 'end': 1024},
                        'sha256': '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef'
                    }
                ]
            }
        ]}
        assert replace_uuids(s.metadata) == expected

    def test_with_multiple_fragments(self):
        s = Scenario('test scenario with a single file')
        s.add(ZeroesFragment(1024))
        s.add(ZeroesFragment(512))
        s.add(ZeroesFragment(2050))
        expected = {'name': 'test scenario with a single file', 'files': [
            {
                'original': {
                    'size': 1024, 'id': 'uuid', 'type': 'filler', 'path': 'zeroes',
                    'sha256': '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef'},
                'fragments': [
                    {
                        'size': 1024, 'number': 1, 'file_offsets': {'start': 0, 'end': 1024},
                        'sha256': '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef'
                    }
                ]
            },
            {
                'original': {
                    'size': 512, 'id': 'uuid', 'type': 'filler', 'path': 'zeroes',
                    'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560'},
                'fragments': [
                    {
                        'size': 512, 'number': 1, 'file_offsets': {'start': 0, 'end': 512},
                        'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560'
                    }
                ]
            },
            {
                'original': {
                    'size': 2050, 'id': 'uuid', 'type': 'filler', 'path': 'zeroes',
                    'sha256': '382e008e5bc647359ed6f41cb932f732b000a96c6048edd3cae85e65df04c175'},
                'fragments': [
                    {
                        'size': 2050, 'number': 1, 'file_offsets': {'start': 0, 'end': 2050},
                        'sha256': '382e008e5bc647359ed6f41cb932f732b000a96c6048edd3cae85e65df04c175'
                    }
                ]
            }
        ]}
        assert replace_uuids(s.metadata) == expected


def replace_uuids(metadata):
    for file_meta in metadata['files']:
        file_meta['original']['id'] = 'uuid'
    return metadata
