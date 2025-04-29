from pathlib import Path

class Tool:

    # Taken from https://py.imagej.net/en/latest/Puncta-Segmentation.html
    categories = ['Fiji', 'Registration']
    dependencies = dict(python='3.10', conda=['conda-forge::pyimagej==1.5.0', 'conda-forge::openjdk=11'], pip=['numy==1.26.4'])
    additionalActivateCommands = dict(all=[], linux=[], mac=['export DYLD_LIBRARY_PATH="/usr/local/lib/"'])
    environment = 'pyimagej'
    # test = ['--input_image', 'celegans_stack.tif', '--output_image', 'stackreg.tif']
        
    name = "StackReg"
    description = "Stack registration with the StackReg Fiji plugin."
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
                name = 'transformation',
                shortname = 't',
                help = 'The transformation applied on each slice.',
                default = 'Rigid Body',
                choices = ['Translation', 'Rigid Body', 'Scaled rotation', 'Affine'],
                type = 'str',
            ),
    ]
    outputs = [
            dict(
                name = 'output_image',
                shortname = 'o',
                help = 'The output image path.',
                default = '{input_image.stem}_stackreg{input_image.exts}',
                type = 'Path',
            ),
    ]

    def initialize(self, args):
        print('Loading libraries...')
        import imagej
        import scyjava

        pluginsPath = Path(__file__).parent / 'StackReg'
        scyjava.config.add_option(f'-Dplugins.dir={pluginsPath.resolve()}')

        # initialize imagej
        self.ij = imagej.init('sc.fiji:fiji:2.15.0', mode='headless')
        print(f"ImageJ version: {self.ij.getVersion()}")
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/3]] Load image {input_image}')
        # load test data
        image = self.ij.io().open(input_image)
        image = self.ij.op().convert().int32(image) # convert image to 32-bit

        # convert ImgPlus to ImagePlus
        image = self.ij.py.to_imageplus(image)

        print(f'[[2/3]] Process image')
        # run the analyze particle plugin
        self.ij.py.run_plugin(plugin="StackReg ", args=f"transformation=[{args.transformation}]", imp=image)

        print(f'[[3/3]] Save image')
        self.ij.io().save(image, args.output_image)
        

