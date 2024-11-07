import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(conda=['conda-forge::pycudadecon|linux-64,win-64'], pip=[])
    environment = 'condadecon'
    # test = ['--input_image', 'otf.tif', '--psf', '?' '--output_image', 'otf_decon.tif']
    
    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("condaDecon", description="CUDA/C++ implementation of an accelerated Richardson Lucy Deconvolution algorithm.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-p', '--psf', help='Path to the PSF or OTF file.', required=True, type=Path)
        inputs_parser.add_argument('-b', '--background', help='User-supplied background to subtract. If "auto", the median value of the last Z plane will be used as background.', default='80', type=str)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image path.', default='{input_image.stem}_stackreg.{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )

    def initialize(self, args):
        print('Loading libraries...')
        from pycudadecon import decon
        from skimage import io
        self.decon = decon
        self.io = io

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)
        try:
            background = int(args.background) if args.background != 'auto' else args.background
        except ValueError as e:
            sys.exit('Error: the background argument must be an integer or "auto"; but it is "{args.background}".')
        
        print(f'[[1/3]] Load image {input_image}')
        im = self.io.imread(input_image)
        
        print(f'[[2/3]] Process image')
        out_im = self.decon(im, psf=args.psf, background=background)
        
        print(f'[[3/3]] Save image')
        self.io.imsave(args.output_image, out_im)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)