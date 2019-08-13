import pathlib
import tempfile

from woodblock.utils import get_file_list


class TestGetFileList:

    def test_that_no_files_are_returned_for_an_empty_directory(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            assert len(get_file_list(tmpdir)) == 0

    def test_that_the_correct_number_files_are_returned(self, test_corpus_path):
        path = pathlib.Path(test_corpus_path) / 'letters'
        files = get_file_list(path.absolute())
        assert len(files) == 3
        file_names = tuple(f.name for f in files)
        assert file_names == ('ascii_letters', 'ascii_lowercase', 'ascii_uppercase')
