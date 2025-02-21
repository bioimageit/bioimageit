from pathlib import Path
import SimpleITK as sitk

class BinaryThreshold:

    name = "Binary threshold"
    description = "SimpleITK Binary threshold."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Input image path',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--channel'],
            help = 'Channel to threshold',
            type = int,
            default = 0,
        ),
        dict(
            names = ['--lowerThreshold'],
            help = 'Lower threshold',
            type = float,
            default = 0,
        ),
        dict(
            names = ['--upperThreshold'],
            help = 'Upper threshold',
            type = float,
            default = 255,
        ),
        dict(
            names = ['--insideValue'],
            help = 'Inside value',
            type = int,
            default = 1,
        ),
        dict(
            names = ['--outsideValue'],
            help = 'Outside value',
            type = int,
            default = 0,
        ),
    ]
    outputs = [
        dict(
            names = ['--thresholded_image'],
            help = 'Output image path',
            type = Path,
        ),
    ]

    def processData(self, args):
        if not args.image.exists():
            raise Exception(f'Error: input image {args.image} does not exist.')
        inputImage = sitk.ReadImage(args.image)
        if 'vector' in inputImage.GetPixelIDTypeAsString():
            inputImage = inputImage.ToScalarImage()[args.channel, :, :]
        thresholdedImage = sitk.BinaryThreshold(inputImage, args.lowerThreshold, args.upperThreshold, args.insideValue, args.outsideValue)
        sitk.WriteImage(thresholdedImage, args.threshold_image)
        return