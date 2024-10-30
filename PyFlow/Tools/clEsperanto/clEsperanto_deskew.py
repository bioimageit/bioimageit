import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['Segmentation']
    dependencies = dict(conda=['conda-forge::pyopencl', 'conda-forge::pyclesperanto-prototype'], pip=[])
    environment = 'clEsperanto'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("clEsperanto  Deskew", description="Deskew with clEsperanto.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        
        inputs_parser.add_argument('--input_image', type = Path, help = 'Input image path')
        inputs_parser.add_argument('--angle', type = float, help = 'Deskewing angle in degrees')
        inputs_parser.add_argument('--sigma_outline', type = float, help = 'sigma_outline')
        inputs_parser.add_argument('--voxel_size_x', type = float, help = 'voxel_size_x_in_microns')
        inputs_parser.add_argument('--voxel_size_y', type = float, help = 'voxel_size_y_in_microns')
        inputs_parser.add_argument('--voxel_size_z', type = float, help = 'voxel_size_z_in_microns')
        
        outputs_parser = parser.add_argument_group('outputs')

        outputs_parser.add_argument('--out', type=Path, help = 'output image path')

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
            sys.exit('Error: input image {args.input_image} does not exist.')
        
        print(f'[[1/3]] Load image {input_image}')

        input_image = args.input_image
        voxel_size_x_in_microns = args.voxel_size_x
        voxel_size_y_in_microns = args.voxel_size_y
        voxel_size_z_in_microns = args.voxel_size_z
        deskewing_angle_in_degrees = args.angle
        output = args.out

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