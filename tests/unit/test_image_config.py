import io
import pathlib
import string

import pytest
from pytest_lazy_fixtures import lf

import woodblock
from woodblock.errors import ImageConfigError
from woodblock.image import Image


class TestImageConfig:
    def test_that_an_invalid_path_raises_an_error(self):
        with pytest.raises(FileNotFoundError):
            Image.from_config(pathlib.Path('/some/path'))

    @pytest.mark.parametrize('path', (
            lf('empty_config'), lf('config_without_general_section')))
    def test_that_a_missing_general_section_raises_an_error(self, path):
        with pytest.raises(ImageConfigError):
            Image.from_config(path)

    @pytest.mark.parametrize('path', (
            lf('empty_config'), lf('config_without_general_section'),
            lf('config_without_corpus')
    ))
    def test_that_a_missing_corpus_option_raises_an_error(self, path):
        with pytest.raises(ImageConfigError):
            Image.from_config(path)

    def test_that_the_seed_is_set(self, minimal_config):
        Image.from_config(minimal_config)
        assert woodblock.random.get_seed() == 123

    @pytest.mark.parametrize('config, num_expected_scenarios', (
            (lf('minimal_config'), 1),
    ))
    def test_that_the_correct_number_of_scenarios_is_present(self, config, num_expected_scenarios):
        image = Image.from_config(config)
        assert len(image.metadata['scenarios']) == num_expected_scenarios

    @pytest.mark.parametrize('config, num_expected_files', (
            (lf('minimal_config'), (3,)),
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
            lf('config_with_zeroes_fillers'),
            lf('config_with_random_fillers')
    ))
    def test_that_fillers_can_be_added(self, config):
        image = Image.from_config(config)
        scenario = image.metadata['scenarios'][0]
        assert len(scenario['files']) == 3
        assert sum(1 for f in scenario['files'] if f['original']['type'] == 'filler') == 2

    @pytest.mark.parametrize('config', (
            lf('config_with_invalid_sizes_in_general_section'),
            lf('config_with_invalid_sizes_in_scenario_section')
    ))
    def test_that_invalid_min_max_blocks_raise_an_error(self, config):
        with pytest.raises(ImageConfigError):
            Image.from_config(config)

    @pytest.mark.parametrize('config', (
            lf('config_with_fillers_and_sizes_in_general_section'),
            lf('config_with_fillers_and_min_size_in_scenario_section'),
            lf('config_with_fillers_and_max_size_in_scenario_section')
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
            lf('config_with_fillers_and_sizes_in_scenario_section'),
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
            lf('config_with_simple_intertwine_layout'),
            lf('config_with_intertwine_layout_and_fragment_sizes')
    ))
    def test_that_the_intertwine_layout_works(self, config):
        image = Image.from_config(config['path'])
        scenario = image.metadata['scenarios'][0]
        expected = config['expected']
        assert len(scenario['files']) == expected['num_files']
        for file in scenario['files']:
            assert expected['min_frags'] <= len(file['fragments']) <= expected['max_frags']

    @pytest.mark.parametrize('config', (
            lf('config_with_intertwine_layout_but_no_num_files'),
            lf('config_with_invalid_frag_sizes_in_intertwine_layout'),
    ))
    def test_that_invalid_intertwine_scenarios_raise_an_error(self, config):
        with pytest.raises(ImageConfigError):
            Image.from_config(config)

    @pytest.mark.parametrize('layout', ('intertwined', 'interwine', 'intertwin', 'INTERTWINED', 'foo'))
    def test_that_an_unknown_layout_type_raises_a_clear_error(self, layout, configs_dir, general_section):
        path = configs_dir / 'unknown-layout.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\nnum files = 3\n')
            config.write(f'layout = {layout}\n')
        with pytest.raises(ImageConfigError) as excinfo:
            Image.from_config(pathlib.Path(path))
        assert layout in str(excinfo.value)
        path.unlink()

    @pytest.mark.parametrize('layout', ('INTERTWINE', '  intertwine  ', 'Intertwine'))
    def test_that_the_intertwine_keyword_is_case_and_whitespace_insensitive(self, layout, configs_dir,
                                                                            general_section):
        path = configs_dir / 'intertwine-keyword.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\nnum files = 3\n')
            config.write(f'layout = {layout}\n')
        image = Image.from_config(pathlib.Path(path))
        scenario = image.metadata['scenarios'][0]
        assert len(scenario['files']) == 3
        path.unlink()

    @pytest.mark.parametrize('layout', ('1-1', '1.1'))
    def test_that_a_single_file_reference_layout_works(self, layout, configs_dir, general_section):
        path = configs_dir / 'single-file-ref-layout.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\nfrags file1 = 1\n')
            config.write(f'layout = {layout}\n')
        image = Image.from_config(pathlib.Path(path))
        scenario = image.metadata['scenarios'][0]
        assert len(scenario['files']) == 1
        assert len(scenario['files'][0]['fragments']) == 1
        path.unlink()

    @pytest.mark.parametrize('layout', ('r', 'R', 'z', 'Z'))
    def test_that_a_single_filler_layout_works(self, layout, configs_dir, general_section):
        path = configs_dir / 'single-filler-layout.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n')
            config.write(f'layout = {layout}\n')
        image = Image.from_config(pathlib.Path(path))
        scenario = image.metadata['scenarios'][0]
        assert len(scenario['files']) == 1
        assert scenario['files'][0]['original']['type'] == 'filler'
        path.unlink()

    @pytest.mark.parametrize('layout', ('1-1, 1-1', '1.1, 1.1', '1-1, 2-1, 1.1'))
    def test_that_a_repeated_file_fragment_reference_raises_an_error(self, layout, configs_dir, general_section):
        path = configs_dir / 'repeated-fragment-layout.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\nfrags file1 = 2\nfrags file2 = 1\n')
            config.write(f'layout = {layout}\n')
        with pytest.raises(ImageConfigError):
            Image.from_config(pathlib.Path(path))
        path.unlink()

    @pytest.mark.parametrize('layout', ('R, R', 'Z, Z', 'R, Z, R, Z'))
    def test_that_repeated_filler_references_are_accepted(self, layout, configs_dir, general_section):
        path = configs_dir / 'repeated-filler-layout.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n')
            config.write(f'layout = {layout}\n')
        image = Image.from_config(pathlib.Path(path))
        assert len(image.metadata['scenarios']) == 1
        path.unlink()

    def test_that_a_malformed_multi_token_sequence_still_raises_an_error(self, configs_dir, general_section):
        path = configs_dir / 'malformed-sequence-layout.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\nfrags file1 = 1\n')
            config.write('layout = 1-1, intertwined\n')
        with pytest.raises(ImageConfigError):
            Image.from_config(pathlib.Path(path))
        path.unlink()

    @pytest.mark.parametrize('key', ('blocksize', 'seeed', 'min fragments'))
    def test_that_an_unknown_key_in_the_general_section_raises_an_error(self, key, configs_dir,
                                                                        scenario_sec_with_only_frag_options):
        path = configs_dir / 'unknown-general-key.conf'
        with path.open('w') as config:
            config.write(f'[general]\nseed = 123\ncorpus = ../corpus/\n{key} = 512\n\n')
            config.write(scenario_sec_with_only_frag_options)
        with pytest.raises(ImageConfigError) as excinfo:
            Image.from_config(pathlib.Path(path))
        assert key in str(excinfo.value)
        path.unlink()

    @pytest.mark.parametrize('key', ('min fragments', 'max fragments', 'numfiles', 'foo'))
    def test_that_an_unknown_key_in_an_intertwine_scenario_raises_an_error(self, key, configs_dir, general_section):
        path = configs_dir / 'unknown-intertwine-key.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\nlayout = intertwine\nnum files = 3\n')
            config.write(f'{key} = 2\n')
        with pytest.raises(ImageConfigError) as excinfo:
            Image.from_config(pathlib.Path(path))
        assert key in str(excinfo.value)
        path.unlink()

    @pytest.mark.parametrize('key', ('frags', 'fragsfile1', 'filex', 'foo'))
    def test_that_an_unknown_key_in_a_fragment_sequence_scenario_raises_an_error(self, key, configs_dir,
                                                                                 general_section):
        path = configs_dir / 'unknown-fragment-sequence-key.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\nfrags file1 = 1\n')
            config.write(f'{key} = 2\n')
            config.write('layout = 1-1\n')
        with pytest.raises(ImageConfigError) as excinfo:
            Image.from_config(pathlib.Path(path))
        assert key in str(excinfo.value)
        path.unlink()

    def test_that_known_fragment_sequence_keys_are_accepted(self, configs_dir, general_section):
        path = configs_dir / 'known-fragment-sequence-keys.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n'
                         'frags file1 = 2\n'
                         'frags_file2 = 1\n'
                         'file2 = 1024\n'
                         'min filler blocks = 1\n'
                         'max filler blocks = 2\n'
                         'layout = 1-1, R, 2-1, 1-2\n')
        image = Image.from_config(pathlib.Path(path))
        assert len(image.metadata['scenarios']) == 1
        path.unlink()

    def test_that_explicit_sizes_produce_exact_fragment_sizes(self, configs_dir, general_section):
        path = configs_dir / 'explicit-sizes.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n'
                         'file1 = 4096\n'
                         'sizes file1 = 2, 3, 3\n'
                         'layout = 1-1, 1-2, 1-3\n')
        image = Image.from_config(pathlib.Path(path))
        fragments = image.metadata['scenarios'][0]['files'][0]['fragments']
        assert [f['size'] for f in fragments] == [1024, 1536, 1536]
        path.unlink()

    def test_that_explicit_sizes_compose_with_a_missing_middle(self, configs_dir, general_section):
        path = configs_dir / 'explicit-sizes-missing-middle.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n'
                         'file1 = 4096\n'
                         'frags file1 = 3\n'
                         'sizes file1 = 2, 3, 3\n'
                         'layout = 1-1, 1-3\n')
        image = Image.from_config(pathlib.Path(path))
        fragments = image.metadata['scenarios'][0]['files'][0]['fragments']
        sizes = {f['number']: f['size'] for f in fragments}
        assert sorted(sizes) == [1, 3]
        assert sizes[1] == 1024
        assert sizes[3] == 1536
        path.unlink()

    def test_that_explicit_sizes_work_for_a_single_fragment_file(self, configs_dir, general_section):
        path = configs_dir / 'explicit-sizes-single.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n'
                         'file1 = 1024\n'
                         'sizes file1 = 2\n'
                         'layout = 1-1\n')
        image = Image.from_config(pathlib.Path(path))
        fragments = image.metadata['scenarios'][0]['files'][0]['fragments']
        assert [f['size'] for f in fragments] == [1024]
        path.unlink()

    @pytest.mark.parametrize('kind, blocks', (('R', 5), ('Z', 3), ('r', 1), ('z', 8)))
    def test_that_explicit_filler_sizes_are_honored(self, kind, blocks, configs_dir, general_section):
        path = configs_dir / 'explicit-filler-sizes.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n'
                         'frags file1 = 1\n'
                         f'layout = 1-1, {kind}:{blocks}\n')
        image = Image.from_config(pathlib.Path(path))
        fillers = [f for f in image.metadata['scenarios'][0]['files'] if f['original']['type'] == 'filler']
        assert len(fillers) == 1
        assert fillers[0]['fragments'][0]['size'] == blocks * 512
        path.unlink()

    def test_that_the_scenario_gap_shifts_later_scenario_offsets(self, configs_dir):
        path = configs_dir / 'scenario-gap.conf'
        with path.open('w') as config:
            config.write('[general]\nseed = 1\ncorpus = ../corpus/\nblock size = 512\nscenario gap = 2\n\n')
            config.write('[s1]\nfile1 = 1024\nsizes file1 = 2\nlayout = 1-1\n\n')
            config.write('[s2]\nfile1 = 1024\nsizes file1 = 2\nlayout = 1-1\n')
        meta = Image.from_config(pathlib.Path(path)).metadata
        # scenario 1 fills bytes [0, 1024); a 2-block (1024-byte) gap follows; scenario 2 starts at 2048.
        s2_fragment = meta['scenarios'][1]['files'][0]['fragments'][0]
        assert s2_fragment['image_offsets']['start'] == 2048
        path.unlink()

    def test_that_the_image_is_padded_to_the_target_size(self, configs_dir):
        path = configs_dir / 'image-size.conf'
        with path.open('w') as config:
            config.write('[general]\nseed = 1\ncorpus = ../corpus/\nblock size = 512\nimage size = 10\n\n')
            config.write('[s]\nfile1 = 1024\nsizes file1 = 2\nlayout = 1-1\n')
        buffer = io.BytesIO()
        Image.from_config(pathlib.Path(path)).write(buffer)
        assert len(buffer.getvalue()) == 10 * 512
        path.unlink()

    @pytest.mark.parametrize('scenario_body', (
            # number of sizes does not match frags
            'file1 = 4096\nfrags file1 = 2\nsizes file1 = 2, 3, 3\nlayout = 1-1, 1-2\n',
            # last size does not equal the file tail
            'file1 = 4096\nsizes file1 = 2, 3\nlayout = 1-1, 1-2\n',
            # a size of zero is not allowed
            'file1 = 4096\nsizes file1 = 0, 8\nlayout = 1-1, 1-2\n',
            # sizes have to be integers
            'file1 = 4096\nsizes file1 = a, 8\nlayout = 1-1, 1-2\n',
            # explicit filler size has to be >= 1
            'file1 = 4096\nsizes file1 = 8\nlayout = 1-1, R:0\n',
            # explicit filler size has to be an integer
            'file1 = 4096\nsizes file1 = 8\nlayout = 1-1, R:x\n',
    ))
    def test_that_invalid_sizes_raise_an_error(self, scenario_body, configs_dir, general_section):
        path = configs_dir / 'invalid-sizes.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n')
            config.write(scenario_body)
        with pytest.raises(ImageConfigError):
            Image.from_config(pathlib.Path(path))
        path.unlink()

    @pytest.mark.parametrize('general_body', (
            'image size = 1\n',   # smaller than the content
            'scenario gap = -1\n',  # negative gap
            'scenario gap = x\n',  # non-integer gap
            'image size = 0\n',   # non-positive target size
    ))
    def test_that_invalid_general_sizing_keys_raise_an_error(self, general_body, configs_dir):
        path = configs_dir / 'invalid-general-sizing.conf'
        with path.open('w') as config:
            config.write(f'[general]\nseed = 1\ncorpus = ../corpus/\nblock size = 512\n{general_body}\n')
            config.write('[s]\nfile1 = 4096\nsizes file1 = 8\nlayout = 1-1\n')
        with pytest.raises(ImageConfigError):
            Image.from_config(pathlib.Path(path))
        path.unlink()

    def test_that_a_file_with_only_sizes_needs_no_frags(self, configs_dir, general_section):
        path = configs_dir / 'sizes-without-frags.conf'
        with path.open('w') as config:
            config.write(general_section)
            config.write('[scenario]\n'
                         'file1 = 4096\n'
                         'sizes file1 = 3, 5\n'
                         'layout = 1-1, 1-2\n')
        image = Image.from_config(pathlib.Path(path))
        assert len(image.metadata['scenarios'][0]['files'][0]['fragments']) == 2
        path.unlink()

    def test_that_an_invalid_sizes_config_file_raises_an_error(self, configs_dir):
        path = configs_dir / 'invalid' / 'sizes-exceed-file.conf'
        with pytest.raises(ImageConfigError):
            Image.from_config(path)


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
