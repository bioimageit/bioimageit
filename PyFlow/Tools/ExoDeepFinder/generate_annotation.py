import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):

    name = "Generate annotations"
    description = "Generate annotations from a segmentation."
    inputs = [
            dict(
                name = 'segmentation',
                shortname = 's',
                help = 'Input segmentation (in .h5 format).',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'cluster_radius',
                shortname = 'cr',
                help = 'Approximate size in voxel of the objects to cluster. 5 is a good value for events of 400nm on films with a pixel size of 160nm.',
                default = 5,
                type = 'int',
            ),
            dict(
                name = 'keep_labels_unchanged',
                shortname = 'klu',
                help = 'By default, bright spots are removed (labels 1 are set to 0) and exocytose events (labels 2) are set to 1. This option skip this step, so labels are kept unchanged.',
                default = False,
                type = 'bool',
            ),
    ]
    outputs = [
            dict(
                name = 'annotation',
                shortname = 'a',
                help = 'Output annotation file (in .xml format).',
                default = '[workflow_folder]/dataset/{segmentation.parent.name}/annotation.xml',
                type = 'Path',
            ),
    ]

    def processData(self, args):
        print(f'Annotate {args.segmentation}')
        klu = ['-klu'] if args.keep_labels_unchanged else []
        commandArgs = ['edf_generate_annotation', '-s', args.segmentation, '-cr', args.cluster_radius, '-a', args.annotation] + klu
        subprocess.run([str(arg) for arg in commandArgs], check=True)

