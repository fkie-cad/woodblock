.. _ground-truth-logs:

*****************
Ground Truth Logs
*****************

Woodblock creates a JSON-based ground thruth file for every image generated.
This makes it easy to find out where the fragments of the file contained in
the scenarios are stored within the image.

Consider the following configuration file from the :code:`examples/` folder:

.. code-block:: ini
   
   # three-scenarios.conf
   # To generate the image use: woodblock generate three-scenarios.conf three-scenarios.dd
   [general]
   seed = 4711
   corpus = ../../tests/data/corpus/
   
   [Three files intertwined]
   layout = intertwine
   num files = 3
   min fragments = 2
   max fragments = 4
   
   [One file with missing middle]
   file1 = letters/ascii_letters
   frags file1 = 3
   layout = 1-1, 1-3
   
   [Two fragments with random data in between]
   frags file1 = 2
   layout = 1-1, R, 1-2

If you use the command indicated in the comment, you will get a ground truth JSON log named
:code:`three-scenarios.dd.json` with the following contents:

.. code-block:: json

   {
     "block_size": 512,
     "seed": 4711,
     "corpus": "../../tests/data/corpus",
     "scenarios": [
       {
         "name": "Three files intertwined",
         "files": [
           {
             "original": {
               "type": "file",
               "sha256": "d9b6da39852ccf532d87a2f8a3866ba1a53c0e863b8a35c3665a987bdc8e2554",
               "size": 2000,
               "path": "2000",
               "id": "48e1e12cf1984ee6ac09a687788968da"
             },
             "fragments": [
               {
                 "sha256": "06aed7f43b72ab019f06f2cbf0a94237ad29cc36d2c91e27a9d3e734c90b665b",
                 "size": 1024,
                 "number": 1,
                 "file_offsets": {
                   "start": 0,
                   "end": 1024
                 },
                 "image_offsets": {
                   "start": 0,
                   "end": 1024
                 }
               },
               {
                 "sha256": "de8a02038edcda61821ee2e11392af1c2ee2d65a18e4b7146708ccfc55d7a47f",
                 "size": 976,
                 "number": 2,
                 "file_offsets": {
                   "start": 1024,
                   "end": 2000
                 },
                 "image_offsets": {
                   "start": 28160,
                   "end": 29136
                 }
               }
             ]
           },
           {
             "original": {
               "type": "file",
               "sha256": "32beecb58a128af8248504600bd203dcc676adf41045300485655e6b8780a01d",
               "size": 512,
               "path": "512",
               "id": "7f28bf55e8944397a5ce0b044d40a9fc"
             },
             "fragments": [
               {
                 "sha256": "32beecb58a128af8248504600bd203dcc676adf41045300485655e6b8780a01d",
                 "size": 512,
                 "number": 1,
                 "file_offsets": {
                   "start": 0,
                   "end": 512
                 },
                 "image_offsets": {
                   "start": 1024,
                   "end": 1536
                 }
               }
             ]
           },
           {
             "original": {
               "type": "file",
               "sha256": "4db89db3034b36fc4577a674846f40b1a18d9e25eb2d6ad1aeb1e9b52264dbd0",
               "size": 26624,
               "path": "letters/ascii_letters",
               "id": "afd0c33885df409f89edb3ac08958645"
             },
             "fragments": [
               {
                 "sha256": "4db89db3034b36fc4577a674846f40b1a18d9e25eb2d6ad1aeb1e9b52264dbd0",
                 "size": 26624,
                 "number": 1,
                 "file_offsets": {
                   "start": 0,
                   "end": 26624
                 },
                 "image_offsets": {
                   "start": 1536,
                   "end": 28160
                 }
               }
             ]
           }
         ]
       },
       {
         "name": "One file with missing middle",
         "files": [
           {
             "original": {
               "type": "file",
               "sha256": "4db89db3034b36fc4577a674846f40b1a18d9e25eb2d6ad1aeb1e9b52264dbd0",
               "size": 26624,
               "path": "letters/ascii_letters",
               "id": "776280a6bec6446287d527245abc803b"
             },
             "fragments": [
               {
                 "sha256": "9c0cb8b84a7598bc9bbc0794aa962b9cb8bc7127df81b53a5ff107864fdb1a78",
                 "size": 1024,
                 "number": 1,
                 "file_offsets": {
                   "start": 0,
                   "end": 1024
                 },
                 "image_offsets": {
                   "start": 29184,
                   "end": 30208
                 }
               },
               {
                 "sha256": "daee5198e158edf8bd786f431038c39feb635f597bf4828d4943b5eec8c7a9f5",
                 "size": 12288,
                 "number": 3,
                 "file_offsets": {
                   "start": 14336,
                   "end": 26624
                 },
                 "image_offsets": {
                   "start": 30208,
                   "end": 42496
                 }
               }
             ]
           }
         ]
       },
       {
         "name": "Two fragments with random data in between",
         "files": [
           {
             "original": {
               "type": "file",
               "sha256": "d9b6da39852ccf532d87a2f8a3866ba1a53c0e863b8a35c3665a987bdc8e2554",
               "size": 2000,
               "path": "2000",
               "id": "850c4c0f6bff45e6b9f45be0ecdb3ff6"
             },
             "fragments": [
               {
                 "sha256": "6b9cf2a799611d2de886d7ee0cbaea384a4c72d5545378acd52cefc124830307",
                 "size": 1536,
                 "number": 1,
                 "file_offsets": {
                   "start": 0,
                   "end": 1536
                 },
                 "image_offsets": {
                   "start": 42496,
                   "end": 44032
                 }
               },
               {
                 "sha256": "00746f414a01c8f60190cecc38eaa58dee2f10b5357cb1680042cff91eba16a8",
                 "size": 464,
                 "number": 2,
                 "file_offsets": {
                   "start": 1536,
                   "end": 2000
                 },
                 "image_offsets": {
                   "start": 48640,
                   "end": 49104
                 }
               }
             ]
           },
           {
             "original": {
               "type": "filler",
               "sha256": "01b284754695dc102b53ba7e41ca3904aabd1993a1c27f00d8aa591a203851c2",
               "size": 4608,
               "path": "random",
               "id": "dd00cafd4d3d404491c7ec5504dacc83"
             },
             "fragments": [
               {
                 "sha256": "01b284754695dc102b53ba7e41ca3904aabd1993a1c27f00d8aa591a203851c2",
                 "size": 4608,
                 "number": 1,
                 "file_offsets": {
                   "start": 0,
                   "end": 4608
                 },
                 "image_offsets": {
                   "start": 44032,
                   "end": 48640
                 }
               }
             ]
           }
         ]
       }
     ]
   }

