title:      Woodblock API
desc:       Woodblock Python API.
date:       2019/08/14
template:   document
nav:        Usage>API __2__
percent:    75

For most use cases, the [configuration files](configs.md) should suffice.
If you need more fine-grained control over your scenarios you can use the
Python API. For instance, the API lets you define the exact fragmentation
points of your files, exact sizes of filler fragments, and so forth.

Here is a simple script illustrating the basic usage of the API:

```python
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
```

This script randomly chooses two files from the file corpus. The first one is
split into three fragments at random fragmentation points, the second one is
split into two fragments of equal size. After that the scenario with the name 
“First API Scenario” is created and the file frgments as well as two filler
fragments are added to the scenario. Finally, the scenario is added to an
image object which is then written to disk.

Let’s go through this example step by step. The first lines are just some
imports.

```python
from woodblock.file import File, draw_files
from woodblock.fragments import RandomDataFragment, ZeroesFragment
from woodblock.image import Image
from woodblock.scenario import Scenario
```

After we define the file corpus and randomly draw two files:

```python
woodblock.file.corpus(HERE / '..' / 'data' / 'corpus')
files = draw_files(number_of_files=2)
```

These files are then split into fragments. The first file is split into three
fragments. The fragmentation points are chosen randomly. The second file is
split into two fragments. The fragmentation point is chosen so that both
fragments are of equal size:

```python
f_a = files[0].fragment_randomly(num_fragments=3)
f_b = files[1].fragment_evenly(num_fragments=2)
```

After that, a `Scenario` object is created. Its argument is the name of the
scenario:

```python
s = Scenario('First API Scenario')
```

A `Scenario` object has a method to `add` fragments to it. A call to `add`
appends a fragment to any previously added fragments, so that the order of the
`add` calls defines the order of the fragments in the scenario:

```python
s.add(f_a[1])
s.add(ZeroesFragment(1024))
s.add(f_b[0])
s.add(f_a[2])
s.add(RandomDataFragment(512))
s.add(f_a[0])
s.add(f_b[1])
```

We did not only added the fragments of our files but also two filler
fragments: a `ZerroesFragment` of 1024 bytes of size and a
`RandomDataFragment` of 512 bytes of size. As you can see, you can specify the
exact size of the filler fragments using the API.

After that, our scenario is complete and we create an `Image` object with a
block size of 512 bytes. `Image` objects represent test image files to be
written to disk. Just like we could add fragments to a scenario, we can add
scenarios to an `Image`. If we added all of the scenarios, we can finally
write the image using the `write` method.

Those are already the basic blocks you need to create your own test images
using the API: you select files from the test file corpus, fragments them
in some way, add the fragments to a scenario, add the scenario to an image,
and finally write the image to disk.

The following sections describe the available API functions and objects in
a more detailed way.

## Files and Fragments
Files are always selected from a file corpus. Therefore, you have to specify
the path to your file corpus before you can select any files. This is done
using the `woodblock.files.corpus` function.


## Scenarios

## Images

## Data Generators

## Helpers

# API Reference

The following sections provide a brief documentation of the API.

## Overview

#### `woodblock.file`

| Function/Class/Method  | Purpose |
| ---------------------- | ------- |
| `corpus(path)`         | Set the file corpus. |
| `get_corpus()`         | Return the path to the file corpus. |
| `draw_files(path=None, number_of_files=1, unique=False, min_size=0)` | Choose random files from the file corpus. |
| `draw_fragmented_files(path=None, number_of_files=1, block_size=512, min_fragments=1, max_fragments=4)` | Choose random files from the given path and fragment them randomly. |
| `intertwine_randomly(path=None, number_of_files=2, block_size=512, min_fragments=1, max_fragments=4)` | Choose random files from the given path and intertwine them randomly. |
| `File(path=None, number_of_files=1, unique=False, min_size=0)` | Represents an actual file of the test file corpus. |
| `File.hash()`          | Return the SHA-256 hash of the file as hexadecimal string. |
| `File.id()`            | Return the ID of the file. |
| `File.path()`          | Return the path of the file relative to the corpus path. |
| `File.size()`          | Return the file size. |
| `File.as_fragment()`   | Return the file as a single fragment. |
| `File.max_fragments(block_size)`  | Return the max. number of fragments which can be created for a given block size. |
| `File.fragment(fragmentation_points, block_size=512)`        | Fragment the file at the given fragmentation points using the given block size. |
| `File.fragment_evenly(num_fragments, block_size=512)`        | Fragment the file evenly into the given number of fragment fragments. |
| `File.fragment_randomly(num_fragments=None, block_size=512)` | Fragment the file at random fragmentation points. |

