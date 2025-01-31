import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):
    
    name = "Generate segmentation"
    description = "Generate segmentation from an annotation file."
    inputs = [
            dict(
                names = ['-mf', '--movie_folder'],
                help = 'Input folder containing the movie files (a least a movie in h5 format, and an expert annotation file).',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['-m', '--movie'],
                help = 'Input movie.',
                default = 'movie.h5',
                type = Path,
            ),
            dict(
                names = ['-a', '--annotation'],
                help = 'Corresponding annotation (.xml generated with napari-exodeepfinder or equivalent, can also be a .csv file).',
                default = 'expert_annotation.xml',
                type = Path,
            ),
    ]
    outputs = [
            dict(
                names = ['-oa', '--output_annotation'],
                help = 'Output annotation (a symlink to the annotation input).',
                default = '[workflow_folder]/dataset/{movie_folder.name}/expert_annotation.xml',
                type = Path,
                autoIncrement = False,
            ),
            dict(
                names = ['-os', '--output_segmentation'],
                help = 'Output segmentation (in .h5 format).',
                default = '[workflow_folder]/dataset/{movie_folder.name}/expert_segmentation.h5',
                type = Path,
                autoIncrement = False,
            ),
    ]

    def processData(self, args):
        print(f'Generate segmentation for {args.movie} with {args.annotation}')
        commandArgs = ['edf_generate_segmentation', '-m', args.movie_folder / args.movie, '-a', args.movie_folder / args.annotation, '-s', args.output_segmentation]
        completedProcess = subprocess.run([str(arg) for arg in commandArgs])
        return completedProcess

