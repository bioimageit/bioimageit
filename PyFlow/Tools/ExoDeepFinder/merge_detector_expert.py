import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):
    
    name = "Merge detector and expert data"
    description = "Merge detector detections with expert annotations."
    inputs = [
            dict(
                name = 'movie_folder',
                shortname = 'mf',
                help = 'Movie folder.',
                required = True,
                type = 'Path',
                autoColumn = True,
                autoIncrement = False,
            ),
            dict(
                name = 'detector_segmentation',
                shortname = 'ds',
                help = 'Detector segmentation (in .h5 format).',
                default = 'detector_segmentation.h5',
                type = 'Path',
            ),
            dict(
                name = 'expert_segmentation',
                shortname = 'es',
                help = 'Expert segmentation (in .h5 format).',
                default = 'expert_segmentation.h5',
                type = 'Path',
            ),
            dict(
                name = 'expert_annotation',
                shortname = 'ea',
                help = 'Expert annotation (in .xml format).',
                default = 'expert_annotation.xml',
                type = 'Path',
            ),
    ]
    outputs = [
            dict(
                name = 'merged_segmentation',
                shortname = 'ms',
                help = 'Output merged segmentation (in .h5 format).',
                default = '[workflow_folder]/dataset/{movie_folder.name}/merged_segmentation.h5',
                type = 'Path',
                autoIncrement = False,
            ),
            dict(
                name = 'merged_annotation',
                shortname = 'ma',
                help = 'Output merged annotation (in .xml format).',
                default = '[workflow_folder]/dataset/{movie_folder.name}/merged_annotation.xml',
                type = 'Path',
                autoIncrement = False,
            ),
    ]

    def processDataFrame(self, dataFrame, argsList):
        self.outputMessage = 'Output table will be computed on execution.'
        return dataFrame

    def processData(self, args):
        print(f'Merge detector and expert data from {args.detector_segmentation}, {args.expert_segmentation} and {args.expert_annotation}')
        # expert_annotation = Path(args.expert_segmentation).parent / args.expert_annotation if not Path(args.expert_annotation).is_absolute() else args.expert_annotation
        commandArgs = ['edf_merge_detector_expert', '-ds', args.movie_folder / args.detector_segmentation, '-es', args.movie_folder / args.expert_segmentation, '-ea', args.movie_folder / args.expert_annotation, '-ms', args.merged_segmentation, '-ma', args.merged_annotation]
        subprocess.run([str(arg) for arg in commandArgs], check=True)
