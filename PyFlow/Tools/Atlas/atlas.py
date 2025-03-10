import subprocess
from pathlib import Path

class Tool:

    categories = ['Detection']
    dependencies = dict(conda=['bioimageit::atlas'], pip=[])
    environment = 'atlas'
    test = ['--input_image', 'M10.tif', '--output_image', 'M10_detections.tif']
    
    name = "Atlas"
    description = "ATLAS is a new spot detection method. The spots size is automatically selected and the detection threshold adapts to the local image dynamics."
    inputs = [
            dict(
                name = 'input_image',
                shortname = 'i',
                help = 'The input image path. The width and height of the image should be even for best results.',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'gaussian_std',
                shortname = 'rad',
                help = 'Standard deviation of the Gaussian window (0 for global threshold).',
                default = 60,
                type = 'int',
            ),
            dict(
                name = 'p_value',
                shortname = 'pval',
                help = 'P-value to account for the probability of false detection.',
                default = 0.001,
                decimals = 6,
                type = 'float',
            ),
            dict(
                name = 'area_lim',
                shortname = 'arealim',
                help = 'Remove detections smaller than this area.',
                default = 0,
                decimals = 2,
                type = 'float',
            ),
            dict(
                name = 'verbose',
                shortname = 'v',
                help = 'Verbose mode.',
                default = False,
                type = 'bool',
            ),
    ]
    outputs = [
            dict(
                name = 'output_image',
                shortname = 'o',
                help = 'The output image.',
                default = '{input_image.stem}_detections{input_image.exts}',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        blobsFile = Path(__file__).parent.resolve() / 'data' / 'blobs.txt'
        blobsFile.parent.mkdir(exist_ok=True)
        blobsFileExists = blobsFile.exists()
        nSteps = 1 if blobsFileExists else 2
        if not blobsFileExists:
            print(f'[[1/{nSteps}]] Run Blobsref')
            subprocess.run(['blobsref', '-o', blobsFile], check=True)

        print(f'[[{nSteps}/{nSteps}]] Run Atlas')
        verbose = ['-v'] if args.verbose else []
        command = ['atlas', '-ref', blobsFile, '-i', args.input_image, '-o', args.output_image, '-rad', args.gaussian_std, '-pval', args.p_value] + verbose

        subprocess.run([str(c) for c in command], check=True)

