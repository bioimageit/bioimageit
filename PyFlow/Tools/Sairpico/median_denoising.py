from pathlib import Path
import subprocess

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "Median"
    description = "Median filtering."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Input Image',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'type',
                help = 'Perform 2D, 3D or 3D + time denoising.',
                default = '2D',
                choices = ['2D', '3D', '4D'],
                type = 'str',
            ),
            dict(
                name = 'radius_x',
                help = 'Radius of the filter in the X direction',
                default = 2,
                type = 'int',
            ),
            dict(
                name = 'radius_y',
                help = 'Radius of the filter in the Y direction',
                default = 2,
                type = 'int',
            ),
            dict(
                name = 'radius_z',
                help = 'Radius of the filter in the Z direction (for 3D and 3D + time only)',
                default = 1,
                type = 'int',
            ),
            dict(
                name = 'radius_t',
                help = 'Radius of the filter in the time direction (for 3D + time only)',
                default = 1,
                type = 'int',
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
                help = 'Output path for the filtered image.',
                default = '{input.name}_filtered{input.exts}',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        print('Performing Median 4D filtering')

        command = 'simgmedian' + args.type.lower()
        commandArgs = [
            command, '-i', args.input_image, '-o', args.output,
            '-rx', args.radius_x, '-ry', args.radius_y,
            '-padding', 'true' if args.padding else 'false'
        ]
        if '3D' in args.type:
            commandArgs += ['-rz', args.radius_z]
        if args.type == '4D':
            commandArgs += ['-rt', args.radius_t]
        subprocess.run([str(ca) for ca in commandArgs], check=True)

