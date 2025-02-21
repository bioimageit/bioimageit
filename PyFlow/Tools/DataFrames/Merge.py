
class MergeDataFrames:

    name = "Merge DataFrames"
    description = "Merge DataFrames."
    multipleInputs = True

    inputs = [
            dict(
            names = ['--how'],
            help = 'How',
            type = str,
            default = None,
            static=True
        ),
        dict(
            names = ['--on'],
            help = 'On',
            type = str,
            default = None,
            static=True
        ),
        dict(
            names = ['--left_on'],
            help = 'Left on',
            type = str,
            default = None,
            static=True
        ),
        dict(
            names = ['--right_on'],
            help = 'Right on',
            type = str,
            default = None,
            static=True
        ),
        dict(
            names = ['--left_index'],
            help = 'Left index',
            type = bool,
            default = None,
            static=True
        ),
        dict(
            names = ['--right_index'],
            help = 'Right index',
            type = bool,
            default = None,
            static=True
        ),
        dict(
            names = ['--sort'],
            help = 'Sort',
            type = bool,
            default = None,
            static=True
        ),
        dict(
            names = ['--left_suffix'],
            help = 'Left suffix',
            type = str,
            default = '_x',
            static=True
        ),
        dict(
            names = ['--right_suffix'],
            help = 'Right suffix',
            type = str,
            default = '_y',
            static=True
        ),
    ]
    outputs = [
    ]

    def processDataFrames(self, dataFrames, argsList):
        df = dataFrames[0]
        args = argsList[0]
        mergeArgs = vars(args)
        del mergeArgs['last_suffix']
        del mergeArgs['right_suffix']
        mergeArgs['suffixes'] = (args.left_suffix, args.right_suffix)
        for i in range(len(dataFrames)-1):
            df = df.merge(dataFrames[i+1], **mergeArgs)
        return df