As you can see, the log file contains general image metadata such as the block size,
the seed, and the corpus used. Moreover, it contains a list of scenarios. Each scenario
entry has its name and a list of files it contains listed. The most important parts of
the log file are the :code:`fragments` entries. These list which fragments of a file are
included in the scenario and where they have been written to in the image file. That is,
using these entries, you can tell exactly where the fragments of all files in the image
are.

Here is a single fragment entry:

.. code-block:: json
   
   {
     "sha256": "06aed7f43b72ab019f06f2cbf0a94237ad29cc36d2c91e27a9d3e734c90b665b",
     "size": 1024,
     "number": 1,
     "file_offsets": {
       "start": 0,
       "end": 1024
     },
     "image_offsets": {
       "start": 0,
       "end": 1024
     }
   }

Here is what the different keys and values indicate:

.. option:: number
   
   The fragment number.

   When a file is split into fragments the fragments are numbered from 1 to n.
   This field shows you which number the current fragment has.
      
.. option:: size
   
   Size of the fragment in bytes.

.. option:: sha256
   
   SHA-256 hash of the fragment data.
   
.. option:: file_offsets
   
   Start and end offset of the fragment with respect to the current file.

   The :code:`start` and :code:`end` offsets given here relate to the original
   file.
   
.. option:: image_offsets
   
   Start and end offsets where the fragment is stored in the image.


