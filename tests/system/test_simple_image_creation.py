import json
import os
import pathlib

import woodblock
from woodblock.file import File, get_corpus
from woodblock.fragments import ZeroesFragment, FillerFragment
from woodblock.image import Image
from woodblock.scenario import Scenario

HERE = pathlib.Path(__file__).absolute().parent


class TestSimpleImageCreation:

    def test_an_image_with_a_single_zeroes_fragment(self, test_corpus_path):
        woodblock.random.seed(13)
        woodblock.file.corpus(test_corpus_path)
        image_path = HERE / 'simple-zeroes.dd'
        metadata_path = pathlib.Path('.'.join((str(image_path), 'json')))
        s = Scenario('simple zeroes')
        s.add(ZeroesFragment(1024))
        image = Image()
        image.add(s)
        image.write(image_path)
        assert image_path.is_file()
        assert image_path.stat().st_size == 1024
        assert image_path.open('rb').read() == b'\x00' * 1024
        assert metadata_path.is_file()
        assert _replace_uuids(json.load(metadata_path.open('r'))) == {
            'block_size': 512,
            'corpus': str(test_corpus_path),
            'seed': woodblock.random.get_seed(),
            'scenarios': [
                {'name': 'simple zeroes',
                 'files': [
                     {'original': {'type': 'filler', 'path': 'zeroes',
                                   'size': 1024, 'id': 'uuid',
                                   'sha256': '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef'},
                      'fragments': [{
                          'number': 1, 'size': 1024,
                          'sha256': '5f70bf18a086007016e948b04aed3b82103a36bea41755b6cddfaf10ace3c6ef',
                          'file_offsets': {'start': 0, 'end': 1024},
                          'image_offsets': {'start': 0, 'end': 1024}}]
                      }]}]}
        os.remove(image_path)
        os.remove(metadata_path)

    def test_an_image_padding_with_a_single_zeroes_fragment(self, test_corpus_path):
        woodblock.random.seed(13)
        woodblock.file.corpus(test_corpus_path)
        image_path = HERE / 'simple-zeroes-with-padding.dd'
        metadata_path = pathlib.Path('.'.join((str(image_path), 'json')))
        s = Scenario('simple zeroes with padding')
        s.add(ZeroesFragment(1000))
        image = Image(block_size=512, padding_generator=lambda x: b'A' * x)
        image.add(s)
        image.write(image_path)
        assert image_path.is_file()
        assert image_path.stat().st_size == 1024
        assert image_path.open('rb').read() == b''.join((b'\x00' * 1000, b'A' * 24))
        assert metadata_path.is_file()
        metadata = _replace_uuids(json.load(metadata_path.open('r')))
        assert metadata == {
            'block_size': 512,
            'corpus': str(test_corpus_path),
            'seed': woodblock.random.get_seed(),
            'scenarios': [
                {'name': 'simple zeroes with padding',
                 'files': [
                     {'original': {'type': 'filler', 'path': 'zeroes',
                                   'size': 1000, 'id': 'uuid',
                                   'sha256': '541b3e9daa09b20bf85fa273e5cbd3e80185aa4ec298e765db87742b70138a53'},
                      'fragments': [{
                          'number': 1, 'size': 1000,
                          'sha256': '541b3e9daa09b20bf85fa273e5cbd3e80185aa4ec298e765db87742b70138a53',
                          'file_offsets': {'start': 0, 'end': 1000},
                          'image_offsets': {'start': 0, 'end': 1000}}]
                      }]}]}
        os.remove(image_path)
        os.remove(metadata_path)

    def test_an_image_padding_and_two_zeroes_fragments(self, test_corpus_path):
        woodblock.random.seed(13)
        woodblock.file.corpus(test_corpus_path)
        image_path = HERE / 'two-zeroes-with-padding.dd'
        metadata_path = pathlib.Path('.'.join((str(image_path), 'json')))
        s = Scenario('two zeroes with padding')
        s.add(ZeroesFragment(1000))
        s.add(ZeroesFragment(2048))
        image = Image(block_size=512, padding_generator=lambda x: b'A' * x)
        image.add(s)
        image.write(image_path)
        assert image_path.is_file()
        assert image_path.stat().st_size == 1024 + 2048
        assert image_path.open('rb').read() == b''.join((b'\x00' * 1000, b'A' * 24, b'\x00' * 2048))
        assert metadata_path.is_file()
        metadata = _replace_uuids(json.load(open(metadata_path, 'r')))
        assert metadata == {
            'block_size': 512,
            'corpus': str(test_corpus_path),
            'seed': woodblock.random.get_seed(),
            'scenarios': [
                {'name': 'two zeroes with padding',
                 'files': [
                     {'original': {
                         'type': 'filler', 'path': 'zeroes', 'size': 1000, 'id': 'uuid',
                         'sha256': '541b3e9daa09b20bf85fa273e5cbd3e80185aa4ec298e765db87742b70138a53'},
                         'fragments': [{
                             'number': 1, 'size': 1000,
                             'sha256': '541b3e9daa09b20bf85fa273e5cbd3e80185aa4ec298e765db87742b70138a53',
                             'file_offsets': {'start': 0, 'end': 1000},
                             'image_offsets': {'start': 0, 'end': 1000}}]},
                     {'original': {'type': 'filler', 'path': 'zeroes', 'size': 2048, 'id': 'uuid',
                                   'sha256': 'e5a00aa9991ac8a5ee3109844d84a55583bd20572ad3ffcd42792f3c36b183ad'},
                      'fragments': [{
                          'number': 1, 'size': 2048,
                          'sha256': 'e5a00aa9991ac8a5ee3109844d84a55583bd20572ad3ffcd42792f3c36b183ad',
                          'file_offsets': {'start': 0, 'end': 2048},
                          'image_offsets': {'start': 1024, 'end': 3072}}]
                      }
                 ]}]}
        os.remove(image_path)
        os.remove(metadata_path)

    def test_an_image_with_a_single_file_fragment(self, test_corpus_path):
        woodblock.random.seed(13)
        woodblock.file.corpus(test_corpus_path)
        image_path = HERE / 'simple-file.dd'
        metadata_path = pathlib.Path('.'.join((str(image_path), 'json')))
        s = Scenario('simple file fragment')
        s.add(File(test_corpus_path / '512').as_fragment())
        image = Image(block_size=512)
        image.add(s)
        image.write(image_path)
        assert image_path.is_file()
        assert image_path.stat().st_size == 512
        assert image_path.open('rb').read() == b'A' * 512
        assert metadata_path.is_file()
        assert _replace_uuids(json.load(metadata_path.open('r'))) == {
            'block_size': 512,
            'corpus': str(test_corpus_path),
            'seed': woodblock.random.get_seed(),
            'scenarios': [
                {'name': 'simple file fragment',
                 'files': [
                     {'original': {'type': 'file',
                                   'path': str((HERE.parent / 'data' / 'corpus' / '512').relative_to(get_corpus())),
                                   'size': 512, 'id': 'uuid',
                                   'sha256': '32beecb58a128af8248504600bd203dcc676adf41045300485655e6b8780a01d'},
                      'fragments': [{
                          'number': 1, 'size': 512,
                          'sha256': '32beecb58a128af8248504600bd203dcc676adf41045300485655e6b8780a01d',
                          'file_offsets': {'start': 0, 'end': 512},
                          'image_offsets': {'start': 0, 'end': 512}}]
                      }]}]}
        os.remove(image_path)
        os.remove(metadata_path)

    def test_an_image_with_a_single_filler_fragment(self, test_corpus_path):
        woodblock.random.seed(13)
        woodblock.file.corpus(test_corpus_path)
        image_path = HERE / 'simple-filler.dd'
        metadata_path = pathlib.Path('.'.join((str(image_path), 'json')))
        s = Scenario('simple filler fragment')
        s.add(FillerFragment(1024))
        image = Image(block_size=512)
        image.add(s)
        image.write(image_path)
        assert image_path.is_file()
        assert image_path.stat().st_size == 1024
        assert metadata_path.is_file()
        meta = json.load(metadata_path.open('r'))
        assert meta['block_size'] == 512
        assert meta['seed'] == 13
        assert len(meta['scenarios']) == 1
        assert len(meta['scenarios'][0]['files']) == 1
        assert meta['scenarios'][0]['files'][0]['original']['type'] == 'filler'
        assert meta['scenarios'][0]['files'][0]['original']['size'] == 1024
        assert len(meta['scenarios'][0]['files'][0]['fragments']) == 1
        assert meta['scenarios'][0]['files'][0]['fragments'][0]['number'] == 1
        assert meta['scenarios'][0]['files'][0]['fragments'][0]['size'] == 1024
        assert meta['scenarios'][0]['files'][0]['fragments'][0]['file_offsets'] == {'start': 0, 'end': 1024}
        assert meta['scenarios'][0]['files'][0]['fragments'][0]['image_offsets'] == {'start': 0, 'end': 1024}
        os.remove(image_path)
        os.remove(metadata_path)


def _replace_uuids(metadata):
    for s in metadata['scenarios']:
        for file_meta in s['files']:
            file_meta['original']['id'] = 'uuid'
    return metadata
