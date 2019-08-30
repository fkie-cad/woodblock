.. _configuration-files:

*******************
Configuration Files
*******************

Most test images can be created using configuration files.
They are easy to write and do not require any coding at all.
For more complex scenarios not covered by the configuration files, 
have a look at how to use the :ref:`Woodblock Python API <woodblock-python-api>`.

Configuration File Structure
============================

A Woodblock configuration files use a simple INI syntax.
Here is a simple example with one scenario:

.. code-block:: ini

   [general]
   block size = 4096
   seed = 123
   corpus = ../test_file_corpus/
   
   [my first scenario]
   frags file1 = 3
   frags file2 = 1
   frags file3 = 2
   layout = 1-1, 3-1, 1-2, 2-1, 1-3, 3-2

The following paragraphs describe the available options in more detail.

.. ini:option:: block size
   
   | **Required:** no
   | **Default:** 512
   
   The :code:`block size` option defines the block size to be used for the
   image file. When using the configuration file, all fragments of the
   scenarios will be aligned and padded according to this size. The padding
   will be made up of random data.

.. ini:option:: corpus
   
   | **Required:** yes
   | **Default:** `None`  
   
   The path (relative to the configuration file) to the corpus to be used.

.. ini:option:: seed
   
   | **Required:** no
   | **Default:** randomly generated integer
   
   The seed for the random number generator. If you do not specify a seed
   explicitly, Woodblock will generate a random seed for you.

.. ini:option:: min filler blocks
   
   | **Required:** no
   | **Default:** 1
   
   This parameter defines the minimum number of blocks for filler fragments.
   The actual size of a filler fragments will be randomly chosen from the
   interval [`min filler blocks`, `max filler blocks`], including both endpoints.

.. ini:option:: max filler blocks
   
   | **Required:** no
   | **Default:** 10
   
   This parameter defines the maximum number of blocks for filler fragments.
   The actual size of a filler fragments will be randomly chosen from the
   interval [`min filler blocks`, `max filler blocks`], including both endpoints.


Scenario Sections
=================
As already mentioned, every section apart from :code:`[general]` is considered to be
a scenario section. As the name implies a scenario section defines a scenario
to be included in the final image. The name of the section will be the name of
the scenario and the order of appearance of the sections in the configuration
file corresponds to the order of the scenarios in the image.

The supported and required options of a scenario section depend on the layout
type of the scenario you want to generate.

.. ini:option:: layout
   
   | **Required:** yes
   | **Default:** None
   
   As the name implies, this option defines the layout of the scenario. It can be
   either :code:`intertwine` to create intertwined scenarios or a comma-separated list
   of *fragment identifiers*. We will cover both options in the next sections in
   more details.

Creating Intertwined Scenarios
******************************
Creating intertwined scenarios is really easy using the configuration file.
All you have to do is provide the number of files that you want to have.
Optionally, you can specify the minimal and maximal number of fragments per
file.

A complete section for an intertwined scenario looks like this:

.. code-block: ini
   
   [An intertwined scenario]
   layout = intertwine
   num files = 4
   min frags = 2
   max frags = 5

An intertwined scenario created with a section like the one above will have
the following properties.
 
- There will be `num files` files in the scenario.
- Each of these files will be split into [`min frags`, `max frags`] fragments (endpoints are included).
- The fragments of each file will be in order, i.e. fragment 1 comes before fragment 2 which comes before fragment 3 and so on.
- No two fragments of the same file will be adjacent to one other.

.. ini:option:: layout = intertwine
   
   In order to have Woodblock create an intertwined scenario for you, the
   :code:`layout` option has to be set to :code:`intertwine`.

.. ini:option:: num files
   
   | **Required:** yes
   | **Default:** `None`
   
   This options defines the number of files to include in the scenario. Note that
   it is not possible to specify specific files here. Instead, Woodblock will
   randomly pick files which can be fragmented according to your :code:`min frags` and
   :code:`max frags` constraints.

.. ini:option:: min frags
   
   | **Required:** no
   | **Default:** 1
   
   This option defines the minimal number of fragments to split a file into.

.. ini:option:: max frags
   
   | **Required:** no
   | **Default:** 4
   
   This option defines the maximal number of fragments to split a file into. Note
   that :code:`max frags` has to be ≥ :code:`min frags`.

Manually Specifying a Scenario Layout
***************************************
If you are not creating an intertwined scenario, you have to specify the
layout of the scenario yourself. This is, however, almost as easy as using
the :code:`intertwine` keyword.

Here is an example for a simple scenario:

.. code-block:: ini

   [A Simple Scenario]
   frags file1 = 2
   frags file2 = 3
   layout = 1.1, 2.3, 2.2, 1.2, 2.1

This definition randomly chooses two files from the corpus, splits the first
one into two fragments and the second into three, and generates the following
fragment order:

.. image:: images/usage-simple-scenario-layout.png
   :alt: a simple scenario layout

