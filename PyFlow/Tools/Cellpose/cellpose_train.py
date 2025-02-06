import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Segmentation']
    dependencies = dict(conda=[], pip=['cellpose==3.1.0', 'pandas==2.2.2'])
    environment = 'cellpose'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Cellpose", description="Segment cells with cellpose.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-tr', '--train_directory', help='The directory path containing the training data.', required=True, type=Path)
        inputs_parser.add_argument('-te', '--test_directory', help='The directory path containing the testing data.', default=None, type=Path)
        inputs_parser.add_argument('-if', '--image_filter', help='The filter for selecting image files.', default='_img', type=str)
        inputs_parser.add_argument('-mf', '--mask_filter', help='The filter for selecting mask files.', default=None, type=str)
        inputs_parser.add_argument('-lold', '--look_one_level_down', help='Whether to look for data in subdirectories of train_dir and test_dir.', action='store_true')

        inputs_parser.add_argument('-m', '--model_type', help='Model type. Full built-in models: "cyto”=cytoplasm model; "nuclei”=nucleus model; "cyto2”=cytoplasm model with additional user images; "cyto3”=super-generalist model. For other built-in models, see https://cellpose.readthedocs.io/en/latest/models.html', default='cyto3', choices=['cyto', 'cyto2', 'cyto3', 'nuclei', 'tissuenet_cp3', 'tissuenet_cp3', 'livecell_cp3', 'yeast_PhC_cp3', 'yeast_BF_cp3', 'bact_phase_cp3', 'bact_fluor_cp3', 'deepbacs_cp3', 'cyto2_cp3', 'CP', 'CPx', 'TN1', 'TN2', 'TN3', 'LC1', 'LC2', 'LC3', 'LC4'], type=str)
        inputs_parser.add_argument('-c', '--channels', help='Channels to run segementation on. For example: "[0,0]" for grayscale, "[2,3]" for G=cytoplasm and B=nucleus, "[2,1]" for G=cytoplasm and R=nucleus.', default='[0,0]', type=str)
        inputs_parser.add_argument('-g', '--use_gpu', help='Use GPU (default is CPU).', action='store_true')

        inputs_parser.add_argument('-sn', '--skip_normalizaton', help='Whether to sktip the data normalization.', action='store_false')
        inputs_parser.add_argument('-wd', '--weight_decay', help='Weight decay for the optimizer.', default=1e-5, type=float)
        inputs_parser.add_argument('-sdg', '--SDG', help='Whether to use SGD as optimization instead of RAdam.', action='store_true')
        inputs_parser.add_argument('-lr', '--learning_rate', help='Learning rate for the training.', default=0.005, type=float)
        inputs_parser.add_argument('-ne', '--n_epochs', help='Number of times to go through the whole training set during training.', default=2000, type=int)
        inputs_parser.add_argument('-mn', '--model_name', help='Name of the new network.', default=None, type=str)

        inputs_parser.add_argument('-e', '--evaluate', help='Whether to evaluate the model after training.', action='store_true')

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--out', help='The output path.', default='[node_folder]/model/', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )

    def initialize(self, args):
        print('Loading libraries...')
        import cellpose
        self.cellpose = cellpose
    
    def processData(self, args):
        if not args.train_directory.exists():
            raise Exception(f'Error: train directory {args.train_directory} does not exist.')

        print(f'[[1/4]] Load data {args.train_directory}')

        self.cellpose.io.logger_setup()

        output = self.cellpose.io.load_train_test_data(str(args.train_directory), str(args.test_directory), image_filter=args.image_filter,
                                        mask_filter=args.mask_filter, look_one_level_down=args.look_one_level_down)
        images, labels, image_names, test_images, test_labels, image_names_test = output

        print(f'[[2/4]] Load model {args.model_type}')

        # e.g. retrain a Cellpose model
        model = self.cellpose.models.CellposeModel(model_type=args.model_type)

        channels = json.loads(args.channels)

        print(f'[[3/4]] Train model {args.model_name}')

        model_path, train_losses, test_losses = self.cellpose.train.train_seg(model.net,
                                    train_data=images, train_labels=labels,
                                    channels=channels, normalize=not args.skip_normalization,
                                    test_data=test_images, test_labels=test_labels,
                                    weight_decay=args.weight_decay, SGD=args.SDG, learning_rate=args.learning_rate,
                                    n_epochs=args.n_epochs, model_name=args.model_name)

        # diameter of labels in training images
        diam_labels = model.diam_labels.copy()

        if args.evaluate == 'Yes':

            print(f'[[4/4]] Evaluate model {args.model_name}')

            # get files (during training, test_data is transformed so we will load it again)
            output = self.cellpose.io.load_train_test_data(str(args.test_directory), mask_filter='_seg.npy')
            test_data, test_labels = output[:2]

            # run model on test images
            masks = model.eval(test_data, channels=channels, diameter=diam_labels)[0]

            # check performance using ground truth labels
            ap = self.cellpose.metrics.average_precision(test_labels, masks)[0]

            print(f'>>> average precision at iou threshold 0.5 = {ap[:,0].mean():.3f}')
        else:
            print(f'[[4/4]] Skip model evaluation')


if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)