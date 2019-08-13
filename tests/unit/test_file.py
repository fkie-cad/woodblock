import pathlib
from operator import itemgetter
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

import woodblock
from woodblock.errors import WoodblockError, InvalidFragmentationPointError
from woodblock.file import draw_files, File, intertwine_randomly, draw_fragmented_files
from woodblock.fragments import FileFragment


class TestFile:
    def test_that_an_error_is_raised_when_no_corpus_is_set(self, path_test_file_4k):
        woodblock.file.corpus(None)
        with pytest.raises(WoodblockError):
            File(path_test_file_4k)

    def test_that_a_non_existing_file_raises_an_error(self):
        with pytest.raises(FileNotFoundError):
            File(pathlib.Path('/nonexisting'))

    def test_that_an_empty_file_raises_an_error(self):
        with NamedTemporaryFile() as tmp:
            with pytest.raises(WoodblockError):
                File(pathlib.Path(tmp.name))

    @pytest.mark.parametrize('block_size,expected_frags', (
            (1, 4096), (2, 2048), (512, 8), (1024, 4), (2048, 2), (4096, 1), (4097, 1), (10000, 1)
    ))
    def test_that_max_fragments_returns_correct_number(self, block_size, expected_frags, path_test_file_4k):
        assert File(path_test_file_4k).max_fragments(block_size) == expected_frags

    @pytest.mark.parametrize('block_size', (0, -1, -2, -1000))
    def test_that_max_fragments_raises_for_invalid_block_sizes(self, block_size, path_test_file_4k):
        with pytest.raises(WoodblockError):
            File(path_test_file_4k).max_fragments(block_size)


class TestFragment:
    def test_that_a_too_small_file_cannot_be_fragmented(self, path_test_file_4k):
        with pytest.raises(InvalidFragmentationPointError):
            File(path_test_file_4k).fragment((1,), File(path_test_file_4k).size * 2)

    def test_that_an_empty_list_of_fragmentation_points_return_a_single_fragment(self, path_test_file_4k):
        frags = File(path_test_file_4k).fragment(tuple(), block_size=512)
        assert len(frags) == 1
        assert _replace_uuids(frags[0].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 1, 0, 4096).metadata)

    def test_that_a_file_can_be_fragmented_into_two_fragments(self, path_test_file_4k):
        frags = File(path_test_file_4k).fragment((1,), block_size=512)
        assert len(frags) == 2
        assert _replace_uuids(frags[0].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 1, 0, 512).metadata)
        assert _replace_uuids(frags[1].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 2, 512, 4096).metadata)

    def test_that_a_file_can_be_fragmented_into_three_fragments(self, path_test_file_4k):
        frags = File(path_test_file_4k).fragment((1, 3), block_size=512)
        assert len(frags) == 3
        assert _replace_uuids(frags[0].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 1, 0, 512).metadata)
        assert _replace_uuids(frags[1].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 2, 512, 1536).metadata)
        assert _replace_uuids(frags[2].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 3, 1536, 4096).metadata)

    def test_that_a_file_can_be_fragmented_into_four_fragments(self, path_test_file_4k):
        frags = File(path_test_file_4k).fragment((1, 3, 7), block_size=512)
        assert len(frags) == 4
        assert _replace_uuids(frags[0].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 1, 0, 512).metadata)
        assert _replace_uuids(frags[1].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 2, 512, 1536).metadata)
        assert _replace_uuids(frags[2].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 3, 1536, 3584).metadata)
        assert _replace_uuids(frags[3].metadata) == _replace_uuids(
            FileFragment(File(path_test_file_4k), 4, 3584, 4096).metadata)

    @pytest.mark.parametrize('fragmentation_points', (
            (1, 'a', 3),
            (0,), (0, 1, 2), (1, 0, 2), (1, 2, 0),
            (8,), (8, 1, 2), (1, 8, 2), (1, 2, 8), (1, 9, 5), (11, 12, 13, 14),
            (-1,), (1, -2, 3), (1, 2, -3), (-1, 2, 3),
            (1, 1), (1, 2, 3, 2)
    ))
    def test_that_invalid_fragmentation_points_raise_an_error(self, fragmentation_points, path_test_file_4k):
        f = File(path_test_file_4k)
        with pytest.raises(InvalidFragmentationPointError):
            f.fragment(fragmentation_points)


