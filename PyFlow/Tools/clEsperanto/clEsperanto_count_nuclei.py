import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['Segmentation']
    dependencies = dict(conda=['conda-forge::pyopencl', 'conda-forge::pyclesperanto-prototype'], pip=[])
    environment = 'clEsperanto'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("clEsperanto count with channels", description="Count particles with channels in clEsperanto.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        
        inputs_parser.add_argument('--input_image', type = Path, help = 'Input image path')
        inputs_parser.add_argument('--spot_sigma', type = str, help = 'Spot sigma')
        
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
            sys.exit('Error: input image {args.input_image} does not exist.')
        
        print(f'[[1/3]] Load image {input_image}')

        input_image = args.input_image
        spot_sigma = args.spot_sigma
        output = args.out

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

        number_of_nuclei_b = nuclei_b.max()
        number_of_nuclei_g = nuclei_g.max()
        number_of_nuclei_r = nuclei_r.max()

        print("Nuclei blue positive:", number_of_nuclei_b)
        print("Nuclei green positive:", number_of_nuclei_g)
        print("Nuclei red positive:", number_of_nuclei_r)

        count_map_bg = self.cle.proximal_other_labels_count_map(nuclei_b, nuclei_g)
        count_map_br = self.cle.proximal_other_labels_count_map(nuclei_b, nuclei_r)
        count_map_gb = self.cle.proximal_other_labels_count_map(nuclei_g, nuclei_b)
        count_map_gr = self.cle.proximal_other_labels_count_map(nuclei_g, nuclei_r)
        count_map_rb = self.cle.proximal_other_labels_count_map(nuclei_r, nuclei_b)
        count_map_rg = self.cle.proximal_other_labels_count_map(nuclei_r, nuclei_g)

        print("\n")

        double_positive_bg = self.cle.exclude_labels_with_map_values_out_of_range(
            count_map_bg, 
            nuclei_b, 
            minimum_value_range=1)
        double_positive_br = self.cle.exclude_labels_with_map_values_out_of_range(
            count_map_br, 
            nuclei_b, 
            minimum_value_range=1)
        double_positive_gb = self.cle.exclude_labels_with_map_values_out_of_range(
            count_map_gb, 
            nuclei_g, 
            minimum_value_range=1)
        double_positive_gr = self.cle.exclude_labels_with_map_values_out_of_range(
            count_map_gr, 
            nuclei_g, 
            minimum_value_range=1)
        double_positive_rb = self.cle.exclude_labels_with_map_values_out_of_range(
            count_map_rb, 
            nuclei_r, 
            minimum_value_range=1)
        double_positive_rg = self.cle.exclude_labels_with_map_values_out_of_range(
            count_map_rg, 
            nuclei_r, 
            minimum_value_range=1)

        number_of_double_bg = double_positive_bg.max()
        number_of_double_br = double_positive_br.max()
        number_of_double_gb = double_positive_gb.max()
        number_of_double_gr = double_positive_gr.max()
        number_of_double_rb = double_positive_rb.max()
        number_of_double_rg = double_positive_rg.max()

        print("Number of blue positives that also express green", number_of_double_bg)
        print("Number of blue positives that also express red", number_of_double_br)
        print("Number of green positives that also express blue", number_of_double_gb)
        print("Number of green positives that also express red", number_of_double_gr)
        print("Number of red positives that also express blue", number_of_double_rb)
        print("Number of red positives that also express green", number_of_double_rg)

        print(f'[[3/3]] Save output file {output}')

        with open(args.out, 'w') as f:
            f.write("b = " + str(number_of_nuclei_b) + "\t")
            f.write("g = " + str(number_of_nuclei_g) + "\t")
            f.write("r = " + str(number_of_nuclei_r) + "\t")
            f.write("bg = " + str(number_of_double_bg) + "\t")
            f.write("br = " + str(number_of_double_br) + "\t")
            f.write("gb = " + str(number_of_double_gb) + "\t")
            f.write("gr = " + str(number_of_double_gr) + "\t")
            f.write("rb = " + str(number_of_double_rb) + "\t")
            f.write("rg = " + str(number_of_double_rg))

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)