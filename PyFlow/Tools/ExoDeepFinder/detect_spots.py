import subprocess
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict(python='3.10.14', conda=['bioimageit::atlas'], pip=['scikit-learn==1.3.2', 'scikit-image==0.22.0', 'h5py==3.11.0', 'mrcfile==1.4.3', 'matplotlib==3.8.1', 'pillow==10.3.0'], pip_no_deps=['exodeepfinder==0.3.13'])
    environment = 'exodeepfinder-atlas'
    
    name = "Detect spots"
    description = "Generate annotations from a segmentation."
    inputs = [
            dict(
                names = ['-mf', '--movie_folder'],
                help = 'Input folder containing the movie files (a least a tiff folder containing the movie frames).',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['-t', '--tiff'],
                help = 'Path to the folder containing the tiff frames, relative to --movie_folder.',
                default = 'tiff/',
                type = Path,
            ),
            dict(
                names = ['-aa', '--atlas_args'],
                help = 'Additional atlas arguments.',
                default = '-rad 21 -pval 0.001 -arealim 3',
                type = str,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output'],
                help = 'Output segmentation.',
                default = '[workflow_folder]/dataset/{movie_folder.name}/detector_segmentation.h5',
                type = Path,
                autoIncrement = False,
            ),
    ]
    
    def processData(self, args):
        print(f'Detect spots in {args.movie_folder / args.tiff}')
        commandArgs = ['edf_detect_spots_with_atlas', '-m', args.movie_folder / args.tiff, '-o', args.output, '-aa', args.atlas_args]
        subprocess.run([str(arg) for arg in commandArgs], check=True)

