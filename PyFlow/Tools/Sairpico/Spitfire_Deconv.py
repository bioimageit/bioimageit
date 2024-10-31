import argparse
from pathlib import Path

class Tool:

    categories = ['Sairpico', 'Deconvolution']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2'], pip=[])
    environment = 'simglib'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("SPITFIR(e)", description="SPITFIR(e) deconvolution.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument("--input", type=Path, help="Input Image", required=True)
        inputs_parser.add_argument("--type", choices=['2D', '2D Slice', '3D'], help="Perform 2D, 2D Slice or 3D deconvolution.", default='2D', type=str)
        inputs_parser.add_argument("--sigma", type=float, help="Gaussian PSF width (for 2D and 2D Slice only)", default=1.5)
        inputs_parser.add_argument("--psf", type=Path, help="PSF Image (for 3D only)")
        inputs_parser.add_argument("--regularization", type=float, help="Regularization parameter pow(2,-x)", default=12)
        inputs_parser.add_argument("--weighting", type=float, help="Weighting", default=0.6)
        inputs_parser.add_argument("--method", choices=['HV', 'SV'], default='HV', help="Method for regularization")
        inputs_parser.add_argument("--padding", action='store_true', help="Add padding to process border pixels")

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument("-o", "--output", help="Output path for the deconvolved image.", default="{input.name}_deconvolved.{input.exts}", type=Path)
        return parser, dict(input=dict(autoColumn=True))

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

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

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)
