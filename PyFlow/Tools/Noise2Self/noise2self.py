
class Tool:

    categories = ['Denoising']
    dependencies = dict(conda=['pytorch::pytorch', 'pytorch::torchvision'], pip=['matplotlib', 'noise2self'])
    environment = 'noise2self'
    
    name = "Noise2Self"
    description = "Noise2Self - Learning Denoising from Single Noisy Images."
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
                default = 'Unet',
                choices = ['BabyUnet', 'DnCNN', 'SingleConvolution', 'Unet'],
                type = 'str',
            ),
            dict(
                name = 'num_of_layers',
                help = 'Number of layers in the convolutional network',
                default = None,
                type = 'int',
            ),
            dict(
                name = 'masker_width',
                help = 'Width of the mask',
                default = None,
                type = 'int',
            ),
            dict(
                name = 'iterations',
                help = 'Number of iterations during training',
                default = None,
                type = 'int',
            ),
    ]
    outputs = [
            dict(
                name = 'out',
                shortname = 'o',
                help = 'The output denoised image path.',
                default = '{input_image.stem}_denoised{input_image.exts}',
                type = 'Path',
            ),
    ]
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/4]] Load libraries and image {input_image}')

        import torch
        import numpy as np
        from skimage import img_as_float
        from skimage.metrics import peak_signal_noise_ratio
        from skimage.io import imread, imsave
        from noise2self.mask import Masker
        from noise2self.models.dncnn import DnCNN
        from noise2self.models.babyunet import BabyUnet
        from noise2self.models.singleconv import SingleConvolution
        from noise2self.models.unet import Unet
        from torch.nn import MSELoss
        from torch.optim import Adam

        input_image = str(args.input_image)
        image = imread(input_image)
        image = img_as_float(image)
        num_of_layers = args.num_of_layers
        masker_width = args.masker_width
        iterations = args.iterations
        output_image = args.out

        print("Input image : ", input_image)
        print("Image shape : ", image.shape)
        print("Number of layers : ", num_of_layers)
        print("Interations : ", iterations)

        print(f'[[2/4]] Mask and create model')

        noisy = torch.Tensor(image[np.newaxis, np.newaxis])

        device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        masker = Masker(width = masker_width, mode='interpolate')

        torch.manual_seed(3)

        if args.model == "DnCNN":
            model = DnCNN(1, num_of_layers = num_of_layers)
        if args.model == "BabyUnet":
            model = BabyUnet(1, num_of_layers = num_of_layers)
        if args.model == "SingleConvolution":
            model = SingleConvolution(1, num_of_layers = num_of_layers)
        if args.model == "Unet":
            model = Unet(1, num_of_layers = num_of_layers)


        sum(p.numel() for p in model.parameters() if p.requires_grad)
        image.ravel().shape

        print(f'[[3/4]] Train model')

        loss_function = MSELoss()
        optimizer = Adam(model.parameters(), lr=0.01)
        model = model.to(device)
        noisy = noisy.to(device)

        losses = []
        val_losses = []
        best_images = []
        best_val_loss = 1

        for i in range(iterations):
            model.train()
            
            net_input, mask = masker.mask(noisy, i % (masker.n_masks - 1))
            net_output = model(net_input)
            
            loss = loss_function(net_output*mask, noisy*mask)
            optimizer.zero_grad()
        
            loss.backward()
            
            optimizer.step()
            
            if i % 10 == 0:
                losses.append(loss.item())
                model.eval()
                
                net_input, mask = masker.mask(noisy, masker.n_masks - 1)
                net_output = model(net_input)
            
                val_loss = loss_function(net_output*mask, noisy*mask)
                
                val_losses.append(val_loss.item())
                
                print("(", i, ") Loss: \t", round(loss.item(), 5), "\tVal Loss: \t", round(val_loss.item(), 5))

                if val_loss < best_val_loss:
                    best_val_loss = val_loss
                    denoised = np.clip(model(noisy).detach().cpu().numpy()[0, 0], 0, 1).astype(np.float64)
                    best_psnr = peak_signal_noise_ratio(denoised, image)
                    best_images.append(denoised)
                    print("\tModel PSNR: ", np.round(best_psnr, 2))

        denoised = best_images[-1]
        peak_signal_noise_ratio(denoised, image)

        print(f'[[4/4]] Save denoised image {output_image}')
        
        imsave(output_image, denoised)

