import argparse
from pathlib import Path

class Tool:

    categories = ['Deconvolution']
    dependencies = dict(python='3.9', conda=['bioimageit::matirf|osx-64,win-64,linux-64'], pip=[])
    environment = 'matirf'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("MATIRF", description="3D multi-angle TIRF image deconvolution.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument("--input_image", type=Path, help="Path to the input image, or input text file for image sequence.", required=True)

        inputs_parser.add_argument("--microscope_params", type=Path, help="Microscope parameters (json format)", required=True)
        inputs_parser.add_argument("--depth", type=float, help="Depth", default=500)
        inputs_parser.add_argument("--nplanes", type=int, help="Number of planes", default=20)
        inputs_parser.add_argument("--lambda", type=str, help="Regularization (XY,Z)", default="0.001,0.001")
        inputs_parser.add_argument("--gamma", type=float, help="Gamma / time step", default=10)
        inputs_parser.add_argument("--iterations", type=int, help="Number of iterations", default=1000)
        inputs_parser.add_argument("--reg_type", type=int, help="Regularization type", default=1)
        inputs_parser.add_argument("--zmin", type=int, help="Z0", default=0)
        
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument("-o", "--output", help="Output path for the denoised image.", default="{input_image.name}_denoised{input_image.exts}", type=Path)
        return parser, dict(input_image=dict(autoColumn=True))
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

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)