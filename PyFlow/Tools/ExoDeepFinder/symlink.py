import argparse
from pathlib import Path

class Tool:

    categories = ['Detection', 'ExoDeepFinder']
    dependencies = dict()
    environment = 'bioimageit'

    @staticmethod
    def getArgumentParser():
        parser = argparse.ArgumentParser("Symlink", description="Symlink files to workflow folder.", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
        inputs_parser = parser.add_argument_group('inputs')
        inputs_parser.add_argument('-m', '--movie_folder', help='Path to the input movie folder.', default=None, type=Path)

        outputs_parser = parser.add_argument_group('outputs')
        outputs_parser.add_argument('-o', '--output', help='Path to the output movie folder.', default='[workflow_folder]/dataset/{movie_folder.name}', type=Path)

        options = dict( movie_folder = dict(autoColumn=True), output = dict(autoIncrement=False) )
        
        return parser, options

    def processDataFrame(self, dataFrame, argsList):
        return dataFrame

    def processData(self, args):
        print(f'Symlink {args.movie_folder} to {args.output}')
        (args.output / args.movie_folder.name).mkdir(exist_ok=True, parents=True)
        for file in sorted(list(args.movie_folder.iterdir())):
            link = args.output / file.name
            if link.exists():
                link.unlink()
            print(f'   symlink {link} to {file}')
            link.symlink_to(file, file.is_dir())

if __name__ == '__main__':
    tool = Tool()
    parser, _ = tool.getArgumentParser()
    args = parser.parse_args()
    tool.initialize(args)
    tool.processData(args)
