import hashlib
import pathlib

from woodblock.image import Image

HERE = pathlib.Path(__file__).absolute().parent


def test_two_consecutive_image_creations(config_path):
    image_path = pathlib.Path('/tmp/reproduce-me.dd')
    config = config_path / 'three-scenarios.conf'
    image = Image.from_config(config)
    image.write(image_path)
    image_digest = hashlib.sha256(image_path.open('rb').read()).hexdigest()

    image = Image.from_config(config)
    image.write(pathlib.Path('/tmp/reproduce-me.dd'))

    assert image_digest == hashlib.sha256(image_path.open('rb').read()).hexdigest()
