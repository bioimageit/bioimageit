import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['clEsperanto']
    dependencies = dict(conda=['conda-forge::pyopencl', 'conda-forge::pyclesperanto-prototype'], pip=[])
    environment = 'clEsperanto'
    test = ['--input_image', 'beads.tif', '--out', 'beads_info.csv']

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("clEsperanto Voronoi Otsu", description="Voronoi otsu labeling with clEsperanto.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        
        inputs_parser.add_argument('--input_image', type = Path, help = 'Input image path')
        # inputs_parser.add_argument('--sigma', type = float, help = 'sigma')
        inputs_parser.add_argument('--scalar', type = float, help = 'scalar for thresholds', default=0.5)
        
        outputs_parser = parser.add_argument_group('outputs')

        outputs_parser.add_argument('--out', type=Path, help = 'output csv file path')

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
        
        import csv
        from itertools import zip_longest

        print(f'[[1/3]] Load image {input_image}')

        input_image = args.input_image
        # sigma = args.sigma
        scalar = args.scalar
        output = args.out

        image = self.io.imread(input_image)
        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/3]] Process image {input_image}')

        # Local Maxima detection
        maxima = self.cle.detect_maxima_box(input_to_GPU)

        # Local threshold determination
        labeled_maxima = self.cle.label_spots(maxima)
        max_intensities = self.cle.read_intensities_from_map(labeled_maxima, input_to_GPU)
        thresholds = self.cle.multiply_image_and_scalar(max_intensities, scalar=scalar)

        # Make local threshold image
        voronoi_label_image = self.cle.extend_labeling_via_voronoi(labeled_maxima)
        threshold_image = self.cle.replace_intensities(voronoi_label_image, thresholds)
        binary_segmented = self.cle.greater(input_to_GPU, threshold_image)

        # Making bounding box
        labels = self.cle.connected_components_labeling_box(binary_segmented)
        stats = self.cle.statistics_of_labelled_pixels(label_image=labels)
        print('Bounding box widths', stats['bbox_width'])
        print('Bounding box heights', stats['bbox_height'])

        bbox_width = stats['bbox_width']
        bbox_height = stats['bbox_height']

        header = [bbox_width, bbox_height]

        print(f'[[3/3]] Save output file {output}')

        export_data = zip_longest(*header, fillvalue = '')

        with open(output, "w", encoding="ISO-8859-1", newline='') as f:
            wr = csv.writer(f)
            wr.writerow(("bbox_width", "bbox_height"))
            wr.writerows(export_data)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)