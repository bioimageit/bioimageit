
class Tool:

    categories = ['Deconvolution']
    dependencies = dict(conda=['conda-forge::pycudadecon|linux-64,win-64'], pip=[])
    environment = 'condadecon'
    # test = ['--input_image', 'otf.tif', '--psf', '?' '--output_image', 'otf_decon.tif']
        
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
                name = 'psf',
                shortname = 'p',
                help = 'Path to the PSF or OTF file.',
                required = True,
                type = 'Path',
            ),
            dict(
                name = 'background',
                shortname = 'b',
                help = 'User-supplied background to subtract. If "auto", the median value of the last Z plane will be used as background.',
                default = '80',
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
        from pycudadecon import decon
        from skimage import io
        self.decon = decon
        self.io = io
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)
        try:
            background = int(args.background) if args.background != 'auto' else args.background
        except ValueError as e:
            raise Exception(f'Error: the background argument must be an integer or "auto"; but it is "{args.background}".')
        
        print(f'[[1/3]] Load image {input_image}')
        im = self.io.imread(input_image)
        
        print(f'[[2/3]] Process image')
        out_im = self.decon(im, psf=args.psf, background=background)
        
        print(f'[[3/3]] Save image')
        self.io.imsave(args.output_image, out_im)

