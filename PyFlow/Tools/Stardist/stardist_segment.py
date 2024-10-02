import sys
from importlib import import_module
import argparse
import json
from pathlib import Path

class Tool:

    categories = ['Segmentation']
    dependencies = dict(python='3.8', conda=['nvidia::cudatoolkit=11.0.*', 'nvidia::cudnn=8.0.*', 'jupyter', 'pip'], pip=['tensorflow==2.4.*', 'csbdeep==0.8.0', 'stardist==0.9.1'])
    environment = 'stardist'
    autoInputs = ['input_image']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Stardist", description="Segment cells with stardist.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path)
        inputs_parser.add_argument('-m', '--model_name', help='The model to use.', required=True, choices=['2D_versatile_fluo', '2D_versatile_he', '2D_paper_dsb2018', '2D_demo'], type=str)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--out', help='The output mask path.', default='{input_image.stem}_segmentation.{input_image.exts}', type=Path)
        return parser

    def initialize(self, args):
        print('Loading libraries...')
        from stardist.models import StarDist2D
        from csbdeep.utils import normalize
        from skimage import io
        self.normalize = normalize
        self.model = StarDist2D.from_pretrained(args.model_name)
    
    def processDataFrame(self, dataFrame):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit('Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/3]] Load image {input_image}')
        channels = json.loads(args.channels)
        image = self.io.imread(input_image)
        
        print('[[2/3]] Compute segmentation', image.shape)
        labels, _ = self.model.predict_instances(self.normalize(image))
        input_image = Path(input_image)

        print(f'[[3/3]] Save segmentation {args.out}')
        self.io.imsave(args.out, labels)
        print(f'Saved segmentation: {args.out}')

if __name__ == '__main__':
    tool = Tool()
    parser = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)