import subprocess
import sys
from pathlib import Path
from .core import ndsafir_series

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['bioimageit::ndsafir|osx-64,win-64,linux-64'], pip=[])
    environment = 'ndsafir'
    test = ['--input_image', '03_rab_bruite.tif', '--type', '3D', '-n', 'Adaptive-Gauss', '-nf', '2', '--output_image', 'DN.tif']

    noiseChoices = ['Gauss', 'Poisson-Gauss', 'Adaptive-Gauss']
    
    name = "ND-Safir"
    description = "Denoising method dedicated to microscopy image and sequence analysis."
    inputs = [
            dict(
                names = ['-i', '--input_image'],
                help = 'The input image path.',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['-t', '--type'],
                help = 'Perform 2D, 3D or 3D + time denoising.',
                default = '2D',
                choices = ['2D', '3D', '4D'],
                type = str,
            ),
            dict(
                names = ['-n', '--noise'],
                help = 'Model used to evaluate the noise variance.',
                default = 'Gauss',
                choices = ['Gauss', 'Poisson-Gauss', 'Adaptive-Gauss'],
                type = str,
            ),
            dict(
                names = ['-p', '--patch'],
                help = 'Patch radius. Must be of the form AxB (for 2D) or AxBxC (for 3D) where A, B and C are the patch radius in each dimension.',
                default = '7x7x1',
                type = str,
            ),
            dict(
                names = ['-nf', '--noise_factor'],
                help = 'Noise factor.',
                default = 1,
                type = float,
            ),
            dict(
                names = ['-nit', '--n_iterations'],
                help = 'Number of iterations.',
                default = 5,
                type = int,
            ),
            dict(
                names = ['-ts', '--time_series'],
                help = 'Consider the image as a sequence (for 3D only).',
                default = False,
                type = bool,
            ),
            dict(
                names = ['-nfr', '--n_frames'],
                help = 'Number of frames to process in a batch. Use 0 to process everything at once (for 4D only).',
                default = 0,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output_image'],
                help = 'The output image.',
                default = '{input_image.stem}_denoised{input_image.exts}',
                type = Path,
            ),
    ]
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        noise = Tool.noiseChoices.index(args.noise)
        print(f'[[1/1]] Run ND-Safir on image {args.input_image}')
        if args.type == '4D':
            ndsafir_series.ndsafir_series(args.input_image, args.output_image, noise, args.n_iterations, args.noise_factor, args.patch, args.n_frames)
        else:
            command = ['ndsafir', '-i', args.input_image, '-o', args.output_image, '-noise', noise, '-iter', args.n_iterations, '-nf', args.noise_factor, '-2dt', 1 if args.time_series and args.type != '2D' else 0, '-patch', args.patch]
            subprocess.run([str(c) for c in command], check=True)

