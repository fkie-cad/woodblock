import pathlib
import sys

import click

import woodblock

CONTEXT_SETTINGS = {'help_option_names': ['-h', '--help']}


@click.group(context_settings=CONTEXT_SETTINGS)
def main():
    pass


@main.command(name='generate')
@click.argument('config', type=click.Path(exists=True))
@click.argument('image', type=click.Path())
@click.option('--visualize', is_flag=True, help='Also write an interactive HTML visualization (IMAGE.html).')
def generate_image(config, image, visualize):
    """Generate an image based on the given configuration file.

    \b
    CONFIG is the path to the configuration file to use.
    IMAGE  is the output path of the generated image."""
    image_path = pathlib.Path(image)
    img = woodblock.image.Image.from_config(pathlib.Path(config))
    img.write(image_path)
    if visualize:
        output = woodblock.visualization.create_visualization(
            image_path.with_name(image_path.name + '.json'), image_path
        )
        click.echo(f'Visualization written to {output}')


@main.command(name='visualize')
@click.argument('metadata', type=click.Path(exists=True))
@click.option('-i', '--image', type=click.Path(exists=True), help='Image whose bytes feed the hex viewer.')
@click.option('-o', '--output', type=click.Path(), help='Output HTML path (default: derived from IMAGE/METADATA).')
def visualize_image(metadata, image, output):
    """Build an interactive HTML visualization from a ground-truth file.

    \b
    METADATA is the path to a ground-truth ".json" file written alongside an image.
    Pass --image to embed the image bytes so the hex viewer works without further interaction."""
    out = woodblock.visualization.create_visualization(metadata, image=image, output=output)
    click.echo(f'Visualization written to {out}')


if __name__ == '__main__':
    sys.exit(main())
