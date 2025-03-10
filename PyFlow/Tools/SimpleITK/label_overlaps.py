import SimpleITK as sitk
import numpy as np
import pandas

class Tool:
    
    name = "Label overlaps"
    description = "Compute label overlap statistics from two label images."
    categories = ['SimpleITK', 'Custom']
    multipleInputs = True
    inputs = [
            dict(
            name = 'label1',
            help = 'Input label image 1',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
            dict(
            name = 'label2',
            help = 'Input label image 2',
            type = 'Path',
            required = True,
            autoColumn = True,
        )
    ]
    outputs = [
    ]

    def processDataFrame(self, dataFrame, argsList):
        self.outputMessage = 'Label overlap statistics will be computed on execution.'
        return dataFrame

    def processData(self, args):
        if not args.label1.exists():
            raise Exception(f'Error: input label image 1 {args.label1} does not exist.')
        if not args.label2.exists():
            raise Exception(f'Error: input label image 2 {args.label2} does not exist.')
        label1 = sitk.ReadImage(args.label1)
        label2 = sitk.ReadImage(args.label2)
        label1Data = sitk.GetArrayFromImage(label1).astype(np.uint64)
        label2Data = sitk.GetArrayFromImage(label2).astype(np.uint64)
        records = []
        for i in range(label1Data.max()):
            uniques, counts = np.unique(label2Data[label1Data == i], return_counts=True)
            for u, c in zip(uniques, counts):
                records.append(dict(label1=i, label2=u, overlap=c))
        self.outputMessage = ''
        return pandas.DataFrame.from_records(records)