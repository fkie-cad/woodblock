import pathlib

import pytest

import woodblock.file

HERE = pathlib.Path(__file__).absolute().parent
DATA_FILES = HERE.parent / 'data'


@pytest.fixture
def test_data_path():
    return DATA_FILES


@pytest.fixture
def test_corpus_path(test_data_path):
    return test_data_path / 'corpus'


@pytest.fixture
def config_path(test_data_path):
    return test_data_path / 'configs'


@pytest.fixture(autouse=True)
def reset_corpus():
    woodblock.file.corpus(None)
