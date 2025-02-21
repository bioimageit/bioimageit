from pathlib import Path
import pandas

class ListFiles:
    
    name = "list_files"
    description = "Reads a folder and create a pandas DataFrame from the file list."
    environment = 'bioimageit'
    categories = ['Data']

    inputs = [
            dict(
            names = ['--folderPath'],
            help = 'Folder path',
            type = Path,
            required = True,
        ),
        dict(
            names = ['--filter'],
            help = 'Filter',
            type = str,
            default = '*',
        ),
    ]
    outputs = [
        dict(
            names = ['--columnName'],
            help = 'Column name',
            type = str,
        ),
    ]

    def processDataFrame(self, dataFrame, argsList):
        allFiles = []
        for args in argsList:
            if args.folderPath is None: continue
            if not args.folderPath.exists(): continue
            try:
                files = sorted(list(args.folderPath.glob(args.filter))) if args.filter is not None and len(args.filter)>0 else None
            except ValueError as e:
                print(e)
            if files is None:
                files = sorted(list(args.folderPath.iterdir()))
            allFiles += [f for f in files if f.name != '.DS_Store']
        dataFrame = pandas.DataFrame(data={self.parameters['outputs']['columnName']['value']:allFiles})
        # ThumbnailGenerator.get().generateThumbnails(self.name, dataFrame)
        return dict(dataFrame=dataFrame)
