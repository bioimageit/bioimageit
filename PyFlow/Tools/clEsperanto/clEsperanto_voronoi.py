from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'IXMtest_A02_s9.tif', '--out', 'IXMtest_A02_s9_voronoi.csv']
    
    name = "clEsperanto Voronoi Otsu"
    description = "Voronoi otsu labeling with clEsperanto."
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
                default = 5,
                type = 'float',
            ),
            dict(
                name = 'sigma_outline',
                help = 'sigma_outline',
                default = 1,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                help = 'output image path',
                default = '{input_image.stem}_voronoi_otsu{input_image.exts}',
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

