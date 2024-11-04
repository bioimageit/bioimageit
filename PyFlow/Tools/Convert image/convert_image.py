import subprocess
import sys
import argparse
from pathlib import Path

class Tool:

    categories = ['Format conversion']
    dependencies = dict(conda=['bioconda::bftools'], pip=[])
    environment = 'bftools'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Convert images", description='Convert image file formats. The extension of the output file specifies the file format to use for the conversion. For example, to convert the input image to png and keep the input name, use "{input_image.stem}.png"', formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-i', '--input_image', help='The input image path.', required=True, type=Path, metavar='input_image')
        advanced_parser = inputs_parser.add_argument_group('advanced')
        advanced_parser.add_argument('--stitch', help='Stitch input files with similar names.', action='store_true')
        advanced_parser.add_argument('--separate', help='Split RGB images into separate channels.', action='store_true')
        advanced_parser.add_argument('--merge', help='Combine separate channels into RGB image.', action='store_true')
        advanced_parser.add_argument('--expand', help='Expand indexed color to RGB.', action='store_true')
        advanced_parser.add_argument('--bigtiff', help='Force BigTIFF files to be written.', action='store_true')
        advanced_parser.add_argument('--nobigtiff', help='Do not automatically switch to BigTIFF.', action='store_true')
        advanced_parser.add_argument('--compression', help='Specify the codec to use when saving images.', choices=['', 'Uncompressed', 'LZW', 'JPEG-2000', 'JPEG-2000 Lossy', 'JPEG', 'zlib'], default='')
        advanced_parser.add_argument('--series', help='Specify which image series to convert.', type=int, default=None)
        advanced_parser.add_argument('--noflat', help='Do not flatten subresolutions.', action='store_true')
        advanced_parser.add_argument('--cache', help='Cache the initialized reader.', action='store_true')
        advanced_parser.add_argument('--cache-dir', help='Use the specified directory to store the cached initialized reader. If unspecified, the cached reader will be stored under the same folder as the image file.', type=Path)
        advanced_parser.add_argument('--no-sas', help='Do not preserve the OME-XML StructuredAnnotation elements.', action='store_true')
        advanced_parser.add_argument('--map', help='Specify file on disk to which name should be mapped.', type=Path)
        advanced_parser.add_argument('--range', help='Specify the range of planes to convert. Must be of the form MIN,MAX where MIN is the first plane index and MAX is the last plane index. For example 0,5 will only convert planes 0 to 5. Default will convert every planes.', type=str)
        advanced_parser.add_argument('--nogroup', help='Force multi-file datasets to be read as individual files.', action='store_true')
        advanced_parser.add_argument('--nolookup', help='Disable the conversion of lookup tables.', action='store_true')
        advanced_parser.add_argument('--autoscale', help='Automatically adjust brightness and contrast before converting; this may mean that the original pixel values are not preserved.', action='store_true')
        advanced_parser.add_argument('--overwrite', help='Always overwrite the output file, if it already exists.', action='store_true')
        advanced_parser.add_argument('--nooverwrite', help='Never overwrite the output file, if it already exists.', action='store_true')
        advanced_parser.add_argument('--crop', help='Crop images before converting. Must be in the form x,y,w,h.', type=str)
        advanced_parser.add_argument('--channel', help='Only convert the specified channel (indexed from 0).', type=int)
        advanced_parser.add_argument('--z', help='Only convert the specified Z section (indexed from 0).', type=int)
        advanced_parser.add_argument('--timepoint', help='Only convert the specified timepoint (indexed from 0).', type=int)
        advanced_parser.add_argument('--padded', help='Filename indexes for series, z, c and t will be zero padded.', action='store_true')
        advanced_parser.add_argument('--novalid', help='Will not validate the OME-XML for the output file.', action='store_true')
        advanced_parser.add_argument('--validate', help='Will validate the generated OME-XML for the output file.', action='store_true')
        advanced_parser.add_argument('--tilex', help='Image will be converted one tile at a time using the given tile width.', type=int)
        advanced_parser.add_argument('--tiley', help='Image will be converted one tile at a time using the given tile height.', type=int)
        advanced_parser.add_argument('--pyramid-scale', help='Generates a pyramid image with each subsequent resolution level divided by scale.', type=int)
        advanced_parser.add_argument('--pyramid-resolutions', help='Generates a pyramid image with the given number of resolution levels.', type=int)
        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output_image', help='The output image.', default='{input_image.stem}.ome.tiff', type=Path)
        return parser, dict( input_image = dict(autoColumn=True) )
    
    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        if not args.input_image.exists():
            sys.exit(f'Error: input image {args.input_image} does not exist.')

        print(f'[[1/1]] Convert image {args.input_image}')
        command = ['bfconvert']
        
        # Set boolean options
        for key, value in args.__dict__.items():
            if isinstance(value, bool) and value:
                command += [f'-{key}']
        
        # Set options which must be passed as is
        for option in ['compression', 'series', 'cache_dir', 'map', 'crop', 'channel', 'z', 'timepoint', 'tilex', 'tiley', 'pyramid_scale', 'pyramid_resolutions']:
            if option == 'compression' and getattr(args, option) == '': continue
            if getattr(args, option) is not None:
                command += [f'-{option}'.replace('_', '-'), getattr(args, option)]

        # Parse and set the range option
        if args.range is not None:
            rangeIndices = args.range.split(',')
            if len(rangeIndices)!=2:
                raise Exception('Range must be of the form MIN,MAX')
            command += ['-range', rangeIndices[0], rangeIndices[1]]
        
        command += [args.input_image, args.output_image]
        return subprocess.run([str(c) for c in command])

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)