#### `woodblock.fragments`

| Function/Class/Method  | Purpose |
| ---------------------- | ------- |
| `FileFragment(file, fragment_number, start_offset, end_offset, chunk_size=8192)` | A fragment of an actual file. |
| `FileFragment.hash()`     | Return the SHA-256 digest as hexadecimal string. |
| `FileFragment.metadata()` | Return the fragment metadata. |
| `FileFragment.size()`     | Return the size of the fragment. |
| `FillerFragment(size, data_generator=None, chunk_size=8192)` | A filler fragment. |
| `FillerFragment.hash()`     | Return the SHA-256 digest as hexadecimal string. |
| `FillerFragment.metadata()` | Return the fragment metadata. |
| `FillerFragment.size()`     | Return the size of the fragment. |
| `RandomDataFragment(size, chunk_size=8192)` | A fragment filled with random bytes. |
| `RandomDataFragment.hash()`     | Return the SHA-256 digest as hexadecimal string. |
| `RandomDataFragment.metadata()` | Return the fragment metadata. |
| `RandomDataFragment.size()`     | Return the size of the fragment. |
| `ZeroesFragment(size, chunk_size=8192)` | A fragment filled completely with zero bytes. |
| `ZeroesFragment.hash()`     | Return the SHA-256 digest as hexadecimal string. |
| `ZeroesFragment.metadata()` | Return the fragment metadata. |
| `ZeroesFragment.size()`     | Return the size of the fragment. |

#### `woodblock.scenario`

| Function/Class/Method  | Purpose |
| ---------------------- | ------- |
| `Scenario(name)` | Represents a file carving scenario. |
| `Scenario.add(fragment)`  | Add a single fragment to the scenario. |
| `Scenario.add(fragments)` | Add a list of fragments to the scenario. |
| `Scenario.metadata()`     | Return the scenario metadata. |

#### `woodblock.image`

| Function/Class/Method  | Purpose |
| ---------------------- | ------- |
| `Image(block_size=512, padding_generator=woodblock.datagen.Random())` | Represents a carving test image. |
| `Image.add(scenario)`     | Add a scenario to the image. |
| `Image.from_config(path)` | Create an Image instance based on a configuration file. |
| `Image.write(path)`       | Write the image to disk. |
| `Image.metadata()`        | Return the image metadata. |


## woodblock.file
---
#### woodblock.file.`corpus(path)`
Specifies the path to the test file corpus to use. `path` can either be a string
or a `pathlib.Path` object. In any way, it has to be an existing directory. All
paths used for `File` objects are relative to the file corpus path.
---
#### woodblock.file.`get_corpus()`
Return the specified file corpus path.
---
#### woodblock.file.`draw_files(path=None, number_of_files=1, unique=False, min_size=0)`
Chooses `number_of_files` random files from the file corpus.

If `path` is `None`, the complete corpus will be considered. If it set to a
path relative to the corpus, then only files in this directory (and its
subdirectories) are considered.

If `unique` is set to `True`, then the resulting list will not contain file
objects pointing to the same path in the corpus.

`min_size` can be set to define a minimal file size of the files to be chosen.
---
#### woodblock.files.`draw_fragmented_files(path=None, number_of_files=1, block_size=512, min_fragments=1, max_fragments=4)`
Choose `number_of_files` random files from `path` and fragment them randomly.

This function chooses `number_of_files` files from the given `path` (relative
to the corpus) and fragments them at random fragmentation points. The number
of fragments per file will be between `min_fragments` and `max_fragments`
(both numbers included, i.e. min_fragments ≤ number of fragments ≤ max_fragments).

The result is a list of fragment lists, e.g. `[ [f1.1, f1.2, f1.3], [f2.1, ], [f3.1, f3.2] ]`.

If `path` is `None`, the complete corpus will be considered. If it set to a
path relative to the corpus, then only files in this directory (and its
subdirectories) are considered.

