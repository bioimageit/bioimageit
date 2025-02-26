from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'IXMtest_A02_s9.tif', '--out', 'IXMtest_A02_s9_mask.tif']
    
    name = "clEsperanto Segmentation"
    description = "Segment with clEsperanto."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Input image path',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'sigma_spot_detection',
                help = 'sigma_spot_detection',
                default = None,
                type = 'float',
            ),
            dict(
                name = 'sigma_outline',
                help = 'sigma_outline',
                default = None,
                type = 'float',
            ),
            dict(
                name = 'voxel_size_x',
                help = 'voxel_size_x',
                default = None,
                type = 'float',
            ),
            dict(
                name = 'voxel_size_y',
                help = 'voxel_size_y',
                default = None,
                type = 'float',
            ),
            dict(
                name = 'voxel_size_z',
                help = 'voxel_size_z',
                default = None,
                type = 'float',
            ),
            dict(
                name = 'radius_x',
                help = 'radius_x',
                default = None,
                type = 'float',
            ),
            dict(
                name = 'radius_y',
                help = 'radius_y',
                default = None,
                type = 'float',
            ),
            dict(
                name = 'radius_z',
                help = 'radius_z',
                default = None,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                help = 'Output image path',
                default = '{input_image.stem}_segmentation{input_image.exts}',
                type = 'Path',
            ),
    ]

    def initialize(self, args):
        print('Loading libraries...')
        
        import pyclesperanto_prototype as cle
        import skimage.io

        self.cle = cle
        self.io = skimage.io
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/4]] Load image {args.input_image}')
                
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

        image = self.io.imread(args.input_image)
        print("Input image : {}".format(args.input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/4]] Resample image {args.input_image}')

        resampled = self.cle.create([int(input_to_GPU.shape[0] * voxel_size_z), int(input_to_GPU.shape[1] * voxel_size_y), int(input_to_GPU.shape[2] * voxel_size_x)])
        self.cle.scale(input_to_GPU, resampled, factor_x=voxel_size_x, factor_y=voxel_size_y, factor_z=voxel_size_z, centered=False)

        print("New image size: " + str(resampled.shape))

        equalized_intensities_stack = self.cle.create_like(resampled)
        a_slice = self.cle.create([resampled.shape[1], resampled.shape[0]])
        num_slices = resampled.shape[0]

        print(f'[[3/4]] Process image {args.input_image}')

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

