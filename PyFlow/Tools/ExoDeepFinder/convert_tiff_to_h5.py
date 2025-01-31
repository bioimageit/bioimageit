import subprocess
from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):
    
    name = "Convert tiff to h5"
    description = "Convert tiff frames to h5 movie."
    inputs = [
            dict(
                names = ['-t', '--tiff'],
                help = 'Path to the input movie folder. It must contain one tiff file per frame, their names must end with the frame number.',
                default = None,
                type = Path,
                autoColumn = True,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output'],
                help = 'Output path to the h5 file.',
                default = '[workflow_folder]/dataset/{tiff.name}/movie.h5',
                type = Path,
                autoIncrement = False,
            ),
    ]
    
    def processData(self, args):
        print(f'Convert {args.tiff} to {args.output}')
        # Never use --make_subfolder in edf_convert_tiff_to_h5 since we do not want to modify the input folder
        completedProcess = subprocess.run(['edf_convert_tiff_to_h5', '-t', args.tiff, '-o', args.output])
        if completedProcess.returncode != 0: return completedProcess
        # Symlink the tiff folder
        tiffLink = (args.output.parent.resolve() / 'tiff')
        if tiffLink.exists():
            tiffLink.unlink()
        tiffLink.symlink_to(args.tiff, True)
        return completedProcess

