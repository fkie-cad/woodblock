.. _woodblock-python-api:

**********
Python API
**********

For most use cases, the :ref:`configuration-files` should suffice.
If you need more fine-grained control over your scenarios you can use the
Python API. For instance, the API lets you define the exact fragmentation
points of your files, exact sizes of filler fragments, and so forth.

Here is a simple script illustrating the basic usage of the API:

.. code-block:: python
   
   #!/usr/bin/env python3
   import pathlib
   import sys
   
   from woodblock.file import File, draw_files
   from woodblock.fragments import RandomDataFragment, ZeroesFragment
   from woodblock.image import Image
   from woodblock.scenario import Scenario
   
   HERE = pathlib.Path(__file__).absolute().parent
   
   
   def main():
       woodblock.file.corpus(HERE / '..' / 'data' / 'corpus')
       files = draw_files(number_of_files=2)
       f_a = files[0].fragment_randomly(num_fragments=3)
       f_b = files[1].fragment_evenly(num_fragments=2)
   
       s = Scenario('First API Scenario')
       s.add(f_a[1])
       s.add(ZeroesFragment(1024))
       s.add(f_b[0])
       s.add(f_a[2])
       s.add(RandomDataFragment(512))
       s.add(f_a[0])
       s.add(f_b[1])
   
       image = Image(block_size=512)
       image.add(s)
       image.write(HERE / 'api-demo.dd')
   
    
   if __name__ == '__main__':
       sys.exit(main())

This script randomly chooses two files from the file corpus. The first one is
split into three fragments at random fragmentation points, the second one is
split into two fragments of equal size. After that the scenario with the name 
“First API Scenario” is created and the file fragments as well as two filler
fragments are added to the scenario. Finally, the scenario is added to an
image object which is then written to disk.

Let’s go through this example step by step. The first lines are just some
imports.

.. code-block:: python
   
   from woodblock.file import File, draw_files
   from woodblock.fragments import RandomDataFragment, ZeroesFragment
   from woodblock.image import Image
   from woodblock.scenario import Scenario

After we define the file corpus and randomly draw two files:

.. code-block:: python
   
   woodblock.file.corpus(HERE / '..' / 'data' / 'corpus')
   files = draw_files(number_of_files=2)

These files are then split into fragments. The first file is split into three
fragments. The fragmentation points are chosen randomly. The second file is
split into two fragments. The fragmentation point is chosen so that both
fragments are of equal size:

.. code-block:: python
   
   f_a = files[0].fragment_randomly(num_fragments=3)
   f_b = files[1].fragment_evenly(num_fragments=2)

After that, a :code:`Scenario` object is created. Its argument is the name
of the scenario:

.. code-block:: python
   
   s = Scenario('First API Scenario')

A :code:`Scenario` object has a method to :code:`add` fragments to it.
A call to :code:`add` appends a fragment to any previously added fragments,
so that the order of the :code:`add` calls defines the order of the
fragments in the scenario:

.. code-block:: python
   
   s.add(f_a[1])
   s.add(ZeroesFragment(1024))
   s.add(f_b[0])
   s.add(f_a[2])
   s.add(RandomDataFragment(512))
   s.add(f_a[0])
   s.add(f_b[1])

We did not only added the fragments of our files but also two filler
fragments: a :code:`ZeroesFragment` of 1024 bytes of size and a
:code:`RandomDataFragment` of 512 bytes of size. As you can see, you
can specify the exact size of the filler fragments using the API.

After that, our scenario is complete and we create an :code:`Image`
object with a block size of 512 bytes. :code:`Image` objects represent
test image files to be written to disk. Just like we could add fragments
to a scenario, we can add scenarios to an :code:`Image`. If we added all
of the scenarios, we can finally write the image using the :code:`write`
method.

Those are already the basic blocks you need to create your own test images
using the API: you select files from the test file corpus, fragments them
in some way, add the fragments to a scenario, add the scenario to an image,
and finally write the image to disk.

