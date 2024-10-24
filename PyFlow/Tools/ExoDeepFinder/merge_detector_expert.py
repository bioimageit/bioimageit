import subprocess
import argparse
from pathlib import Path
class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|windows,linux', 'conda-forge::cudnn|windows,linux'], pip=['exodeepfinder==0.3.13'])
    environment = 'exodeepfinder'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Merge detector and expert data", description="Merge detector detections with expert annotations.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument('-mf', '--movie_folder', help='Movie folder.', required=True, type=Path)
        inputs_parser.add_argument('-ds', '--detector_segmentation', help='Detector segmentation (in .h5 format).', default='detector_segmentation.h5', type=Path)
        inputs_parser.add_argument('-es', '--expert_segmentation', help='Expert segmentation (in .h5 format).', default='expert_segmentation.h5', type=Path)
        inputs_parser.add_argument('-ea', '--expert_annotation', help='Expert annotation (in .xml format).', default='expert_annotation.xml', type=Path)
        
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-ms', '--merged_segmentation', help='Output merged segmentation (in .h5 format).', default='[workflow_folder]/dataset/{movie_folder.name}/merged_segmentation.h5', type=Path)
        outputs_parser.add_argument('-ma', '--merged_annotation', help='Output merged annotation (in .xml format).', default='[workflow_folder]/dataset/{movie_folder.name}/merged_annotation.xml', type=Path)
        
        return parser, dict( merged_segmentation=dict(autoIncrement=False), merged_annotation=dict(autoIncrement=False), movie_folder=dict(autoColumn=True, autoIncrement=False) )

    def processDataFrame(self, dataFrame, argsList):
        return dict(outputMessage='Output table will be computed on execution.', dataFrame=dataFrame)

    def processData(self, args):
        print(f'Merge detector and expert data from {args.detector_segmentation}, {args.expert_segmentation} and {args.expert_annotation}')
        # expert_annotation = Path(args.expert_segmentation).parent / args.expert_annotation if not Path(args.expert_annotation).is_absolute() else args.expert_annotation
        commandArgs = ['edf_merge_detector_expert', '-ds', args.movie_folder / args.detector_segmentation, '-es', args.movie_folder / args.expert_segmentation, '-ea', args.movie_folder / args.expert_annotation, '-ms', args.merged_segmentation, '-ma', args.merged_annotation]
        completedProcess =  subprocess.run([str(arg) for arg in commandArgs])
        return completedProcess

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
