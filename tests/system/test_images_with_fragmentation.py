import hashlib
import json
import os
import pathlib

import woodblock
from woodblock.file import File, get_corpus
from woodblock.fragments import ZeroesFragment, RandomDataFragment
from woodblock.image import Image
from woodblock.scenario import Scenario

HERE = pathlib.Path(__file__).absolute().parent


def _explicit_layout_config(corpus_path):
    return (
        '[general]\n'
        'seed = 4711\n'
        f'corpus = {corpus_path.absolute()}\n'
        'block size = 512\n'
        'scenario gap = 4\n'
        'image size = 32\n'
        '\n'
        '[bifragment gap]\n'
        'file1 = 4096\n'
        'sizes file1 = 3, 5\n'
        'layout = 1-1, R:8, 1-2\n'
        '\n'
        '[explicit missing middle]\n'
        'file1 = 4096\n'
        'frags file1 = 3\n'
        'sizes file1 = 2, 3, 3\n'
        'layout = 1-1, Z:2, 1-3\n'
    )


class TestExplicitPlacementFromConfig:
    """End-to-end coverage for explicit sizes, filler/gap sizes, scenario gaps and target image size."""

    def test_that_all_explicit_placement_features_are_honored(self, test_corpus_path, tmp_path):
        config = tmp_path / 'explicit.conf'
        config.write_text(_explicit_layout_config(test_corpus_path))
        image_path = tmp_path / 'image.dd'
        Image.from_config(config).write(image_path)

        # The whole image is padded up to the target size of 32 blocks.
        assert image_path.stat().st_size == 32 * 512

        data = image_path.read_bytes()
        log = json.loads((tmp_path / 'image.dd.json').read_text())

        fragments = {}
        for scenario in log['scenarios']:
            for file in scenario['files']:
                for fragment in file['fragments']:
                    fragments[(scenario['name'], fragment['number'], file['original']['type'])] = fragment
                    # Every recorded offset range must hash to the recorded fragment hash.
                    offsets = fragment['image_offsets']
                    on_disk = data[offsets['start']:offsets['end']]
                    assert hashlib.sha256(on_disk).hexdigest() == fragment['sha256']

        # Exact file-fragment sizes.
        assert fragments[('bifragment gap', 1, 'file')]['size'] == 3 * 512
        assert fragments[('bifragment gap', 2, 'file')]['size'] == 5 * 512
        assert fragments[('explicit missing middle', 1, 'file')]['size'] == 2 * 512
        assert fragments[('explicit missing middle', 3, 'file')]['size'] == 3 * 512
        # The missing middle fragment is not part of the image.
        assert ('explicit missing middle', 2, 'file') not in fragments

        # Exact filler/gap sizes.
        assert fragments[('bifragment gap', 1, 'filler')]['size'] == 8 * 512
        assert fragments[('explicit missing middle', 1, 'filler')]['size'] == 2 * 512

        # The bifragment gap sits exactly between the two file fragments.
        first = fragments[('bifragment gap', 1, 'file')]['image_offsets']
        gap = fragments[('bifragment gap', 1, 'filler')]['image_offsets']
        second = fragments[('bifragment gap', 2, 'file')]['image_offsets']
        assert gap['start'] == first['end']
        assert second['start'] == gap['end']

        # The scenario gap of 4 blocks precedes the second scenario.
        second_scenario_start = fragments[('explicit missing middle', 1, 'file')]['image_offsets']['start']
        assert second_scenario_start == second['end'] + 4 * 512

    def test_that_the_explicit_placement_image_is_reproducible(self, test_corpus_path, tmp_path):
        config = tmp_path / 'explicit.conf'
        config.write_text(_explicit_layout_config(test_corpus_path))

        first = tmp_path / 'first.dd'
        Image.from_config(config).write(first)
        second = tmp_path / 'second.dd'
        Image.from_config(config).write(second)

        assert first.read_bytes() == second.read_bytes()


