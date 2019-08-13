title:      Configuration Files
desc:       Data Set Configuration Files.
date:       2019/07/14
template:   document
nav:        Usage > Configuration Files __1__

Most test images can be created using configuration files.
They are easy to write and do not require any coding at all.
For more complex scenarios not covered by the configuration files, 
have a look at how to use the [Woodblock API](api.md).

# Configuration File Structure
A Woodblock configuration files use a simple INI syntax.
Here is a simple example with one scenario:

```ini
[general]
  block size = 4096
  seed = 123
  corpus = ../test_file_corpus/

[my first scenario]
  frags file1 = 3
  frags file2 = 1
  frags file3 = 2
  layout = 1-1, 3-1, 1-2, 2-1, 1-3, 3-2
```

The `[general]` section is mandatory and defines global options for the test
image to be generated. In the example, we set the block size of the image to
`4096` bytes, the seed for the random number generator to `123`, and the file
corpus to the `../test_file_corpus` folder. Note that all paths provided in a
configuration file are relative to very file.

In addition to the `[general]` section, there has to be at least one section
defining a scenario. Basically, every section except for `[general]` is 
considered to be a scenario.

# The `[general]` Section
The `[general]` section defines global options for the image to be generated.
Here is an example showing all available options:

```ini
[general]
  block size = 512
  corpus = testfiles/
  seed = 12345
  min filler blocks = 1
  max filler blocks = 10
```

## `block size`
*Default value:* `512`.  
*Required:* no

The `block size` option defines the block size to be used for the image file.
When using the configuration file, all fragments of the scenarios will be
aligned and padded according to this size. The padding will be made up of
random data.

## `corpus`
*Default value:* `None`  
*Required:* yes

The path (relative to the configuration file) to the corpus to be used.

## `seed`
*Default value:* randomly generated integer  
*Required:* no

The seed for the random number generator. If you do not specify a seed
explicitly, Woodblock will generate a random seed for you.

## `min filler blocks`
*Default:* `1`  
*Required:* no

This parameter defines the minimum number of blocks for filler fragments.
The actual size of a filler fragments will be randomly chosen from the
interval [`min filler blocks`, `max filler blocks`], including both endpoints.

## `max filler blocks`
*Default:* `10`  
*Required:* no

This parameter defines the maximum number of blocks for filler fragments.
The actual size of a filler fragments will be randomly chosen from the
interval [`min filler blocks`, `max filler blocks`], including both endpoints.

# Scenario Sections
As already mentioned, every section apart from `[general]` is considered to be
a scenario section. As the name implies a scenario section defines a scenario
to be included in the final image. The name of the section will be the name of
the scenario and the order of appearance of the sections in the configuration
file corresponds to the order of the scenarios in the image.

The supported and required options of a scenario section depend on the layout
type of the scenario you want to generate.

### `layout`
*Default:* `None`  
*Required:* yes

As the name implies, this option defines the layout of the scenario. It can be
either `intertwine` to create intertwined scenarios or a comma-separated list
of *fragment identifiers*. We will cover both options in the next sections in
more details.

## Creating Intertwined Scenarios
Creating intertwined scenarios is really easy using the configuration file.
All you have to do is provide the number of files that you want to have.
Optionally, you can specify the minimal and maximal number of fragments per
file.

A complete section for an intertwined scenario looks like this:

```ini
[An intertwined scenario]
  layout = intertwine
  num files = 4
  min frags = 2
  max frags = 5
```

An intertwined scenario created with a section like the one above will have
the following properties.
 
 - There will be `num files` files in the scenario.
 - Each of these files will be split into [`min frags`, `max frags`] fragments (endpoints are included).
 - The fragments of each file will be in order, i.e. fragment 1 comes before fragment 2 which comes before fragment 3 and so on.
 - No two fragments of the same file will be adjacent to one other.


### `layout`
In order to have Woodblock create an intertwined scenario for you, the
`layout` option has to be set to `intertwine`.

### `num files`
*Default:* `None`  
*Required:* yes

This options defines the number of files to include in the scenario. Note that
it is not possible to specify specific files here. Instead, Woodblock will
randomly pick files which can be fragmented according to your `min frags` and
`max frags` constraints.

### `min frags`
*Default:* `1`  
*Required:* no

This option defines the minimal number of fragments to split a file into.

### `max frags`
*Default:* `4`  
*Required:* no

