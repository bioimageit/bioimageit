import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):
    
    name = "Structure training dataset"
    description = "Convert the default dataset structure to the training file structure."
    inputs = [
            dict(
                name = 'movies_folder',
                shortname = 'mf',
                help = 'Input movies folder',
                default = '[workflow_folder]/dataset',
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'split',
                shortname = 's',
                help = 'Splits the dataset in two random sets for training and validation, with --split %% of the movies in the training set, and the rest in the validation set (creates train/ and valid/ folders). Does not split if 0.',
                default = 70,
                type = 'float',
            ),
            dict(
                name = 'movie',
                shortname = 'm',
                help = 'Path to the movie (relative to the movie folder).',
                default = 'movie.h5',
                type = 'Path',
            ),
            dict(
                name = 'merged_segmentation',
                shortname = 'ms',
                help = 'Path to the merged segmentation (relative to the movie folder).',
                default = 'merged_segmentation.h5',
                type = 'Path',
            ),
            dict(
                name = 'merged_annotation',
                shortname = 'ma',
                help = 'Path to the merged annotation (relative to the movie folder).',
                default = 'merged_annotation.xml',
                type = 'Path',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'Output folder',
                default = '[workflow_folder]/train_valid',
                type = 'Path',
            ),
    ]
    
    def processAllData(self, argsList):
        args = argsList[0]
        inputDatasetPath = Path(args.movies_folder)
        output = args.output
        if output.is_dir() and len(list(output.iterdir()))>0:
            raise Exception(f'The output folder "{output}" is not empty. Please empty it before structuring the training dataset.')
        print(f'Structure training dataset from "{inputDatasetPath}" to "{output}"')
        commandArgs = ['edf_structure_training_dataset', '-i', inputDatasetPath, '-s', args.split, '-m', args.movie, '-ms', args.merged_segmentation, '-ma', args.merged_annotation, '-o', output]
        subprocess.run([str(arg) for arg in commandArgs], check=True)

    def processData(self, args):
        return

