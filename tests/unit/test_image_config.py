import pathlib
import string

import pytest

import woodblock
from woodblock.errors import ImageConfigError
from woodblock.image import Image


class TestImageConfig:
    def test_that_an_invalid_path_raises_an_error(self):
        with pytest.raises(FileNotFoundError):
            Image.from_config(pathlib.Path('/some/path'))

    @pytest.mark.parametrize('path', (
            pytest.lazy_fixture('empty_config'), pytest.lazy_fixture('config_without_general_section')))
    def test_that_a_missing_general_section_raises_an_error(self, path):
        with pytest.raises(ImageConfigError):
            Image.from_config(path)

    @pytest.mark.parametrize('path', (
            pytest.lazy_fixture('empty_config'), pytest.lazy_fixture('config_without_general_section'),
            pytest.lazy_fixture('config_without_corpus')
    ))
    def test_that_a_missing_corpus_option_raises_an_error(self, path):
        with pytest.raises(ImageConfigError):
            Image.from_config(path)

    def test_that_the_seed_is_set(self, minimal_config):
        Image.from_config(minimal_config)
        assert woodblock.random.get_seed() == 123

    @pytest.mark.parametrize('config, num_expected_scenarios', (
            (pytest.lazy_fixture('minimal_config'), 1),
    ))
    def test_that_the_correct_number_of_scenarios_is_present(self, config, num_expected_scenarios):
        image = Image.from_config(config)
        assert len(image.metadata['scenarios']) == num_expected_scenarios

    @pytest.mark.parametrize('config, num_expected_files', (
            (pytest.lazy_fixture('minimal_config'), (3,)),
    ))
    def test_that_the_correct_number_of_files_per_scenario_is_present(self, config, num_expected_files):
        image = Image.from_config(config)
        files_per_scenario = tuple(len(s['files']) for s in image.metadata['scenarios'])
        assert files_per_scenario == num_expected_files

    @pytest.mark.parametrize('sep', string.printable)
    def test_that_an_invalid_file_fragment_separator_raises_an_error(self, sep, general_section, configs_dir):
        if sep == '-' or sep == '.':
            return
        path = configs_dir / 'invalid-sep.conf'
        with path.open('w') as tmp:
            tmp.write(general_section)
            tmp.write('[some scenario]\nfrags file1 = 2\nfrags_file2 = 2\n')
            tmp.write('layout = 1-1, 2.1, 1')
            tmp.write(sep)
            tmp.write('2\n')
        with pytest.raises(ImageConfigError):
            Image.from_config(pathlib.Path(tmp.name))
        path.unlink()

    def test_that_file_cannot_be_used_without_number_of_frags(self, configs_dir, general_section):
        path = configs_dir / 'file-without-frags.conf'
        with path.open('w') as tmp:
            tmp.write(general_section)
            tmp.write('[some scenario]\n'
                      'file1 = 1024\n'
                      'frags file2 = 2\n')
            tmp.write('layout = 1-1, 2.1, 1-2')
        with pytest.raises(ImageConfigError):
            Image.from_config(pathlib.Path(tmp.name))
        path.unlink()

    def test_that_a_missing_layout_line_raises_an_error(self, configs_dir, general_section):
        path = configs_dir / 'no-layout.conf'
        with path.open('w') as tmp:
            tmp.write(general_section)
            tmp.write('[some scenario]\n'
                      'file1 = 1024\n'
                      'frags file1 = 2\n')
        with pytest.raises(ImageConfigError):
            Image.from_config(pathlib.Path(tmp.name))
        path.unlink()

    @pytest.mark.parametrize('config', (
            pytest.lazy_fixture('config_with_zeroes_fillers'),
            pytest.lazy_fixture('config_with_random_fillers')
    ))
    def test_that_fillers_can_be_added(self, config):
        image = Image.from_config(config)
        scenario = image.metadata['scenarios'][0]
        assert len(scenario['files']) == 3
        assert sum(1 for f in scenario['files'] if f['original']['type'] == 'filler') == 2

    @pytest.mark.parametrize('config', (
            pytest.lazy_fixture('config_with_invalid_sizes_in_general_section'),
            pytest.lazy_fixture('config_with_invalid_sizes_in_scenario_section')
    ))
    def test_that_invalid_min_max_blocks_raise_an_error(self, config):
        with pytest.raises(ImageConfigError):
            Image.from_config(config)

    @pytest.mark.parametrize('config', (
            pytest.lazy_fixture('config_with_fillers_and_sizes_in_general_section'),
            pytest.lazy_fixture('config_with_fillers_and_min_size_in_scenario_section'),
            pytest.lazy_fixture('config_with_fillers_and_max_size_in_scenario_section')
    ))
    def test_that_the_fillers_have_the_correct_size(self, config):
        image = Image.from_config(config['config'])
        block_size = image.metadata['block_size']
        scenario = image.metadata['scenarios'][0]
        expected = config['expected_results']
        for file in scenario['files']:
            if file['original']['type'] == 'filler':
                assert len(file['fragments']) == 1
                assert file['fragments'][0]['size'] % block_size == 0
                assert expected['min'] <= file['fragments'][0]['size'] / block_size <= expected['max']

    @pytest.mark.parametrize('config', (
            pytest.lazy_fixture('config_with_fillers_and_sizes_in_scenario_section'),
    ))
    def test_that_min_max_blocks_from_scenario_section_are_preferred(self, config):
        image = Image.from_config(config['config'])
        block_size = image.metadata['block_size']
        scenario = image.metadata['scenarios'][0]
        expected = config['expected_results']
        for file in scenario['files']:
            if file['original']['type'] == 'filler':
                assert len(file['fragments']) == 1
                assert file['fragments'][0]['size'] % block_size == 0
                assert expected['min'] <= file['fragments'][0]['size'] / block_size <= expected['max']

    @pytest.mark.parametrize('config', (
            pytest.lazy_fixture('config_with_simple_intertwine_layout'),
            pytest.lazy_fixture('config_with_intertwine_layout_and_fragment_sizes')
    ))
    def test_that_the_intertwine_layout_works(self, config):
        image = Image.from_config(config['path'])
        scenario = image.metadata['scenarios'][0]
        expected = config['expected']
        assert len(scenario['files']) == expected['num_files']
        for file in scenario['files']:
            assert expected['min_frags'] <= len(file['fragments']) <= expected['max_frags']

    @pytest.mark.parametrize('config', (
            pytest.lazy_fixture('config_with_intertwine_layout_but_no_num_files'),
            pytest.lazy_fixture('config_with_invalid_frag_sizes_in_intertwine_layout'),
    ))
    def test_that_invalid_intertwine_scenarios_raise_an_error(self, config):
        with pytest.raises(ImageConfigError):
            Image.from_config(config)


