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
     generate  Generate an image based on the given configuration file.


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

