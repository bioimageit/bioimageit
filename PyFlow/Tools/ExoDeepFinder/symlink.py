from pathlib import Path
from .exodeepfinder_tool import ExoDeepFinderTool

class Tool(ExoDeepFinderTool):

    dependencies = dict(pip=[])
    
    name = "Symlink"
    description = "Symlink files to the workflow folder."
    inputs = [
            dict(
                name = 'input_movie_folder',
                shortname = 'imf',
                help = 'Path to the input movie folder.',
                default = None,
                type = 'Path',
                autoColumn = True,
            ),
            dict(
                name = 'movie',
                shortname = 'm',
                help = 'Input movie.',
                default = 'movie.h5',
                type = 'Path',
            ),
    ]
    outputs = [
            dict(
                name = 'output_movie_folder',
                shortname = 'omf',
                help = 'Path to the output movie folder.',
                default = '[workflow_folder]/dataset/{input_movie_folder.name}',
                type = 'Path',
                autoIncrement = False,
            ),
            dict(
                name = 'output_movie',
                shortname = 'om',
                help = 'Path to the symlinked movie.',
                default = '[workflow_folder]/dataset/{input_movie_folder.name}/movie.h5',
                type = 'Path',
                autoIncrement = False,
            ),
    ]
    
    def processData(self, args):
        print(f'Symlink {args.input_movie_folder} to {args.output_movie_folder}')
        args.output_movie_folder.mkdir(exist_ok=True, parents=True)
        for file in sorted(list(args.input_movie_folder.iterdir())):
            link = args.output_movie_folder / file.name
            if link.is_symlink():
                link.unlink()
            print(f'   symlink {link} to {file}')
            link.symlink_to(file, file.is_dir())

