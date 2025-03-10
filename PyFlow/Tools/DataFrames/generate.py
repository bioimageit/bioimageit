import pandas
import numpy as np
import numbers

class Tool:

    name = 'Generate data'
    description = 'Generate a DataFrame from the given values, range or space.\nSee the numpy documentation on array creation routines for more information (arange, linspace, logspace and geomspace, https://numpy.org/doc/stable/reference/generated/numpy.arange.html).'

    categories = ['Data']
    dependencies = dict(conda=[], pip=[])
    environment = 'bioimageit'
    test = []
    
    inputs = [
        dict(
            name = 'values',
            help = 'Comma separated values.',
            type = 'str',
        ),
        dict(
            name = 'arange',
            help = 'Return evenly spaced values within a given interval. (see numpy.arange). Provide the parameters in the form start,stop,step ; for example "0,10,2".',
            type = 'str',
        ),
        dict(
            name = 'linspace',
            help = 'Return evenly spaced numbers over the specified interval (see numpy.linspace). Provide the parameters in the form start,stop,num,endpoint ; for example "0,10,50,True" or "-5, 5".',
            type = 'str',
        ),
        dict(
            name = 'logspace',
            help = 'Return numbers spaced evenly on a log scale (see numpy.logspace).',
            type = 'str',
        ),
        dict(
            name = 'geomspace',
            help = 'Return numbers spaced evenly on a log scale (a geometric progression, see numpy.geomspace).',
            type = 'str',
        ),
        dict(
            name = 'columnName',
            help = 'Column name',
            type = 'str',
            default = 'values',
            static = True,
        ),
    ]
    outputs = []

    def num(self, s):
        try:
            return int(s)
        except ValueError:
            try:
                return float(s)
            except ValueError:
                return None
    
    def parseArgs(self, values):
        result = [self.num(v) for v in values.replace('[', '').replace(']', '').split(',')]
        return [v for v in result if isinstance(v, numbers.Number)]
    
    def processDataFrame(self, dataFrame, argsList):
        values = []
        for args in argsList:
            if args.values is not None and len(args.values)>0:
                values = self.parseArgs(args.values)
            elif args.arange is not None and len(args.arange)>0:
                values = np.arange(*self.parseArgs(args.arange))
            elif args.linspace is not None and len(args.linspace)>0:
                values = np.linspace(*self.parseArgs(args.linspace))
            elif args.logspace is not None and len(args.logspace)>0:
                values = np.logspace(*self.parseArgs(args.logspace))
            elif args.geomspace is not None and len(args.geomspace)>0:
                values = np.geomspace(*self.parseArgs(args.geomspace))
        return pandas.DataFrame({args.columnName: values})