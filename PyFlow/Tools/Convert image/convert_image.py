import subprocess
import platform
from pathlib import Path

class Tool:

    categories = ['Format conversion']
    # dependencies = dict(conda=['bioconda::bftools'], pip=[])
    dependencies = dict(conda=['conda-forge::openjdk=11'], pip=[])
    additionalInstallCommands = dict(all=[], 
                                     windows=[f'Set-Location -Path "{Path(__file__).parent.resolve()}"',
                                              f'Invoke-WebRequest -URI https://downloads.openmicroscopy.org/bio-formats/8.0.1/artifacts/bftools.zip -OutFile bftools.zip',
                                              f'Expand-Archive -Force bftools.zip',
                                              f'Remove-Item bftools.zip'],
                                     linux=[f'cd {Path(__file__).parent.resolve()}',
                                            'wget https://downloads.openmicroscopy.org/bio-formats/8.0.1/artifacts/bftools.zip',
                                            'unzip -o bftools.zip',
                                            'rm bftools.zip'], 
                                     mac=[f'cd {Path(__file__).parent.resolve()}',
                                            'wget https://downloads.openmicroscopy.org/bio-formats/8.0.1/artifacts/bftools.zip',
                                            'unzip -o bftools.zip',
                                            'rm bftools.zip'])
    environment = 'bftools'
    test = ['--input_image', 'img02.png', '--overwrite', '--output_image', 'img02.tif']
    
    name = "Convert images"
    description = "Convert image file formats. The extension of the output file specifies the file format to use for the conversion. For example, to convert the input image to png and keep the input name, use \"{input_image.stem}.png\""
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
                name = 'stitch',
                help = 'Stitch input files with similar names.',
                default = False,
                type = 'bool',
            ),
            dict(
                name = 'separate',
                help = 'Split RGB images into separate channels.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'merge',
                help = 'Combine separate channels into RGB image.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'expand',
                help = 'Expand indexed color to RGB.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'bigtiff',
                help = 'Force BigTIFF files to be written.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'nobigtiff',
                help = 'Do not automatically switch to BigTIFF.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'compression',
                help = 'Specify the codec to use when saving images.',
                default = '',
                choices = ['', 'Uncompressed', 'LZW', 'JPEG-2000', 'JPEG-2000 Lossy', 'JPEG', 'zlib'],
                type = 'str',
                advanced = True,
            ),
            dict(
                name = 'series',
                help = 'Specify which image series to convert.',
                default = None,
                type = 'int',
                advanced = True,
            ),
            dict(
                name = 'noflat',
                help = 'Do not flatten subresolutions.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'cache',
                help = 'Cache the initialized reader.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = '--cache-dir',
                help = 'Use the specified directory to store the cached initialized reader. If unspecified, the cached reader will be stored under the same folder as the image file.',
                default = None,
                type = 'Path',
                advanced = True,
            ),
            dict(
                name = '--no-sas',
                help = 'Do not preserve the OME-XML StructuredAnnotation elements.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'map',
                help = 'Specify file on disk to which name should be mapped.',
                default = None,
                type = 'Path',
                advanced = True,
            ),
            dict(
                name = 'range',
                help = 'Specify the range of planes to convert. Must be of the form MIN,MAX where MIN is the first plane index and MAX is the last plane index. For example 0,5 will only convert planes 0 to 5. Default will convert every planes.',
                default = None,
                type = 'str',
                advanced = True,
            ),
            dict(
                name = 'nogroup',
                help = 'Force multi-file datasets to be read as individual files.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'nolookup',
                help = 'Disable the conversion of lookup tables.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'autoscale',
                help = 'Automatically adjust brightness and contrast before converting; this may mean that the original pixel values are not preserved.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'overwrite',
                help = 'Always overwrite the output file, if it already exists.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'nooverwrite',
                help = 'Never overwrite the output file, if it already exists.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'crop',
                help = 'Crop images before converting. Must be in the form x,y,w,h.',
                default = None,
                type = 'str',
                advanced = True,
            ),
            dict(
                name = 'channel',
                help = 'Only convert the specified channel (indexed from 0).',
                default = None,
                type = 'int',
                advanced = True,
            ),
            dict(
                name = 'z',
                help = 'Only convert the specified Z section (indexed from 0).',
                default = None,
                type = 'int',
                advanced = True,
            ),
            dict(
                name = 'timepoint',
                help = 'Only convert the specified timepoint (indexed from 0).',
                default = None,
                type = 'int',
                advanced = True,
            ),
            dict(
                name = 'padded',
                help = 'Filename indexes for series, z, c and t will be zero padded.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'novalid',
                help = 'Will not validate the OME-XML for the output file.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'validate',
                help = 'Will validate the generated OME-XML for the output file.',
                default = False,
                type = 'bool',
                advanced = True,
            ),
            dict(
                name = 'tilex',
                help = 'Image will be converted one tile at a time using the given tile width.',
                default = None,
                type = 'int',
                advanced = True,
            ),
            dict(
                name = 'tiley',
                help = 'Image will be converted one tile at a time using the given tile height.',
                default = None,
                type = 'int',
                advanced = True,
            ),
            dict(
                name = '--pyramid-scale',
                help = 'Generates a pyramid image with each subsequent resolution level divided by scale.',
                default = None,
                type = 'int',
                advanced = True,
            ),
            dict(
                name = '--pyramid-resolutions',
                help = 'Generates a pyramid image with the given number of resolution levels.',
                default = None,
                type = 'int',
                advanced = True,
            ),
    ]
    outputs = [
            dict(
                name = 'output_image',
                shortname = 'o',
                help = 'The output image.',
                default = '{input_image.stem}.ome.tiff',
                type = 'Path',
            ),
    ]
    
    def processData(self, args):
        if not args.input_image.exists():
            raise Exception(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Convert image {args.input_image}')

        argumentList = []
        # Set boolean options
        for key, value in args.__dict__.items():
            if isinstance(value, bool) and value:
                argumentList += [f'-{key}']
        
        # Set options which must be passed as is
        for option in ['compression', 'series', 'cache_dir', 'map', 'crop', 'channel', 'z', 'timepoint', 'tilex', 'tiley', 'pyramid_scale', 'pyramid_resolutions']:
            value = getattr(args, option)
            if option == 'compression' and value == '': continue
            if value is not None:
                # argumentList += [f'-{option}'.replace('_', '-'), value if option not in ['cache_dir', 'map'] else f'"{value}"']
                argumentList += [f'-{option}'.replace('_', '-'), value]

        # Parse and set the range option
        if args.range is not None:
            rangeIndices = args.range.split(',')
            if len(rangeIndices)!=2:
                raise Exception('Range must be of the form MIN,MAX')
            argumentList += ['-range', rangeIndices[0], rangeIndices[1]]
        
        # argumentList += [f'"{args.input_image}"', f'"{args.output_image}"']
        argumentList += [args.input_image, args.output_image]
        parent = Path(__file__).parent.resolve()
        command = [str(parent / 'bfconvert')] if platform.system() != 'Windows' else [str(parent / 'bftools/bftools/bfconvert.bat')]
        command += [str(c) for c in argumentList]
        print('command:')
        print(command)
        subprocess.run(command, check=True)