The following sections describe the available API functions and objects in
a more detailed way.


Files and Fragments
*******************
Files are always selected from a file corpus. Therefore, you have to specify
the path to your file corpus before you can select any files. This is done
using the :code:`woodblock.files.corpus` function. This function takes the path
to your file corpus as its only argument. An example call would look like this:

.. code-block:: python
   
   # You can provide the path using a string...
   woodblock.file.corpus('path/to/your/corpus/')
   # ... or via a pathlib.Path object
   path = pathlib.Path('path/to/your/corpus/')
   woodblock.file.corpus(path)

Once you have defined your corpus, you can start using its files. If you do
not care which exact files to use from your corpus, you can use the
:code:`draw_files` function, which randomly chooses the given number of files
from your corpus. The function lets you not only specify the number of files
but also the minimal size of each files. Moreover, you can specify if duplicate
files are allowed or not. Duplicate files are basically two different objects
pointing to the same original file. Finally, you can indicate that you want
the files to be drawn only from a special subdirectory of your corpus. The
following examples show how to use this function:

.. code-block:: python
   
   # This will give you one randomly chosen file:
   single_file = woodblock.file.draw_files()
   
   # Here is an example with four randomly chosen files:
   files = woodblock.file.draw_files(number_of_files=4)
   
   # Now we want three files, but only from the jpeg/ subdirectory:
   files = woodblock.file.draw_files(path='jpeg', number_of_files=3)
   
   # The same but only files with a minimal size of 2 MB:
   files = woodblock.file.draw_files(path='jpeg', number_of_files=3, min_size=2*1024**2)
   
   # Finally, choose ten files without duplicates:
   files = woodblock.file.draw_files(number_of_files=10, unique=True)

Note that :code:`draw_files` always returns a list of :code:`File` objects,
that is, even :code:`single_file` is a list (with only one item).

:code:`File` objects represent files from your corpus. If you don't want to use
:code:`draw_files` to get your :code:`File` objects, you can create them manually.
This allows you to choose specific files from your corpus. To create a :code:`File`
object, simply pass the path of the file you want (relative to the corpus)
to the constructor:

.. code-block:: python
   
   some_file = woodblock.file.File('some/path/relative/to/the/corpus.jpg')

:code:`File` objects provide some methods returning metadata about the file they
represent. For example, there are the methods :code:`size`, :code:`path`,
:code:`id`, and :code:`hash` which return just what you would expect from the names.

More interesting are the methods used to split a file into fragments. Here, we
have :code:`as_fragment`, :code:`fragment`, :code:`fragment_evenly`, and
:code:`fragment_randomly`. The first one simply converts the file into a single
fragment. This is can be used, when you want to add a contiguous file to your
scenario (:code:`Scenario` objects can only be used with fragments; see below).
:code:`fragment` can be used to fragment a file at specific fragmentation points.
:code:`fragment_evenly` and :code:`fragment_randomly` are convenience methods, which
split a file into a given number of evenly sized fragments or into a given number of
randomly sized fragments. The following snippet provides some usage examples for the
methods to fragment a file:

.. code-block:: python
   
   # some_file as a single fragment:
   contiguous = some_file.as_fragment()
   
   # some_file spit at specific fragmentation points. Fragmentation points are
   # defined with respect to the block_size, i.e. the following example splits
   # the file at bytes 1024, 1536, and 3584:
   fragments = some_file.fragment(fragmentation_points=(2, 3, 7), block_size=512)
   
   # Split some_file into three evenly sized fragments:
   evenly_fragmented = some_file.fragment_evenly(num_fragments=3, block_size=512)
   # or shorter:
   evenly_fragmented = some_file.fragment_evenly(3)
   
   # Split some_file into three fragments at random fragmentation points:
   randomly_fragmented: some_file.fragment_randomly(num_fragments=3, block_size=512)
   # or shorter:
   randomly_fragmented: some_file.fragment_randomly(3)

