import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['bioimageit::atlas'], pip=['scikit-learn==1.3.2', 'scikit-image==0.22.0', 'h5py==3.11.0', 'mrcfile==1.4.3', 'matplotlib==3.8.1', 'pillow==10.3.0'], pip_no_deps=['exodeepfinder'])
    environment = 'exodeepfinder-atlas'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Detect spots", description="Generate annotations from a segmentation.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-mf', '--movie_folder', help='Input folder containing the movie files (a least a tiff folder containing the movie frames).', required=True, type=Path)
        inputs_parser.add_argument('-t', '--tiff', help='Path to the folder containing the tiff frames, relative to --movie_folder.', default='tiff/', type=Path)
        inputs_parser.add_argument('-aa', '--atlas_args', help='Additional atlas arguments.', default='-rad 21 -pval 0.001 -arealim 3', type=str)
        
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Output segmentation.', default='{movie_folder.name}/detector_segmentation.h5', type=Path)
        return parser, dict( movie_folder = dict(autoColumn=True), output=dict(autoIncrement=False) )

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print(f'Detect spots in {args.movie_folder / args.tiff}')
        args = ['edf_detect_spots_with_atlas', '-m', args.movie_folder / args.tiff, '-o', args.output, '-aa', args.atlas_args]
        completedProcess = subprocess.run([str(arg) for arg in args])
        if completedProcess.returncode != 0: return completedProcess
        for file in sorted(list(args.movie_folder.iterdir())):
            if not (args.output.parent / file.name).exists():
                (args.output.parent / file.name).symlink_to(file)
        return completedProcess

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
