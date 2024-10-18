import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|windows,linux', 'conda-forge::cudnn|windows,linux'], pip=['exodeepfinder'])
    environment = 'exodeepfinder'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Generate segmentation", description="Generate segmentation from an annotation file.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-mf', '--movie_folder', help='Input folder containing the movie files (a least a movie in h5 format, and an expert annotation file).', required=True, type=Path)
        inputs_parser.add_argument('-m', '--movie', help='Input movie.', default='movie.h5', type=Path)
        inputs_parser.add_argument('-a', '--annotation', help='Corresponding annotation (.xml generated with napari-exodeepfinder or equivalent, can also be a .csv file).', default='expert_annotation.xml', type=Path)
        
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-oa', '--output_annotation', help='Output annotation (a symlink to the annotation input).', default='[workflow_folder]/dataset/{movie_folder.name}/expert_annotation.xml', type=Path)
        outputs_parser.add_argument('-os', '--output_segmentation', help='Output segmentation (in .h5 format).', default='[workflow_folder]/dataset/{movie_folder.name}/expert_segmentation.h5', type=Path)
        return parser, dict( movie_folder = dict(autoColumn=True), output_annotation=dict(autoIncrement=False) , output_segmentation=dict(autoIncrement=False) )

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print(f'Generate segmentation for {args.movie} with {args.annotation}')
        commandArgs = ['edf_generate_segmentation', '-m', args.movie_folder / args.movie, '-a', args.movie_folder / args.annotation, '-s', args.output_segmentation]
        completedProcess = subprocess.run([str(arg) for arg in commandArgs])
        return completedProcess

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
