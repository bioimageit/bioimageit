import argparse
import sys
from pathlib import Path
from .core import ndsafir_series

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['bioimageit::ndsafir'], pip=[])
    environment = 'ndsafir'
    autoInputs = ['input_image']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("ND-Safir 3D", description="Denoising method dedicated to microscopy image and sequence analysis.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-n', '--noise', help='Model used to evaluate the noise variance.', default='Gauss', choices=['Gauss', 'Poisson-Gauss', 'Adaptive-Gauss'], type=str)
        inputs_parser.add_argument('-p', '--patch', help='Patch radius. Must be of the form AxBxC where A, B and C are the patch radius in each dimension.', default='7x7x1', type=str)
        inputs_parser.add_argument('-nf', '--noise_factor', help='Noise factor.', default=1, type=float)
        inputs_parser.add_argument('-nit', '--n_iterations', help='Number of iterations.', default=5, type=int)
        inputs_parser.add_argument('-nfr', '--n_frames', help='Number of frames to process in a batch. Use 0 to process everything at once.', default=0)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image.', default='{input_image.stem}_denoised{input_image.exts}', type=Path)
        return parser
    
    def processDataFrame(self, dataFrame):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run ND-Safir on image {args.input_image}')
        ndsafir_series.ndsafir_series(args.input_image, args.output_image, args.noise, args.n_iterations, args.noise_factor, args.patch, args.n_frames)

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)