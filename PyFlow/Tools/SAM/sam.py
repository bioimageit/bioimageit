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
            mask_generator = SAM2AutomaticMaskGenerator(predictor)
            image = Image.open(args.image)
            image = np.array(image.convert("RGB"))
            masks = mask_generator.generate(image)
            segmentation = Image.fromarray(self.createSegmentation(masks))
            segmentation.save(args.segmentation)
        return