@pytest.fixture
def configs_dir(test_data_path):
    return test_data_path / 'configs'


@pytest.fixture(params=('only-general.conf', 'single-scenario.conf'))
def configs(request, configs_dir):
    return configs_dir / request.param


@pytest.fixture
def general_section():
    return '[general]\nseed = 123\ncorpus = ../corpus/\n\n'


@pytest.fixture(params=((5, 7), (2, 2), (1, 1)))
def general_section_with_filler_sizes(request):
    return (
        '[general]\nseed = 123\ncorpus = ../corpus/\n'
        f'min filler blocks = {request.param[0]}\nmax filler blocks = {request.param[0]}\n\n'
    )


@pytest.fixture
def scenario_sec_with_only_frag_options():
    return '[only frags]\nfrags file1 = 3\nfrags file2 = 1\nfrags file3 = 2\nlayout = 1-1, 2-1, 1-2, 3-1, 1-3, 3-2\n\n'


@pytest.fixture
def scenario_with_zeroes_filler_symbols():
    return '[zeroes fillers]\nfrags_file1 = 2\nlayout = 1-1, z, 1-2, Z'


@pytest.fixture
def scenario_with_random_filler_symbols():
    return '[random fillers]\nfrags_file1 = 2\nlayout = 1-1, r, 1-2, R'


