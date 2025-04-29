from pathlib import Path

class Tool:

    categories = ['Segmentation']
    dependencies = dict(
        python='3.9', 
        conda=[], 
        pip=['tensorflow==2.16.1', 'csbdeep==0.8.1', 'stardist==0.9.1'],
        optional = dict(conda = ['nvidia::cudatoolkit=11.0.*|win-64,linux-64', 'nvidia::cudnn=8.0.*|win-64,linux-64'])
        )
    environment = 'stardist'
    modelName = None
    
    name = "Stardist"
    description = "Segment cells with stardist."
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
                name = 'model_name',
                shortname = 'm',
                help = 'The model to use.',
                required = True,
                choices = ['2D_versatile_fluo', '2D_versatile_he', '2D_paper_dsb2018', '2D_demo', '3D_demo'],
                type = 'str',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                shortname = 'o',
                help = 'The output mask path.',
                default = '{input_image.stem}_segmentation{input_image.exts}',
                type = 'Path',
            ),
    ]

    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        input_image = str(args.input_image)

        print(f'[[1/3]] Load libraries and model {args.model_name}')

        print('Loading libraries...')
        from csbdeep.utils import normalize
        from skimage import io

        if self.modelName != args.model_name:
            self.modelName = args.model_name
            if args.model_name.startswith('2D'):
                from stardist.models import StarDist2D
                self.model = StarDist2D.from_pretrained(args.model_name)
            else:
                from stardist.models import StarDist3D
                self.model = StarDist3D.from_pretrained(args.model_name)
        

        print(f'[[1/3]] Load image {input_image}')
        image = io.imread(input_image)
        if len(image.shape)==3:
            image = image[:,:,0]
        if len(image.shape)>3:
            raise Exception(f'Error: input image {args.input_image} has too many dimension, should be 2 or 3 (in which case the channel 0 will be segmented).')

        print('[[2/3]] Compute segmentation', image.shape)
        labels, _ = self.model.predict_instances(normalize(image))
        input_image = Path(input_image)

        print(f'[[3/3]] Save segmentation {args.out}')
        io.imsave(args.out, labels)
        print(f'Saved segmentation: {args.out}')

