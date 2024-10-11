import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|windows,linux', 'conda-forge::cudnn|windows,linux'], pip=['exodeepfinder'])
    environment = 'exodeepfinder'
    autoInputs = ['tiff']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Convert tiff to h5", description="Convert tiff frames to h5 movie.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-t', '--tiff', help='Path to the input movie folder. It must contain one tiff file per frame, their names must end with the frame number.', default=None, type=Path)
        # inputs_parser.add_argument('-ms', '--make_subfolder', help='Put all tiffs in a tiff/ subfolder in the --tiff input folder, and saves the output h5 file beside.', action='store_true')

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Output path to the h5 file.', default='{tiff.name}/movie.h5', type=Path)
        return parser

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print(f'Convert {args.tiff} to {args.output}')
        # Never use --make_subfolder in edf_convert_tiff_to_h5 since we do not want to modify the input folder
        subprocess.run(['edf_convert_tiff_to_h5', '-t', args.tiff, '-o', args.output])
        # Symlink the tiff folder
        tiffLink = (args.output.parent.resolve() / 'tiff')
        if tiffLink.exists():
            tiffLink.unlink()
        tiffLink.symlink_to(args.tiff, True)

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
