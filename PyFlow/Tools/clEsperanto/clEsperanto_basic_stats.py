from .clEsperanto_tool import ClEsperantoTool

class Tool(ClEsperantoTool):

    test = ['--input_image', 'IXMtest_A02_s9.tif', '--out', 'IXMtest_A02_s9_info.csv']
    
    name = "clEsperanto Basic Stats"
    description = "Basic stats with clEsperanto."
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
                help = 'spot_sigma',
                default = 3.5,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                help = 'output csv file path',
                default = '{input_image.stem}_stats.csv',
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
        
        import csv
        from itertools import zip_longest

        input_image = args.input_image
        spot_sigma = args.spot_sigma
        output = args.out

        print(f'[[1/3]] Load image {input_image}')
        image = self.io.imread(input_image)
        print("Input image : {}".format(input_image))
        print("Loaded image size : " + str(image.shape))
        input_to_GPU = self.cle.push(image)
        print("Image size in GPU : " + str(input_to_GPU.shape))

        print(f'[[2/3]] Process image {input_image}')

        labels = self.cle.voronoi_otsu_labeling(input_to_GPU, spot_sigma=spot_sigma)
        statistics = self.cle.statistics_of_labelled_pixels(input_to_GPU, labels)

        label = statistics["label"]
        original_label = statistics["original_label"]
        bbox_min_x = statistics["bbox_min_x"]
        bbox_min_y = statistics["bbox_min_y"]
        bbox_min_z = statistics["bbox_min_z"]
        bbox_max_x = statistics["bbox_max_x"]
        bbox_max_y = statistics["bbox_max_y"]
        bbox_max_z = statistics["bbox_max_z"]
        bbox_width = statistics["bbox_width"]
        bbox_depth = statistics["bbox_depth"]
        bbox_height = statistics["bbox_height"]
        min_intensity = statistics["min_intensity"]
        max_intensity = statistics["max_intensity"]
        sum_intensity = statistics["sum_intensity"]
        area = statistics["area"]
        mean_intensity = statistics["mean_intensity"]
        sum_intensity_times_x = statistics["sum_intensity_times_x"]
        mass_center_x = statistics["mass_center_x"]
        sum_intensity_times_y = statistics["sum_intensity_times_y"]
        mass_center_y = statistics["mass_center_y"]
        sum_intensity_times_z = statistics["sum_intensity_times_z"]
        mass_center_z = statistics["mass_center_z"]
        sum_x = statistics["sum_x"]
        centroid_x = statistics["centroid_x"]
        sum_y = statistics["sum_y"]
        centroid_y = statistics["centroid_y"]
        sum_z = statistics["sum_z"]
        centroid_z = statistics["centroid_z"]
        sum_distance_to_centroid = statistics["sum_distance_to_centroid"]
        mean_distance_to_centroid = statistics["mean_distance_to_centroid"]
        sum_distance_to_mass_center = statistics["sum_distance_to_mass_center"]
        mean_distance_to_mass_center = statistics["mean_distance_to_mass_center"]
        standard_deviation_intensity = statistics["standard_deviation_intensity"]
        max_distance_to_centroid = statistics["max_distance_to_centroid"]
        max_distance_to_mass_center = statistics["max_distance_to_mass_center"]
        mean_max_distance_to_centroid_ratio = statistics["mean_max_distance_to_centroid_ratio"]
        mean_max_distance_to_mass_center_ratio = statistics["mean_max_distance_to_mass_center_ratio"]

        print("label : {}".format(label))

        print(f'[[3/3]] Save output file {output}')

        header = [label,
            original_label,
            bbox_min_x,
            bbox_min_y,
            bbox_min_z,
            bbox_max_x,
            bbox_max_y,
            bbox_max_z,
            bbox_width,
            bbox_height,
            bbox_depth,
            min_intensity,
            max_intensity,
            sum_intensity,
            area,
            mean_intensity,
            sum_intensity_times_x,
            mass_center_x,
            sum_intensity_times_y,
            mass_center_y,
            sum_intensity_times_z,
            mass_center_z,
            sum_x,
            centroid_x,
            sum_y,
            centroid_y,
            sum_z,
            centroid_z,
            sum_distance_to_centroid,
            mean_distance_to_centroid,
            sum_distance_to_mass_center,
            mean_distance_to_mass_center,
            standard_deviation_intensity,
            max_distance_to_centroid,
            max_distance_to_mass_center,
            mean_max_distance_to_centroid_ratio,
            mean_max_distance_to_mass_center_ratio
            ]

        export_data = zip_longest(*header, fillvalue = '')

        with open(output, "w", encoding="ISO-8859-1", newline='') as f:
            wr = csv.writer(f)
            wr.writerow(("label",
                "original_label",
                "bbox_min_x",
                "bbox_min_y",
                "bbox_min_z",
                "bbox_max_x",
                "bbox_max_y",
                "bbox_max_z",
                "bbox_width",
                "bbox_height",
                "bbox_depth",
                "min_intensity",
                "max_intensity",
                "sum_intensity",
                "area",
                "mean_intensity",
                "sum_intensity_times_x",
                "mass_center_x",
                "sum_intensity_times_y",
                "mass_center_y",
                "sum_intensity_times_z",
                "mass_center_z",
                "sum_x",
                "centroid_x",
                "sum_y",
                "centroid_y",
                "sum_z",
                "centroid_z",
                "sum_distance_to_centroid",
                "mean_distance_to_centroid",
                "sum_distance_to_mass_center",
                "mean_distance_to_mass_center",
                "standard_deviation_intensity",
                "max_distance_to_centroid",
                "max_distance_to_mass_center",
                "mean_max_distance_to_centroid_ratio",
                "mean_max_distance_to_mass_center_ratio"))
            wr.writerows(export_data)