Note that the size of the individual fragments is chosen randomly as a
multiple of the block size defined in the general section.

So, how did this work? The option :code:`frags fileN` tells Woodblock to pick
file :code:`N` and split it into the corresponding number of fragments. :code:`N`
has to be an integer and refers to the :code:`N`:sup:`th` file in the scenario. As
we did not define a
specify file (more on this later), random files from the corpus will be picked.
Then, in the `layout` line, we defined the fragment order, that we would like
to have. The order is a comma-separated list of *fragment identifiers*. A
fragment identifier is composed of the file number and the fragments number,
separated by either a dot (:code:`.`) or a hyphen (:code:`-`). That is, if you would like
to reference the fourth fragment of the second file, then you could write
either :code:`2.4` or :code:`2-4`.

If you want to specify which files Woodblock should use, you can do this using
the :code:`fileN` option. For instance, if you want one random file and one
specific file, then you could modify the above configuration:

.. code-block:: ini
   
   [A Simple Scenario]
   file2 = path/to/some/file.jpg
   frags file1 = 2
   frags file2 = 3
   layout = 1.1, 2.3, 2.2, 1.2, 2.1

Adding the :code:`file2` option, tells Woodblock to choose the file 
:code:`path/to/some/file.jpg` as the second file. The path is relative
to the file corpus defined in the :code:`[general]` section. The first
file will still be chosen randomly.


Filler Fragments
****************
Filler fragments can be added by adding an :code:`R` or :code:`Z` to the
:code:`layout` of the scenario (both, upper and lower case letters work).
:code:`R` adds a random data fragment and :code:`Z` adds a fragment filled
with zeroes. As described in the :code:`[general]` section, the size of the
filler fragment depends on the values of :code:`min filler blocks` and
:code:`max filler blocks`. These can be specified in the :code:`[general]`
section as well as in a scenario section. The definition in a scenario section
has precedence over a definition in the :code:`[general]` section.

Here is a simple scenario definition with fillers:

.. code-block:: ini
   
   [A Simple Scenario with Filler]
   frags file1 = 2
   layout = 1.1, R, 1.2, Z

This creates a scenario looking like this:

.. image:: images/file_with_fillers.png
   :alt: scenario layout with fillers

We have the first fragment of the file, then some random data, then
the second fragment, and finally some blocks filled with zeroes.


Multiple Scenarios
******************
As already mentioned, every section except for the one named :code:`[general]`
is considered to be a scenario. Therefore, defining multiple scenarios boils
down to creating multiple sections in a configuration file:

Here is an example defining three scenarios:

.. code-block:: ini

   [First Scenario]
   frags file1 = 2
   layout = 1.1, R, 1.2, Z
   
   [Second Scenario]
   file2 = path/to/some/file.jpg
   frags file1 = 2
   frags file2 = 3
   layout = 1.1, 2.3, 2.2, 1.2, 2.1
   
   [Last Scenario]
   layout = intertwine
   num files = 4
   min frags = 2
   max frags = 5


Again, the order of the scenarios in the resulting test image corresponds
to the order of the definition in the configuration file.

Note that Woodblock will not add any additional blocks between two scenarios.
That is, the first block of the second scenario will be next to the last block
of the first scenario. If you would like to have filler blocks between two
scenarios, you have to add filler blocks to the beginning or end of a scenario.


Option Reference
****************
This sections provides a brief description of all the options available in a
scenario section.

+---------------------+----------+---------+-------------+-------------------------------------------------------------------------------------+
| Option              | Required | Default | Layout Type | Description                                                                         |
+=====================+==========+=========+=============+=====================================================================================+
| :code:`fileN`       | no       | *n/a*   | manual      | Path to the :code:`N`:sup:`th` file to use. Path is relative to the file corpus.    |
+---------------------+----------+---------+-------------+-------------------------------------------------------------------------------------+
| :code:`frags fileN` | no       | *n/a*   | manual      | Number of fragments to split the :code:`N`:sup:`th` into.                           |
+---------------------+----------+---------+-------------+-------------------------------------------------------------------------------------+
| :code:`layout`      | yes      | *n/a*   | all         | Defines the layout type. It can be either `intertwine` or a fragment specification. |
+---------------------+----------+---------+-------------+-------------------------------------------------------------------------------------+
| :code:`min frags`   | no       | 1       | intertwine  | Defines the minimal number of fragments per file.                                   |
+---------------------+----------+---------+-------------+-------------------------------------------------------------------------------------+
| :code:`max frags`   | no       | 4       | intertwine  | Defines the maximal number of fragments per file.                                   |
+---------------------+----------+---------+-------------+-------------------------------------------------------------------------------------+
| :code:`num files`   | yes      | *n/a*   | intertwine  | Defines the number of files to intertwine.                                          |
+---------------------+----------+---------+-------------+-------------------------------------------------------------------------------------+

Generating an Image
===================
To generate an image based on a configuration file, use the :code:`woodblock`
:ref:`command line tool <cli-tool>`.
