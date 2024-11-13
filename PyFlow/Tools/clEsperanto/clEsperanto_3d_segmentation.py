import sys
import argparse
from pathlib import Path
from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'IXMtest_A02_s9.tif', '--out', 'IXMtest_A02_s9_mask.tif']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("clEsperanto Segmentation", description="Segment with clEsperanto.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        
        inputs_parser.add_argument('--input_image', type = Path, help = 'Input image path')
        inputs_parser.add_argument('--sigma_spot_detection', type = float, help = 'sigma_spot_detection')
        inputs_parser.add_argument('--sigma_outline', type = float, help = 'sigma_outline')
        inputs_parser.add_argument('--voxel_size_x', type = float, help = 'voxel_size_x')
        inputs_parser.add_argument('--voxel_size_y', type = float, help = 'voxel_size_y')
        inputs_parser.add_argument('--voxel_size_z', type = float, help = 'voxel_size_z')
        inputs_parser.add_argument('--radius_x', type = float, help = 'radius_x')
        inputs_parser.add_argument('--radius_y', type = float, help = 'radius_y')
        inputs_parser.add_argument('--radius_z', type = float, help = 'radius_z')
        
        outputs_parser = parser.add_argument_group('outputs')

        outputs_parser.add_argument('--out', type=Path, help = 'Output image path', default='{input_image.stem}_segmentation{input_image.exts}')

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

        print(f'[[1/4]] Load image {input_image}')
                
        input_image = args.input_image
        voxel_size_x = args.voxel_size_x
        voxel_size_y = args.voxel_size_y
        voxel_size_z = args.voxel_size_z
        sigma_outline = args.sigma_outline
        sigma_spot_detection = args.sigma_spot_detection
        radius_x = args.radius_x
        radius_y = args.radius_y
        radius_z = args.radius_z
        output = args.out

        image = self.io.imread(input_image)
        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/4]] Resample image {input_image}')

        resampled = self.cle.create([int(input_to_GPU.shape[0] * voxel_size_z), int(input_to_GPU.shape[1] * voxel_size_y), int(input_to_GPU.shape[2] * voxel_size_x)])
        self.cle.scale(input_to_GPU, resampled, factor_x=voxel_size_x, factor_y=voxel_size_y, factor_z=voxel_size_z, centered=False)

        print("New image size: " + str(resampled.shape))

        equalized_intensities_stack = self.cle.create_like(resampled)
        a_slice = self.cle.create([resampled.shape[1], resampled.shape[0]])
        num_slices = resampled.shape[0]

        print(f'[[3/4]] Process image {input_image}')

        mean_intensity_stack = self.cle.mean_of_all_pixels(resampled)
        corrected_slice = None

        for z in range(0, num_slices):
            # get a single slice out of the stack
            self.cle.copy_slice(resampled, a_slice, z)
            # measure its intensity
            mean_intensity_slice = self.cle.mean_of_all_pixels(a_slice)
            # correct the intensity
            correction_factor = mean_intensity_slice/mean_intensity_stack
            corrected_slice = self.cle.multiply_image_and_scalar(a_slice, corrected_slice, correction_factor)
            # copy slice back in a stack
            self.cle.copy_slice(corrected_slice, equalized_intensities_stack, z)

        backgrund_subtracted = self.cle.top_hat_box(equalized_intensities_stack, radius_x=radius_x, radius_y=radius_y, radius_z=radius_z)

        segmented = self.cle.voronoi_otsu_labeling(backgrund_subtracted, spot_sigma=sigma_spot_detection, outline_sigma=sigma_outline)

        print(f'[[4/4]] Save output image {output}')

        self.io.imsave(output, segmented)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)