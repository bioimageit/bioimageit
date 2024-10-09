import subprocess
import argparse
import pandas
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|windows,linux', 'conda-forge::cudnn|windows,linux'], pip=['exodeepfinder'])
    environment = 'exodeepfinder'
    autoInputs = ['input']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Structure training dataset", description="Convert the default dataset structure to the training file structure.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input', help='Input dataset folder', type=Path, required=True)
        inputs_parser.add_argument('-s', '--split', help='Splits the dataset in two random sets for training and validation, with --split %% of the movies in the training set, and the rest in the validation set (creates train/ and valid/ folders). Does not split if 0.', default=70, type=float)
        inputs_parser.add_argument('-m', '--movie', help='Path to the movie (relative to the movie folder).', default='movie.h5', type=Path)
        inputs_parser.add_argument('-ms', '--merged_segmentation', help='Path to the merged segmentation (relative to the movie folder).', default='merged_segmentation.h5', type=Path)
        inputs_parser.add_argument('-ma', '--merged_annotation', help='Path to the merged annotation (relative to the movie folder).', default='merged_annotation.xml', type=Path)

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Output folder', type=Path, default='dataset/')
        return parser

    def processDataFrame(self, dataFrame):
        return pandas.DataFrame.from_records(dict(dataset='dataset'))

    def processData(self, args):
        print(f'Structure training dataset from {args.input} to {args.output}')
        args = ['edf_structure_training_dataset', '-i', args.input, '-s', args.split, '-m', args.movie, '-ms', args.merged_segmentation, '-ma', args.merged_annotation, '-o', args.output]
        subprocess.run([str(arg) for arg in args])

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
