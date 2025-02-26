import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):
    
    name = "Generate segmentation"
    description = "Generate segmentation from an annotation file."
    inputs = [
            dict(
                name = 'movie_folder',
                shortname = 'mf',
                help = 'Input folder containing the movie files (a least a movie in h5 format, and an expert annotation file).',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'movie',
                shortname = 'm',
                help = 'Input movie.',
                default = 'movie.h5',
                type = 'Path',
            ),
            dict(
                name = 'annotation',
                shortname = 'a',
                help = 'Corresponding annotation (.xml generated with napari-exodeepfinder or equivalent, can also be a .csv file).',
                default = 'expert_annotation.xml',
                type = 'Path',
            ),
    ]
    outputs = [
            dict(
                name = 'output_annotation',
                shortname = 'oa',
                help = 'Output annotation (a symlink to the annotation input).',
                default = '[workflow_folder]/dataset/{movie_folder.name}/expert_annotation.xml',
                type = 'Path',
                autoIncrement = False,
            ),
            dict(
                name = 'output_segmentation',
                shortname = 'os',
                help = 'Output segmentation (in .h5 format).',
                default = '[workflow_folder]/dataset/{movie_folder.name}/expert_segmentation.h5',
                type = 'Path',
                autoIncrement = False,
            ),
    ]

    def processData(self, args):
        print(f'Generate segmentation for {args.movie} with {args.annotation}')
        commandArgs = ['edf_generate_segmentation', '-m', args.movie_folder / args.movie, '-a', args.movie_folder / args.annotation, '-s', args.output_segmentation]
        subprocess.run([str(arg) for arg in commandArgs], check=True)

