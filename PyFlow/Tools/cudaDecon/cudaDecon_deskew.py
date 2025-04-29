class Tool:

    categories = ['Deconvolution']
    dependencies = dict(conda=['conda-forge::pycudadecon|linux-64,win-64'], pip=['scikit-image==0.24.0'])
    environment = 'condadecon'
    test = ['--input_image', 'deskew.tif', '--output_image', 'deskewed.tif']
        
    name = "condaDecon"
    description = "CUDA/C++ implementation of an accelerated Richardson Lucy Deconvolution algorithm."
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
                name = 'dxdata',
                shortname = 'dx',
                help = 'XY Pixel size of image volume.',
                default = 0.1,
                type = 'float',
            ),
            dict(
                name = 'dzdata',
                shortname = 'dz',
                help = 'Z-step size in image volume. In a typical light sheet stage-scanning acquisition, this corresponds to the step size that the stage takes between planes, NOT the final Z-step size between planeds after deskewing along the optical axis of the detection objective.',
                default = 0.5,
                type = 'float',
            ),
            dict(
                name = 'angle',
                shortname = 'a',
                help = 'Deskew angle (usually, angle between sheet and axis of stage motion).',
                default = 31.5,
                type = 'float',
            ),
            dict(
                name = 'width',
                shortname = 'w',
                help = 'If not 0, crop output image to specified width',
                default = 0,
                type = 'int',
            ),
            dict(
                name = 'shift',
                shortname = 's',
                help = 'If not 0, shift image center by this value',
                default = 0,
                type = 'int',
            ),
            dict(
                name = 'pad_val',
                shortname = 'pv',
                help = 'Value to pad image with when deskewing. If None the median value of the last Z plane will be used.',
                default = None,
                type = 'int',
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
        import pycudadecon
        from skimage import io
        self.pycudadecon = pycudadecon
        self.io = io
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/3]] Load image {input_image}')
        im = self.io.imread(input_image)
        
        print(f'[[2/3]] Process image')
        out_im = self.pycudadecon.deskewGPU(im, dxdata=args.dxdata, dzdata=args.dzdata, angle=args.angle, width=args.width, shift=args.shift, pad_val=args.pad_val)

        print(f'[[3/3]] Save image')
        self.io.imsave(args.output_image, out_im)

