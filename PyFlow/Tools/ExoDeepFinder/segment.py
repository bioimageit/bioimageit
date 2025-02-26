import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):
    
    name = "Segment"
    description = "Segment exocytosis events."
    inputs = [
            dict(
                name = 'movie',
                shortname = 'm',
                help = 'Exocytosis movie (in .h5 format).',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'model_weights',
                shortname = 'mw',
                help = 'Model weigths (in .h5 format).',
                default = None,
                type = 'Path',
            ),
            dict(
                name = 'patch_size',
                shortname = 'ps',
                help = 'Patch size (the movie is split in cubes of --patch_size before being processed). Must be a multiple of 4.',
                default = 160,
                type = 'int',
            ),
            dict(
                name = 'visualization',
                shortname = 'v',
                help = 'Generate visualization images.',
                default = False,
                type = 'bool',
            ),
    ]
    outputs = [
            dict(
                name = 'segmentation',
                shortname = 's',
                help = 'Output segmentation (in .h5 format).',
                default = '[workflow_folder]/dataset/{movie.parent.name}/segmentation.h5',
                type = 'Path',
            ),
    ]
    def processData(self, args):
        print(f'Segment {args.movie}')
        vizualisation = ['-v'] if args.visualization else []
        model_weights = ['-mw', args.model_weights] if args.model_weights is not None else []
        commandArgs = ['edf_segment', '-m', args.movie, '-ps', args.patch_size, '-s', args.segmentation] + model_weights + vizualisation
        subprocess.run([str(arg) for arg in commandArgs], check=True)