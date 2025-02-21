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
            type = str,
            static = True,
        ),
        dict(
            name = 'regex',
            help = 'Regex',
            type = str,
            default = r'(?P<column1>\w+)_(?P<column2>\w+)',
            static = True,
        ),
    ]
    outputs = [
    ]
    
    def processDataFrame(self, dataFrame: pandas.DataFrame, argsList):
        args = argsList[0]
        df: pandas.DataFrame = dataFrame.copy()
        regex = args.regex
        columnName = args.columnName
        columnIndex = None
        try:
            columnIndex = int(columnName)
        except ValueError as e:
            pass
        for index, row in dataFrame.iterrows():
            m = re.search(regex, str(row[columnName] if columnIndex is None else row.iloc[columnIndex]))
            if m is None: continue
            for key, value in m.groupdict().items():
                df.at[index, key] = value
        return df