Note that there is no guarantee that a file is not chosen more than once.
---
#### woodblock.files.`intertwine_randomly(path=None, number_of_files=2, block_size=512, min_fragments=1, max_fragments=4)`
Choose `number_of_files` random files from `path` and intertwine them randomly.

This function chooses `number_of_files` files from the given `path` (relative
to the corpus), fragments them at random fragmentation points, and intertwines
them randomly. The number of fragments per file will be between `min_fragments`
and `max_fragments` (both numbers included, i.e. min_fragments ≤ number of
fragments ≤ max_fragments).

The result is a list of fragments, e.g. `[f3.1, f1.1, f3.2, f2.1, f1.2, f2.2, f1.3]`.

The function ensures that there will in fact be unique `number_of_files` files.
Moreover, the function guarantees that two fragments of the same file will not
be at consecutive list positions. The fragments of each file will be stored in
order.
---

### woodblock.file.File
---
#### woodblock.file.`File(path)`
This class represents an actual file of the test file corpus. `path` has to be
a path relative to the specified corpus.
---
#### woodblock.file.File.`hash()`
Return the SHA-256 hash of the file contents as hexadecimal string.
---
#### woodblock.file.File.`id()`
Returns the ID of the file. The ID is a UUID generated when the `File` object
is instantiated. Each `File` object has a unique ID—even if it references
the same file of the corpus. This is useful, if you want to add the same file
twice to the same scenario.
---
#### woodblock.file.File.`path()`
Returns the path of the file relative to the corpus path.
---
#### woodblock.file.File.`size()`
Returns the size of the file.
---
#### woodblock.file.File.`as_fragment()`
Convert the `File` to a single `FileFragment`. This is useful, if you want to
add a contiguous, non-fragmented file to a scenario.
---
#### woodblock.file.File.`max_fragments(block_size)`
Returns the maximal number of fragments which can be created for a given
`block_size`.
---
#### woodblock.file.File.`fragment(fragmentation_points, block_size=512)`
Fragments the file at the given `fragmentation_points` with respect to the
given `block_size`.

This method fragments the current file at the specified `fragmentation_points`.
The fragmentation points are multiplied with the given `block_size` in order to
compute the actual fragmentation offsets. `fragmentation_points` has to be a
sequence of integers, `block_size` has to be an integer and defaults to 512 if
it is not specified.

`fragment` returns a list of `woodblock.fragments.FileFragments`.
---
#### woodblock.file.File.`fragment_evenly(num_fragments, block_size=512)`
This method fragments the current file into `num_fragments` fragments. The
fragmentation points are chosen so that each fragment will be of the same size
(if possible). If the file cannot be fragmented evenly, then all but the last
fragment will have the same size and the last one will be smaller than the other
ones.

The block size to be used when splitting the file can be specified using the
`block_size` argument, which defaults to 512.

`num_fragments` and `block_size` have to be an integers.

`fragment_evenly` returns a list of `woodblock.fragments.FileFragments`.
---
#### woodblock.file.File.`fragment_randomly(num_fragments, block_size=512)`
This method fragments the current file into `num_fragments` fragments. The
fragmentation points are chosen randomly. If `num_fragments` is `None`, then
the number of fragments is chosen randomly between 1 and the maximum
number of fragments for the given `block_size`.

`fragment_randomly` returns a list of `woodblock.fragments.FileFragments`.
---

## woodblock.fragments
---
### woodblock.fragments.FileFragment
---
#### woodblock.fragments.`FileFragment(file, fragment_number, start_offset, end_offset, chunk_size=8192)`
This class represents a fragments of an actual file from the file corpus.

`file` is the `File` object representing the original file and
`fragment_number` is the number of the fragment (i.e. is it the first
fragment, is the second one and so on). `start_offset` and `end_offset`
define the offsets where the fragment starts and ends (relative to the
original file).

---
#### woodblock.fragments.FileFragment.`hash()`
Return the SHA-256 digest as hexadecimal string.
---
#### woodblock.fragments.FileFragment.`metadata()`
Return the fragment metadata.

The fragment metadata is a `dict` containing information about the file the
fragments originates from (e.g. the hash, the size, and the path) as well
as information about the current fragment (e.g. the hash, the size, and the 
fragment number with respect to the original file).
---
#### woodblock.fragments.FileFragment.`size()`
Return the size of the fragment.
---

