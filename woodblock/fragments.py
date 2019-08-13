"""This module contains the different fragment classes which can be used in file carving scenarios."""

import hashlib
from uuid import uuid4

import woodblock.datagen
from woodblock.errors import WoodblockError


class FillerFragment:
    """A filler fragment.

    A filler fragment is a fragment containing synthetic data (e.g. random data). It can be used to simulate wiped
    areas or areas with random data.
    """

    def __init__(self, size, data_generator=None, chunk_size=8192):
        self._size = size
        self._chunk_size = min(size, chunk_size)
        self._orig_chunk_size = chunk_size
        if data_generator is None:
            data_generator = woodblock.datagen.Random()
        self._generate_data = data_generator
        self._bytes_read = 0
        if self._size < 1:
            raise WoodblockError('Fragments must not be empty!')
        self._hash = None
        self._hasher = hashlib.sha256()
        self._id = uuid4().hex

    @property
    def size(self):
        """Return the size of the fragment."""
        return self._size

    @property
    def hash(self):
        """Return the SHA-256 digest as hexadecimal string."""
        if self._hash is None:
            self._hash = self._compute_hash()
        return self._hash

    @property
    def metadata(self) -> dict:
        """Return the fragment metadata."""
        if self._hash is None:
            self._hash = self._compute_hash()
        return {'file': {'type': 'filler', 'sha256': self.hash, 'size': self.size, 'path': str(self._generate_data),
                         'id': self._id},
                'fragment': {'sha256': self.hash, 'size': self.size, 'number': 1,
                             'file_offsets': {'start': 0, 'end': self.size}}}

    def __iter__(self):
        self._hasher = hashlib.sha256()
        return self

    def __next__(self):
        if self._chunk_size <= 0:
            self._reset_state()
            raise StopIteration()
        chunk = self._generate_data(min(self._chunk_size, self._size))
        self._bytes_read += self._chunk_size
        self._chunk_size = max(0, min(self._chunk_size, self._size - self._bytes_read))
        if self._hash is None:
            self._hasher.update(chunk)
        return chunk

    def _compute_hash(self):
        hasher = hashlib.sha256()
        for chunk in self:
            hasher.update(chunk)
        return hasher.hexdigest()

    def _reset_state(self):
        if self._hash is None:
            self._hash = self._hasher.hexdigest()
        self._chunk_size = self._orig_chunk_size


class ZeroesFragment(FillerFragment):
    """A fragment filled completely with zero bytes (0x00)."""

    def __init__(self, size, chunk_size=8192):
        super().__init__(size=size, data_generator=woodblock.datagen.Zeroes(), chunk_size=chunk_size)


class RandomDataFragment(FillerFragment):
    """A fragment filled with random bytes."""

    def __init__(self, size, chunk_size=8192):
        self._rng = woodblock.datagen.Random()
        super().__init__(size=size, data_generator=self._rng, chunk_size=chunk_size)

    def _reset_state(self):
        super()._reset_state()
        self._rng.reset()


class FileFragment:
    """A fragment of an actual file."""

    def __init__(self, file, fragment_number, start_offset, end_offset, chunk_size=8192):
        self._file = file
        self._number = fragment_number
        self._start_offset = start_offset
        self._end_offset = end_offset
        self._size = end_offset - start_offset
        self._hash = None
        self._hasher = hashlib.sha256()
        self._chunk_size = chunk_size
        self._orig_chunk_size = chunk_size
        self._bytes_read = 0
        self._file_handle = None

    @property
    def size(self):
        """Return the size of the fragment."""
        return self._size

    @property
    def hash(self):
        """Return the SHA-256 digest as hexadecimal string."""
        if self._hash is None:
            self._compute_hash()
        return self._hash

    def __iter__(self):
        self._hasher = hashlib.sha256()
        self._file_handle = open(self._file.path, 'rb')
        self._file_handle.seek(self._start_offset)
        return self

    def __next__(self):
        if self._chunk_size <= 0:
            self._reset_state()
            raise StopIteration()
        chunk = self._file_handle.read(min(self._chunk_size, self._size))
        self._bytes_read += len(chunk)
        self._chunk_size = max(0, min(self._chunk_size, self._size - self._bytes_read))
        if self._hash is None:
            self._hasher.update(chunk)
        return chunk

    @property
    def metadata(self):
        """Return the fragment metadata."""
        if self._hash is None:
            self._compute_hash()
        return {'file': {'type': 'file', 'sha256': self._file.hash, 'size': self._file.size,
                         'path': str(self._file.path.relative_to(woodblock.file.get_corpus())), 'id': self._file.id},
                'fragment': {'sha256': self.hash, 'size': self.size, 'number': self._number,
                             'file_offsets': {'start': self._start_offset, 'end': self._end_offset}}}

    def _compute_hash(self):
        for _ in self:
            pass

    def _reset_state(self):
        if self._hash is None:
            self._hash = self._hasher.hexdigest()
        self._file_handle.close()
        self._chunk_size = self._orig_chunk_size
