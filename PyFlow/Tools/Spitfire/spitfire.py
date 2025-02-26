import subprocess

class Tool:

    categories = ['Denoising']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "Spitfire"
    description = "SPITFIR(e) utilizes the primal-dual optimization principle for fast energy minimization. Experimental results in various microscopy modalities from wide field up to lattice light sheet demonstrate the ability of the SPITFIR(e) algorithm to efficiently reduce noise, blur, and out-of-focus background, while avoiding the emergence of deconvolution artifacts."
    inputs = [
            dict(
                name = 'input_image',
                shortname = 'i',
                help = 'The input image path. The dimensions (width, height, depth) of the image should be even for best results.',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'type',
                help = 'Perform 2D, 3D or 4D deconvolution.',
                default = '2D',
                choices = ['2D', '3D', '4D'],
                type = 'str',
            ),
            dict(
                name = 'regularization',
                shortname = 'r',
                help = 'Regularization parameter pow(2,-x).',
                default = 2,
                type = 'float',
            ),
            dict(
                name = 'weighting',
                shortname = 'w',
                help = 'Weighting. Regularization parameter pow(2,-x). Must be in range [0.0, 1.0].',
                default = 0.6,
                type = 'float',
            ),
            dict(
                name = 'method',
                shortname = 'm',
                help = 'Method.',
                default = 'Hessian variation',
                choices = ['Sparse variation', 'Hessian variation'],
                type = 'str',
            ),
            dict(
                name = 'padding',
                shortname = 'p',
                help = 'Add a padding to process pixels in borders.',
                default = False,
                type = 'bool',
            ),
    ]
    outputs = [
            dict(
                name = 'output_image',
                shortname = 'o',
                help = 'The output image.',
                default = '{input_image.stem}_denoised{input_image.exts}',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Run Spitfire on image {args.input_image}')
        process = 'simgspitfiredenoise' + args.type.lower()
        command = [process, '-i', args.input_image, '-o', args.output_image, '-regularization', args.regularization, '-weighting', args.weighting, '-method', 'SV' if args.method == 'Sparse variation' else 'HV', '-padding', 'True' if args.padding else 'False', '-niter', 200]
        subprocess.run([str(c) for c in command], check=True)

