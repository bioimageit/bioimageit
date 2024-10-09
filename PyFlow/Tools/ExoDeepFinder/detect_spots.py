import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(conda=['bioimageit::atlas'], pip=['scikit-learn==1.3.2', 'scikit-image==0.22.0'], pip_no_deps=['exodeepfinder'])
    environment = 'exodeepfinder-atlas'
    autoInputs = ['movie']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Detect spots", description="Generate annotations from a segmentation.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-mf', '--movie_folder', help='Input folder containing the movie files (a least a tiff folder containing the movie frames).', required=True, type=Path)
        inputs_parser.add_argument('-t', '--tiff', help='Path to the folder containing the tiff frames, relative to --movie_folder.', default='tiff/', type=Path)
        inputs_parser.add_argument('-aa', '--atlas_args', help='Additional atlas arguments.', default='-rad 21 -pval 0.001 -arealim 3', type=str)
        
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Output segmentation.', default='{movie_folder.name}/detector_segmentation.h5', type=Path)
        return parser

    def processDataFrame(self, dataFrame):
        return dataFrame

    def processData(self, args):
        print(f'Detect spots in {args.movie}')
        args = ['edf_detect_spots_with_atlas', '-m', args.movie_folder / args.tiff, '-o', args.segmentation] + args.atlas_args.split(' ')
        subprocess.run([str(arg) for arg in args])

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
