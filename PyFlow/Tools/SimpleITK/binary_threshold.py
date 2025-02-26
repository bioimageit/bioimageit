from pathlib import Path
import SimpleITK as sitk

class Tool:

    name = "Binary threshold"
    description = "SimpleITK Binary threshold."
    categories = ['SimpleITK', 'Custom']
    inputs = [
            dict(
            name = 'image',
            help = 'Input image path',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
        dict(
            name = 'channel',
            help = 'Channel to threshold',
            type = 'int',
            default = 0,
        ),
        dict(
            name = 'lowerThreshold',
            help = 'Lower threshold',
            type = 'float',
            default = 0,
        ),
        dict(
            name = 'upperThreshold',
            help = 'Upper threshold',
            type = 'float',
            default = 255,
        ),
        dict(
            name = 'insideValue',
            help = 'Inside value',
            type = 'int',
            default = 1,
        ),
        dict(
            name = 'outsideValue',
            help = 'Outside value',
            type = 'int',
            default = 0,
        ),
    ]
    outputs = [
        dict(
            name = 'thresholded_image',
            help = 'Output image path',
            default = '{image.stem}_thresholded{image.exts}',
            type = 'Path',
        ),
    ]

    def processData(self, args):
        if not args.image.exists():
            raise Exception(f'Error: input image {args.image} does not exist.')
        inputImage = sitk.ReadImage(args.image)
        if 'vector' in inputImage.GetPixelIDTypeAsString():
            inputImage = inputImage.ToScalarImage()[args.channel, :, :]
        thresholdedImage = sitk.BinaryThreshold(inputImage, args.lowerThreshold, args.upperThreshold, args.insideValue, args.outsideValue)
        sitk.WriteImage(thresholdedImage, args.thresholded_image)
        return