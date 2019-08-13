import json
import os
import pathlib

import woodblock
from woodblock.file import File, get_corpus
from woodblock.fragments import ZeroesFragment, RandomDataFragment
from woodblock.image import Image
from woodblock.scenario import Scenario

HERE = pathlib.Path(__file__).absolute().parent


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