These methods give you a high level of control to create very specific
fragmentation scenarios. However, if you just want some fragmented files,
Woodblock has some convenience functions for you. :code:`draw_fragmented_files`
basically combines :code:`draw_files` and :code:`File.fragment_randomly`
and gives you a list of fragment lists.

.. code-block:: python
   
   from woodblock.file import draw_fragmented_files
   
   # Three fragmented files:
   fragments = draw_fragmented_files(number_of_files=3)
   
   # Three fragmented files from the png/large subdirectory:
   fragments = draw_fragmented_files(path='png/large', number_of_files=3)
   
   # Three fragmented files each split into at least three and at most six fragments:
   fragments = draw_fragmented_files(number_of_files=3, min_fragments=3, max_fragments=6)

Since scenarios with intertwined files (or braided files as they are sometimes
called) are quite common, Woodblock provides a helper function for this, too.
:code:`intertwine_randomly` chooses a given number of files from your corpus, splits
them into fragments, and orders the fragments for you. Again, there are
various arguments that you can pass to the function:

.. code-block:: python
   
   from woodblock.file import intertwine_randomly
   
   # Intertwine three files:
   intertwined = intertwine_randomly(number_of_files=3)
   
   # Intertwine three files from the png/large subdirectory:
   intertwined = intertwine_randomly(path='png/large', number_of_files=3)
   
   # Intertwine two files and make sure that each file has
   # at least three and at most six fragments:
   intertwined = intertwine_randomly(number_of_files=3, min_fragments=3, max_fragments=6)

Note that :code:`intertwine_randomly` makes sure that fragments of the
same file are never next to each other.

All of the different fragmentation functions and methods described above
create :code:`FileFragment` objects. A :code:`FileFragment` represents a
fragment of a file from your corpus. Additionally, Woodblock provides special
fragment types for synthetic data. For instance, you can create a region of
zero bytes using the :code:`ZeroesFragment`. This is useful, if you want to
simulate unused or wiped disk areas. Here's how to create a fragment filled
with :code:`0x00` of 4096 bytes of size:

.. code-block:: python
   
   zeroes = woodblock.fragments.ZeroesFragment(size=4096)

Creating a fragment of 4096 bytes of size filled with random data is equally
simple:

.. code-block:: python
   
   random_data = woodblock.fragments.RandomDataFragment(size=4096)

ll of the different fragment types have various methods to provide
information about themselves: you can query the :code:`size` and the
SHA-256 :code:`hash` as well as a dictionary containing all of the
:code:`metadata` of the fragment.

Now that we know how to create fragments, let's find out how to create a
carving test scenario out of them.

Scenarios
*********
A :code:`Scenario` object represents a test scenario for a file carver.
That is, it consists of a certain number of file fragments arranged in a
certain order. Moreover, a scenario can contain filler fragments such as
the ones described above (e.g. :code:`ZeroesFragment` or
:code:`RandomDataFragment`).

To create such a scenario using the Woodblock API, simply create an instance
of the :code:`Scenario` class:

.. code-block:: python
   
   scenario = woodblock.scenario.Scenario('A simple scenario')

The parameter provided to :code:`Scenario` is the name of the scenario. This
name appears in the ground truth files generated and should be as descriptive as
possible. Have a look at the descriptions used in the
`DFRWS 2007 File Image Layout page`_ for inspiration.

After you created a :code:`Scenario` instance, you can add fragments to it:

.. code-block:: python
   
   import woodblock
   from woodblock.file import File
   from woodblock.fragments import RandomDataFragment, ZeroesFragment

   scenario = woodblock.scenario.Scenario('contiguous file with filler before and after')

   scenario.add(ZeroesFragment(size=4096))
   scenario.add(File('some/path/relative/to/the/corpus.jpg').as_fragment())
   scenario.add(RandomDataFragment(size=4096))

The example above creates the scenario “contiguous file with filler before 
and after” consisting of 4096 zero bytes, then the contiguously stored file 
“some/path/relative/to/the/corpus.jpg”, and finally 4096 bytes of random data.
The order in which fragments are added to the scenario is the order in which
these fragments will be written to disk later on.

