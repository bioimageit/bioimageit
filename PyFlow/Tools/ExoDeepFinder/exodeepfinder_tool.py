class ExoDeepFinderTool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python = '3.10.14', 
                        conda = [], 
                        pip = ['exodeepfinder==0.3.13'], 
                        optional = dict(conda = ['nvidia/label/cuda-12.3.0::cuda-toolkit|win-64,linux-64', 'conda-forge::cudnn|win-64,linux-64']), 
                        viewer = dict(pip = ['napari-exodeepfinder==0.0.11']))
    environment = 'exodeepfinder'