@pytest.fixture
def empty_config(configs_dir):
    path = configs_dir / 'empty.conf'
    with path.open('w'):
        pass
    yield path
    path.unlink()


@pytest.fixture
def config_without_general_section(configs_dir, scenario_sec_with_only_frag_options):
    path = configs_dir / 'no-general.conf'
    with path.open('w') as config:
        config.write(scenario_sec_with_only_frag_options)
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture
def config_without_corpus(configs_dir):
    path = configs_dir / 'no-corpus.conf'
    with path.open('w') as config:
        config.write('[general]\nseed = 123\n\n')
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture
def config_without_scenarios(configs_dir, general_section):
    path = configs_dir / 'no-scenarios.conf'
    with open(path, 'w') as config:
        config.write(general_section)
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture
def minimal_config(configs_dir, general_section, scenario_sec_with_only_frag_options):
    path = configs_dir / 'minimal.conf'
    with path.open('w') as config:
        config.write(general_section)
        config.write(scenario_sec_with_only_frag_options)
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture
def config_with_zeroes_fillers(configs_dir, general_section, scenario_with_zeroes_filler_symbols):
    path = configs_dir / 'zeroes-fillers.conf'
    with path.open('w') as config:
        config.write(general_section)
        config.write(scenario_with_zeroes_filler_symbols)
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture
def config_with_random_fillers(configs_dir, general_section, scenario_with_random_filler_symbols):
    path = configs_dir / 'random-fillers.conf'
    with path.open('w') as config:
        config.write(general_section)
        config.write(scenario_with_random_filler_symbols)
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture(params=[(5, 7), (2, 2), (1, 1), (3, 4), (10, 100)])
def config_with_fillers_and_sizes_in_general_section(request, configs_dir, scenario_with_zeroes_filler_symbols):
    path = configs_dir / 'fillers-with-sizes-in-general.conf'
    with path.open('w') as config:
        config.write((
            '[general]\nseed = 123\ncorpus = ../corpus/\n'
            f'min filler blocks = {request.param[0]}\nmax filler blocks = {request.param[1]}\n\n'))
        config.write(scenario_with_zeroes_filler_symbols)
    yield {'config': pathlib.Path(path), 'expected_results': {'min': request.param[0], 'max': request.param[1]}}
    path.unlink()


@pytest.fixture(params=[(0, 10), (10, 2), (1, 0), (-1, 2)])
def config_with_invalid_sizes_in_general_section(request, configs_dir, scenario_with_zeroes_filler_symbols):
    path = configs_dir / 'fillers-with-invalid-sizes-in-general.conf'
    with path.open('w') as config:
        config.write('[general]\n'
                     'seed = 123\n'
                     'corpus = ../corpus/\n'
                     f'min filler blocks = {request.param[0]}\n'
                     f'max filler blocks = {request.param[1]}\n\n')
        config.write(scenario_with_zeroes_filler_symbols)
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture(params=[(0, 10), (10, 2), (1, 0), (-1, 2)])
def config_with_invalid_sizes_in_scenario_section(request, configs_dir, general_section):
    path = configs_dir / 'fillers-with-invalid-sizes-in-section.conf'
    with path.open('w') as config:
        config.write(general_section)
        config.write('[invalid block numbers]\n'
                     'frags_file1 = 2\n'
                     f'min filler blocks = {request.param[0]}\n'
                     f'max filler blocks = {request.param[1]}\n'
                     'layout = 1-1, z, 1-2, R')
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture(params=[(5, 7), (4, 4), (1, 1), (4, 5), (10, 100)])
def config_with_fillers_and_sizes_in_scenario_section(request, configs_dir):
    path = configs_dir / 'fillers-with-sizes-in-section.conf'
    with path.open('w') as config:
        config.write('[general]\n'
                     'seed = 123\n'
                     'corpus = ../corpus/\n'
                     'min filler blocks = 2\n'
                     'max filler blocks = 3\n\n'
                     '[scenario]\n'
                     'frags_file1 = 2\n'
                     f'min filler blocks = {request.param[0]}\n'
                     f'max filler blocks = {request.param[1]}\n'
                     'layout = 1-1, z, 1-2, R')
    yield {'config': pathlib.Path(path), 'expected_results': {'min': request.param[0], 'max': request.param[1]}}
    path.unlink()


