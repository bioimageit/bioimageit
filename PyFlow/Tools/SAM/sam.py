import numpy as np

class Tool:

    name = 'Segment Anything Model 2'
    description = 'SAM 2: Segment Anything in Images and Videos.'

    categories = ['Segmentation']
    dependencies = dict(conda=[], pip=['sam2==1.1.0', 'huggingface_hub==0.29.2'])
    environment = 'sam'
    test = []
    
    inputs = [
        dict(
            name = 'image',
            help = 'The input image to segment.',
            required = True,
            type = 'Path',
            autoColumn = True,
        ),
        dict(
            name = 'points_per_side',
            help = ' The number of points to be sampled along one side of the image. The total number of points is points_per_side**2.',
            default = 32,
            type = 'int',
        ),
        dict(
            name = 'pred_iou_thresh',
            help = "A fitering threshold in [0,1], using the model's predicted mask quality.",
            default = 0.8,
            type = 'float',
        ),
        dict(
            name = 'stability_score_thresh',
            help = "A filtering threshold in [0,1], using the stability of the mask under changes to the cutoff used to binarize the model's mask predictions.",
            default = 0.95,
            type = 'float',
        ),
        dict(
            name = 'stability_score_offset',
            help = "The amount to shift the cutoff when calculated the stability score.",
            default = 1.0,
            type = 'float',
        ),
    ]
    outputs = [
        dict(
            name = 'segmentation',
            help = 'The output segmentation.',
            default = '{image.stem}_segmentation{image.exts}',
            type = 'Path',
        ),
    ]

    def createSegmentation(self, annotations):
        image = np.ones((annotations[0]['segmentation'].shape[0], annotations[0]['segmentation'].shape[1]))
        for i, annotation in enumerate(annotations):
            image[annotation['segmentation']] = i+1
        return image

    def processData(self, args):
        import torch
        from PIL import Image
        from sam2.sam2_image_predictor import SAM2ImagePredictor
        from sam2.build_sam import build_sam2_hf
        from sam2.automatic_mask_generator import SAM2AutomaticMaskGenerator

        # predictor = SAM2ImagePredictor.from_pretrained("facebook/sam2.1-hiera-large", device=torch.device('cpu'), apply_postprocessing=False)
        predictor = build_sam2_hf("facebook/sam2.1-hiera-large", device=torch.device('cpu'), apply_postprocessing=False)

        with torch.inference_mode(), torch.autocast("cuda", dtype=torch.bfloat16):
            mask_generator = SAM2AutomaticMaskGenerator(predictor, 
                points_per_side=args.points_per_side,
                pred_iou_thresh=args.pred_iou_thresh,
                stability_score_thresh=args.stability_score_thresh,
                stability_score_offset=args.stability_score_offset)
            image = Image.open(args.image)
            image = np.array(image.convert("RGB"))
            masks = mask_generator.generate(image)
            segmentation = Image.fromarray(self.createSegmentation(masks))
            segmentation.save(args.segmentation)
        return