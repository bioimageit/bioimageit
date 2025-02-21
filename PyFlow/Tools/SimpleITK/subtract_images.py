from pathlib import Path
import SimpleITK as sitk

class SubtractImages:

    name = "subtract_images"
    description = "Subtract images."
    inputs = [
            dict(
            names = ['--image1'],
            help = 'Input image 1',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--image2'],
            help = 'Input image 2',
            type = Path,
            required = True,
            autoColumn = True,
        ),
    ]
    outputs = [
        dict(
            names = ['--out'],
            help = 'Output image',
            type = Path,
        ),
    ]


    def processData(self, args):
        if not args.image1.exists():
            raise Exception(f'Error: input image {args.image1} does not exist.')
        if not args.image2.exists():
            raise Exception(f'Error: input image {args.image2} does not exist.')
        inputImage1 = sitk.ReadImage(args.image1, sitk.sitkInt32)
        inputImage2 = sitk.ReadImage(args.image2, sitk.sitkInt32)
        resultImage = sitk.Subtract(inputImage1, inputImage2)
        sitk.WriteImage(sitk.Cast(resultImage, sitk.sitkUInt8), args.out)