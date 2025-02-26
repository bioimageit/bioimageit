import subprocess
class Tool:

    categories = ['PSF']
    dependencies = dict(python='3.9', conda=['sylvainprigent::simglib=0.1.2|osx-64,win-64,linux-64'], pip=[])
    environment = 'simglib'
    
    name = "PSF"
    description = "3D Gaussian PSF."
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
                name = 'sigmaxy',
                help = 'PSF width and height',
                default = 1.0,
                type = 'float',
            ),
            dict(
                name = 'sigmaz',
                help = 'PSF depth',
                default = 1.0,
                type = 'float',
            ),
    ]
    outputs = [
            dict(
                name = 'output',
                shortname = 'o',
                help = 'The output 3D Gaussian PSF path.',
                default = 'psf.tiff',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        print('Generate PSF')
        commandArgs = ['simggaussian3dpsf', '-o', args.output, '-sigmaxy', args.sigmaxy, '-sigmaz', args.sigmaz, '-depth', args.depth, '-height', args.height, '-width', args.width]
        subprocess.run([str(ca) for ca in commandArgs], check=True)
        