@pytest.fixture(params=(3, 4, 5, 10, 20, 50))
def config_with_fillers_and_min_size_in_scenario_section(request, configs_dir):
    path = configs_dir / 'fillers-with-sizes-in-section.conf'
    with path.open('w') as config:
        config.write('[general]\n'
                     'seed = 123\n'
                     'corpus = ../corpus/\n'
                     'min filler blocks = 2\n'
                     'max filler blocks = 100\n\n'
                     '[scenario]\n'
                     'frags_file1 = 2\n'
                     f'min filler blocks = {request.param}\n'
                     'layout = 1-1, z, 1-2, R')
    yield {'config': pathlib.Path(path), 'expected_results': {'max': 100, 'min': request.param}}
    path.unlink()


@pytest.fixture(params=(3, 4, 5, 10, 20, 50))
def config_with_fillers_and_max_size_in_scenario_section(request, configs_dir):
    path = configs_dir / 'fillers-with-sizes-in-section.conf'
    with path.open('w') as config:
        config.write('[general]\n'
                     'seed = 123\n'
                     'corpus = ../corpus/\n'
                     'min filler blocks = 2\n'
                     'max filler blocks = 3\n\n'
                     '[scenario]\n'
                     'frags_file1 = 2\n'
                     f'max filler blocks = {request.param}\n'
                     'layout = 1-1, z, 1-2, R')
    yield {'config': pathlib.Path(path), 'expected_results': {'min': 2, 'max': request.param}}
    path.unlink()


@pytest.fixture(params=(2, 3, 4, 5))
def config_with_simple_intertwine_layout(request, configs_dir, general_section):
    path = configs_dir / 'intertwined-layout.conf'
    with path.open('w') as config:
        config.write(general_section)
        config.write('[scenario]\n'
                     f'num files = {request.param}\n'
                     'layout = intertwine')
    yield {'path': pathlib.Path(path), 'expected': {'min_frags': 1, 'max_frags': 4, 'num_files': request.param}}
    path.unlink()


@pytest.fixture(params=((2, 3), (2, 5), (None, 6), (3, None)))
def config_with_intertwine_layout_and_fragment_sizes(request, configs_dir, general_section):
    path = configs_dir / 'intertwined-layout.conf'
    min_frags = 1
    max_frags = 4
    with path.open('w') as config:
        config.write(general_section)
        config.write('[scenario]\n'
                     'num files = 3\n'
                     'layout = intertwine\n')
        if request.param[0] is not None:
            config.write(f'min frags = {request.param[0]}\n')
            min_frags = request.param[0]
        if request.param[1] is not None:
            config.write(f'max frags = {request.param[1]}\n')
            max_frags = request.param[1]
    yield {'path': pathlib.Path(path), 'expected': {'min_frags': min_frags, 'max_frags': max_frags, 'num_files': 3}}
    path.unlink()


@pytest.fixture(params=[(0, 10), (10, 2), (1, 0), (-1, 2), (1, 'a'), ('x', 5)])
def config_with_invalid_frag_sizes_in_intertwine_layout(request, configs_dir, general_section):
    path = configs_dir / 'invalid-frag-num-in-intertwine.conf'
    with path.open('w') as config:
        config.write(general_section)
        config.write('[invalid frag numbers]\n'
                     f'min frags = {request.param[0]}\n'
                     f'max frags = {request.param[1]}\n'
                     'num files = 3\n'
                     'layout = intertwine')
    yield pathlib.Path(path)
    path.unlink()


@pytest.fixture
def config_with_intertwine_layout_but_no_num_files(configs_dir, general_section):
    path = configs_dir / 'intertwine-without-num-files.conf'
    with path.open('w') as config:
        config.write(general_section)
        config.write('[invalid frag numbers]\n'
                     'layout = intertwine')
    yield pathlib.Path(path)
    path.unlink()
