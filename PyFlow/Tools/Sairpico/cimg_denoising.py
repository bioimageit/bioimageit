import sys
from importlib import import_module
import json
from pathlib import Path

class Tool:

    categories = ['Denoising']
    dependencies = dict(conda=['bioimageit::cimgdenoising==1.0.0|osx-64,win-64'], pip=[])
    environment = 'cimgdenoising'
    test = ['--input_image', 'Montage.tif', '--algo', 'PEWA', '--patch', '3', '--neigh', '7', '--output_image', 'pewa_result.tif']
    
    name = "CImg denoising"
    description = "Denoise 2D+T images corrupted by Gaussian or Poisson noise with patch based methods and basic methods and variational methods."
    inputs = [
            dict(
                names = ['-i', '--input_image'],
                help = 'The input image path.',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['--first'],
                help = 'Number of the first image (0: default value)',
                default = 0,
                type = int,
            ),
            dict(
                names = ['--last'],
                help = 'Number of the last image (depth or time: default value)',
                default = -1,
                type = int,
            ),
            dict(
                names = ['--alpha'],
                help = 'Alpha mixing of input/output images [0. - 1.] (0.: default value)',
                default = 0.0,
                type = float,
            ),
            dict(
                names = ['--scale'],
                help = 'Resize the volume in the range [0.5 - 1.5] (1.: default value)',
                default = 1.0,
                type = float,
            ),
            dict(
                names = ['--range'],
                help = 'Automatic intensity scaling (-1) or manual scaling',
                default = 1.0,
                type = float,
            ),
            dict(
                names = ['--algo'],
                help = 'Algorithm name',
                default = None,
                choices = ['BM3D', 'NLBayes', 'NLMeans', 'BayesNLmeans', 'SAFIR', 'PEWA', 'OWF', 'DCT', 'Wiener', 'Bilateral', 'Gaussian', 'Median', 'TV', 'SV', 'HV'],
                type = str,
            ),
            dict(
                names = ['--ng'],
                help = 'Add artificial Gaussian noise before applying the algorithm',
                default = 0.0,
                type = float,
            ),
            dict(
                names = ['--np'],
                help = 'Add artificial Poisson noise before applying the algorithm',
                default = False,
                type = bool,
            ),
            dict(
                names = ['--msg'],
                help = 'Adjust manually the assumed Gaussian noise standard deviation',
                default = 0.0,
                type = float,
            ),
            dict(
                names = ['--stab'],
                help = 'Variance stabilization for Poisson noise removal',
                default = False,
                type = bool,
            ),
            dict(
                names = ['--patch'],
                help = 'Half size of the patch (NLMeans, PEWA, OWF, SAFIR, DCT, Wiener)',
                default = 3,
                type = int,
            ),
            dict(
                names = ['--neigh'],
                help = 'Half size of the neighborhood (NLMeans, PEWA, OWF, SAFIR, DCT, Median, Bilateral)',
                default = 7,
                type = int,
            ),
            dict(
                names = ['--denoisep'],
                help = 'Denoising parameter (NLMeans: 3.5 | DCT: 3.0 | Wiener: 1.25 | Bilateral: 2.0 | Gaussian: 1.0 | TV: 6.0 | SV: 6.0 | HV: 6.0)',
                default = -1.0,
                type = float,
            ),
            dict(
                names = ['--sparsep'],
                help = 'Sparsity parameter (SV and HV algorithms) in the range [0.1 - 0.9]',
                default = 0.6,
                type = float,
            ),
            dict(
                names = ['--iter'],
                help = 'Number of iterations (NDSafir only)',
                default = 4,
                type = int,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output_image'],
                help = 'The output image path.',
                default = '{input_image.stem}_denoised{input_image.exts}',
                type = Path,
            ),
    ]

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
        

