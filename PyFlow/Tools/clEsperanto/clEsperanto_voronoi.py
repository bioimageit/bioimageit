import argparse
from pathlib import Path
from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'IXMtest_A02_s9.tif', '--out', 'IXMtest_A02_s9_voronoi.csv']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("clEsperanto Voronoi Otsu", description="Voronoi otsu labeling with clEsperanto.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        
        inputs_parser.add_argument('--input_image', type = Path, help = 'Input image path')
        inputs_parser.add_argument('--sigma_spot_detection', type = float, help = 'sigma_spot_detection', default=5)
        inputs_parser.add_argument('--sigma_outline', type = float, help = 'sigma_outline', default=1)
        
        outputs_parser = parser.add_argument_group('outputs')

        outputs_parser.add_argument('--out', type=Path, help = 'output image path', default='{input_image.stem}_voronoi_otsu{input_image.exts}')

        return parser, dict( input_image = dict(autoColumn=True) )

    def initialize(self, args):
        print('Loading libraries...')
        
        import pyclesperanto_prototype as cle
        import skimage.io

        self.cle = cle
        self.io = skimage.io
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')


        input_image = args.input_image
        input_sigma_detect = args.sigma_spot_detection
        input_sigma_outline = args.sigma_outline
        output = args.out

        print(f'[[1/3]] Load image {input_image}')
        image = self.io.imread(input_image)
        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))


        print(f'[[2/3]] Process image {input_image}')

        segmented = self.cle.voronoi_otsu_labeling(input_to_GPU, spot_sigma=input_sigma_detect, outline_sigma=input_sigma_outline)

        print(f'[[3/3]] Save output image {output}')

        self.io.imsave(output, segmented)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)