class TestFragmentFragmentRandomly:
    def test_that_a_too_small_file_cannot_be_fragmented(self, path_test_file_4k):
        with pytest.raises(InvalidFragmentationPointError):
            File(path_test_file_4k).fragment_randomly(2, File(path_test_file_4k).size * 2)

    @pytest.mark.parametrize('num_fragments', (0, 9, 10, 13))
    def test_that_invalid_num_fragments_raises_an_error(self, num_fragments, path_test_file_4k):
        with pytest.raises(InvalidFragmentationPointError):
            File(path_test_file_4k).fragment_randomly(num_fragments, 512)

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4, 5, 7, 8))
    def test_that_the_correct_number_of_fragments_is_generated(self, num_fragments, path_test_file_4k):
        frags = File(path_test_file_4k).fragment_randomly(num_fragments=num_fragments, block_size=512)
        assert len(frags) == num_fragments

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4))
    def test_that_the_correct_number_of_fragments_is_generated_for_2k_file(self, num_fragments, path_test_file_2000):
        frags = File(path_test_file_2000).fragment_randomly(num_fragments=num_fragments, block_size=512)
        assert len(frags) == num_fragments


class TestFragmentFragmentEvenly:
    def test_that_a_too_small_file_cannot_be_fragmented(self, path_test_file_4k):
        with pytest.raises(InvalidFragmentationPointError):
            File(path_test_file_4k).fragment_evenly(2, File(path_test_file_4k).size * 2)

    @pytest.mark.parametrize('num_fragments', (0, 9, 10, 13))
    def test_that_invalid_num_fragments_raises_an_error(self, num_fragments, path_test_file_4k):
        with pytest.raises(InvalidFragmentationPointError):
            File(path_test_file_4k).fragment_evenly(num_fragments, 512)

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4, 5, 7, 8))
    def test_that_the_correct_number_of_fragments_is_generated(self, num_fragments, path_test_file_4k):
        frags = File(path_test_file_4k).fragment_evenly(num_fragments=num_fragments, block_size=512)
        assert len(frags) == num_fragments

    @pytest.mark.parametrize('block_size, num_fragments, expected_frag_offsets', (
            (512, 1, ((0, 4096),)),
            (512, 2, ((0, 2048), (2048, 4096))),
            (512, 3, ((0, 1536), (1536, 3072), (3072, 4096))),
            (512, 4, ((0, 1024), (1024, 2048), (2048, 3072), (3072, 4096))),
            (512, 5, ((0, 1024), (1024, 2048), (2048, 3072), (3072, 3584), (3584, 4096))),
            (512, 6, ((0, 1024), (1024, 2048), (2048, 2560), (2560, 3072), (3072, 3584), (3584, 4096))),
            (512, 7, ((0, 1024), (1024, 1536), (1536, 2048), (2048, 2560), (2560, 3072), (3072, 3584), (3584, 4096))),
            (512, 8, ((0, 512), (512, 1024), (1024, 1536), (1536, 2048), (2048, 2560), (2560, 3072), (3072, 3584),
                      (3584, 4096))),
            (500, 1, ((0, 4096),)),
            (500, 2, ((0, 2000), (2000, 4096))),
            (500, 3, ((0, 1500), (1500, 3000), (3000, 4096))),
            (500, 4, ((0, 1000), (1000, 2000), (2000, 3000), (3000, 4096))),
            (500, 5, ((0, 1000), (1000, 2000), (2000, 3000), (3000, 3500), (3500, 4096))),
            (500, 6, ((0, 1000), (1000, 2000), (2000, 2500), (2500, 3000), (3000, 3500), (3500, 4096))),
            (500, 7, ((0, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 3000), (3000, 3500), (3500, 4096))),
            (500, 8, ((0, 500), (500, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 3000), (3000, 3500),
                      (3500, 4096))),
            (500, 9, ((0, 500), (500, 1000), (1000, 1500), (1500, 2000), (2000, 2500), (2500, 3000), (3000, 3500),
                      (3500, 4000), (4000, 4096))),

    ))
    def test_that_the_file_is_split_evenly(self, block_size, num_fragments, expected_frag_offsets, path_test_file_4k):
        frags = File(path_test_file_4k).fragment_evenly(num_fragments=num_fragments, block_size=block_size)
        frag_offsets = tuple(itemgetter('start', 'end')(x.metadata['fragment']['file_offsets']) for x in frags)
        assert frag_offsets == expected_frag_offsets

    @pytest.mark.parametrize('num_fragments', (1, 2, 3, 4, 5, 6, 7, 8))
    def test_that_all_fragments_have_the_same_id(self, num_fragments, path_test_file_4k):
        frags = File(path_test_file_4k).fragment_evenly(num_fragments=num_fragments, block_size=512)
        for i in range(len(frags)):
            assert frags[i - 1].metadata['file']['id'] == frags[i].metadata['file']['id']


