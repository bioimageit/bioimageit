import subprocess
import argparse
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Structure training dataset", description="Convert the default dataset structure to the training file structure.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-mf', '--movies_folder', help='Input movies folder', type=Path, default='[workflow_folder]/dataset')
        inputs_parser.add_argument('-s', '--split', help='Splits the dataset in two random sets for training and validation, with --split %% of the movies in the training set, and the rest in the validation set (creates train/ and valid/ folders). Does not split if 0.', default=70, type=float)
        inputs_parser.add_argument('-m', '--movie', help='Path to the movie (relative to the movie folder).', default='movie.h5', type=Path)
        inputs_parser.add_argument('-ms', '--merged_segmentation', help='Path to the merged segmentation (relative to the movie folder).', default='merged_segmentation.h5', type=Path)
        inputs_parser.add_argument('-ma', '--merged_annotation', help='Path to the merged annotation (relative to the movie folder).', default='merged_annotation.xml', type=Path)

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Output folder', type=Path, default='[workflow_folder]/train_valid')
        return parser, dict( movies_folder = dict(autoColumn=True) )
    def processAllData(self, argsList):
        args = argsList[0]
        inputDatasetPath = Path(args.movies_folder)
        output = args.output
        print(f'Structure training dataset from {inputDatasetPath} to {output}')
        commandArgs = ['edf_structure_training_dataset', '-i', inputDatasetPath, '-s', args.split, '-m', args.movie, '-ms', args.merged_segmentation, '-ma', args.merged_annotation, '-o', output]
        return subprocess.run([str(arg) for arg in commandArgs])

    def processData(self, args):
        return

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
