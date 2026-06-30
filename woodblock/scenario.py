"""This module contains file carving scenario related classes and functions."""


class Scenario(list):
    """This class represents a file carving scenario.

    A scenario contains fragments in a certain order.

    Args:
        name: The name of the scenario.
    """

    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def add(self, fragments):
        """Add a fragment, or a list/tuple of fragments, to the scenario.

        Args:
            fragments: A single fragment (``FileFragment`` or ``FillerFragment``) or a
                list/tuple of fragments to be added.
        """
        if isinstance(fragments, (list, tuple)):
            self.extend(fragments)
        else:
            self.append(fragments)

    @property
    def metadata(self) -> dict:
        """Return the scenario metadata."""
        files = {}
        for frag in self:
            frag_meta = frag.metadata
            file_id = frag_meta['file']['id']
            if file_id not in files:
                files[file_id] = {'original': frag_meta['file'], 'fragments': []}
            files[file_id]['fragments'].append(frag_meta['fragment'])
        meta = {'name': self.name, 'files': list(files.values())}
        self._sort_fragments_by_number(meta)
        return meta

    @staticmethod
    def _sort_fragments_by_number(meta):
        for file in meta['files']:
            file['fragments'] = sorted(file['fragments'], key=lambda x: x['number'])