class TestDrawFiles:
    def test_that_an_error_is_raised_when_the_path_is_empty(self):
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(WoodblockError):
                draw_files(tmpdir)

    @pytest.mark.parametrize('num_files', (1, 2, 3, 5, 100, 500))
    def test_that_the_correct_number_of_files_gets_drawn(self, num_files, test_corpus_path):
        assert len(draw_files(test_corpus_path, num_files)) == num_files

    @pytest.mark.parametrize('num_files', (-100, -10, -9, -5, -4, -3, -2, -1, 0))
    def test_that_invalid_number_of_files_raises_an_error(self, num_files, test_data_path):
        with pytest.raises(WoodblockError):
            draw_files(test_data_path, num_files)

    @pytest.mark.parametrize('path', ('nonexistent', '/nonexistent'))
    def test_that_invalid_paths_raise_an_error(self, path):
        with pytest.raises(WoodblockError):
            draw_files(pathlib.Path(path), number_of_files=1)

    @pytest.mark.slow
    def test_that_consecutive_calls_with_same_seed_return_same_files(self, test_corpus_path):
        seed = 13
        num_files = 100
        woodblock.random.seed(seed)
        files = draw_files(test_corpus_path, num_files)
        for _ in range(1000):
            woodblock.random.seed(seed)
            for f1, f2 in zip(files, draw_files(test_corpus_path, num_files)):
                assert _replace_uuid(f1.as_fragment().metadata) == _replace_uuid(f2.as_fragment().metadata)

    @pytest.mark.parametrize('num_files', (1, 2, 3, 4))
    def test_that_files_are_unique_when_desired(self, num_files, test_corpus_path):
        assert len(draw_files(test_corpus_path, num_files, unique=True)) == num_files

    @pytest.mark.parametrize('num_files', (8, 9, 10))
    def test_that_not_enough_unique_files_raise_an_error(self, num_files, test_corpus_path):
        with pytest.raises(WoodblockError):
            print(draw_files(test_corpus_path, num_files, unique=True))


