import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Segmentation']
    dependencies = dict(conda=[], pip=['cellpose==3.1.0', 'pandas==2.2.2'])
    environment = 'cellpose'
    test = ['--input_image', 'img02.png', '--segmentation', 'img02_segmentation.png', '--visualization', 'img02_segmentation.npy']
    modelType = None

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Cellpose", description="Segment cells with cellpose.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-m', '--model_type', help='Model type. “cyto”=cytoplasm model; “nuclei”=nucleus model; “cyto2”=cytoplasm model with additional user images; “cyto3”=super-generalist model.', default='cyto', choices=['cyto', 'nuclei', 'cyto2', 'cyto3'], type=str)
        inputs_parser.add_argument('-g', '--use_gpu', help='Use GPU (default is CPU).', action='store_true')
        inputs_parser.add_argument('-a', '--auto_diameter', help='Automatically estimate cell diameters, see https://cellpose.readthedocs.io/en/latest/settings.html.', action='store_true')
        inputs_parser.add_argument('-d', '--diameter', help='Estimate of the cell diameters (in pixels).', default=30, type=int)
        inputs_parser.add_argument('-c', '--channels', help='Channels to run segementation on. For example: "[0,0]" for grayscale, "[2,3]" for G=cytoplasm and B=nucleus, "[2,1]" for G=cytoplasm and R=nucleus.', default='[0,0]', type=str)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-s', '--segmentation', help='The output segmentation path.', default='{input_image.stem}_segmentation.png', type=Path)
        outputs_parser.add_argument('-v', '--visualization', help='The output visualisation path.', default='{input_image.stem}_visualization.npy', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )

    def processData(self, args):

        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)
        
        print(f'[[1/5]] Load libraries and model {args.model_type}')
        print('Loading libraries...')
        import cellpose.models
        import cellpose.io

        if self.modelType != args.model_type:
            print('Loading model...')
            self.modelType = args.model_type
            self.model = cellpose.models.Cellpose(gpu=True if args.use_gpu == 'True' else False, model_type=self.modelType)

        print(f'[[2/5]] Load image {input_image}')
        channels = json.loads(args.channels)
        image = cellpose.io.imread(input_image)
        auto_diameter = args.auto_diameter if type(args.auto_diameter) is bool else args.auto_diameter == 'True'

        print('[[3/5]] Compute segmentation', image.shape)
        try:
            masks, flows, styles, diams = self.model.eval(image, diameter=None if auto_diameter else int(args.diameter), channels=channels)
        except Exception as e:
            print(e)
            raise e
        print('segmentation finished.')
        
        input_image = Path(input_image)

        if args.visualization:
            print(f'[[4/5]] Save visualization file {args.visualization}')
            # save results so you can load in gui
            cellpose.io.masks_flows_to_seg(image, masks, flows, input_image, diams, channels)
            if args.visualization.exists(): args.visualization.unlink()
            (input_image.parent / f'{input_image.stem}_seg.npy').rename(args.visualization)
            print(f'Saved visualization: {args.visualization}')

        if args.segmentation:
            print(f'[[5/5]] Save segmentation {args.segmentation}')
            # save results as png
            cellpose.io.save_masks(image, masks, flows, input_image)
            output_mask = input_image.parent / f'{input_image.stem}_cp_masks.png'
            if output_mask.exists():
                if args.segmentation.exists(): args.segmentation.unlink()
                (output_mask).rename(args.segmentation)
                print(f'Saved out: {args.segmentation}')
            else:
                print('Segmentation was not generated because no masks were found.')

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)