The :code:`add` method does not only take single fragments, but also lists of
fragments. This is convenient if you are, well, working with lists of
fragments:

.. code-block:: python
   
   import woodblock
   from woodblock.file import File

   scenario = woodblock.scenario.Scenario('single file with reversed fragments')

   fragments = File('some/file.txt').fragment_randomly(5)
   fragments.reverse()

   scenario.add(fragments)

This is already everything you need to create a scenario. The next step is to
add your scenario to an image file which is written to disk.

Images
******
:code:`Image` objects represent actual test files that you can provide as input
to the carvers you want to evaluate. An image contains one or more scenarios and
can be written to disk as an actual file. Moreover, when being written an
additional log file is written containing the ground truth about this image.
That is, it specifies which files are contained in the image and at which
offsets their fragments are.

Creating an :code:`Image` instance is as easy as:

.. code-block:: python
   
   import woodblock

   # By default an image has a block size of 512 bytes:
   image = woodblock.image.Image()

   # But you can change the block size:
   image4k = woodblock.image.Image(block_size=4096)

As you can see from the examples above, an image has a fixed block size. This
means that any fragment in this image is padded to this block size. Consider
for instance the image and the fragments shown below. The image has a fixed
block size but the size of the fragments B and A.2 are no multiples of this
block size.

.. image: images/image-padding-01.png
   :alt: image and fragments without padding

The padding introduced by the :code:`Image` instance will align the fragments
to the block size specified in the constructor. That is, padding data will be
appended to B and A.2. This is indicated by the dark gray areas labeled with
“p”.

.. image: images/image-padding-02.png
   :alt: image and fragments with padding

By default, random data is used where padding is required. However, you can
provide your own data generator when creating your :code:`Image` instance.
For example you can use :code:`0x00` as padding like this:

.. code-block:: python
   
   zeroes_padding = woodblock.datagen.Zeroes()
   image = woodblock.image.Image(padding_generator=zeroes_padding)

The object that you provide as :code:`padding_generator` has to fulfill the
data generator interface described in section “Data Generators”.

After creating an :code:`Image` instance, you can add scenarios to it.
This works in the same way as you added fragments to a scenario:

.. code-block:: python
   
   s1 = woodblock.scenario.Scenario("first scenario")
   s2 = woodblock.scenario.Scenario("second scenario")
   # add some fragments to the scenarios
   image = woodblock.image.Image()
   image.add(s1)
   image.add(s2)

The order of the scenarios in the resulting image corresponds to the order in
which you added them. Just as before with fragments and scenarios.

The last step to do is to write the image to disk:

.. code-block:: python
   
   image.write(pathlib.Path('test-image.dd'))

This will not only write all of the scenarios to the image file
:code:`test-image.dd`, but it will also write a JSON file containing the ground
truth of the image. This file will be placed next to the image and will have the
same same with :code:`.json` appended. In the example above, you would find your
ground truth in the file :code:`test-image.dd.json`.

.. _data-generator-interface:

Data Generators
***************
Data generators are objects implementing a certain interface. They are used in
Woodblock to generate the block padding that is used in an image or within
some :code:`FillerFragments` for example. The interface is quite simple, so it’s
easy to write your own data generators. Here is the :code:`Zeroes` data generator
class that is already included in Woodblock:

.. code-block:: python
   
   # You can find this in the module woodblock.datagen
   
   class Zeroes:
   """Generates zero bytes."""
   
       def __call__(self, size):
           return b'\x00' * size
   
       def __str__(self):
           return 'zeroes'

As you can see, a data generator has to be callable. For classes this means
that you have to implement the :code:`__call__` magic method. While this would
be sufficient to make your data generator work, we highly recommend to implement
the :code:`__str__` magic method, too. When your data generator is used within
one of the fragment classes for example, its string representation will be written
to the ground truth file. So, returning something meaningful from :code:`__str__`
helps you and others reading and understanding what is within your image.

