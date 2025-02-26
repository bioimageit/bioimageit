from pathlib import Path
from matplotlib.image import thumbnail
import pandas

class Tool:
    
    name = "List Files"
    description = "Reads a folder and create a pandas DataFrame from the file list."
    environment = 'bioimageit'
    categories = ['Data']

    inputs = [
            dict(
            name = 'folderPath',
            help = 'Folder path',
            type = 'Path',
            autoColumn = True,
            required = True,
        ),
        dict(
            name = 'filter',
            help = 'Filter',
            type = 'str',
            default = '*',
        ),
        dict(
            name = 'columnName',
            help = 'Column name',
            type = 'str',
            default = 'path',
            static = True,
        ),
    ]
    outputs = [
    ]

    def processDataFrame(self, dataFrame, argsList):
        allFiles = []
        for args in argsList:
            if args.folderPath is None or not args.folderPath.is_dir(): continue
            try:
                files = sorted(list(args.folderPath.glob(args.filter))) if args.filter is not None and len(args.filter)>0 else None
            except ValueError as e:
                print(e)
            if files is None:
                files = sorted(list(args.folderPath.iterdir()))
            allFiles += [f for f in files if f.name != '.DS_Store']
        return pandas.DataFrame(data={argsList[0].columnName:allFiles} if len(argsList)>0 else {})
