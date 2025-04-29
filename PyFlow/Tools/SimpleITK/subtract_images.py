from pathlib import Path
import SimpleITK as sitk

class Tool:

    name = "Subtract images"
    description = "Subtract images."
    categories = ['SimpleITK', 'Custom']
    inputs = [
            dict(
            name = 'image1',
            help = 'Input image 1',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
        dict(
            name = 'image2',
            help = 'Input image 2',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
    ]
    outputs = [
        dict(
            name = 'out',
            help = 'Output image',
            default = '{image1.stem}-{image2.stem}{image1.exts}',
            type = 'Path',
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