When data is needed from your data generator, it will be called with a 
:code:`size` argument indicating how many bytes to return. Of course, your data
generator should return the correct number here. Woodblock expects the data
generators to always return as many bytes as requested and doesn't do any checking
on the returned bytes. If your data generator fails to generate the expected
number of bytes for some reason, you should raise an exception and not return
any bytes.

You might have noticed, that the interface would also allow you to use a
“normal” function as data generator. While technically this would work, we
argue against doing so because your data generator function would not have a
descriptive string representation. While there are ways to
`implement a custom string representation`_ for your functions, using a class
is just simpler.

Here is one more simple implementation of a data generator which generates a
repeated sequence of bytes:

.. code-block:: python
   
   class Pattern:
   """Generate a repeated sequence of bytes."""
   
       def __init__(self, pattern=b'AB'):
           self._pattern = pattern
   
       # a data generator has to be callable => implement the __call__ method
       def __call__(self, size):
           it = itertools.cycle(self._pattern)
           return b''.join(bytes([next(it)]) for _ in range(size))
   
       # a data generator should have a descriptive __str__ implementation
       def __str__(self):
           return 'pattern'
   
   # this is how you would use the Pattern data generator to pad an image
   image = woodblock.image.Image(padding_generator=Pattern(b'XO'))


API Reference
*************
The following sections provide a brief documentation of the API.

woodblock.file
==============

.. py:function:: woodblock.file.corpus(path)
   
   Specifies the path to the test file corpus to use.
   
   :param path: The path to the corpus
   
   :code:`path` can either be a string or a :code:`pathlib.Path` object.
   In any way, it has to be an existing directory. All paths used for 
   :code:`File` objects are relative to the file corpus path.

.. py:function:: woodblock.file.get_corpus()
   
   Return the specified file corpus path.
   
   :return: The corpus path
   :rtype: pathlib.Path

.. py:function:: woodblock.file.draw_files(path=None, number_of_files=1, unique=False, min_size=0)
   
   Chooses random files from the file corpus.
   
   :param path: Subdirectory of the corpus
   :param int number_of_files: Number of files to draw
   :param bool unique: Forbid a file to be drawn multiple times
   :param int min_size: Minimal file size
   :return: a list of :code:`File` objects
   :rtype: list
   
   If :code:`path` is :code:`None`, the complete corpus will be considered.
   If it set to a path relative to the corpus, then only files in this directory
   (and its subdirectories) are considered.
   
   If :code:`unique` is set to :code:`True`, then the resulting list will not
   contain file objects pointing to the same path in the corpus.
   
   :code:`min_size` can be set to define a minimal file size of the files to be chosen.

.. py:function:: woodblock.files.draw_fragmented_files(path=None, number_of_files=1, block_size=512, min_fragments=1, max_fragments=4)
   
   Choose :code:`number_of_files` random files from :code:`path` and fragment them randomly.
   
   :param path: Subdirectory of the corpus
   :param int number_of_files: Number of files to draw
   :param int block_size: Block size to be used when splitting files
   :param int min_fragments: Min. number of fragments per file
   :param int max_fragments: Max. number of fragments per file
   :return: a list of fragment lists
   :rtype: list
   
   This function chooses :code:`number_of_files` files from the given :code:`path`
   (relative to the corpus) and fragments them at random fragmentation points. The number
   of fragments per file will be between :code:`min_fragments` and :code:`max_fragments`
   (both numbers included, i.e. :code:`min_fragments` ≤ number of fragments ≤ :code:`max_fragments`).
   
   The result is a list of fragment lists, e.g. :code:`[ [f1.1, f1.2, f1.3], [f2.1, ], [f3.1, f3.2] ]`.
   
   If :code:`path` is :code:`None`, the complete corpus will be considered. If it set to a
   path relative to the corpus, then only files in this directory (and its subdirectories) are considered.
   
   Note that there is no guarantee that a file is not chosen more than once.

