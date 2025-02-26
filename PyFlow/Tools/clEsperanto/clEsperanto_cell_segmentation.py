from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'AICS_12_134_C=0.tif', '--corrected_binary', '--out', 'AICS_12_134_C=0_mask.tif']
    
    name = "clEsperanto Cell Segmentation"
    description = "Cell segmentation with clEsperanto."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Input image path',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'corrected_binary',
                help = 'if non corrected is not good',
                default = False,
                type = 'bool',
            ),
            dict(
                name = 'radius_x',
                help = 'radius_x',
                default = 10,
                type = 'float',
            ),
            dict(
                name = 'radius_y',
                help = 'radius_y',
                default = 10,
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


        input_image = args.input_image
        radius_x = args.radius_x
        radius_y = args.radius_y
        output = args.out

        print(f'[[1/3]] Load image {input_image}')
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

