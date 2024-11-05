import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(conda=['conda-forge::pycudadecon'], pip=[])
    environment = 'condadecon'
    test = ['--input_image', 'deskew.tif', '--output_image', 'deskewed.tif']
    
    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("condaDecon", description="CUDA/C++ implementation of an accelerated Richardson Lucy Deconvolution algorithm.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-dx', '--dxdata', help='XY Pixel size of image volume.', type=float, default=0.1)
        inputs_parser.add_argument('-dz', '--dzdata', help='Z-step size in image volume. In a typical light sheet stage-scanning acquisition, this corresponds to the step size that the stage takes between planes, NOT the final Z-step size between planeds after deskewing along the optical axis of the detection objective.', type=float, default=0.5)
        inputs_parser.add_argument('-a', '--angle', help='Deskew angle (usually, angle between sheet and axis of stage motion).', type=float, default=31.5)
        inputs_parser.add_argument('-w', '--width', help='If not 0, crop output image to specified width', type=int, default=0)
        inputs_parser.add_argument('-s', '--shift', help='If not 0, shift image center by this value', type=int, default=0)
        inputs_parser.add_argument('-pv', '--pad_val', help='Value to pad image with when deskewing. If None the median value of the last Z plane will be used.', type=int, default=None)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image path.', default='{input_image.stem}_stackreg.{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )

    def initialize(self, args):
        print('Loading libraries...')
        import pycudadecon
        from skimage import io
        self.pycudadecon = pycudadecon
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
        out_im = self.pycudadecon.deskewGPU(im, dxdata=args.dxdata, dzdata=args.dzdata, angle=args.angle, width=args.width, shift=args.shift, pad_val=args.pad_val)

        print(f'[[3/3]] Save image')
        self.io.imsave(args.output_image, out_im)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)