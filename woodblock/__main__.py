import argparse
import pathlib
import sys

import woodblock


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    args = _parse_command_line(argv)
    if args.command == 'generate':
        _generate_image_from_config(config=args.config, image_path=args.image, corpus=args.corpus)


def _parse_command_line(argv):
    parser = argparse.ArgumentParser(description='Woodblock file carving generator')
    subparsers = parser.add_subparsers(title='commands', dest='command')
    generate_cmd_parser = subparsers.add_parser('generate', help='Generate an image')
    generate_cmd_parser.add_argument('config', help='Path to the configuration file')
    generate_cmd_parser.add_argument('corpus', help='Path to the file corpus')
    generate_cmd_parser.add_argument('image', help='Output path for the image')
    return parser.parse_args(argv)


def _generate_image_from_config(config, image_path, corpus):
    woodblock.file.corpus(corpus)
    image = woodblock.image.Image.from_config(pathlib.Path(config))
    image.write(pathlib.Path(image_path))


if __name__ == '__main__':
    sys.exit(main())
