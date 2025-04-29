# List files

The "List files" nodes reads a folder and creates a pandas DataFrame from its file list.

The `folderPath` parameter defines the folder to read. 

:::{tip}

A "List files" node which lists a folder containing subfolder can send them to another "List files" node.
The `folderPath` parameter of the second node can be set to the column of the input DataFrame. This will make the second "List files" node to list all subfolders.
:::

The `filter` parameter enables to list a subset of the folder files, using [the Pattern language](https://docs.python.org/3/library/pathlib.html#pattern-language) defined in Python ("List files" uses the [`Path.glob()`](https://docs.python.org/3/library/pathlib.html#pathlib.Path.glob) method under the hood).


:::{note}

The `.DS_Store` files are excluded automatically.
:::

The `columnName` parameter defines the column name of the output DataFrame.

```{literalinclude} /../PyFlow/Tools/DataFrames/ListFiles.py
:language: python
:linenos:
```