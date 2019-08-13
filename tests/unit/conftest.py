import pathlib

import pytest

import woodblock.file

HERE = pathlib.Path(__file__).absolute().parent
DATA_FILES = HERE.parent / 'data'


def pytest_addoption(parser):
    parser.addoption('--run-slow', action='store_true', default=False, help='run slow tests')


def pytest_configure(config):
    config.addinivalue_line("markers", "slow: mark test as slow to run")


def pytest_collection_modifyitems(config, items):
    if config.getoption('--run-slow'):
        return
    skip_slow = pytest.mark.skip(reason='need --run-slow option to run')
    for item in items:
        if 'slow' in item.keywords:
            item.add_marker(skip_slow)


@pytest.fixture
def test_data_path():
    return pathlib.Path(DATA_FILES)


@pytest.fixture
def test_corpus_path(test_data_path):
    return test_data_path / 'corpus'


@pytest.fixture(autouse=True)
def corpus(test_corpus_path):
    woodblock.file.corpus(test_corpus_path)


@pytest.fixture
def path_test_file_512(test_corpus_path):
    return test_corpus_path / '512'


@pytest.fixture
def path_test_file_2000(test_corpus_path):
    return test_corpus_path / '2000'


@pytest.fixture
def path_test_file_4k(test_corpus_path):
    return test_corpus_path / '4096'
