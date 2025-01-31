from pathlib import Path

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "SPITFIR(e)"
    description = "SPITFIR(e) deconvolution."
    inputs = [
            dict(
                names = ['--input'],
                help = 'Input Image',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['--type'],
                help = 'Perform 2D, 2D Slice or 3D deconvolution.',
                default = '2D',
                choices = ['2D', '2D Slice', '3D'],
                type = str,
            ),
            dict(
                names = ['--sigma'],
                help = 'Gaussian PSF width (for 2D and 2D Slice only)',
                default = 1.5,
                type = float,
            ),
            dict(
                names = ['--psf'],
                help = 'PSF Image (for 3D only)',
                default = None,
                type = Path,
            ),
            dict(
                names = ['--regularization'],
                help = 'Regularization parameter pow(2,-x)',
                default = 12,
                type = float,
            ),
            dict(
                names = ['--weighting'],
                help = 'Weighting',
                default = 0.6,
                type = float,
            ),
            dict(
                names = ['--method'],
                help = 'Method for regularization',
                default = 'HV',
                choices = ['HV', 'SV'],
            ),
            dict(
                names = ['--padding'],
                help = 'Add padding to process border pixels',
                default = False,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output'],
                help = 'Output path for the deconvolved image.',
                default = '{input.name}_deconvolved{input.exts}',
                type = Path,
            ),
    ]
    
    def processData(self, args):
        print('Performing SPITFIR(e) 2D deconvolution')
        import subprocess
        commandArgs = [
            'simgspitfiredeconv' + args.type.replace(' ', '').lower(), '-i', args.input, '-o', args.output,
            '-regularization', args.regularization,
            '-weighting', args.weighting, '-method', args.method, '-padding', 'true' if args.padding else 'false', '-niter', '200'
        ]
        if  args.type != '3D':
            commandArgs += ['-sigma', args.sigma]
        else:
            commandArgs += ['-psf', args.psf]
        return subprocess.run([str(ca) for ca in commandArgs])

