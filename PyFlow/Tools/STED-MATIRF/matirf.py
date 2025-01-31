from pathlib import Path

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(python='3.9', conda=['bioimageit::matirf|osx-64,win-64,linux-64'], pip=[])
    environment = 'matirf'
    
    name = "MATIRF"
    description = "3D multi-angle TIRF image deconvolution."
    inputs = [
            dict(
                names = ['--input_image'],
                help = 'Path to the input image, or input text file for image sequence.',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['--microscope_params'],
                help = 'Microscope parameters (json format)',
                required = True,
                type = Path,
            ),
            dict(
                names = ['--depth'],
                help = 'Depth',
                default = 500,
                type = float,
            ),
            dict(
                names = ['--nplanes'],
                help = 'Number of planes',
                default = 20,
                type = int,
            ),
            dict(
                names = ['--lambda'],
                help = 'Regularization (XY,Z)',
                default = '0.001,0.001',
                type = str,
            ),
            dict(
                names = ['--gamma'],
                help = 'Gamma / time step',
                default = 10,
                type = float,
            ),
            dict(
                names = ['--iterations'],
                help = 'Number of iterations',
                default = 1000,
                type = int,
            ),
            dict(
                names = ['--reg_type'],
                help = 'Regularization type',
                default = 1,
                type = int,
            ),
            dict(
                names = ['--zmin'],
                help = 'Z0',
                default = 0,
                type = int,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output'],
                help = 'Output path for the denoised image.',
                default = '{input_image.name}_denoised{input_image.exts}',
                type = Path,
            ),
    ]
    
    def processData(self, args):
        print('Performing MATIRF deconvolution')
        import subprocess

        commandArgs = ['python', (Path(__file__).parent /'scripts' / 'matirf_sequence.py').resolve()] if args.input_image.suffix == '.txt' else ['matirf']
        commandArgs += [
            '-i', args.input_image, '-p', args.microscope_params, '-o', args.output,
            '-d', args.depth, '-n', args.nplanes, '-lambda', getattr(args, 'lambda'), '-gamma', args.gamma,
            '-iter', args.iterations, '-reg', args.reg_type, '-zmin', args.zmin
        ]
        return subprocess.run([str(ca) for ca in commandArgs])

