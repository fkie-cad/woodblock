"""File related classes and functions."""
import itertools
import math
import pathlib
import random
import typing
from operator import attrgetter
from uuid import uuid4

import numpy as np

import woodblock.utils
from woodblock.errors import WoodblockError, InvalidFragmentationPointError
from woodblock.fragments import FileFragment

_CORPUS = None


def corpus(path):
    """Set the file corpus.

    Args:
        path: Path to the corpus directory.
    """
    global _CORPUS  # pylint: disable=global-statement
    if isinstance(path, str):
        _CORPUS = pathlib.Path(path)
    elif isinstance(path, pathlib.Path):
        _CORPUS = path
    elif path is None:
        _CORPUS = None
    else:
        raise WoodblockError('Unsupported object type for corpus.')


def get_corpus() -> pathlib.Path:
    """Return the path to the test file corpus."""
    if _CORPUS is None:
        raise WoodblockError('No corpus specified.')
    return _CORPUS


class File:
    """This class represents an actual file of the test file corpus.

    Args:
        path: Path to the file on disk.
    """

    def __init__(self, path: pathlib.Path):
        self._path = get_corpus() / path
        if not self.path.exists():
            raise FileNotFoundError(path.name)
        self._size = self._path.stat().st_size
        self._id = uuid4().hex
        self._hash = None
        if self._size < 1:
            raise WoodblockError('File contains no data!')

    def __str__(self):
        return ': '.join((self.__repr__(), self._path))  # pragma: no cover

    @property
    def hash(self) -> str:
        """Return the SHA-256 hash of the file as hexadecimal string."""
        if self._hash is None:
            self._hash = woodblock.utils.hash_file(self._path)
        return self._hash

    @property
    def id(self) -> str:  # pylint: disable=invalid-name
        """Return the ID of the file."""
        return self._id

    @property
    def path(self) -> pathlib.Path:
        """Return the path of the file relative to the corpus path."""
        return self._path

    @property
    def size(self) -> int:
        """Return the file size."""
        return self._size

    def as_fragment(self):
        """Return the file as a single fragment."""
        return FileFragment(file=self, fragment_number=1, start_offset=0, end_offset=self._size)

    def max_fragments(self, block_size):
        """Return the maximal number of fragments which can be created for a given block size."""
        if block_size < 1:
            raise WoodblockError('Block size has to be at least 1.')
        return math.ceil(self.size / block_size)

    def fragment(self, fragmentation_points: typing.Sequence, block_size: int = 512) -> list:
        """Fragment the file at the given ``fragmentation_points`` using the given ``block_size``.

        This method fragments the current file at the specified ``fragmentation_points``. The fragmentation points are
        multiplied with the given ``block_size`` in order to compute the actual fragmentation offsets.

        Args:
            fragmentation_points: A sequence of fragmentation points.
            block_size: The block size to use.
        """
        if not fragmentation_points:
            return [self.as_fragment(), ]
        self._validate_fragmentation_points(fragmentation_points, block_size)
        fragments = list()
        frag_points = sorted(fragmentation_points)
        fragment_number = 2
        len_frag_points = len(frag_points)
        for i in range(len_frag_points):
            if i == 0:
                fragments.append(FileFragment(self, 1, 0, frag_points[0] * block_size))
            if i < len_frag_points - 1:
                fragments.append(
                    FileFragment(self, fragment_number, frag_points[i] * block_size, frag_points[i + 1] * block_size))
            if i == len_frag_points - 1:
                fragments.append(
                    FileFragment(self, len_frag_points + 1, frag_points[i] * block_size, self._size))
            fragment_number += 1
        return fragments

    def fragment_randomly(self, num_fragments: int = None, block_size: int = 512) -> list:
        """Fragment the file at random fragmentation points.

        This method fragments the current file into ``num_fragments`` fragments. The fragmentation points are chosen
        randomly. If `num_fragments` is None, then the number of fragments is chosen randomly between 1 and the maximum
        number of fragments for the given `block_size`.

        Args:
            num_fragments: Number of fragments to create.
            block_size: Block size to use.
        """
        blocks_in_file = math.floor(self._size / block_size)
        if num_fragments is None:
            num_fragments = random.randint(1, blocks_in_file)  # nosec
        if self._size < block_size:
            raise InvalidFragmentationPointError(
                f'File "{self.path}" is too small to be fragmented with a block size of {block_size}!')
        if num_fragments < 1:
            raise InvalidFragmentationPointError('Number of fragments has to be at least 1.')
        if num_fragments > blocks_in_file and not (
                num_fragments == blocks_in_file + 1 and self._size % block_size != 0):
            raise InvalidFragmentationPointError('Number of fragments is too large.')
        if num_fragments == 1:
            return [self.as_fragment(), ]
        max_frag_point = blocks_in_file
        if self._size % block_size != 0:
            max_frag_point += 1
        return self.fragment(random.sample(range(1, max_frag_point), num_fragments - 1), block_size)

    def fragment_evenly(self, num_fragments: int, block_size: int = 512) -> list:
        """Fragment the file evenly into ``num_fragment`` fragments.

        This method fragments the current file into ``num_fragments`` fragments. The fragmentation points are chosen
        so that each fragment will be of the same size (if possible).

        Args:
            num_fragments: Number of fragments to create.
            block_size: Block size to use.
        """
        blocks_in_file = math.floor(self._size / block_size)
        if self._size < block_size:
            raise InvalidFragmentationPointError(
                f'File is too small to be fragmented with a block size of {block_size}!')
        if num_fragments < 1:
            raise InvalidFragmentationPointError('Number of fragments has to be at least 1.')
        if num_fragments > blocks_in_file and not (
                num_fragments == blocks_in_file + 1 and self._size % block_size != 0):
            raise InvalidFragmentationPointError('Number of fragments is too large.')
        if num_fragments == 1:
            return [self.as_fragment(), ]

        if num_fragments == blocks_in_file + 1 and self._size % block_size != 0:
            frag_points = range(1, blocks_in_file + 1)
        elif num_fragments == blocks_in_file:
            frag_points = range(1, blocks_in_file)
        else:
            frag_points = tuple(
                int(x[-1]) for x in np.array_split(np.array(range(1, blocks_in_file + 1)), num_fragments))[:-1]
        return self.fragment(frag_points, block_size)

    def _validate_fragmentation_points(self, fragmentation_points, block_size):
        if self._size < block_size:
            raise InvalidFragmentationPointError(
                f'File is too small to be fragmented with a block size of {block_size}!')
        if not all(isinstance(x, int) for x in fragmentation_points):
            raise InvalidFragmentationPointError('Fragmentation points have to be integers.')
        if 0 in fragmentation_points:
            raise InvalidFragmentationPointError('0 is not a valid fragmentation point.')
        if not all(f < math.ceil(self._size / block_size) for f in fragmentation_points):
            raise InvalidFragmentationPointError('Fragmentation point is too large.')
        if not all(f > 0 for f in fragmentation_points):
            raise InvalidFragmentationPointError('Fragmentation points have to be positive integers.')
        if len(set(fragmentation_points)) < len(fragmentation_points):
            raise InvalidFragmentationPointError('Duplicate fragmentation points are not allowed.')


