import subprocess

class Tool:

    categories = ['Localization']
    dependencies = dict(python='3.9', conda=['bioimageit::matirf|osx-64,win-64,linux-64'], pip=[])
    environment = 'docker'
    
    name = "MATIRF Localize"
    description = "3D multi-angle TIRF image localizations."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Path to the input image.',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'microscope_params',
                help = 'Microscope parameters (json format)',
                required = True,
                type = 'Path',
            ),
            dict(
                name = 'depth',
                help = 'Depth',
                default = 500,
                type = 'float',
            ),
            dict(
                name = 'nplanes',
                help = 'Number of planes',
                default = 20,
                type = 'int',
            ),
            dict(
                name = 'lambda',
                help = 'Regularization (XY,Z)',
                default = '0.001,0.001',
                type = 'str',
            ),
            dict(
                name = 'gamma',
                help = 'Gamma / time step',
                default = 10,
                type = 'float',
            ),
            dict(
                name = 'iterations',
                help = 'Number of iterations',
                default = 1000,
                type = 'int',
            ),
            dict(
                name = 'reg_type',
                help = 'Regularization type',
                default = 1,
                type = 'int',
            ),
            dict(
                name = 'zmin',
                help = 'Z0',
                default = 0,
                type = 'int',
            ),
            dict(
                name = 'mode',
                help = 'Mode (0:batch, 1:visu)',
                default = 0,
                type = 'int',
            ),
            dict(
                name = 'object_size_nm',
                help = 'Objects size in nm',
                default = 300,
                type = 'int',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'Output path for the denoised image.',
                default = '{input_image.name}_localized{input_image.exts}',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        print('Performing MATIRF localization')
        commandArgs = [
            'matirf', 'localize', '-i', args.input_image, '-p', args.microscope_params, '-o', args.output,
            '-d', args.depth, '-n', args.nplanes, '-lambda', getattr(args, 'lambda'), '-gamma', args.gamma,
            '-iter', args.iterations, '-reg', args.reg_type, '-zmin', args.zmin, '-mode', args.mode, '-s', args.object_size_nm
        ]

        subprocess.run([str(ca) for ca in commandArgs], check=True)