.. py:function:: woodblock.files.intertwine_randomly(path=None, number_of_files=2, block_size=512, min_fragments=1, max_fragments=4)
   
   Choose :code:`number_of_files` random files from :code:`path` and intertwine them randomly.
   
   :param path: Subdirectory of the corpus
   :param int number_of_files: Number of files to intertwine
   :param int block_size: Block size to used when splitting files
   :param int min_fragments: Min. number of fragments per file
   :param int max_fragments: Max. number of fragments per file
   :return: a list of intertwined fragments
   :rtype: list
   
   This function chooses :code:`number_of_files` files from the given :code:`path` (relative
   to the corpus), fragments them at random fragmentation points, and intertwines them randomly.
   The number of fragments per file will be between :code:`min_fragments` and :code:`max_fragments`
   (both numbers included, i.e. :code:`min_fragments` ≤ number of fragments ≤ :code`max_fragments`).
   
   The result is a list of fragments, e.g. :code:`[f3.1, f1.1, f3.2, f2.1, f1.2, f2.2, f1.3]`.
   
   The function ensures that there will in fact be unique :code:`number_of_files` files.
   Moreover, the function guarantees that two fragments of the same file will not be at
   consecutive list positions. The fragments of each file will be stored in order.

.. py:class:: woodblock.file.File(path)
   
   This class represents an actual file of the test file corpus.
   
   :param pathlib.Path path: a path relative to the specified corpus

.. py:method:: woodblock.file.File.hash
   :property:
   
   Return the SHA-256 hash of the file contents as hexadecimal string.
   
   :rtype: str

.. py:method:: woodblock.file.File.id
   :property:
   
   Returns the ID of the file.
   
   :rtype: str
   
   The ID is a UUID generated when the :code:`File` object
   is instantiated. Each :code:`File` object has a unique ID—even if it references
   the same file of the corpus. This is useful, if you want to add the same file
   twice to the same scenario.

.. py:method:: woodblock.file.File.path
   :property:
   
   Returns the path of the file relative to the corpus path.
   
   :rtype: pathlib.Path

.. py:method:: woodblock.file.File.size
   :property:
   
   Returns the size of the file.
   
   :rtype: int

.. py:method:: woodblock.file.File.as_fragment()
   
   Convert the :code:`File` to a single :code:`FileFragment`. This is useful,
   if you want to add a contiguous, non-fragmented file to a scenario.
   
   :rtype: woodblock.fragments.FileFragment

.. py:method:: woodblock.file.File.max_fragments(block_size)
   
   Returns the maximal number of fragments which can be created for a given
   :code:`block_size`.
   
   :rtype: int

.. py:method:: woodblock.file.File.fragment(fragmentation_points, block_size=512)
   
   Fragments the file at the given :code:`fragmentation_points` with respect to
   the given :code:`block_size`.
   
   :param typing.Sequence fragmentation_points: a sequence of fragmentation points relative to the block size
   :param int block_size: block size to use when splitting the file
   :return: a list of :code:`woodblock.fragments.FileFragment` objects
   :rtype: list
   
   This method fragments the current file at the specified :code:`fragmentation_points`.
   The fragmentation points are multiplied with the given :code:`block_size` in order to
   compute the actual fragmentation offsets. :code:`fragmentation_points` has to be a
   sequence of integers, :code:`block_size` has to be an integer and defaults to 512 if
   it is not specified.

.. py:method:: woodblock.file.File.fragment_evenly(num_fragments, block_size=512)
   
   This method fragments the current file into :code:`num_fragments` fragments.
   
   :param int num_fragments: number of fragments to create
   :param int block_size: block size to use when splitting the file
   :return: a list of :code:`wwodblock.fragments.FileFragment` objects
   :rtype: list
   
   The fragmentation points are chosen so that each fragment will be of the same size
   (if possible). If the file cannot be fragmented evenly, then all but the last
   fragment will have the same size and the last one will be smaller than the other
   ones.
   
   The block size to be used when splitting the file can be specified using the
   :code:`block_size` argument, which defaults to 512.
   
