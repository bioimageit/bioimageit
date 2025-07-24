from pathlib import Path
import shutil
import numbers

NONE_VALUE = -666

class Tool:

    categories = ['Segmentation']
    dependencies = dict(conda=[], pip=['cellpose==4.0.5'])
    environment = 'cellpose_sam'
    test = ['--input_image', 'img02.png', '--segmentation', 'img02_segmentation.png', '--visualization', 'img02_segmentation.npy']
    model = None
    use_gpu = None
    
    name = "Cellpose SAM"
    description = "Segment cells with Cellpose SAM."
    inputs = [
            dict(
                name = 'input_image',
                help = 'The input image path.',
                required = True,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'use_gpu',
                help = 'Use GPU (default is CPU).',
                default = False,
                type = 'bool',
            ),
            dict(
                name = 'channel_axis',
                help = 'Channel axis. if None, channels dimension is attempted to be automatically determined.',
                default = NONE_VALUE,
                type = 'int',
            ),
            dict(
                name = 'z_axis',
                help = 'Z axis. if None, 2 dimension is attempted to be automatically determined.',
                default = NONE_VALUE,
                type = 'int',
            ),
            dict(
                name = 'diameter',
                help = 'Estimate of the cell diameters (in pixels).',
                default = NONE_VALUE,
                type = 'float',
            ),
            dict(
                name = 'flow_threshold',
                help = 'Flow error threshold (all cells with errors below threshold are kept) (not used for 3D).',
                default = 0.4,
                type = 'float',
            ),
            dict(
                name = 'cellprob_threshold',
                help = 'All pixels with value above threshold kept for masks, decrease to find more and larger masks.',
                default = 0.0,
                type = 'float',
            ),
            dict(
                name = 'do_3D',
                help = 'Run 3D segmentation on 3D/4D image input.',
                default = False,
                type = 'bool',
            ),
            dict(
                name = 'flow3D_smooth',
                help = 'If do_3D and flow3D_smooth>0, smooth flows with gaussian filter of this stddev.',
                default = 0,
                type = 'int',
            ),
            dict(
                name = 'min_size',
                help = 'All ROIs below this size, in pixels, will be discarded. Defaults to 15.',
                default = 15,
                type = 'int',
            ),
            dict(
                name = 'max_size_fraction',
                help = 'Masks larger than max_size_fraction of total image size are removed. Default is 0.4.',
                default = 0.4,
                type = 'float',
            ),
            dict(
                name = 'niter',
                help = 'number of iterations for dynamics computation. if None, it is set proportional to the diameter.',
                default = NONE_VALUE,
                type = 'int',
            ),
    ]
    outputs = [
            dict(
                name = 'segmentation',
                help = 'The output segmentation path.',
                default = '{input_image.astem}_segmentation.png',
                type = 'Path',
            ),
    ]

    def processData(self, args):

        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')
        
        print(f'[[1/5]] Load libraries and model')
        print('Loading libraries...')
        from cellpose import models
        from cellpose.io import imread, save_masks

        if self.model is None or self.use_gpu != args.use_gpu:
            print('Loading model...')
            self.use_gpu = args.use_gpu
            self.model = models.CellposeModel(gpu=args.use_gpu)
        
        print(f'[[2/5]] Load image {args.input_image}')
        image = imread(args.input_image)
        
        
        print(args.channel_axis,
                args.z_axis,
                args.diameter,
                args.flow_threshold,
                args.cellprob_threshold,
                args.do_3D,
                args.flow3D_smooth,
                args.min_size,
                args.max_size_fraction,
                args.niter)
        
        for arg in vars(args):
            if isinstance(getattr(args, arg), numbers.Number) and int(getattr(args, arg)) == NONE_VALUE:
                setattr(args, arg, None)

        print(args.channel_axis,
                args.z_axis,
                args.diameter,
                args.flow_threshold,
                args.cellprob_threshold,
                args.do_3D,
                args.flow3D_smooth,
                args.min_size,
                args.max_size_fraction,
                args.niter)
        
        print('[[3/5]] Compute segmentation', image.shape)

        masks, flows, styles = self.model.eval(image, 
                                                channel_axis=args.channel_axis, 
                                                z_axis=args.z_axis, 
                                                diameter=args.diameter,
                                                flow_threshold=args.flow_threshold,
                                                cellprob_threshold=args.cellprob_threshold,
                                                do_3D=args.do_3D,
                                                flow3D_smooth=args.flow3D_smooth,
                                                min_size=args.min_size,
                                                max_size_fraction=args.max_size_fraction,
                                                niter=args.niter)
        
        input_image = Path(args.input_image)

        print(f'[[5/5]] Save segmentation {args.segmentation}')
        # save results as png
        save_masks(image, masks, flows, input_image)
        output_mask = input_image.parent / f'{input_image.stem}_cp_masks.png'
        if output_mask.exists():
            if args.segmentation.exists(): args.segmentation.unlink()
            shutil.move(output_mask, args.segmentation)
            print(f'Saved out: {args.segmentation}')
        else:
            print('Segmentation was not generated because no masks were found.')

