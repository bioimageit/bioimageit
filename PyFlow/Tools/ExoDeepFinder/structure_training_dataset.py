import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):
    
    name = "Structure training dataset"
    description = "Convert the default dataset structure to the training file structure."
    inputs = [
            dict(
                names = ['-mf', '--movies_folder'],
                help = 'Input movies folder',
                default = '[workflow_folder]/dataset',
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['-s', '--split'],
                help = 'Splits the dataset in two random sets for training and validation, with --split %% of the movies in the training set, and the rest in the validation set (creates train/ and valid/ folders). Does not split if 0.',
                default = 70,
                type = float,
            ),
            dict(
                names = ['-m', '--movie'],
                help = 'Path to the movie (relative to the movie folder).',
                default = 'movie.h5',
                type = Path,
            ),
            dict(
                names = ['-ms', '--merged_segmentation'],
                help = 'Path to the merged segmentation (relative to the movie folder).',
                default = 'merged_segmentation.h5',
                type = Path,
            ),
            dict(
                names = ['-ma', '--merged_annotation'],
                help = 'Path to the merged annotation (relative to the movie folder).',
                default = 'merged_annotation.xml',
                type = Path,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output'],
                help = 'Output folder',
                default = '[workflow_folder]/train_valid',
                type = Path,
            ),
    ]
    
    def processAllData(self, argsList):
        args = argsList[0]
        inputDatasetPath = Path(args.movies_folder)
        output = args.output
        print(f'Structure training dataset from {inputDatasetPath} to {output}')
        commandArgs = ['edf_structure_training_dataset', '-i', inputDatasetPath, '-s', args.split, '-m', args.movie, '-ms', args.merged_segmentation, '-ma', args.merged_annotation, '-o', output]
        return subprocess.run([str(arg) for arg in commandArgs])

    def processData(self, args):
        return

