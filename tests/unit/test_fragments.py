from math import ceil

import pytest

from woodblock.errors import WoodblockError
from woodblock.file import File, get_corpus
from woodblock.fragments import ZeroesFragment, RandomDataFragment, FileFragment


class TestZeroesFragment:
    def test_that_a_size_of_zero_raises_an_error(self):
        with pytest.raises(WoodblockError):
            ZeroesFragment(0)

    @pytest.mark.parametrize('size', (1, 2, 3, 512, 1024, 8192, 16384, 16385))
    def test_that_fragment_is_created_correctly(self, size):
        fragment = ZeroesFragment(size)
        assert fragment.size == size
        call_count = 0
        data = b''
        for chunk in fragment:
            call_count += 1
            data = b''.join((data, chunk))
        assert call_count == ceil(size / 8192)
        assert len(data) == size
        assert data == b'\x00' * size

    @pytest.mark.parametrize('size, expected_hash', (
            (1, '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'),
            (512, '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560'),
            (1024, '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef'),
            (2047, '48c58cb7e4833bdaaf08e6ff3b78343eab33a3098b01e27aa6396d9a82cb4442')
    ))
    def test_explicit_hash_computation(self, size, expected_hash):
        fragment = ZeroesFragment(size)
        assert fragment.hash == expected_hash

    @pytest.mark.parametrize('size, expected_hash', (
            (1, '6e340b9cffb37a989ca544e6bb780a2c78901d3fb33738768511a30617afa01d'),
            (512, '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560'),
            (1024, '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef'),
            (2047, '48c58cb7e4833bdaaf08e6ff3b78343eab33a3098b01e27aa6396d9a82cb4442')
    ))
    def test_implicit_hash_computation(self, size, expected_hash):
        fragment = ZeroesFragment(size)
        for _ in fragment:
            pass
        assert fragment.hash == expected_hash

    def test_that_the_metadata_is_correct(self):
        fragment = ZeroesFragment(512)
        meta = _replace_uuids(fragment.metadata)
        assert meta == {
            'file': {'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560',
                     'id': 'uuid', 'type': 'filler', 'size': 512, 'path': 'zeroes'},
            'fragment': {'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560', 'size': 512,
                         'number': 1, 'file_offsets': {'start': 0, 'end': 512}}
        }

    @pytest.mark.parametrize('iterations', (2, 3, 4, 5, 10, 20, 50))
    def test_that_it_is_possible_to_read_the_framgment_multiple_times(self, iterations):
        fragment = ZeroesFragment(512)
        data = b''.join(c for c in fragment)
        for _ in range(iterations):
            data2 = b''.join(c for c in fragment)
            print(len(data), len(data2))
            assert data2 == data


class TestRandomDataFragment:
    def test_that_a_size_of_zero_raises_an_error(self):
        with pytest.raises(WoodblockError):
            RandomDataFragment(0)

    @pytest.mark.parametrize('size', (1, 2, 3, 512, 1024, 8192, 16384, 16385))
    def test_that_fragment_is_created_correctly(self, size):
        fragment = RandomDataFragment(size)
        assert fragment.size == size
        call_count = 0
        data = b''
        for chunk in fragment:
            call_count += 1
            data = b''.join((data, chunk))
        assert call_count == ceil(size / 8192)
        assert len(data) == size

    def test_that_the_metadata_is_correct(self):
        fragment = RandomDataFragment(512)
        meta = _replace_uuids(fragment.metadata)
        assert meta['file']['type'] == 'filler'
        assert meta['file']['path'] == 'random'
        assert meta['file']['size'] == 512
        assert meta['fragment']['number'] == 1
        assert meta['fragment']['size'] == 512
        assert meta['fragment']['file_offsets'] == {'start': 0, 'end': 512}

    @pytest.mark.parametrize('iterations', (2, 3, 4, 5, 10, 20, 50))
    def test_that_multiple_iterations_produce_same_bytes(self, iterations):
        fragment = RandomDataFragment(512)
        data = b''.join(c for c in fragment)
        for _ in range(iterations):
            assert b''.join(c for c in fragment) == data


class TestFileFragment:
    def test_that_fragment_is_created_correctly(self, path_test_file_512):
        fragment = FileFragment(File(path_test_file_512), 1, 0, 512)
        assert fragment.size == 512
        call_count = 0
        data = b''
        for chunk in fragment:
            call_count += 1
            data = b''.join((data, chunk))
        assert call_count == ceil(512 / 8192)
        assert len(data) == 512
        assert data == b'A' * 512

    def test_that_the_metadata_is_correct(self, path_test_file_512):
        fragment = FileFragment(File(path_test_file_512), 1, 0, 512)
        meta = _replace_uuids(fragment.metadata)
        assert meta == {
            'file': {'sha256': '32beecb58a128af8248504600bd203dcc676adf41045300485655e6b8780a01d',
                     'id': 'uuid', 'type': 'file', 'size': 512,
                     'path': str(path_test_file_512.relative_to(get_corpus()))},
            'fragment': {'sha256': '32beecb58a128af8248504600bd203dcc676adf41045300485655e6b8780a01d', 'size': 512,
                         'number': 1, 'file_offsets': {'start': 0, 'end': 512}}
        }

    def test_that_the_correct_hash_is_computed(self, path_test_file_4k):
        assert FileFragment(File(path_test_file_4k), 1, 0,
                            1024).hash == '06aed7f43b72ab019f06f2cbf0a94237ad29cc36d2c91e27a9d3e734c90b665b'
        assert FileFragment(File(path_test_file_4k), 1, 1024,
                            2048).hash == 'dbbed6c65649c043888d421b8a950374faa0f5f3af28a12f9a2224d3b7c3fd9a'
        assert FileFragment(File(path_test_file_4k), 1, 2048,
                            3072).hash == '036c079fccd6a7527eb31f9dc7aaeb1cac70796c1a4a1627b81309ee018d11da'
        assert FileFragment(File(path_test_file_4k), 1, 3072,
                            4096).hash == '57434187458631358bbf7241a53990c77be44fa37194ae149b32427c5bc5fcac'


class FakeRng:
    def __init__(self):
        self._seed = None

    def seed(self, seed):
        self._seed = seed

    @staticmethod
    def bytes(size):
        return b'A' * size


def _replace_uuids(metadata):
    metadata['file']['id'] = 'uuid'
    return metadata
