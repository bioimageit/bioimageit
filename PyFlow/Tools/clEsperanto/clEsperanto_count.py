from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'segmentation.tif', '--sigma_x', '1', '--sigma_y', '1', '--out', 'segmentation_count.csv']
    
    name = "clEsperanto Count objects"
    description = "Count objects with clEsperanto."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Input image path',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'sigma_x',
                help = 'sigma_x',
                default = 0,
                type = 'float',
            ),
            dict(
                name = 'sigma_y',
                help = 'sigma_y',
                default = 0,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                help = 'output file path',
                default = '{input_image.stem}_count.csv',
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
        input_sigma_x = args.sigma_x
        input_sigma_y = args.sigma_y
        output = args.out

        print(f'[[1/3]] Load image {input_image}')
        image = self.io.imread(input_image)
        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/3]] Process image {input_image}')

        blurred = self.cle.gaussian_blur(input_to_GPU, sigma_x = input_sigma_x, sigma_y = input_sigma_y)
        binary = self.cle.threshold_otsu(blurred)
        labeled = self.cle.connected_components_labeling_box(binary)

        num_labels = self.cle.maximum_of_all_pixels(labeled)
        print("Number of objects in the image: " + str(num_labels))

        print(f'[[3/3]] Save output file {output}')

        with open(args.out, 'w') as f:
            f.write(str(num_labels))

