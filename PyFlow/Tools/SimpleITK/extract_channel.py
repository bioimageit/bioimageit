from pathlib import Path
import SimpleITK as sitk

class Tool:

    name = "Extract channel"
    description = "Extract an image channel."
    categories = ['SimpleITK', 'Custom']
    inputs = [
            dict(
            name = 'image',
            help = 'Input image',
            type = 'Path',
            required = True,
            autoColumn = True,
        ),
        dict(
            name = 'channel',
            help = 'Channel to extract',
            type = 'int',
            default = 0,
        ),
    ]
    outputs = [
        dict(
            name = 'out',
            help = 'Output image',
            default = '{image.stem}_channel{channel}{image.exts}',
            type = 'Path',
        ),
    ]

    def processData(self, args):
        if not args.image.exists():
            raise Exception(f'Error: input image {args.image} does not exist.')
        inputImage = sitk.ReadImage(args.image)
        if 'vector' in inputImage.GetPixelIDTypeAsString():
            nChannels = inputImage.ToScalarImage().GetSize()[0]
            outputImage = inputImage[min(args.channel, nChannels), :, :]
        else:
            outputImage = inputImage[:,:, min(args.channel, inputImage.GetSize()[-1])]
        sitk.WriteImage(outputImage, args.out)