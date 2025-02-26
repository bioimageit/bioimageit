
class Tool:

    categories = ['Measurements']
    dependencies = dict(python='3.12', conda=[], pip=['pandas==2.2.2', 'scikit-image==0.24.0', 'scipy==1.14.1'])
    environment = 'scikit-image_scipy'
    test = ['--input_image', 'img02.png', '--label', 'img02_segmentation.png', '--pixel', '4', '--out', 'measurements.csv']
    
    name = "LabelsMeasure"
    description = "LabelsMeasure provides the tools to generate the regions of interest from label images."
    inputs = [
            dict(
                name = 'input_image',
                shortname = 'i',
                help = 'The input image path.',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'label',
                help = 'Label image path, from cellpose for instance.',
                required = True,
                type = 'Path',
            ),
            dict(
                name = 'pixel',
                help = 'Size of the pixel erosion',
                required = True,
                type = 'int',
            ),
            dict(
                name = 'binary_map',
                help = 'If false, labels in your black & white image',
                default = False,
                type = 'bool',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                shortname = 'o',
                help = 'The output csv path.',
                default = '{input_image.stem}_measurements.csv',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/3]] Load image {input_image} and libraries')

        from skimage import io
        from skimage.morphology import disk, erosion
        from skimage.measure import label, regionprops, regionprops_table
        from scipy.stats import skew, kurtosis
        import numpy as np
        import pandas as pd

        original_img = io.imread(str(args.input_image))
        label_img = io.imread(str(args.label))

        original_img = np.float32(original_img)
        print("Original shape = {}".format(original_img.shape))

        if args.binary_map == "True":
            label_img = label(label_img)
            binary = "True"
        else:
            binary = "False"
        print("Binary = {}".format(binary))

        print("Pixel erosion = {}".format(args.pixel))
        label_img = erosion(label_img, disk(args.pixel))

        print('[[2/3]] Process regions', label_img.shape)

        regions = regionprops(label_img)
        print("Regions created")

        def stdDev(regionmask, intensity_image):
            return np.std(intensity_image[regionmask])

        def skewness(regionmask, intensity_image):
            return skew(intensity_image[regionmask])

        def kurt(regionmask, intensity_image):
            return kurtosis(intensity_image[regionmask], fisher = True)

        def center_mass(intensity_image):
            return regions[0].centroid

        print("\n")

        ###########################################################
        ###################### save csv ###########################
        ###########################################################

        print('[[3/3]] Save output table')

        props = regionprops_table(label_img, original_img, properties = ('area', 'intensity_mean', 'intensity_min', 'intensity_max', 'perimeter', 'centroid', 'bbox', 'feret_diameter_max', 'slice'), 
            extra_properties=(stdDev, skewness, kurt, center_mass))
        table = pd.DataFrame(props)
        print(table.head())

        table.to_csv(args.out)
        print("Table saved as {}".format(args.out))

