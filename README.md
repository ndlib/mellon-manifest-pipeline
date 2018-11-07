# mellon-manifest-pipeline

## Generating a JSON file from CSV fles

The initial input to the manifest pipeline is two CSV files.

### First CSV file
The first CSV file contains the main metadata. It should end with *main.csv*

The following labels are expected:

**Label** The label for the image sequence
**Description**  A short description of the image sequence
**Rights**  Licensing or Copyright information
**Attribution** Artist attribution
**Sequence_filename** **Not Used**
**Sequence_label** The name of the image sequence array in the metadata JSON
**Sequence_viewing_experience** the value should be *paged*
**unique_identifier** id used for generating IIIF manifest
**Metadata_label** on second and subsequent lines, and be used to specify metadata common to all images in the sequence
**Metadata_value** on second and subsequent lines, and be used to specify metadata common to all images in the sequence

An example file, *example-main.csv*, looks like this:

```

Label,Description,Rights,Attribution,Sequence_filename,Sequence_label,Sequence_viewing_experience,unique_identifier,Metadata_label,Metadata_value
Label,Description,rights,attribution,,sequency,paged,2018_example_001,,
,,,,,,,,Title,"Wunder der Verenbung"
,,,,,,,,Author(s),"Bolle, Fritz"
,,,,,,,,"Publication date","[1951]"
,,,,,,,,Attribution,""Welcome Library<br/>License: CC-BY-NC"

```

### Second CSV file
The first CSV file contains the image sequence  metadata. It should end with *sequence.csv*

The following labels are expected:

**Filenames** the actual file name under the image directory
**Label** This file's Label
**Description** a file-specific description

The order in which the files are entered, by row, demotes their order in the image sequence.

An example:

```

Filenames,Label,Description
009_output,009,
046_output.tif,046,
2018_009.jpg,2018 009,
2018_049_009.jpg,2018 049 009,"Look, a JPG file"

```

### CSV conversion script

The `create-json-from_csv` script will look for a main and sequence CSV located in a directory together, and use them to generate a JSON file to standard out (the commandline). By default, it looks in the current directory. If an argument is provided on the command line, it will look for the files in that directory instead.

An example:

Let's say that the directory *myCsvFiles* contains the above example main and sequence files, named *mycsv-main.csv* and  *mycsv-sequence.csv*.

The command: `create-json-from_csv myCsvFiles`

would produce the following output:

```
{
  "errors": [],
  "attribution": "attribution",
  "description": "Description",
  "iiif-server": "https://image-server.library.nd.edu:8182/iiif/2",
  "creator": "creator@email.com",
  "rights": "rights",
  "unique-identifier": "2018_example_001",
  "label": "Label",
  "sequences": [
    {
      "viewingHint": "paged",
      "pages": [
        {
          "file": "009_output",
          "label": "009"
        },
        {
          "file": "046_output.tif",
          "label": "046"
        },
        {
          "file": "2018_009.jpg",
          "label": "2018 009"
        },
        {
          "file": "2018_049_009.jpg",
          "label": "2018 049 009"
        }
      ],
      "label": "sequency"
    }
  ],
  "metadata": [
    {
      "value": "Wunder der Verenbung",
      "label": "Title"
    },
    {
      "value": "Bolle, Fritz",
      "label": "Author(s)"
    },
    {
      "value": "[1951]",
      "label": "Publication date"
    },
    {
      "value": "Welcome Library<br/>License: CC-BY-NC\"",
      "label": "Attribution"
    }
  ]
}
```