def draw_files(path: pathlib.Path = None, number_of_files: int = 1, unique: bool = False, min_size: int = 0) -> list:
    """Choose random files from the file corpus.

    If `path` is None, the complete corpus will be considered. If it set to a path relative to the corpus, then only
    files in this directory (and its subdirectories) are considered.

    Args:
        path: The directory relative to the file corpus from which the file should be chosen.
        number_of_files: The number of files to draw.
        unique: If set to True, the resulting list will contain no duplicates.
        min_size: Minimal file size of the selected files.
    """
    if number_of_files < 1:
        raise WoodblockError('Number of files has to be at least 1.')
    start_path = get_corpus()
    if path is not None:
        start_path = start_path / path
    candidates = woodblock.utils.get_file_list(start_path, min_size)
    if not candidates:
        raise WoodblockError(f'Given path does not contain enough files with a minimal size of {min_size}.')
    if unique:
        try:
            return list(File(f) for f in random.sample(candidates, k=number_of_files))
        except ValueError:
            raise WoodblockError('Not enough unique files to choose from.')
    else:
        return list(File(f) for f in random.choices(candidates, k=number_of_files))


def draw_fragmented_files(path: pathlib.Path = None, number_of_files: int = 1, block_size: int = 512,
                          min_fragments: int = 1, max_fragments: int = 4) -> list:
    """Choose random files from ``path`` and fragment them randomly.

    ``draw_fragmented_files`` chooses ``number_of_files`` files from the given ``path`` and fragments them at random
    fragmentation points. The number of fragments per file will be between ``min_fragments`` and ``max_fragments``
    (both numbers included, i.e. min_fragments <= number of fragments <= max_fragments).

    The result is a list of fragment lists, e.g. [ [f1.1, f1.2, f1.3], [f2.1, ], [f3.1, f3.2] ].

    If `path` is None, the complete corpus will be considered. If it set to a path relative to the corpus, then only
    files in this directory (it its subdirectories) are considered.

    Note that there is no guarantee that a file is not chosen more than once.

    Args:
        path: Directory relative to the corpus to choose the files from.
        number_of_files: Number of files to select.
        block_size: The block size to be used when fragmenting the files.
        min_fragments: Minimal number of fragments.
        max_fragments: Maximal number of fragments.
    """
    if min_fragments > max_fragments:
        raise WoodblockError('min_fragments has to be <= max_fragments.')
    files = draw_files(path, number_of_files, min_size=block_size * min_fragments)
    frags = list()
    for file in files:
        num_frags = random.randint(min_fragments, min(max_fragments, file.max_fragments(block_size)))  # nosec
        frags.append(file.fragment_randomly(num_frags, block_size))
    return frags


