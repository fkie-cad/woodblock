"""End-to-end checks that a config-generated image matches its ground-truth JSON.

For every fragment recorded in the ``<image>.json`` file, the SHA-256 of the bytes at the
recorded image offsets must equal the recorded fragment hash. This exercises the full
``from_config`` -> ``write`` path, including random fillers and random padding.
"""

import hashlib
import json
import pathlib

from woodblock.image import Image


def _verify_image_against_log(image_path):
    data = image_path.read_bytes()
    log_path = pathlib.Path('.'.join((str(image_path.absolute()), 'json')))
    log = json.loads(log_path.read_text())
    checked = 0
    for scenario in log['scenarios']:
        for file in scenario['files']:
            for fragment in file['fragments']:
                offsets = fragment['image_offsets']
                on_disk = data[offsets['start']:offsets['end']]
                assert hashlib.sha256(on_disk).hexdigest() == fragment['sha256']
                checked += 1
    assert checked > 0


def test_config_image_matches_its_ground_truth(config_path, tmp_path):
    image_path = tmp_path / 'image.dd'
    Image.from_config(config_path / 'three-scenarios.conf').write(image_path)
    _verify_image_against_log(image_path)


def test_config_image_with_fillers_matches_its_ground_truth(test_corpus_path, tmp_path):
    config = tmp_path / 'with-fillers.conf'
    config.write_text(
        '[general]\n'
        'block size = 512\n'
        'seed = 7\n'
        f'corpus = {test_corpus_path.absolute()}\n'
        '\n'
        '[fragments and fillers]\n'
        'file1 = 4096\n'
        'frags file1 = 3\n'
        'layout = 1-1, R, 1-2, Z, 1-3\n'
    )
    image_path = tmp_path / 'image.dd'
    Image.from_config(config).write(image_path)
    _verify_image_against_log(image_path)


def test_writing_the_same_config_image_twice_is_reproducible(config_path, tmp_path):
    config = config_path / 'three-scenarios.conf'

    first = tmp_path / 'first.dd'
    Image.from_config(config).write(first)

    second = tmp_path / 'second.dd'
    Image.from_config(config).write(second)

    assert first.read_bytes() == second.read_bytes()