class TestDrawFragmentedFiles:
    def test_that_an_error_is_raised_when_the_path_is_empty(self):
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(WoodblockError):
                draw_fragmented_files(tmpdir)

    @pytest.mark.parametrize('num_files', (1, 2, 3, 5, 100, 500))
    def test_that_the_correct_number_of_files_gets_drawn(self, num_files, test_corpus_path):
        assert len(draw_fragmented_files(test_corpus_path, num_files)) == num_files

    @pytest.mark.parametrize('num_files', (-100, -10, -9, -5, -4, -3, -2, -1, 0))
    def test_that_invalid_number_of_files_raises_an_error(self, num_files, test_corpus_path):
        with pytest.raises(WoodblockError):
            draw_fragmented_files(test_corpus_path, num_files)

    @pytest.mark.parametrize('path', ('nonexistent', '/nonexistent'))
    def test_that_invalid_paths_raise_an_error(self, path):
        with pytest.raises(WoodblockError):
            draw_fragmented_files(pathlib.Path(path), number_of_files=1)

    @pytest.mark.slow
    def test_that_consecutive_calls_with_same_seed_return_same_files(self, test_corpus_path):
        seed = 13
        num_files = 100
        woodblock.random.seed(seed)
        files = draw_fragmented_files(test_corpus_path, num_files)
        for _ in range(1000):
            woodblock.random.seed(seed)
            for files1, files2 in zip(files, draw_fragmented_files(test_corpus_path, num_files)):
                for frags1, frags2 in zip(files1, files2):
                    assert _replace_uuid(frags1.metadata) == _replace_uuid(frags2.metadata)

    @pytest.mark.parametrize('min_frags, max_frags', ((2, 1), (3, 2), (10, 5)))
    def test_that_min_frags_larger_than_max_frags_raises_an_error(self, min_frags, max_frags, test_corpus_path):
        with pytest.raises(WoodblockError):
            draw_fragmented_files(test_corpus_path, 2, min_fragments=min_frags, max_fragments=max_frags)

    @pytest.mark.parametrize('num_files, min_frags, max_frags', (
            (7, 1, 1), (7, 1, 2), (7, 1, 3), (8, 1, 3), (6, 2, 2), (6, 2, 4), (4, 4, 4), (4, 4, 10), (100, 2, 10)))
    def test_that_the_correct_number_of_fragments_is_created(self, num_files, min_frags, max_frags, test_corpus_path):
        for i in range(1, num_files + 1):
            files = draw_fragmented_files(test_corpus_path, number_of_files=i, min_fragments=min_frags,
                                          max_fragments=max_frags)
            assert len(files) == i


class TestIntertwineRandomly:
    def test_that_an_error_is_raised_when_the_path_is_empty(self):
        with TemporaryDirectory() as tmpdir:
            with pytest.raises(WoodblockError):
                intertwine_randomly(tmpdir)

    @pytest.mark.parametrize('path', ('nonexistent', '/nonexistent'))
    def test_that_invalid_paths_raise_an_error(self, path):
        with pytest.raises(WoodblockError):
            intertwine_randomly(pathlib.Path(path), number_of_files=2)

    @pytest.mark.parametrize('num_files', (-100, -10, -9, -5, -4, -3, -2, -1, 0, 1))
    def test_that_invalid_number_of_files_raises_an_error(self, num_files, test_corpus_path):
        with pytest.raises(WoodblockError):
            intertwine_randomly(test_corpus_path, num_files)

    @pytest.mark.parametrize('num_files', (2, 3, 4))
    def test_that_the_correct_number_of_files_gets_drawn(self, num_files, test_corpus_path):
        frags = intertwine_randomly(test_corpus_path, num_files)
        assert _get_number_of_files_from_fragment_list(frags) == num_files

    @pytest.mark.parametrize('num_files, min_frags, max_frags', (
            (2, 1, 10), (2, 1, 100), (2, 2, 10), (2, 2, 2), (2, 1, 1), (2, 3, 6), (2, 5, 6),
            (3, 1, 10), (3, 2, 10), (3, 2, 2),
            (4, 1, 1), (4, 1, 10), (4, 2, 10), (4, 3, 3)
    ))
    def test_that_consecutive_fragments_are_from_different_files(self, num_files, min_frags, max_frags,
                                                                 test_corpus_path):
        frags = intertwine_randomly(test_corpus_path, num_files, min_fragments=min_frags, max_fragments=max_frags)
        for i in range(1, len(frags)):
            assert frags[i - 1].metadata['file']['id'] != frags[i].metadata['file']['id']

    @pytest.mark.parametrize('min_frags, max_frags', ((2, 1), (3, 2), (10, 5)))
    def test_that_min_frags_larger_than_max_frags_raises_an_error(self, min_frags, max_frags, test_corpus_path):
        with pytest.raises(WoodblockError):
            intertwine_randomly(test_corpus_path, 2, min_fragments=min_frags, max_fragments=max_frags)


def _get_number_of_files_from_fragment_list(fragments):
    files = set(f.metadata['file']['id'] for f in fragments)
    print(files)
    return len(files)


def _replace_uuids(metadata):
    metadata['file']['id'] = 'uuid'
    return metadata


def _replace_uuid(metadata):
    metadata['file']['id'] = 'uuid'
    return metadata


class FakeFile:
    def __init__(self, size):
        self._size = size

    @property
    def size(self):
        return self._size
