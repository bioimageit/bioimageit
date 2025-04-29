from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'deskew.tif', '--voxel_size_x', 0.1449922, '--voxel_size_y', 0.1449922, '--voxel_size_z', 0.3, '--out', 'deskewed.tif']
    
    name = "clEsperanto Deskew"
    description = "Deskew with clEsperanto."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Input image path',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'angle',
                help = 'Deskewing angle in degrees',
                default = 30,
                type = 'float',
            ),
            dict(
                name = 'voxel_size_x',
                help = 'voxel_size_x_in_microns',
                default = 0.202,
                type = 'float',
            ),
            dict(
                name = 'voxel_size_y',
                help = 'voxel_size_y_in_microns',
                default = 0.202,
                type = 'float',
            ),
            dict(
                name = 'voxel_size_z',
                help = 'voxel_size_z_in_microns',
                default = 1,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                help = 'output image path',
                default = '{input_image.stem}_deskewed{input_image.exts}',
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

