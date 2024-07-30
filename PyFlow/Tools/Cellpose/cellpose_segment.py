import sys
from importlib import import_module
import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Segmentation']
    dependencies = dict(conda=[], pip=['cellpose==3.0.10', 'pandas==2.2.2'])
    environment = 'cellpose'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Cellpose", description="Segment cells with cellpose.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-m', '--model_name', help='The model to use.', default='cyto', type=str)
        inputs_parser.add_argument('-g', '--use_gpu', help='Use GPU (default is CPU).', action='store_true')
        inputs_parser.add_argument('-a', '--auto_diameter', help='Automatically estimate cell diameters, see https://cellpose.readthedocs.io/en/latest/settings.html.', action='store_true')
        inputs_parser.add_argument('-d', '--diameter', help='Estimate of the cell diameters (in pixels).', default=30, type=int)
        inputs_parser.add_argument('-c', '--channels', help='Channels to run segementation on. For example: "[0,0]" for grayscale, "[2,3]" for G=cytoplasm and B=nucleus, "[2,1]" for G=cytoplasm and R=nucleus.', default='[0,0]', type=str)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--out', help='The output mask path.', default='{input_image}_segmentation.tif', type=Path)
        outputs_parser.add_argument('-n', '--npy', help='The output segmentation path.', default='{input_image}_segmentation.npy', type=Path)
        return parser

    def initialize(self, args):
        print('Loading libraries...')
        # self.models = import_module('cellpose.models')
        # self.io: cellpose.io = import_module('cellpose.io')
        import cellpose.models
        import cellpose.io
        self.models = cellpose.models
        self.io = cellpose.io
        self.model = self.models.Cellpose(gpu=True if args.use_gpu == 'True' else False, model_type=args.model_name)
    
    def processDataFrame(self, dataFrame):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/4]] Load image {input_image}')
        channels = json.loads(args.channels)
        image = self.io.imread(input_image)
        auto_diameter = args.auto_diameter if type(args.auto_diameter) is bool else args.auto_diameter == 'True'

        print('[[2/4]] Compute segmentation', image.shape)
        masks, flows, styles, diams = self.model.eval(image, diameter=None if auto_diameter else int(args.diameter), channels=channels)
        
        input_image = Path(input_image)

        if args.npy:
            print(f'[[3/4]] Save segmentation {args.npy}')
            # save results so you can load in gui
            self.io.masks_flows_to_seg(image, masks, flows, input_image, diams, channels)
            (input_image.parent / f'{input_image.stem}_seg.npy').rename(args.npy)
            print(f'Saved npy: {args.npy}')

        if args.out:
            print(f'[[4/4]] Save segmentation {args.out}')
            # save results as tif
            self.io.save_masks(image, masks, flows, input_image, tif=True)
            import time
            time.sleep(1)
            print('ok')
            output_mask = input_image.parent / f'{input_image.stem}_cp_masks.tif'
            if output_mask.exists():
                (output_mask).rename(args.out)
                print(f'Saved out: {args.out}')
            else:
                print('Segmentation was not generated because no masks were found.')

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)