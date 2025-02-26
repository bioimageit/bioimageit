import subprocess

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "Richardson-Lucy"
    description = "Richardson-Lucy deconvolution."
    inputs = [
            dict(
                name = 'input',
                shortname = 'i',
                help = 'Input image (x and y axis should ideally be even numbers)',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'type',
                help = 'Perform 2D, 2D Slice or 3D deconvolution.',
                default = '2D',
                choices = ['2D', '2D Slice', '3D'],
                type = 'str',
            ),
            dict(
                name = 'sigma',
                help = 'Gaussian PSF width (for 2D and 2D Slice only)',
                default = 1.5,
                type = 'float',
            ),
            dict(
                name = 'psf',
                help = 'PSF Image (for 3D only)',
                default = None,
                type = 'Path',
            ),
            dict(
                name = 'niter',
                help = 'Number of iterations',
                default = 15,
                type = 'int',
            ),
            dict(
                name = 'lambda',
                help = 'Regularization parameter (unused in 3D)',
                default = 0,
                type = 'float',
            ),
            dict(
                name = 'padding',
                help = 'Add padding to process border pixels',
                default = False,
                type = 'bool',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'Output path for the deconvolved image.',
                default = '{input.name}_deconvolved{input.exts}',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        print('Performing Richardson-Lucy deconvolution')

        if args.type == '3D' and (args.psf is None or not args.psf.exists()):
            raise Exception(f'Error: the argument psf must point to an existing PSF image file, it is set to "{args.psf}" which does not exist.')

        commandArgs = [
            'simgrichardsonlucy' + args.type.replace(' ', '').lower(),
            '-i', args.input,
            '-o', args.output,
            '-niter', args.niter,
            '-padding', 'true' if args.padding else 'false'
        ]
        if  args.type != '3D':
            commandArgs += ['-sigma', args.sigma, '-lambda', getattr(args, 'lambda')]
        else:
            commandArgs += ['-psf', args.psf]
        return subprocess.run([str(ca) for ca in commandArgs], check=True)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)
