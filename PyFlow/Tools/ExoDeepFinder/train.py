import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):

    
    name = "Train ExoDeepFinder"
    description = "Train a model from the given dataset."
    inputs = [
            dict(
                name = 'dataset',
                shortname = 'd',
                help = 'Input dataset',
                default = '[workflow_folder]/train_valid',
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'patch_sizes',
                shortname = 'ps',
                help = 'Patch sizes. Can be an integer or a list of the form [patchSizeModel1, patchSizeModel2, ...]. A list enables to train multiple models, each using the previous weights as initialization. For example, with --patch_sizes "[8, 16]": Model1 will use patches of size 8 voxels and Model2 will use patches of 16 voxels and initialize with the Model1 weights. The longest list of the parameters --patch_sizes, --batch_sizes, --random_shifts, --n_epochs and --n_steps will be use to determine the number of trainings ; and shorter lists will be extended with duplicates of their last values (integer parameters are similarly duplicated) to match the number of trainings.',
                default = '[8, 16, 32, 48]',
                type = 'str',
            ),
            dict(
                name = 'batch_sizes',
                shortname = 'bs',
                help = 'Batch sizes. Can be an integer or a list of the form [batchSizeModel1, batchSizeModel2, ...].',
                default = '[256, 128, 32, 10]',
                type = 'str',
            ),
            dict(
                name = 'random_shifts',
                shortname = 'rs',
                help = 'Random shifts. Can be an integer or a list of the form [randomShiftsModel1, randomShiftsModel2, ...].',
                default = '[4, 8, 16, 32]',
                type = 'str',
            ),
            dict(
                name = 'n_epochs',
                shortname = 'ne',
                help = 'Number of epochs. Can be an integer or a list of the form [nEpochsModel1, nEpochsModel2, ...].',
                default = '100',
                type = 'str',
            ),
            dict(
                name = 'n_steps',
                shortname = 'ns',
                help = 'Number of steps per epochs. Can be an integer or a list of the form [nStepsModel1, nStepsModel2, ...].',
                default = '100',
                type = 'str',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'Output folder where the model will be stored',
                default = '[workflow_folder]/model/model',
                type = 'Path',
            ),
    ]
    def processAllData(self, argsList):
        args = argsList[0]
        outputDataset = args.dataset
        output = args.output
        output.parent.mkdir(exist_ok=True, parents=True)
        print(f'Train ExoDeepFinder from dataset {outputDataset}')
        commandArgs = ['edf_train', '-d', outputDataset, '-ps', args.patch_sizes, '-bs', args.batch_sizes, '-rs', args.random_shifts, '-ne', args.n_epochs, '-ns', args.n_steps, '-o', output]
        subprocess.run([str(arg) for arg in commandArgs], check=True)

    def processData(self, args):
        return
    
