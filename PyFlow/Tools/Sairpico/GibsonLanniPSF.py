import argparse
from pathlib import Path

class Tool:

    categories = ['PSF']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("GibsonLanniPSF", description="3D Gibson-Lanni PSF.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument("--width", type=int, help="Image width", default=256)
        inputs_parser.add_argument("--height", type=int, help="Image height", default=256)
        inputs_parser.add_argument("--depth", type=int, help="Image depth", default=20)
        
        inputs_parser.add_argument("--wavelength", type=float, help="Excitation wavelength (nm)", default=610)
        inputs_parser.add_argument("--psxy", type=float, help="Pixel size in XY (nm)", default=100)
        inputs_parser.add_argument("--psz", type=float, help="Pixel size in Z (nm)", default=250)
        inputs_parser.add_argument("--na", type=float, help="Numerical Aperture", default=1.4)
        inputs_parser.add_argument("--ni", type=float, help="Refractive index immersion", default=1.5)
        inputs_parser.add_argument("--ns", type=float, help="Refractive index sample", default=1.3)
        inputs_parser.add_argument("--ti", type=float, help="Working distance (mum)", default=150)

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='The output Gibson-Lanni PSF image path.', default='psf_gibsonlanni.tiff', type=Path)
        return parser, dict()

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print('Generate Gibson-Lanni PSF')
        import subprocess
        commandArgs = [
            'simggibsonlannipsf',
            '-o', args.output,
            '-width', args.width,
            '-height', args.height,
            '-depth', args.depth,
            '-wavelength', args.wavelength,
            '-psxy', args.psxy,
            '-psz', args.psz,
            '-na', args.na,
            '-ni', args.ni,
            '-ns', args.ns,
            '-ti', args.ti
        ]
        
        return subprocess.run([str(ca) for ca in commandArgs])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
