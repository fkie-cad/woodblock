import io
import json
import pathlib

from woodblock.image import Image, ImageLogParser

HERE = pathlib.Path(__file__).absolute().parent


class TestImageFromConfig:
    def test_config(self, config_path):
        config = config_path / 'three-scenarios.conf'
        image = Image.from_config(config)
        image.write(pathlib.Path('/tmp/a.dd'))
        meta = image.metadata
        fragment_order = _get_fragment_order_from_metadata(image.metadata)
        file_ids = dict()

        assert meta['block_size'] == 512
        assert meta['seed'] == 123
        assert len(meta['scenarios']) == 3

        s1 = meta['scenarios'][0]
        assert s1['name'] == 'first scenario'
        assert len(s1['files']) == 3
        file_ids['s1'] = {1: fragment_order[0][0], 2: fragment_order[3][0], 3: fragment_order[1][0]}

        s2 = meta['scenarios'][1]
        assert s2['name'] == 'second scenario'
        assert len(s2['files']) == 2
        file_ids['s2'] = {1: fragment_order[5][0], 2: fragment_order[6][0]}
        file_1 = _get_file_with_id(s2, file_ids['s2'][1])
        file_2 = _get_file_with_id(s2, file_ids['s2'][2])
        assert file_1['original']['path'] == '2000'
        assert file_2['original']['path'] == '1024'

        s3 = meta['scenarios'][2]
        assert s3['name'] == 'third scenario'
        assert len(s3['files']) == 3
        file_ids['s3'] = {2: fragment_order[8][0], 3: fragment_order[9][0], 4: fragment_order[11][0]}
        file_1 = _get_file_with_id(s3, file_ids['s3'][2])
        file_3 = _get_file_with_id(s3, file_ids['s3'][3])
        file_4 = _get_file_with_id(s3, file_ids['s3'][4])
        assert file_1['original']['path'] == '4096'
        assert file_3['original']['path'] == 'letters/ascii_letters'
        assert file_4['original']['path'].startswith('letters/')

        expected_fragment_order = (
            (file_ids['s1'][1], 1),
            (file_ids['s1'][3], 1),
            (file_ids['s1'][1], 2),
            (file_ids['s1'][2], 1),
            (file_ids['s1'][1], 3),

            (file_ids['s2'][1], 1),
            (file_ids['s2'][2], 1),
            (file_ids['s2'][1], 3),

            (file_ids['s3'][2], 1),
            (file_ids['s3'][3], 1),
            (file_ids['s3'][2], 2),
            (file_ids['s3'][4], 2),
            (file_ids['s3'][3], 2),
            (file_ids['s3'][4], 1),
            (file_ids['s3'][2], 4),
            (file_ids['s3'][2], 3))

        assert fragment_order == expected_fragment_order


def _get_fragment_order_from_metadata(metadata):
    log = io.StringIO()
    json.dump(metadata, log)
    log.seek(0)
    return tuple((f[1], f[3]) for f in ImageLogParser(log).get_fragment_order())


def _get_file_with_id(metadata, file_id):
    for file in metadata['files']:
        if file['original']['id'] == file_id:
            return file
