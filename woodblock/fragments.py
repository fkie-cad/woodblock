"""This module contains the different fragment classes which can be used in file carving scenarios."""

import hashlib
from uuid import uuid4

import woodblock.datagen
import woodblock.file
from woodblock.errors import WoodblockError


class FillerFragment:
    """A filler fragment.

    A filler fragment is a fragment containing synthetic data (e.g. random data). It can be used to simulate wiped
    areas or areas with random data.
    """

    def __init__(self, size, data_generator=None, chunk_size=8192):
        if size < 1:
            raise WoodblockError('Fragments must not be empty!')
        self._size = size
        self._chunk_size = chunk_size
        if data_generator is None:
            data_generator = woodblock.datagen.Random()
        self._generate_data = data_generator
        self._hash = None
        self._id = uuid4().hex

    @property
    def size(self):
        """Return the size of the fragment."""
        return self._size

    @property
    def hash(self):
        """Return the SHA-256 digest as hexadecimal string."""
        if self._hash is None:
            for _ in self:
                pass
        return self._hash

    @property
    def metadata(self) -> dict:
        """Return the fragment metadata."""
        return {
            'file': {
                'type': 'filler',
                'sha256': self.hash,
                'size': self.size,
                'path': str(self._generate_data),
                'id': self._id,
            },
            'fragment': {
                'sha256': self.hash,
                'size': self.size,
                'number': 1,
                'file_offsets': {'start': 0, 'end': self.size},
            },
        }

    def __iter__(self):
        # A fresh generator per iteration keeps all iteration state local, so re-iterating always
        # reproduces the complete fragment. Resetting the data generator (when it supports it) makes
        # every pass regenerate byte-identical data regardless of iteration order, so the recorded
        # hash always matches the bytes written.
        if hasattr(self._generate_data, 'reset'):
            self._generate_data.reset()
        hasher = hashlib.sha256() if self._hash is None else None
        remaining = self._size
        while remaining > 0:
            chunk = self._generate_data(min(self._chunk_size, remaining))
            remaining -= len(chunk)
            if hasher is not None:
                hasher.update(chunk)
            yield chunk
        if hasher is not None:
            self._hash = hasher.hexdigest()


class ZeroesFragment(FillerFragment):
    """A fragment filled completely with zero bytes (0x00)."""

    def __init__(self, size, chunk_size=8192):
        super().__init__(size=size, data_generator=woodblock.datagen.Zeroes(), chunk_size=chunk_size)


class RandomDataFragment(FillerFragment):
    """A fragment filled with random bytes."""

    def __init__(self, size, chunk_size=8192):
        self._rng = woodblock.datagen.Random()
        # The base FillerFragment.__iter__ resets the data generator on every iteration, so the
        # RNG is re-seeded to its initial seed each pass and the random data is reproduced
        # byte-for-byte regardless of iteration order or of any other generator.
        super().__init__(size=size, data_generator=self._rng, chunk_size=chunk_size)


class FileFragment:
    """A fragment of an actual file."""

    def __init__(self, file, fragment_number, start_offset, end_offset, chunk_size=8192):
        self._file = file
        self._number = fragment_number
        self._start_offset = start_offset
        self._end_offset = end_offset
        self._size = end_offset - start_offset
        self._hash = None
        self._chunk_size = chunk_size

    @property
    def size(self):
        """Return the size of the fragment."""
        return self._size

    @property
    def hash(self):
        """Return the SHA-256 digest as hexadecimal string."""
        if self._hash is None:
            for _ in self:
                pass
        return self._hash

    def __iter__(self):
        # A fresh generator per iteration keeps all iteration state local, so re-iterating always
        # reads the complete fragment from the file again. The file handle is opened per iteration
        # and closed by the context manager even if iteration stops early.
        hasher = hashlib.sha256() if self._hash is None else None
        with open(self._file.path, 'rb') as handle:
            handle.seek(self._start_offset)
            remaining = self._size
            while remaining > 0:
                chunk = handle.read(min(self._chunk_size, remaining))
                if not chunk:
                    break
                remaining -= len(chunk)
                if hasher is not None:
                    hasher.update(chunk)
                yield chunk
        if hasher is not None:
            self._hash = hasher.hexdigest()

    @property
    def metadata(self):
        """Return the fragment metadata."""
        return {
            'file': {
                'type': 'file',
                'sha256': self._file.hash,
                'size': self._file.size,
                'path': str(self._file.path.relative_to(woodblock.file.get_corpus())),
                'id': self._file.id,
            },
            'fragment': {
                'sha256': self.hash,
                'size': self.size,
                'number': self._number,
                'file_offsets': {'start': self._start_offset, 'end': self._end_offset},
            },
        }
