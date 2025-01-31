import sys
from importlib import import_module
import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Denoising']
    dependencies = dict(conda=['bioimageit::cimgdenoising==1.0.0|osx-64,win-64'], pip=[])
    environment = 'cimgdenoising'
    test = ['--input_image', 'Montage.tif', '--algo', 'PEWA', '--patch', '3', '--neigh', '7', '--output_image', 'pewa_result.tif']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("CImg denoising", description="Denoise 2D+T images corrupted by Gaussian or Poisson noise with patch based methods and basic methods and variational methods.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)

        # General parameters
        inputs_parser.add_argument("--first", type=int, default=0, help="Number of the first image (0: default value)")
        inputs_parser.add_argument("--last", type=int, default=-1, help="Number of the last image (depth or time: default value)")
        inputs_parser.add_argument("--alpha", type=float, default=0.0, help="Alpha mixing of input/output images [0. - 1.] (0.: default value)")
        inputs_parser.add_argument("--scale", type=float, default=1.0, help="Resize the volume in the range [0.5 - 1.5] (1.: default value)")
        inputs_parser.add_argument("--range", type=float, default=1.0, help="Automatic intensity scaling (-1) or manual scaling")

        # Algorithm selection
        inputs_parser.add_argument("--algo", type=str, default=None, help="Algorithm name", choices=['BM3D', 'NLBayes', 'NLMeans', 'BayesNLmeans', 'SAFIR', 'PEWA', 'OWF', 'DCT', 'Wiener', 'Bilateral', 'Gaussian', 'Median', 'TV', 'SV', 'HV'])

        # Noise parameters and simulation
        inputs_parser.add_argument("--ng", type=float, default=0.0, help="Add artificial Gaussian noise before applying the algorithm")
        inputs_parser.add_argument("--np", action="store_true", help="Add artificial Poisson noise before applying the algorithm")
        inputs_parser.add_argument("--msg", type=float, default=0.0, help="Adjust manually the assumed Gaussian noise standard deviation")
        inputs_parser.add_argument("--stab", action="store_true", help="Variance stabilization for Poisson noise removal")

        # Options and parameters of denoising algorithms
        inputs_parser.add_argument("--patch", type=int, default=3, help="Half size of the patch (NLMeans, PEWA, OWF, SAFIR, DCT, Wiener)")
        inputs_parser.add_argument("--neigh", type=int, default=7, help="Half size of the neighborhood (NLMeans, PEWA, OWF, SAFIR, DCT, Median, Bilateral)")
        inputs_parser.add_argument("--denoisep", type=float, default=-1.0,
                            help="Denoising parameter (NLMeans: 3.5 | DCT: 3.0 | Wiener: 1.25 | Bilateral: 2.0 | Gaussian: 1.0 | TV: 6.0 | SV: 6.0 | HV: 6.0)")
        inputs_parser.add_argument("--sparsep", type=float, default=0.6,
                            help="Sparsity parameter (SV and HV algorithms) in the range [0.1 - 0.9]")
        inputs_parser.add_argument("--iter", type=int, default=4, help="Number of iterations (NDSafir only)")

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image path.', default='{input_image.stem}_denoised{input_image.exts}', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit(f'Error: input image {args.input_image} does not exist.')
        
        print(f'Process {args.input_image}')
        import subprocess
        return subprocess.run(["denoise",
                                "-i", str(args.input_image),
                                "-o", str(args.output_image),
                                "-first", str(args.first),
                                "-last", str(args.last),
                                "-alpha", str(args.alpha),
                                "-scale", str(args.scale),
                                "-range", str(args.range),
                                "-algo", args.algo if args.algo is not None else "",
                                "-ng", str(args.ng),
                                "-np" if args.np else "",  # only include if np is True
                                "-msg", str(args.msg),
                                "-stab" if args.stab else "",  # only include if stab is True
                                "-patch", str(args.patch),
                                "-neigh", str(args.neigh),
                                "-denoisep", str(args.denoisep),
                                "-sparsep", str(args.sparsep),
                                "-iter", str(args.iter)
                                ])
        

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)