.. py:method:: woodblock.file.File.fragment_randomly(num_fragments, block_size=512)
   
   This method fragments the current file into :code:`num_fragments` fragments. The
   
   :param int num_fragments: number of fragments to create
   :param int block_size: block size to use when splitting the file
   :return: a list of :code:`woodblock.fragments.FileFragment` objects
   :rtype: list
   
   The fragmentation points are chosen randomly. If :code:`num_fragments` is :code:`None`,
   then the number of fragments is chosen randomly between 1 and the maximum number of
   fragments for the given :code:`block_size`.


woodblock.fragments
===================

.. py:class:: woodblock.fragments.FileFragment(file, fragment_number, start_offset, end_offset, chunk_size=8192)
   
   This class represents a fragments of an actual file from the file corpus.
   
   :param woodblock.file.File file: the file the fragment is part of
   :param int fragment_number: the fragment number of this fragment
   :param int start_offset: start offset of the fragment within the original file
   :param int end_offset: end offset of the fragment within the original file
   
   :code:`file` is the :code:`File` object representing the original file and
   :code:`fragment_number` is the number of the fragment (i.e. is it the first
   fragment, is the second one and so on). :code:`start_offset` and :code:`end_offset`
   define the offsets where the fragment starts and ends (relative to the
   original file).

.. py:method:: woodblock.fragments.FileFragment.hash
   :property:
   
   Return the SHA-256 digest as hexadecimal string.
   
   :rtype: str

.. py:method:: woodblock.fragments.FileFragment.metadata
   :property:
   
   Return the fragment metadata.
   
   :rtype: dict
   
   The fragment metadata is a :code:`dict` containing information about the file the
   fragments originates from (e.g. the hash, the size, and the path) as well as
   information about the current fragment (e.g. the hash, the size, and the fragment
   number with respect to the original file).

.. py:method:: woodblock.fragments.FileFragment.size
   :property:
   
   Return the size of the fragment.
   
   :rtype: int

.. py:class:: woodblock.fragments.FillerFragment(size, data_generator=None, chunk_size=8192)
   
   A filler fragment is a fragment containing synthetic data. It can be used to
   simulate wiped areas or areas with random data.
   
   :param int size: size of the fragment
   :param data_generator: data generator producing the fragment data
   
   :code:`data_generator` has to be an
   object compatible with the :ref:`data generator interface <data-generator-interface>`.

.. py:method:: woodblock.fragments.FillerFragment.hash
   :property:
   
   Return the SHA-256 digest as hexadecimal string.
   
   :rtype: str

.. py:method:: woodblock.fragments.FillerFragment.metadata
   :property:
   
   Return the fragment metadata.
   
   :rtype: dict
   
   The fragment metadata is a :code:`dict` containing information about the file
   the fragments originates from (e.g. the hash, the size, and the type) as well
   as information about the current fragment (e.g. the hash, the size, and the 
   fragment number with respect to the original file).
   
   Note that :code:`FillerFragments` do not point to any “real” files. Therefore,
   the values of the original file and the fragment will be mostly identical.
   The file metadata is included only for consistency with the :code:`FileFragment`.

.. py:method:: woodblock.fragments.FillerFragment.size
   :property:
   
   Return the size of the fragment.
   
   :rtype: int

.. py:class:: woodblock.fragments.RandomDataFragment(size, chunk_size=8192)
   
   A fragment filled with random bytes.
   
   :param int size: the size of the fragment

.. py:method:: woodblock.fragments.RandomDataFragment.hash
   :property:
   
   Return the SHA-256 digest as hexadecimal string.
   
   :rtype: str

