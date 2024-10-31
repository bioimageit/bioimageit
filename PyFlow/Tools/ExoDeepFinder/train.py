import subprocess
import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['nvidia/label/cuda-12.3.0::cuda-toolkit|win-64,linux-64', 'conda-forge::cudnn|win-64,linux-64'], pip=['exodeepfinder==0.3.13'])
    environment = 'exodeepfinder'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Train ExoDeepFinder", description="Train a model from the given dataset.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-d', '--dataset', help='Input dataset', default='[workflow_folder]/train_valid', type=Path)
        inputs_parser.add_argument('-ps', '--patch_sizes', help='Patch sizes. Can be an integer or a list of the form [patchSizeModel1, patchSizeModel2, ...]. A list enables to train multiple models, each using the previous weights as initialization. For example, with --patch_sizes "[8, 16]": Model1 will use patches of size 8 voxels and Model2 will use patches of 16 voxels and initialize with the Model1 weights. The longest list of the parameters --patch_sizes, --batch_sizes, --random_shifts, --n_epochs and --n_steps will be use to determine the number of trainings ; and shorter lists will be extended with duplicates of their last values (integer parameters are similarly duplicated) to match the number of trainings.', default='[8, 16, 32, 48]', type=str)
        inputs_parser.add_argument('-bs', '--batch_sizes', help='Batch sizes. Can be an integer or a list of the form [batchSizeModel1, batchSizeModel2, ...].', default='[256, 128, 32, 10]', type=str)
        inputs_parser.add_argument('-rs', '--random_shifts', help='Random shifts. Can be an integer or a list of the form [randomShiftsModel1, randomShiftsModel2, ...].', default='[4, 8, 16, 32]', type=str)
        inputs_parser.add_argument('-ne', '--n_epochs', help='Number of epochs. Can be an integer or a list of the form [nEpochsModel1, nEpochsModel2, ...].', default='100', type=str)
        inputs_parser.add_argument('-ns', '--n_steps', help='Number of steps per epochs. Can be an integer or a list of the form [nStepsModel1, nStepsModel2, ...].', default='100', type=str)

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Output folder where the model will be stored', default='[workflow_folder]/model', type=Path)
        return parser, dict( dataset = dict(autoColumn=True) )

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processAllData(self, argsList):
        print(argsList)
        args = argsList[0]
        outputDataset = args.dataset
        output = args.output
        print(f'Train ExoDeepFinder from dataset {outputDataset}')
        commandArgs = ['edf_train', '-d', outputDataset, '-ps', args.patch_sizes, '-bs', args.batch_sizes, '-rs', args.random_shifts, '-ne', args.n_epochs, '-ns', args.n_steps, '-o', output]
        return subprocess.run([str(arg) for arg in commandArgs])

    def processData(self, args):
        return
    
if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
