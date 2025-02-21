from pathlib import Path
import SimpleITK as sitk
import pandas

class LabelStatistics:
    
    name = "label_statistics"
    description = "Compute label statistics from a label image."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Input image',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--label'],
            help = 'Input label',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--minSize'],
            help = 'Min size of the labels',
            type = int,
            default = 100,
        ),
        dict(
            names = ['--maxSize'],
            help = 'Max size of the labels',
            type = int,
            default = 600,
        ),
    ]
    outputs = [
        dict(
            names = ['--connected_component'],
            help = 'Output connected component',
            type = Path,
        ),
    ]

    def processDataFrame(self, dataFrames, argsList):
        self.outputMessage = 'Label statistics will be computed on execution.'

    def processData(self, args):
        if not args.image.exists():
            raise Exception(f'Error: input image {args.image} does not exist.')
        if not args.label.exists():
            raise Exception(f'Error: input label image {args.label} does not exist.')
        records = {}
        image = sitk.ReadImage(args.image)
        if 'vector' in image.GetPixelIDTypeAsString():
            image = image.ToScalarImage()[0, :, :]
        label = sitk.ReadImage(args.label)
        lsif = sitk.LabelStatisticsImageFilter()
        lsif.Execute(image, label)
        nLabels = lsif.GetNumberOfLabels()
        # for i in range(1, min(nLabels, maxNLabels)):
        for i in range(1, nLabels):
            minimum = lsif.GetMinimum(i)
            maximum = lsif.GetMaximum(i)
            median = lsif.GetMedian(i)
            mean = lsif.GetMean(i)
            numPixels = lsif.GetCount(i)
            bb = lsif.GetBoundingBox(i)
            if bb[0] == bb[1] or bb[2] == bb[3]: continue
            if numPixels < args.minSize or numPixels > args.maxSize: continue
            cc = image[bb[0]:bb[1], bb[2]:bb[3]]
            # dataImage = sitk.GetArrayFromImage(label)
            # cc = dataImage[bb[2]:bb[3], bb[0]:bb[1]]
            # cc = sitk.GetImageFromArray(cc)
            # cc = image[bb[0]:bb[1], bb[2]:bb[3]]
            # cc = image[bb[0]:bb[0]+bb[2]+1, bb[1]:bb[1]+bb[3]+1]
            # cc = image[bb[1]:bb[1]+bb[3], bb[0]:bb[0]+bb[2]]
            sitk.WriteImage(cc, args.connected_component)
            records.append(dict(image=args.image, label=args.label, connected_component=args.connected_component, label_index=i, minimum=minimum, maximum=maximum, median=median, mean=mean, numPixels=numPixels, bb=str(bb)))
        return pandas.DataFrame.from_records(records)