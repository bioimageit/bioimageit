import pandas
import re

class Tool:

    name = "Column regex"
    description = "Create columns from a regex."
    categories = ['Data']

    inputs = [
            dict(
            required = True,
            name = 'columnName',
            help = 'Column name',
            type = 'str',
            autoColumn = True,
        ),
        dict(
            name = 'regex',
            help = 'Regex',
            type = 'str',
            default = r'(?P<column1>\w+)_(?P<column2>\w+)',
            static = True,
        ),
    ]
    outputs = [
    ]
    
    def processDataFrame(self, dataFrame: pandas.DataFrame, argsList):
        args = argsList[0]
        df: pandas.DataFrame = dataFrame.copy()
        for index, row in dataFrame.iterrows():
            m = re.search(args.regex, str(row[args.columnName]))
            if m is None: continue
            for key, value in m.groupdict().items():
                df.at[index, key] = value
        return df