import argparse
from pathlib import Path

class Tool:

    categories = ['PSF']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("PSF", description="3D Gaussian PSF.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument("--width", type=int, help="Image width", default=256)
        inputs_parser.add_argument("--height", type=int, help="Image height", default=256)
        inputs_parser.add_argument("--depth", type=int, help="Image depth", default=20)

        inputs_parser.add_argument("--sigmaxy", type=float, help="PSF width and height", default=1.0)
        inputs_parser.add_argument("--sigmaz", type=float, help="PSF depth", default=1.0)

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='The output 3D Gaussian PSF path.', default='psf.tiff', type=Path)
        return parser, dict()
    
    def processData(self, args):
        print('Generate PSF')
        import subprocess
        commandArgs = ['simggaussian3dpsf', '-o', args.output, '-sigmaxy', args.sigmaxy, '-sigmaz', args.sigmaz, '-depth', args.depth, '-height', args.height, '-width', args.width]
        return subprocess.run([str(ca) for ca in commandArgs])
        

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)