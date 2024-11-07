import sys
import argparse
from pathlib import Path
from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'AICS_12_134_C=0.tif', '--corrected_binary', '--out', 'AICS_12_134_C=0_mask.tif']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("clEsperanto Cell Segmentation", description="Cell segmentation with clEsperanto.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        
        inputs_parser.add_argument('--input_image', type = Path, help = 'Input image path')
        inputs_parser.add_argument('--corrected_binary', action='store_true', help = 'if non corrected is not good')
        inputs_parser.add_argument('--radius_x', type = float, help = 'radius_x', default=10)
        inputs_parser.add_argument('--radius_y', type = float, help = 'radius_y', default=10)
        
        outputs_parser = parser.add_argument_group('outputs')

        outputs_parser.add_argument('--out', type=Path, help = 'Output image path')

        return parser, dict( input_image = dict(autoColumn=True) )

    def initialize(self, args):
        print('Loading libraries...')
        
        import pyclesperanto_prototype as cle
        import skimage.io

        self.cle = cle
        self.io = skimage.io
    
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/3]] Load image {input_image}')

        input_image = args.input_image
        radius_x = args.radius_x
        radius_y = args.radius_y
        output = args.out

        image = self.io.imread(input_image)
        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/3]] Process image {input_image}')

        binary = self.cle.binary_not(self.cle.threshold_otsu(input_to_GPU))
        labels = self.cle.voronoi_labeling(binary)

        if args.corrected_binary:
            corrected_binary = self.cle.maximum_box(self.cle.minimum_box(binary, radius_x=radius_x, radius_y=radius_y), radius_x=radius_x, radius_y=radius_y)
            labels = self.cle.voronoi_labeling('True')

        print(f'[[3/3]] Save output file {output}')

        self.io.imsave(output, labels)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)