def intertwine_randomly(path: pathlib.Path = None, number_of_files: int = 2, block_size: int = 512,
                        min_fragments: int = 1, max_fragments: int = 4) -> list:
    """Choose random files from ``path`` and intertwine them randomly.

    ``intertwine_randomly`` chooses ``number_of_files`` files from the given ``path``, fragments them at random
    fragmentation points, and intertwines them randomly. The number of fragments per file will be between
    ``min_fragments`` and ``max_fragments`` (both numbers included, i.e. min_fragments <= number of fragments
    <= max_fragments).

    The result is a list of fragments, e.g. [f3.1, f1.1, f3.2, f2.1, f1.2, f2.2, f1.3].

    The function ensures that there will in fact be unique ``number_of_files`` files. Moreover, the function
    guarantees that two fragments of the same file will not be at consecutive list positions. Finally, the fragments
    of each file will be stored in order.

    Args:
        path: Directory to choose the files from.
        number_of_files: Number of files to select.
        block_size: The block size to be used when fragmenting the files.
        min_fragments: Minimal number of fragments.
        max_fragments: Maximal number of fragments.
    """
    if min_fragments > max_fragments:
        raise WoodblockError('min_fragments has to be <= max_fragments.')
    if number_of_files < 2:
        raise WoodblockError('Number of files has to be at least 2.')

    files = draw_files(path, number_of_files, unique=True, min_size=block_size * min_fragments)

    if min_fragments == max_fragments:
        frags = list(itertools.chain.from_iterable(zip(files[0].fragment_randomly(min_fragments, block_size),
                                                       files[1].fragment_randomly(min_fragments, block_size))))
        for file in files[2:]:
            current_file_frags = file.fragment_randomly(min_fragments, block_size)
            _insert_at_slots(frags, current_file_frags, _select_free_slots(len(frags) + 1, min_fragments))
        return frags
    files = sorted(files, key=attrgetter('size'))
    frags_file_1 = _fragment_first_file(files[0], block_size, min_fragments, max_fragments)
    frags_file_2 = _fragment_second_file(files[1], block_size, min_fragments, max_fragments, len(frags_file_1))
    frags = _merge_fragments_of_first_two_files(frags_file_1, frags_file_2)
    min_frags = max(min_fragments, 1)
    for file in files[2:]:
        free_slots = len(frags) + 1
        max_frags = min(max_fragments, file.max_fragments(block_size), free_slots)
        num_frags = random.randint(min_frags, max_frags)  # nosec
        current_file_frags = list(reversed(file.fragment_randomly(num_frags, block_size)))
        _insert_at_slots(frags, current_file_frags, _select_free_slots(free_slots, num_frags))
    return frags


def _merge_fragments_of_first_two_files(frags_file_1, frags_file_2):  # pylint: disable=invalid-name
    frags = frags_file_1[:]
    frags_2 = list(reversed(frags_file_2))
    start = _get_start_index_for_fragments_of_second_file(len(frags_file_1), len(frags_file_2))
    for i in range(len(frags_2)):
        frags.insert(start + 2 * i, frags_2.pop())
    return frags


def _get_start_index_for_fragments_of_second_file(num_frags_file_1, num_frags_file_2):  # pylint: disable=invalid-name
    if num_frags_file_2 == num_frags_file_1 - 1:
        return 1
    if num_frags_file_2 == num_frags_file_1 + 1:
        return 0
    return random.randint(0, 1)  # nosec


def _fragment_first_file(file_1, block_size, min_fragments, max_fragments):
    num_frags = random.randint(max(min_fragments, 1), min(max_fragments, file_1.max_fragments(block_size)))  # nosec
    return file_1.fragment_randomly(num_frags, block_size)


def _fragment_second_file(file_2, block_size, min_fragments, max_fragments, num_fragments_file_1):
    num_frags = random.randint(max(min_fragments, num_fragments_file_1 - 1),  # nosec
                               min(max_fragments, num_fragments_file_1 + 1, file_2.max_fragments(block_size)))
    return file_2.fragment_randomly(num_frags, block_size)


def _insert_at_slots(frag_list, new_fragments, slots):
    new_frags = list(reversed(new_fragments))
    for i, slot in enumerate(slots):
        frag_list.insert(slot + i, new_frags.pop())


def _select_free_slots(num_slots_available, num_slots):
    return sorted(random.sample(range(num_slots_available), k=num_slots))
