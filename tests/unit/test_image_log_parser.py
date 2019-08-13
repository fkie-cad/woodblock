import io
import json

from woodblock.image import ImageLogParser


class TestFragmentOrder:
    def test_that_the_correct_fragment_order_is_returned_for_a_single_scenario(self):
        log = {
            'scenarios': [{
                'name': 'some scenario',
                'files': [
                    {'fragments': [{'file_offsets': {'end': 2048, 'start': 0},
                                    'image_offsets': {'end': 2048, 'start': 0},
                                    'number': 1, 'size': 2048,
                                    'sha256': '291b808471ca4772e260dd50604e93082c22fbcf821fa3db7531e51343473717'},
                                   {'file_offsets': {'end': 3584, 'start': 2048},
                                    'image_offsets': {'end': 4608, 'start': 3072},
                                    'number': 2, 'size': 1536,
                                    'sha256': '94112c8625704b5644ad0d817619dd8d5f377a441f6f3377c77623aa10c81fb6'},
                                   {'file_offsets': {'end': 4096, 'start': 3584},
                                    'image_offsets': {'end': 6144, 'start': 5632},
                                    'number': 3, 'size': 512,
                                    'sha256': 'a6e1997daf03cbb80714f521a4e01c96762c0750f1b084f551251ccd5d32ae4a'}],
                     'original': {'id': 'be62e9845f3b42ed9be8b7e41b029011', 'size': 4096, 'type': 'file',
                                  'path': '4096',
                                  'sha256': '0ec91e13ced59cfc1f297cfedd8c595a6200ac2b8c99bcc321e8c68cf1f166a0'}},
                    {'fragments': [{'file_offsets': {'end': 1024, 'start': 0},
                                    'image_offsets': {'end': 3072, 'start': 2048},
                                    'number': 1, 'size': 1024,
                                    'sha256': '06aed7f43b72ab019f06f2cbf0a94237ad29cc36d2c91e27a9d3e734c90b665b'}],
                     'original': {'id': '9af6174205774d0d95513ec9278f7d78',
                                  'path': '2000',
                                  'sha256': 'd9b6da39852ccf532d87a2f8a3866ba1a53c0e863b8a35c3665a987bdc8e2554',
                                  'size': 2000, 'type': 'file'}},
                    {'fragments': [{'file_offsets': {'end': 1024, 'start': 0},
                                    'image_offsets': {'end': 5632, 'start': 4608},
                                    'number': 1, 'size': 1024,
                                    'sha256': '06aed7f43b72ab019f06f2cbf0a94237ad29cc36d2c91e27a9d3e734c90b665b'}],
                     'original': {'id': '3043696a5e8d4eba87e63b0e4cca2315', 'size': 1024, 'type': 'file',
                                  'path': '1024',
                                  'sha256': '06aed7f43b72ab019f06f2cbf0a94237ad29cc36d2c91e27a9d3e734c90b665b'}}]
            }]}
        expected = (
            ('some scenario', 'be62e9845f3b42ed9be8b7e41b029011', '4096', 1, 0, 2048, 0, 2048),
            ('some scenario', '9af6174205774d0d95513ec9278f7d78', '2000', 1, 0, 1024, 2048, 3072),
            ('some scenario', 'be62e9845f3b42ed9be8b7e41b029011', '4096', 2, 2048, 3584, 3072, 4608),
            ('some scenario', '3043696a5e8d4eba87e63b0e4cca2315', '1024', 1, 0, 1024, 4608, 5632),
            ('some scenario', 'be62e9845f3b42ed9be8b7e41b029011', '4096', 3, 3584, 4096, 5632, 6144),
        )
        log = io.StringIO(json.dumps(log))
        assert ImageLogParser(log).get_fragment_order() == expected