class TestSimpleFragmentation:

    def test_an_image_with_two_file_fragments_and_three_filler_fragments(self, test_corpus_path):
        woodblock.random.seed(13)
        woodblock.file.corpus(test_corpus_path)
        image_path = HERE / 'simple-fragmentation.dd'
        metadata_path = pathlib.Path('.'.join((str(image_path), 'json')))
        file_path = test_corpus_path / '4096'
        frags = File(file_path).fragment_evenly(num_fragments=2)
        s = Scenario('simple fragmentation with fillers')
        s.add(RandomDataFragment(512))
        s.add(frags[0])
        s.add(ZeroesFragment(512))
        s.add(frags[1])
        s.add(RandomDataFragment(512))
        image = Image(block_size=512)
        image.add(s)
        image.write(image_path)
        assert image_path.is_file()
        assert image_path.stat().st_size == 5632
        assert metadata_path.is_file()
        meta = _replace_uuids(json.load(metadata_path.open('r')))
        assert meta['block_size'] == 512
        assert meta['corpus'] == str(test_corpus_path)
        assert meta['seed'] == 13
        assert len(meta['scenarios']) == 1
        sc_meta = meta['scenarios'][0]
        assert sc_meta['name'] == 'simple fragmentation with fillers'
        assert len(sc_meta['files']) == 4
        assert sc_meta['files'][0]['original']['type'] == 'filler'
        assert sc_meta['files'][0]['original']['path'] == 'random'
        assert sc_meta['files'][0]['original']['size'] == 512
        assert len(sc_meta['files'][0]['fragments']) == 1
        assert sc_meta['files'][0]['fragments'][0]['number'] == 1
        assert sc_meta['files'][0]['fragments'][0]['size'] == 512
        assert sc_meta['files'][0]['fragments'][0]['file_offsets'] == {'start': 0, 'end': 512}
        assert sc_meta['files'][0]['fragments'][0]['image_offsets'] == {'start': 0, 'end': 512}
        assert sc_meta['files'][1] == {
            'original': {'type': 'file', 'path': str(file_path.relative_to(get_corpus())), 'size': 4096, 'id': 'uuid',
                         'sha256': '0ec91e13ced59cfc1f297cfedd8c595a6200ac2b8c99bcc321e8c68cf1f166a0'},
            'fragments': [{'number': 1, 'size': 2048,
                           'sha256': '291b808471ca4772e260dd50604e93082c22fbcf821fa3db7531e51343473717',
                           'file_offsets': {'start': 0, 'end': 2048}, 'image_offsets': {'start': 512, 'end': 2560}},
                          {'number': 2, 'size': 2048,
                           'sha256': '570dc7f7ceea7fa7204588456fd00e53b0abf1cca9d35cc074383e8dcc418114',
                           'file_offsets': {'start': 2048, 'end': 4096}, 'image_offsets': {'start': 3072, 'end': 5120}}
                          ]}
        assert sc_meta['files'][2] == {
            'original': {'type': 'filler', 'path': 'zeroes', 'size': 512, 'id': 'uuid',
                         'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560'},
            'fragments': [{'number': 1, 'size': 512,
                           'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560',
                           'file_offsets': {'start': 0, 'end': 512}, 'image_offsets': {'start': 2560, 'end': 3072}}]}
        assert sc_meta['files'][3]['original']['type'] == 'filler'
        assert sc_meta['files'][3]['original']['path'] == 'random'
        assert sc_meta['files'][3]['original']['size'] == 512
        assert len(sc_meta['files'][3]['fragments']) == 1
        assert sc_meta['files'][3]['fragments'][0]['number'] == 1
        assert sc_meta['files'][3]['fragments'][0]['size'] == 512
        assert sc_meta['files'][3]['fragments'][0]['file_offsets'] == {'start': 0, 'end': 512}
        assert sc_meta['files'][3]['fragments'][0]['image_offsets'] == {'start': 5120, 'end': 5632}
        os.remove(image_path)
        os.remove(metadata_path)

    def test_an_image_with_two_reversed_file_fragments_and_three_filler_fragments(self, test_corpus_path):
        woodblock.random.seed(13)
        woodblock.file.corpus(test_corpus_path)
        image_path = HERE / 'simple-fragmentation.dd'
        metadata_path = pathlib.Path('.'.join((str(image_path), 'json')))
        file_path = test_corpus_path / '4096'
        frags = File(file_path).fragment_evenly(num_fragments=2)
        s = Scenario('simple fragmentation with fillers')
        s.add(RandomDataFragment(512))
        s.add(frags[1])
        s.add(ZeroesFragment(512))
        s.add(frags[0])
        s.add(RandomDataFragment(512))
        image = Image(block_size=512)
        image.add(s)
        image.write(image_path)
        assert image_path.is_file()
        assert image_path.stat().st_size == 5632
        assert metadata_path.is_file()
        meta = _replace_uuids(json.load(metadata_path.open('r')))
        assert meta['block_size'] == 512
        assert meta['corpus'] == str(test_corpus_path)
        assert meta['seed'] == 13
        assert len(meta['scenarios']) == 1
        sc_meta = meta['scenarios'][0]
        assert sc_meta['name'] == 'simple fragmentation with fillers'
        assert len(sc_meta['files']) == 4
        assert sc_meta['files'][0]['original']['type'] == 'filler'
        assert sc_meta['files'][0]['original']['path'] == 'random'
        assert sc_meta['files'][0]['original']['size'] == 512
        assert len(sc_meta['files'][0]['fragments']) == 1
        assert sc_meta['files'][0]['fragments'][0]['number'] == 1
        assert sc_meta['files'][0]['fragments'][0]['size'] == 512
        assert sc_meta['files'][0]['fragments'][0]['file_offsets'] == {'start': 0, 'end': 512}
        assert sc_meta['files'][0]['fragments'][0]['image_offsets'] == {'start': 0, 'end': 512}
        assert sc_meta['files'][1] == {
            'original': {'type': 'file', 'path': str(file_path.relative_to(get_corpus())), 'size': 4096, 'id': 'uuid',
                         'sha256': '0ec91e13ced59cfc1f297cfedd8c595a6200ac2b8c99bcc321e8c68cf1f166a0'},
            'fragments': [{'number': 1, 'size': 2048,
                           'sha256': '291b808471ca4772e260dd50604e93082c22fbcf821fa3db7531e51343473717',
                           'file_offsets': {'start': 0, 'end': 2048}, 'image_offsets': {'start': 3072, 'end': 5120}},
                          {'number': 2, 'size': 2048,
                           'sha256': '570dc7f7ceea7fa7204588456fd00e53b0abf1cca9d35cc074383e8dcc418114',
                           'file_offsets': {'start': 2048, 'end': 4096}, 'image_offsets': {'start': 512, 'end': 2560}}
                          ]}
        assert sc_meta['files'][2] == {
            'original': {'type': 'filler', 'path': 'zeroes', 'size': 512, 'id': 'uuid',
                         'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560'},
            'fragments': [{'number': 1, 'size': 512,
                           'sha256': '076a27c79e5ace2a3d47f9dd2e83e4ff6ea8872b3c2218f66c92b89b55f36560',
                           'file_offsets': {'start': 0, 'end': 512}, 'image_offsets': {'start': 2560, 'end': 3072}}]}
        assert sc_meta['files'][3]['original']['type'] == 'filler'
        assert sc_meta['files'][3]['original']['path'] == 'random'
        assert sc_meta['files'][3]['original']['size'] == 512
        assert len(sc_meta['files'][3]['fragments']) == 1
        assert sc_meta['files'][3]['fragments'][0]['number'] == 1
        assert sc_meta['files'][3]['fragments'][0]['size'] == 512
        assert sc_meta['files'][3]['fragments'][0]['file_offsets'] == {'start': 0, 'end': 512}
        assert sc_meta['files'][3]['fragments'][0]['image_offsets'] == {'start': 5120, 'end': 5632}
        os.remove(image_path)
        os.remove(metadata_path)


def _replace_uuids(metadata):
    for s in metadata['scenarios']:
        for file_meta in s['files']:
            file_meta['original']['id'] = 'uuid'
    return metadata
