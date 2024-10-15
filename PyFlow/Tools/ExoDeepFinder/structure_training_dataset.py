import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|windows,linux', 'conda-forge::cudnn|windows,linux'], pip=['exodeepfinder'])
    environment = 'exodeepfinder'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Structure training dataset", description="Convert the default dataset structure to the training file structure.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-mf', '--movie_folder', help='Input movie folder', type=Path, required=True)
        inputs_parser.add_argument('-s', '--split', help='Splits the dataset in two random sets for training and validation, with --split %% of the movies in the training set, and the rest in the validation set (creates train/ and valid/ folders). Does not split if 0.', default=70, type=float)
        inputs_parser.add_argument('-m', '--movie', help='Path to the movie (relative to the movie folder).', default='movie.h5', type=Path)
        inputs_parser.add_argument('-ms', '--merged_segmentation', help='Path to the merged segmentation (relative to the movie folder).', default='merged_segmentation.h5', type=Path)
        inputs_parser.add_argument('-ma', '--merged_annotation', help='Path to the merged annotation (relative to the movie folder).', default='merged_annotation.xml', type=Path)

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Output folder', type=Path, default='dataset')
        return parser, dict( movie_folder = dict(autoColumn=True) )

    def processDataFrame(self, dataFrame, argsList):
        if len(argsList)==0: return dataFrame
        # return pandas.DataFrame.from_records([dict(input=Path(argsList[0].movie_folder).parent, output=Path(argsList[0].output))])
        output = Path(argsList[0].output).name
        dataFrame[dataFrame.columns[-1]] = output[:-2] if output.endswith('_0') else output
        # dataFrame.attrs = dict(groups=dict(output=[1] * len(dataFrame)))
        return dataFrame
    
    def processAllData(self, argsList):
        args = argsList[0]
        inputDatasetPath = Path(args.movie_folder).parent
        output = args.output
        print(f'Structure training dataset from {inputDatasetPath} to {output}')
        args = ['edf_structure_training_dataset', '-i', inputDatasetPath, '-s', args.split, '-m', args.movie, '-ms', args.merged_segmentation, '-ma', args.merged_annotation, '-o', output]
        return subprocess.run([str(arg) for arg in args])

    def processData(self, args):
        return

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
