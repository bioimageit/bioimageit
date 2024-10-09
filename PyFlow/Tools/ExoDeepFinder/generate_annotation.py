import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|windows,linux', 'conda-forge::cudnn|windows,linux'], pip=['exodeepfinder'])
    environment = 'exodeepfinder'
    autoInputs = ['segmentation']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Generate annotations", description="Generate annotations from a segmentation.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-s', '--segmentation', help='Input segmentation (in .h5 format).', type=Path)
        inputs_parser.add_argument('-cr', '--cluster_radius', help='Approximate size in voxel of the objects to cluster. 5 is a good value for events of 400nm on films with a pixel size of 160nm.', default=5, type=int)
        inputs_parser.add_argument('-klu', '--keep_labels_unchanged', help='By default, bright spots are removed (labels 1 are set to 0) and exocytose events (labels 2) are set to 1. This option skip this step, so labels are kept unchanged.', action='store_true')
        
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-a', '--annotation', help='Output annotation file (in .xml format).', default='annotation.xml', type=Path)
        return parser

    def processDataFrame(self, dataFrame):
        return dataFrame

    def processData(self, args):
        print(f'Annotate {args.segmentation}')
        klu = ['-klu'] if args.keep_labels_unchanged else []
        args = ['edf_generate_annotation', '-s', args.segmentation, '-cr', args.cluster_radius, '-a', args.annotation] + klu
        subprocess.run([str(arg) for arg in args])

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
