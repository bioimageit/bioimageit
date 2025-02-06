import argparse
from pathlib import Path
from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'deskew.tif', '--voxel_size_x', 0.1449922, '--voxel_size_y', 0.1449922, '--voxel_size_z', 0.3, '--out', 'deskewed.tif']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("clEsperanto Deskew", description="Deskew with clEsperanto.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        
        inputs_parser.add_argument('--input_image', type = Path, help = 'Input image path')
        inputs_parser.add_argument('--angle', type = float, help = 'Deskewing angle in degrees', default=30)
        inputs_parser.add_argument('--voxel_size_x', type = float, help = 'voxel_size_x_in_microns', default=0.202)
        inputs_parser.add_argument('--voxel_size_y', type = float, help = 'voxel_size_y_in_microns', default=0.202)
        inputs_parser.add_argument('--voxel_size_z', type = float, help = 'voxel_size_z_in_microns', default=1)
        
        outputs_parser = parser.add_argument_group('outputs')

        outputs_parser.add_argument('--out', type=Path, help = 'output image path', default='{input_image.stem}_deskewed{input_image.exts}')

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
        voxel_size_x_in_microns = args.voxel_size_x
        voxel_size_y_in_microns = args.voxel_size_y
        voxel_size_z_in_microns = args.voxel_size_z
        deskewing_angle_in_degrees = args.angle
        output = args.out

        print(f'[[1/3]] Load image {input_image}')
        image = self.io.imread(input_image)

        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/3]] Process image {input_image}')

        deskewed = self.cle.deskew_y(input_to_GPU, 
                                angle_in_degrees=deskewing_angle_in_degrees, 
                                voxel_size_x=voxel_size_x_in_microns, 
                                voxel_size_y=voxel_size_y_in_microns, 
                                voxel_size_z=voxel_size_z_in_microns)

        print(f'[[3/3]] Save output file {output}')

        self.io.imsave(output, deskewed)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)