This option defines the maximal number of fragments to split a file into. Note
that `max frags` has to be &ge; `min frags`.

## Manually Specifying the Scenario Layout
If you are not creating an intertwined scenario, you have to specify the
layout of the scenario yourself. This is, however, almost as easy as using
the `intertwine` keyword.

Here is an example for a simple scenario:

```ini
[A Simple Scenario]
  frags file1 = 2
  frags file2 = 3
  layout = 1.1, 2.3, 2.2, 1.2, 2.1
```

This definition randomly chooses two files from the corpus, splits the first
one into two fragments and the second into three, and generates the following
fragment order:

![simple scenario layout](../assets/usage-simple-scenario-layout.png "a simple scenario layout"){: .noborder}

Note that the size of the individual fragments is chosen randomly as a
multiple of the block size defined in the general section.

So, how did this work? The option `frags fileN` tell Woodblock to pick file `N`
and split it into the corresponding number of fragments. `N` has to be an integer
and refers to the `N`<sup>th</sup> file in the scenario. As we did not define a
specifiy file (more on this later), random files from the corpus will be picked.
Then, in the `layout` line, we defined the fragment order, that we would like
to have. The order is a comma-separated list of *fragment identifiers*. A
fragment identifier is composed of the file number and the fragments number,
separated by either a dot (`.`) or a hyphen (`-`). That is, if you would like
to reference the fourth fragment of the second file, then you could write
either `2.4` or `2-4`.

If you want to specify which files Woodblock should use, you can do this using
the `fileN` option. For instance, if you want one random file and one specific
file, then you could modify the above configuration:

```ini
[A Simple Scenario]
  file2 = path/to/some/file.jpg
  frags file1 = 2
  frags file2 = 3
  layout = 1.1, 2.3, 2.2, 1.2, 2.1
```

Adding the `file2` option, tells Woodblock to choose the file `path/to/some/file.jpg`
as the second file. The path is relative to the file corpus defined in the
`[general]` section. The first file will still be chosen randomly.


## Filler Fragments
Filler fragments can be added by adding an `R` or `Z` to the `layout` of the
scenario (both, upper and lower case letters work). `R` adds a random data
fragment and `Z` adds a fragment filled with zeroes. As described in the
`[general]` section, the size of the filler fragment depends on the values
of `min filler blocks` and `max filler blocks`. These can be specified in
the `[general]` section as well as in a scenario section. The definition in
a scenario section has precedence over a definition in the `[general]`
section.

Here is a simple scenario definition with fillers:

```ini
[A Simple Scenario with Filler]
  frags file1 = 2
  layout = 1.1, R, 1.2, Z
```

This creates a scenario looking like this:

![scenario layout with fillers](../assets/file_with_fillers.png "scenario layout with fillers"){: .noborder}

We have the first fragment of the file, then some random data, then
the second fragment, and finally some blocks filled with zeroes.

## Multiple Scenarios
As already mentioned, every section except for the one named `[general]`
is considered to be a scenario. Therefore, defining multiple scenarios boils
down to creating multiple sections in a configuration file:

Here is an example defining three scenarios:
```ini
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
```

Again, the order of the scenarios in the resulting test image corresponds
to the order of the definition in the configuration file.

Note that Woodblock will not add any additional blocks between two scenarios.
That is, the first block of the second scenario will be next to the last block
of the first scenario. If you would like to have filler blocks between two
scenarios, you have to add filler blocks to the beginning or end of a scenario.

## Option Reference
This sections provides a brief description of all the options available in a
scenario section.

| Option         | Required | Default | Layout Type | Description |
| -------------- | -------- | ------- | ----------- | ----------- |
| `fileN`        | no       | *n/a*   | manual      | Path to the `N`<sup>th</sup> file to use. Path is relative to the file corpus. |
| `frags fileN`  | no       | *n/a*   | manual      | Number of fragments to split the `N`<sup>th</sup> into. |
| `layout`       | yes      | *n/a*   | all         | Defines the layout type. It can be either `intertwine` or a fragment specification. |
| `min frags`    | no       | 1       | intertwine  | Defines the minimal number of fragments per file. |
| `max frags`    | no       | 4       | intertwine  | Defines the maxmial number of fragments per file. |
| `num files`    | yes      | *n/a*   | intertwine  | Defines the number of files to intertwine. |
