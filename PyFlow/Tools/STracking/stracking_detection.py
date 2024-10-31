import argparse
import os
from pathlib import Path

class Tool:

    categories = ['Tracking', 'Stracking']
    dependencies = dict(python='3.9', conda=[], pip=['bioimageit::stracking==0.1.4|osx-64,win-64,linux-64'])
    environment = 'stracking'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Stracking Detection DoH, LoG and DoG", description="Scientific library track particles in 2D+t and 3D+t images. Detection using Difference of Hessians, Laplacian of Gaussian and Difference of Gaussians.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        
        inputs_parser = parser.add_argument_group('inputs')

        inputs_parser.add_argument("--input_image", type=Path, help="Input Image", required=True)
        inputs_parser.add_argument("--detector_type", type=str, help="Type of Stracking detection, using DoH (Difference of Hessians), LoG (Laplacian of Gaussian) or DoG (Difference of Gaussians)", choices=['DoH', 'LoG', 'DoG'], default='DoH')
        inputs_parser.add_argument("--min_sigma", type=float, help="Minimal sigma value", default=1)
        inputs_parser.add_argument("--max_sigma", type=float, help="Maximal sigma value", default=5)
        inputs_parser.add_argument("--n_sigmas", type=int, help="Number of sigmas (for DoH and LoG)", default=10)
        inputs_parser.add_argument("--threshold", type=float, help="Threshold", default=0.2)
        inputs_parser.add_argument("--ratio", type=float, help="Sigma ratio (for DoG)", default=1.6)
        inputs_parser.add_argument("--overlap", type=float, help="Overlap", default=0.5)
        inputs_parser.add_argument("--log_scale", action='store_true', help="Log scale (for DoH and LoG)")

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument("-o", "--output", help="Output path for the result table.", type=Path, required=True)
        
        return parser, dict(input_image=dict(autoColumn=True))

    def initialize(self, args):
        print('Loading libraries...')
        import numpy as np
        import skimage
        import stracking
        self.np = np
        self.skimage = skimage
        self.stracking = stracking

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def read_txt_movie_list(self, path):
        with open(path, 'r') as file:
            return [line.strip() for line in file]

    def read_movie_txt(self, path):
        parent_dir = os.path.dirname(path)
        frames = self.read_txt_movie_list(path)
        return self.np.array([self.skimage.io.imread(os.path.join(parent_dir, frame)) for frame in frames])

    def processData(self, args):
        print('Running stracking detection with DoH')
        
        if args.detector_type == 'DoH':
            detector = self.stracking.detectors.DoHDetector(min_sigma = args.min_sigma, max_sigma = args.max_sigma, num_sigma = args.n_sigmas, threshold = args.threshold, overlap = args.overlap, log_scale = args.log_scale)
        elif args.detector_type == 'DoG':
            detector = self.stracking.detectors.DoGDetector(min_sigma = args.min_sigma, max_sigma = args.max_sigma, sigma_ratio = args.ratio, threshold = args.threshold, overlap = args.overlap)
        elif args.detector_type == 'LoG':
            detector = self.stracking.detectors.LoGDetector(min_sigma = args.min_sigma, max_sigma = args.max_sigma, num_sigma = args.n_sigmas, threshold = args.threshold, overlap = args.overlap, log_scale = args.log_scale)

        out = detector.run(self.read_movie_txt(args.input_image))
        self.stracking.io.write_particles(args.output, out)

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.processData(args)