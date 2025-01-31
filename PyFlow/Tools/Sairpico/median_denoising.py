import argparse
from pathlib import Path

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Median", description="Median filtering.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument("--input_image", type=Path, help="Input Image", required=True)
        inputs_parser.add_argument("--type", choices=['2D', '3D', '4D'], help="Perform 2D, 3D or 3D + time denoising.", default='2D', type=str)
        inputs_parser.add_argument("--radius_x", type=int, help="Radius of the filter in the X direction", default=2)
        inputs_parser.add_argument("--radius_y", type=int, help="Radius of the filter in the Y direction", default=2)
        inputs_parser.add_argument("--radius_z", type=int, help="Radius of the filter in the Z direction (for 3D and 3D + time only)", default=1)
        inputs_parser.add_argument("--radius_t", type=int, help="Radius of the filter in the time direction (for 3D + time only)", default=1)
        inputs_parser.add_argument("--padding", action='store_true', help="Add padding to process border pixels")

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument("-o", "--output", help="Output path for the filtered image.", default="{input.name}_filtered{input.exts}", type=Path)
        return parser, dict(input_image=dict(autoColumn=True))
    def processData(self, args):
        print('Performing Median 4D filtering')
        import subprocess
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
        return subprocess.run([str(ca) for ca in commandArgs])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
