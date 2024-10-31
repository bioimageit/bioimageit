import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|win-64,linux-64', 'conda-forge::cudnn|win-64,linux-64'], pip=['exodeepfinder==0.3.13'])
    environment = 'exodeepfinder'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Segment", description="Segment exocytosis events.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-m', '--movie', help='Exocytosis movie (in .h5 format).', required=True, type=Path)
        inputs_parser.add_argument('-mw', '--model_weights', help='Model weigths (in .h5 format).', default=None, type=Path)
        inputs_parser.add_argument('-ps', '--patch_size', help='Patch size (the movie is split in cubes of --patch_size before being processed). Must be a multiple of 4.', default=160, type=int)
        inputs_parser.add_argument('-v', '--visualization', help='Generate visualization images.', action='store_true')

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-s', '--segmentation', help='Output segmentation (in .h5 format).', default='[workflow_folder]/dataset/{movie.parent.name}/segmentation.h5', type=Path)
        return parser, dict( movie = dict(autoColumn=True) )

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print(f'Segment {args.movie}')
        vizualisation = ['-v'] if args.visualization else []
        model_weights = ['-mw', args.model_weights] if args.model_weights is not None else []
        commandArgs = ['edf_segment', '-m', args.movie, '-ps', args.patch_size, '-s', args.segmentation] + model_weights + vizualisation
        return subprocess.run([str(arg) for arg in commandArgs])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
