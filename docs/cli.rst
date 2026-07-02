.. _cli-tool:

*****************
Command Line Tool
*****************

Woodblock comes with a small and simple command line tool. The main 
purpose of this tool is to generate the actual image files from your 
[configuration files](configs.md).

Currently, the help of the :code:`woodblock` command looks like this:

.. code-block::

   $ woodblock --help
   Usage: woodblock [OPTIONS] COMMAND [ARGS]...

   Options:
     -h, --help  Show this message and exit.

   Commands:
     generate   Generate an image based on the given configuration file.
     visualize  Build an interactive HTML visualization from a ground-truth file.


Generate Image Files
####################
To generate an image based on a configuration file, use the
:code:`generate` subcommand:

.. code-block::

   $ woodblock generate path/to/your/config.conf output/path.dd

This generates the image :code:`output/path.dd` based on the configuration
file :code:`path/to/your/config.conf`. Moreover, the ground truth file
:code:`output/path.dd.json` will be written. Note that all path definitions in
your config are relative to the configuration file and not relative to your
current working directory, whereas all paths given on the command line are
relative to your current working directory.


Visualize Image Files
######################
To explore a generated image interactively, use the :code:`visualize`
subcommand. It builds a self-contained HTML file (no internet connection or
web server required -- just open it in a browser) from a ground truth file:

.. code-block::

   $ woodblock visualize output/path.dd.json --image output/path.dd

This writes :code:`output/path.dd.html` containing

* a color-coded map of the whole image in which every source file has its own
  color and hovering a fragment highlights all fragments of the same file,
* a list of the files contained in the image, and
* a hex viewer to inspect the bytes that were actually written to the image.

Passing :code:`--image` embeds the image bytes so the hex viewer works right
away. For large images the bytes are not embedded; instead the viewer lets you
select the image file in the browser and reads it on demand. Use
:code:`--output` to control where the HTML file is written.

You can also produce the visualization in one step while generating an image by
passing :code:`--visualize` to the :code:`generate` subcommand:

.. code-block::

   $ woodblock generate path/to/your/config.conf output/path.dd --visualize

