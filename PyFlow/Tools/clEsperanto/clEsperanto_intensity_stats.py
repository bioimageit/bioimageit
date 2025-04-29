from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'test.png', '--out', 'test_intensity_stats.csv']
    
    name = "clEsperanto Intensity stats"
    description = "Intensity stats with clEsperanto."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Input image path',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'spot_sigma',
                help = 'Spot sigma',
                default = 20,
                type = 'str',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                help = 'output csv file path',
                default = '{input_image.stem}_beads.csv',
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
        spot_sigma = args.spot_sigma
        output = args.out

        print(f'[[1/3]] Load image {input_image}')
        image = self.io.imread(input_image)

        blue_chan = image[...,0]
        green_chan = image[...,1]
        red_chan = image[...,2]
        spot_sigma = args.spot_sigma
        output = args.out

        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/3]] Process image {input_image}')

        nuclei_b = self.cle.voronoi_otsu_labeling(blue_chan, spot_sigma=spot_sigma)
        nuclei_g = self.cle.voronoi_otsu_labeling(green_chan, spot_sigma=spot_sigma)
        nuclei_r = self.cle.voronoi_otsu_labeling(red_chan, spot_sigma=spot_sigma)

        intensity_map_bg = self.cle.mean_intensity_map(green_chan, nuclei_b)
        intensity_map_br = self.cle.mean_intensity_map(red_chan, nuclei_b)
        intensity_map_gb = self.cle.mean_intensity_map(blue_chan, nuclei_g)
        intensity_map_gr = self.cle.mean_intensity_map(red_chan, nuclei_g)
        intensity_map_rb = self.cle.mean_intensity_map(blue_chan, nuclei_r)
        intensity_map_rg = self.cle.mean_intensity_map(green_chan, nuclei_r)

        statistics_bg = self.cle.statistics_of_background_and_labelled_pixels(green_chan, nuclei_b)
        statistics_br = self.cle.statistics_of_background_and_labelled_pixels(red_chan, nuclei_b)
        statistics_gb = self.cle.statistics_of_background_and_labelled_pixels(blue_chan, nuclei_g)
        statistics_gr = self.cle.statistics_of_background_and_labelled_pixels(red_chan, nuclei_g)
        statistics_rb = self.cle.statistics_of_background_and_labelled_pixels(blue_chan, nuclei_r)
        statistics_rg = self.cle.statistics_of_background_and_labelled_pixels(green_chan, nuclei_r)

        intensity_vector_bg = statistics_bg["mean_intensity"]
        intensity_vector_br = statistics_br["mean_intensity"]
        intensity_vector_gb = statistics_gb["mean_intensity"]
        intensity_vector_gr = statistics_gr["mean_intensity"]
        intensity_vector_rb = statistics_rb["mean_intensity"]
        intensity_vector_rg = statistics_rg["mean_intensity"]

        print("intensity_vector_bg = {}".format(intensity_vector_bg))
        print("intensity_vector_br = {}".format(intensity_vector_br))
        print("intensity_vector_gb = {}".format(intensity_vector_gb))
        print("intensity_vector_gr = {}".format(intensity_vector_gr))
        print("intensity_vector_rb = {}".format(intensity_vector_rb))
        print("intensity_vector_rg = {}".format(intensity_vector_rg))

        print(f'[[3/3]] Save output file {output}')

        header = [intensity_vector_bg,
            intensity_vector_br,
            intensity_vector_gb,
            intensity_vector_gr,
            intensity_vector_rb,
            intensity_vector_rg
            ]

        import csv
        from itertools import zip_longest

        export_data = zip_longest(*header, fillvalue = '')

        with open(output, "w", encoding="ISO-8859-1", newline='') as f:
            wr = csv.writer(f)
            wr.writerow(("intensity_vector_bg","intensity_vector_br","intensity_vector_gb","intensity_vector_gr","intensity_vector_rb","intensity_vector_rg"))
            wr.writerows(export_data)

