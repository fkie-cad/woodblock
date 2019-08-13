"""Utility functions."""

import hashlib
import pathlib
from functools import lru_cache


@lru_cache(maxsize=1024)
def hash_file(path: pathlib.Path) -> str:
    """Return the SHA-256 hash of a file as hexadecimal string.

    The results of this functions are cached in order to avoid multiple computations for the same file.

    Args:
        path: The path of the file to hash
    """
    sha256 = hashlib.sha256()
    with path.open('rb') as file_handle:
        for chunk in iter(lambda: file_handle.read(1048576), b''):
            sha256.update(chunk)
    return sha256.hexdigest()


def get_file_list(path: pathlib.Path, min_size: int = 0) -> tuple:
    """Return all files from the given `path`.

    This function returns a list of all files paths relative to `path`. The resulting file list will be sorted so that
    the order of the files will always be the same for identical directory/file hierarchies.

    Note that README files (and variations such as README.md, ReadMe etc.) are NOT included in the result list.

    Args:
        path: The directory relative to the file corpus from which the file should be chosen.
        min_size: Minimal file size of the selected files.
    """
    basedir = pathlib.Path(path)
    return tuple(
        sorted(f for f in basedir.glob('**/*') if f.is_file() and not _is_readme(f) and f.stat().st_size >= min_size))


def _is_readme(path) -> bool:
    name = path.name.lower()
    return name.startswith('readme')
