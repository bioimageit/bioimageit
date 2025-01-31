from pathlib import Path
import subprocess

class Tool:
    categories = ['Detection']
    dependencies = dict(python='3.9', conda=['bioimageit::hotspot==1.0.0|osx-64,osx-arm64,win-64,linux-64'], pip=[])
    environment = 'hotspot'
    test = ['--input_image', 'arbaGFPProjDebruiteNorm.tif', '--output', 'result.tif']
    
    name = "Hotspot Detection"
    description = "Hotspot detection in microscopy images."
    inputs = [
            dict(
                names = ['--input_image'],
                help = 'Input Image',
                required = True,
                type = Path,
                autoColumn = True,
            ),
            dict(
                names = ['--patch_size'],
                help = 'Patch size (radius)',
                default = 3,
                type = int,
            ),
            dict(
                names = ['--neighborhood_size'],
                help = 'Neighborhood size (radius)',
                default = 5,
                type = int,
            ),
            dict(
                names = ['--p_value'],
                help = 'p-value for false alarm',
                default = 0.2,
                type = float,
            ),
    ]
    outputs = [
            dict(
                names = ['-o', '--output'],
                help = 'Output path for the detected hotspots image.',
                default = '{input_image.stem}_hotspot{input_image.exts}',
                type = Path,
            ),
    ]
    
    def processData(self, args):
        print("Running hotspot detection on the image")
        commandArgs = [
            'hotSpotDetection', '-i', str(args.input_image), '-o', str(args.output),
            '-m', str(args.patch_size), '-n', str(args.neighborhood_size), '-pv', str(args.p_value)
        ]
        return subprocess.run(commandArgs)

