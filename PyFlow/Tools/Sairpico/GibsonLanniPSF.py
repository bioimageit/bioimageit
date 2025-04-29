from pathlib import Path
import subprocess
class Tool:

    categories = ['PSF']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "GibsonLanniPSF"
    description = "3D Gibson-Lanni PSF."
    inputs = [
            dict(
                name = 'width',
                help = 'Image width',
                default = 256,
                type = 'int',
            ),
            dict(
                name = 'height',
                help = 'Image height',
                default = 256,
                type = 'int',
            ),
            dict(
                name = 'depth',
                help = 'Image depth',
                default = 20,
                type = 'int',
            ),
            dict(
                name = 'wavelength',
                help = 'Excitation wavelength (nm)',
                default = 610,
                type = 'float',
            ),
            dict(
                name = 'psxy',
                help = 'Pixel size in XY (nm)',
                default = 100,
                type = 'float',
            ),
            dict(
                name = 'psz',
                help = 'Pixel size in Z (nm)',
                default = 250,
                type = 'float',
            ),
            dict(
                name = 'na',
                help = 'Numerical Aperture',
                default = 1.4,
                type = 'float',
            ),
            dict(
                name = 'ni',
                help = 'Refractive index immersion',
                default = 1.5,
                type = 'float',
            ),
            dict(
                name = 'ns',
                help = 'Refractive index sample',
                default = 1.3,
                type = 'float',
            ),
            dict(
                name = 'ti',
                help = 'Working distance (mum)',
                default = 150,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'The output Gibson-Lanni PSF image path.',
                default = 'psf_gibsonlanni.tiff',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        print('Generate Gibson-Lanni PSF')
        
        commandArgs = [
            'simggibsonlannipsf',
            '-o', args.output,
            '-width', args.width,
            '-height', args.height,
            '-depth', args.depth,
            '-wavelength', args.wavelength,
            '-psxy', args.psxy,
            '-psz', args.psz,
            '-na', args.na,
            '-ni', args.ni,
            '-ns', args.ns,
            '-ti', args.ti
        ]
        
        subprocess.run([str(ca) for ca in commandArgs], check=True)

