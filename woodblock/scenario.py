"""This module contains file carving scenario related classes and functions."""

from multimethod import multimethod

import woodblock.fragments


class Scenario(list):
    """This class represents a file carving scenario.

    A scenario contains fragments in a certain order.

    Args:
        name: The name of the scenario.
    """

    def __init__(self, name: str):
        list.__init__([])
        self.name = name

    @multimethod
    def add(self, fragment: woodblock.fragments.FillerFragment):
        """Add a filler fragment to the scenario.

        Args:
            fragment: The fragment to be added.
        """
        self.append(fragment)

    @multimethod
    def add(self, fragment: woodblock.fragments.FileFragment):  # pylint: disable=function-redefined
        """Add a file fragment to the scenario.

        Args:
            fragment: The fragment to be added.
        """
        self.append(fragment)

    @multimethod
    def add(self, fragments: list):  # pylint: disable=function-redefined
        """Add a list of fragments to the scenario.

        Args:
            fragments: The list of fragments to be added.
        """
        self._add_from_iterable(fragments)

    @multimethod
    def add(self, fragments: tuple):  # pylint: disable=function-redefined
        """Add a tuple of fragments to the scenario.

        Args:
            fragments: The tuple of fragments to be added.
        """
        self._add_from_iterable(fragments)

    def _add_from_iterable(self, iterable):
        self.extend(iterable)

    @property
    def metadata(self) -> dict:
        """Return the scenario metadata."""
        meta = {'name': self.name, 'files': list()}
        files = dict()
        for frag in self:
            frag_meta = frag.metadata
            file_id = frag_meta['file']['id']
            if file_id not in files:
                files[file_id] = {'original': frag_meta['file'], 'fragments': list()}
            files[file_id]['fragments'].append(frag_meta['fragment'])
        meta['files'] = list(files.values())
        self._sort_fragments_by_number(meta)
        return meta

    @staticmethod
    def _sort_fragments_by_number(meta):
        for file in meta['files']:
            file['fragments'] = list(sorted(file['fragments'], key=lambda x: x['number']))