### woodblock.fragments.FillerFragment
---
#### woodblock.fragments.`FillerFragment(size, data_generator=None, chunk_size=8192)`
A filler fragment is a fragment containing synthetic data. It can be used to
simulate wiped areas or areas with random data.

`size` specifies the size of the fragment. `data_generator` has to be an
object compatible with the data generator interface (TODO: add link).
---
#### woodblock.fragments.FillerFragment.`hash()`
Return the SHA-256 digest as hexadecimal string.
---
#### woodblock.fragments.FileFragment.`metadata()`
Return the fragment metadata.

The fragment metadata is a `dict` containing information about the file the
fragments originates from (e.g. the hash, the size, and the type) as well
as information about the current fragment (e.g. the hash, the size, and the 
fragment number with respect to the original file).

Note that `FillerFragments` do not point to any “real” files. Therefore,
the values of the original file and the fragment will be mostly identical.
The file metadata is included only for consistency with the `FileFragment`.
---
#### woodblock.fragments.FillerFragment.`size()`
Return the size of the fragment.
---

### woodblock.fragments.RandomDataFragment
---
#### woodblock.fragments.`RandomDataFragment(size, chunk_size=8192)`
A fragment filled with random bytes.

`size` specifies the size of the fragment.
---
#### woodblock.fragments.RandomDataFragment.`hash()`
Return the SHA-256 digest as hexadecimal string.
---
#### woodblock.fragments.FileFragment.`metadata()`
Return the fragment metadata.

The fragment metadata is a `dict` containing information about the file the
fragments originates from (e.g. the hash, the size, and the type) as well
as information about the current fragment (e.g. the hash, the size, and the 
fragment number with respect to the original file).

Note that `FillerFragments` do not point to any “real” files. Therefore,
the values of the original file and the fragment will be mostly identical.
The file metadata is included only for consistency with the `FileFragment`.
---
#### woodblock.fragments.RandomDataFragment.`size()`
Return the size of the fragment.
---


### woodblock.fragments.ZeroesFragment
---
#### woodblock.fragments.`ZeroesFragment(size, chunk_size=8192)`
A fragment filled with random bytes.

`size` specifies the size of the fragment.
---
#### woodblock.fragments.ZeroesFragment.`hash()`
Return the SHA-256 digest as hexadecimal string.
---
#### woodblock.fragments.FileFragment.`metadata()`
Return the fragment metadata.

The fragment metadata is a `dict` containing information about the file the
fragments originates from (e.g. the hash, the size, and the type) as well
as information about the current fragment (e.g. the hash, the size, and the 
fragment number with respect to the original file).

Note that `FillerFragments` do not point to any “real” files. Therefore,
the values of the original file and the fragment will be mostly identical.
The file metadata is included only for consistency with the `FileFragment`.
---
#### woodblock.fragments.ZeroesFragment.`size()`
Return the size of the fragment.
---

## woodblock.scenario
---
#### woodblock.scenario.`Scenario(name)`
This class represents a file carving scenario. A scenario contains fragments
in a certain order. `name` defines the name of the scenario which identifies
the scenario in the ground truth files.
---
#### woodblock.scenario.Scenario.`add(fragment)`
Add a fragment to the scenario.
---
#### woodblock.scenario.Scenario.`add(fragments)`
The same as `add(scenario)` but this time `scenarios` is a list or tuple of
fragments to be added to the scenario.
---
#### woodblock.scenario.Scenario.`metadata()`
Return a dict containing metadata about the scenario.
---


## woodblock.image
---
#### woodblock.image.`Image(block_size=512, padding_generator=woodblock.datagen.Random())`
The `Image` class represents a carving test image.

An image contains a sequence of `Scenario` instances. An image has a fixed
block size and all blocks smaller than the block size will be padded with data
generated by a configurable data generator. If no `padding_generator` is
specified, random data will be used as padding.
---
#### woodblock.scenario.Image.`add(scenario)`
Add a `Scenario` to the image.
---
#### woodblock.scenario.Image.`from_config(path)`
Create an `Image` instance based on a configuration file.

`path` is the path to the configuration file.
---
#### woodblock.scenario.Image.`write(path)`
This method write the image to the specified `path`. Moreover, it also writes
the image metadata to disk. The metadata file will be `path` with the “.json”
extension. E.g. if `path` is “test-image.dd” then the actual image will be in
“test-image.dd” and the metadata will be in “test-image.dd.json”.