.. py:method:: woodblock.fragments.FileFragment.metadata
   :property:
   
   Return the fragment metadata.
   
   :rtype: dict
   
   The fragment metadata is a :code:`dict` containing information about the file
   the fragments originates from (e.g. the hash, the size, and the type) as well
   as information about the current fragment (e.g. the hash, the size, and the 
   fragment number with respect to the original file).
   
   Note that :code:`FillerFragments` do not point to any “real” files. Therefore,
   the values of the original file and the fragment will be mostly identical.
   The file metadata is included only for consistency with the :code:`FileFragment`.

.. py:method:: woodblock.fragments.RandomDataFragment.size
   :property:
   
   Return the size of the fragment.
   
   :rtype: int

.. py:class:: woodblock.fragments.ZeroesFragment(size, chunk_size=8192)
   
   A fragment filled with random bytes.
   
   :param int size: the size of the fragment

.. py:method:: woodblock.fragments.ZeroesFragment.hash
   :property:
   
   Return the SHA-256 digest as hexadecimal string.
   
   :rtype: str

.. py:method:: woodblock.fragments.FileFragment.metadata
   :property:
   
   Return the fragment metadata.
   
   :rtype: dict
   
   The fragment metadata is a :code:`dict` containing information about the file
   the fragments originates from (e.g. the hash, the size, and the type) as well
   as information about the current fragment (e.g. the hash, the size, and the 
   fragment number with respect to the original file).
   
   Note that :code:`FillerFragments` do not point to any “real” files. Therefore,
   the values of the original file and the fragment will be mostly identical.
   The file metadata is included only for consistency with the :code:`FileFragment`.

.. py:method:: woodblock.fragments.ZeroesFragment.size
   :property:
   
   Return the size of the fragment.
   
   :rtype: int


woodblock.scenario
==================

.. py:class:: woodblock.scenario.Scenario(name)
   
   This class represents a file carving scenario.
   
   :param str name: the name of the scenario
   
   A scenario contains fragments in a certain order. :code:`name` defines the name
   of the scenario which identifies the scenario in the ground truth files.

.. py:method:: woodblock.scenario.Scenario.add(fragment)
   
   Add a fragment to the scenario.
   
   :param fragment: the fragment to add to the scenario

.. py:method:: woodblock.scenario.Scenario.add(fragments)
   
   The same as :code:`add(scenario)` but this time :code:`scenarios`
   is a list or tuple of fragments to be added to the scenario.
   
   :param fragments: a list fragments to add to the scenario

.. py:method:: woodblock.scenario.Scenario.metadata
   :property:
   
   Return a dict containing metadata about the scenario.
   
   :rtype: dict


woodblock.image
===============

.. py:class:: woodblock.image.Image(block_size=512, padding_generator=woodblock.datagen.Random())
   
   The :code:`Image` class represents a carving test image.
   
   :param int block_size: The block size to be used in the image
   :param padding_generator: The data generator to use
   
   An image contains a sequence of :code:`Scenario` instances. An image has a fixed
   block size and all blocks smaller than the block size will be padded with data
   generated by a configurable data generator. If no :code:`padding_generator` is
   specified, random data will be used as padding.

.. py:method:: woodblock.scenario.Image.add(scenario)
   
   Add a :code:`Scenario` to the image.
   
   :param woodblock.scenario.Scenario scenario: The scenario to add

.. py:staticmethod:: woodblock.scenario.Image.from_config(path)
   
   Create an :code:`Image` instance based on a configuration file.
   
   :param pathlib.Path path: Path to the configuration file
   
.. py:method:: woodblock.scenario.Image.write(path)
  
   Write the image to disk.
   
   :param pathlib.Path path: The image output path
   
   This method write the image to the specified :code:`path`. Moreover, it also writes
   the image metadata to disk. The metadata file will be :code:`path` with the “.json”
   extension. E.g. if :code:`path` is “test-image.dd” then the actual image will be in
   “test-image.dd” and the metadata will be in “test-image.dd.json”.


.. _DFRWS 2007 File Image Layout page: http://old.dfrws.org/2007/challenge/layout.shtml
.. _implement a custom string representation: https://stackoverflow.com/a/47452562
