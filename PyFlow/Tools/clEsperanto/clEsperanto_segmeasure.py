from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'test.png', '--out', 'test_segmeasure.csv']
    
    name = "clEsperanto Seg-measure"
    description = "Detect hot spots / local maxima / beads in an image and how to measure their FWHM. To make the algorithm work, the beads should be sufficiently sparse. ."
    inputs = [
            dict(
                name = 'input_image',
                help = 'Input image path',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'scalar',
                help = 'scalar for threshold',
                default = 1,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                help = 'output csv file path',
                default = '{input_image.stem}_segmeasure.csv',
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
        scalar = args.scalar
        output = args.out

        print(f'[[1/3]] Load image {input_image}')
        image = self.io.imread(input_image)
        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/3]] Process image {input_image}')

        maxima = self.cle.detect_maxima_box(input_to_GPU)
        labeled_maxima = self.cle.label_spots(maxima)
        max_intensities = self.cle.read_intensities_from_map(labeled_maxima, input_to_GPU)
        thresholds = self.cle.multiply_image_and_scalar(max_intensities, scalar=scalar)

        voronoi_label_image = self.cle.extend_labeling_via_voronoi(labeled_maxima)
        threshold_image = self.cle.replace_intensities(voronoi_label_image, thresholds)
        binary_segmented = self.cle.greater(input_to_GPU, threshold_image)

        labels = self.cle.connected_components_labeling_box(binary_segmented)
        stats = self.cle.statistics_of_labelled_pixels(label_image=labels)

        bbox_width = stats["bbox_width"]
        bbox_height = stats["bbox_height"]

        print('Bounding box widths', stats['bbox_width'])
        print('Bounding box heights', stats['bbox_height'])

        print(f'[[3/3]] Save output file {output}')

        import csv
        from itertools import zip_longest

        header = [bbox_width, bbox_height]

        export_data = zip_longest(*header, fillvalue = '')

        with open(output, "w", encoding="ISO-8859-1", newline='') as f:
            wr = csv.writer(f)
            wr.writerow(("bbox_width","bbox_height"))
            wr.writerows(export_data)

