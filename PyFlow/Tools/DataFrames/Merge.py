import pandas

class Tool:

    name = "Merge DataFrames"
    description = "Merge DataFrames."
    multipleInputs = True
    categories = ['Data']

    inputs = [
            dict(
            name = 'how',
            help = 'How',
            choices = ['left', 'right', 'outer', 'inner', 'cross'],
            type = 'str',
            default = 'inner',
            static=True
        ),
        dict(
            name = 'on',
            help = 'On',
            type = 'str',
            default = None,
            static=True
        ),
        dict(
            name = 'left_on',
            help = 'Left on',
            type = 'str',
            default = None,
            static=True
        ),
        dict(
            name = 'right_on',
            help = 'Right on',
            type = 'str',
            default = None,
            static=True
        ),
        dict(
            name = 'left_index',
            help = 'Left index',
            type = 'bool',
            default = None,
            static=True
        ),
        dict(
            name = 'right_index',
            help = 'Right index',
            type = 'bool',
            default = None,
            static=True
        ),
        dict(
            name = 'sort',
            help = 'Sort',
            type = 'bool',
            default = None,
            static=True
        ),
        dict(
            name = 'left_suffix',
            help = 'Left suffix',
            type = 'str',
            default = '_x',
            static=True
        ),
        dict(
            name = 'right_suffix',
            help = 'Right suffix',
            type = 'str',
            default = '_y',
            static=True
        ),
    ]
    outputs = [
    ]

    def mergeDataFrames(self, dataFrames, argsList):
        if len(dataFrames)==0 or len(argsList)==0: return pandas.DataFrame()
        df = dataFrames[0]
        args = argsList[0]
        mergeArgs = vars(args)
        mergeArgs['suffixes'] = (args.left_suffix, args.right_suffix)
        mergeArgs = {key: value for key, value in mergeArgs.items() if value is not None and key not in ['left_suffix', 'right_suffix']}
        for i in range(len(dataFrames)-1):
            df = df.merge(dataFrames[i+1], **mergeArgs)
        return df