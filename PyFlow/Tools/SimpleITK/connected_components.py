from pathlib import Path
import SimpleITK as sitk

class Tool:

    name = "Connected components"
    description = "Compute connected components in the given binary image."
    categories = ['SimpleITK', 'Custom']
    inputs = [
            dict(
            name = 'image',
            help = 'Input image path',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
    ]
    outputs = [
        dict(
            name = 'labeled_image',
            help = 'Output image',
            default = '{image.stem}_labeled{image.exts}',
            type = 'Path',
        ),
        dict(
            name = 'labeled_image_rgb',
            help = 'Output rgb image',
            default = '{image.stem}_labeled_rgb{image.exts}',
            type = 'Path',
        ),
    ]

    def processData(self, args):
        if not args.image.exists():
            raise Exception(f'Error: input image {args.image} does not exist.')
        inputImage = sitk.ReadImage(args.image)
        labeledImage = sitk.ConnectedComponent(inputImage)
        sitk.WriteImage(sitk.Cast(labeledImage, sitk.sitkUInt16), args.labeled_image)
        labeledImageRGB = sitk.LabelToRGB(labeledImage)
        sitk.WriteImage(labeledImageRGB, args.labeled_image_rgb)