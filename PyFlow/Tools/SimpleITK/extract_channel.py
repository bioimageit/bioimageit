from pathlib import Path
import SimpleITK as sitk

class ExtractChannel:

    name = "extract_channel"
    description = "Extract an image channel."
    inputs = [
            dict(
            names = ['--image'],
            help = 'Input image',
            type = Path,
            required = True,
            autoColumn = True,
        ),
        dict(
            names = ['--channel'],
            help = 'Channel to extract',
            type = int,
            default = 0,
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
        if not args.image.exists():
            raise Exception(f'Error: input image {args.image} does not exist.')
        inputImage = sitk.ReadImage(args.image)
        if 'vector' in inputImage.GetPixelIDTypeAsString():
            nChannels = inputImage.ToScalarImage().GetSize()[0]-1
            inputImage = inputImage[min(args.channel, nChannels), :, :]
        sitk.WriteImage(inputImage, args.out)